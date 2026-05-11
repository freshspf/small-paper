from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.eval_dataset import EvalDataset
from app.models.eval_dataset_record import EvalDatasetRecord
from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.explanation_eval_record import ExplanationEvalRecord
from app.models.model_config import ModelConfig
from app.models.prompt_template_config import PromptTemplateConfig
from app.schemas.eval_task import EvalTaskCreate
from app.db.session import SessionLocal
from app.services.model_call_service import call_openai_compatible_model


JUDGMENT_PATTERNS = [
    re.compile(r"判断结果\s*[:：]\s*\[?\s*(正确|错误)\s*\]?", re.IGNORECASE),
    re.compile(r"Judgment Result\s*[:：]\s*\[?\s*(Correct|Incorrect)\]?", re.IGNORECASE),
]
EXPLANATION_PATTERNS = [
    re.compile(r"解释\s*[:：]\s*(.+)", re.DOTALL),
    re.compile(r"Explanation\s*[:：]\s*(.+)", re.IGNORECASE | re.DOTALL),
]


def create_eval_task(db: Session, payload: EvalTaskCreate) -> EvaluationTask:
    dataset = db.get(EvalDataset, payload.datasetId)
    if dataset is None:
        raise ValueError("评测数据集不存在")

    model = db.get(ModelConfig, payload.modelId)
    if model is None:
        raise ValueError("模型配置不存在")
    if model.status != 1:
        raise ValueError("所选模型配置未启用")

    prompt = db.get(PromptTemplateConfig, payload.promptId)
    if prompt is None:
        raise ValueError("提示词模板不存在")
    if prompt.status != 1:
        raise ValueError("所选提示词模板未启用")

    records = list(
        db.scalars(
            select(EvalDatasetRecord)
            .where(EvalDatasetRecord.datasetId == dataset.id)
            .order_by(EvalDatasetRecord.id.asc())
        )
    )
    if not records:
        raise ValueError("所选数据集没有样本记录")

    task = EvaluationTask(
        taskName=payload.taskName.strip(),
        datasetId=dataset.id,
        modelId=model.id,
        promptId=prompt.id,
        taskStatus="pending",
        totalCount=len(records),
        successCount=0,
        failCount=0,
        remark=payload.remark,
        name=payload.taskName.strip(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def start_eval_task(db: Session, task_id: int) -> EvaluationTask:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        raise ValueError("评估任务不存在")
    if task.taskStatus == "running":
        raise ValueError("评估任务正在执行中")

    task.taskStatus = "running"
    task.successCount = 0
    task.failCount = 0
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def stop_eval_task(db: Session, task_id: int) -> EvaluationTask:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        raise ValueError("评估任务不存在")
    if task.taskStatus not in {"running", "stopping"}:
        raise ValueError("只有评估中的任务可以停止")

    task.taskStatus = "stopping"
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def run_eval_task_background(task_id: int) -> None:
    with SessionLocal() as db:
        execute_eval_task(db, task_id)


def execute_eval_task(db: Session, task_id: int) -> None:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        return

    try:
        dataset = db.get(EvalDataset, task.datasetId) if task.datasetId else None
        if dataset is None:
            raise ValueError("评测数据集不存在")

        model = db.get(ModelConfig, task.modelId) if task.modelId else None
        if model is None:
            raise ValueError("模型配置不存在")
        if model.status != 1:
            raise ValueError("所选模型配置未启用")

        prompt = db.get(PromptTemplateConfig, task.promptId) if task.promptId else None
        if prompt is None:
            raise ValueError("提示词模板不存在")
        if prompt.status != 1:
            raise ValueError("所选提示词模板未启用")

        records = list(
            db.scalars(
                select(EvalDatasetRecord)
                .where(EvalDatasetRecord.datasetId == dataset.id)
                .order_by(EvalDatasetRecord.id.asc())
            )
        )
        if not records:
            raise ValueError("所选数据集没有样本记录")

        for annotation in db.scalars(select(ExplanationEvalRecord).where(ExplanationEvalRecord.taskId == task.id)):
            db.delete(annotation)
        for result in db.scalars(select(EvaluationResult).where(EvaluationResult.taskId == task.id)):
            db.delete(result)

        task.taskStatus = "running"
        task.totalCount = len(records)
        task.successCount = 0
        task.failCount = 0
        db.add(task)
        db.commit()
    except Exception as exc:
        task.taskStatus = "failed"
        task.failCount = task.totalCount or 0
        task.remark = _append_error_remark(task.remark, str(exc))
        db.add(task)
        db.commit()
        return

    success_count = 0
    fail_count = 0
    for record in records:
        db.refresh(task)
        if task.taskStatus == "stopping":
            task.taskStatus = "stopped"
            db.add(task)
            db.commit()
            return

        prompt_text = render_prompt(prompt.templateContent, record)
        raw_output = ""
        total_tokens = None
        response_time_ms = None
        predict_label = None
        judgment_result = None
        explanation = None
        run_status = "success"
        error_message = None

        try:
            raw_output, total_tokens, response_time_ms = call_openai_compatible_model(model, prompt_text)
            judgment_result, predict_label, explanation = parse_model_response(raw_output)
            if predict_label is None:
                run_status = "failed"
                error_message = "模型输出未解析出判断结果"
        except Exception as exc:
            run_status = "failed"
            error_message = str(exc)[:255]
            raw_output = f"LLM request failed: {exc}"

        if run_status == "success":
            success_count += 1
        else:
            fail_count += 1

        db.add(
            EvaluationResult(
                taskId=task.id,
                datasetRecordId=record.id,
                axiomType=record.axiomType,
                axiomText=record.axiomText,
                trueLabel=record.label,
                predictLabel=predict_label,
                judgmentResult=judgment_result,
                explanation=explanation,
                rawOutput=raw_output,
                runStatus=run_status,
                errorMessage=error_message,
                raw_response=raw_output,
                raw_output=raw_output,
                response_time_ms=response_time_ms if run_status == "success" else None,
                total_tokens=total_tokens if run_status == "success" else None,
                predicted_label=predict_label,
                judgment_result=judgment_result,
                evaluation_task_id=task.id,
                dataset_record_id=None,
            )
        )
        task.successCount = success_count
        task.failCount = fail_count
        db.add(task)
        db.commit()

    task.successCount = success_count
    task.failCount = fail_count
    db.refresh(task)
    if task.taskStatus == "stopping":
        task.taskStatus = "stopped"
    else:
        task.taskStatus = "success" if fail_count == 0 else "completed"
    db.add(task)
    db.commit()


def list_eval_tasks(db: Session, task_name: Optional[str] = None, task_status: Optional[str] = None) -> list[dict[str, Any]]:
    stmt = select(EvaluationTask)
    if task_name:
        stmt = stmt.where(EvaluationTask.taskName.like(f"%{task_name.strip()}%"))
    if task_status:
        stmt = stmt.where(EvaluationTask.taskStatus == task_status.strip())
    tasks = list(db.scalars(stmt.order_by(EvaluationTask.createdTime.desc(), EvaluationTask.id.desc())))
    return [build_task_read(db, task) for task in tasks]


def get_eval_task_detail(db: Session, task_id: int) -> Optional[dict[str, Any]]:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        return None
    dataset = db.get(EvalDataset, task.datasetId) if task.datasetId else None
    model = db.get(ModelConfig, task.modelId) if task.modelId else None
    prompt = db.get(PromptTemplateConfig, task.promptId) if task.promptId else None
    return {
        "task": build_task_read(db, task),
        "dataset": {
            "id": dataset.id,
            "datasetName": dataset.datasetName,
            "recordCount": dataset.recordCount,
            "fileName": dataset.fileName,
        } if dataset else None,
        "model": {
            "id": model.id,
            "modelName": model.modelName,
            "modelCode": model.modelCode,
        } if model else None,
        "prompt": {
            "id": prompt.id,
            "templateName": prompt.templateName,
            "templateType": prompt.templateType,
        } if prompt else None,
        "metrics": calculate_metrics(db, task_id),
    }


def list_eval_results(
    db: Session,
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    axiom_type: Optional[str] = None,
    true_label: Optional[int] = None,
    predict_label: Optional[int] = None,
    run_status: Optional[str] = None,
) -> dict[str, Any]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(EvaluationResult).where(EvaluationResult.taskId == task_id)
    if axiom_type:
        stmt = stmt.where(EvaluationResult.axiomType == axiom_type.strip())
    if true_label is not None:
        stmt = stmt.where(EvaluationResult.trueLabel == true_label)
    if predict_label is not None:
        stmt = stmt.where(EvaluationResult.predictLabel == predict_label)
    if run_status:
        stmt = stmt.where(EvaluationResult.runStatus == run_status.strip())

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    records = list(db.scalars(stmt.order_by(EvaluationResult.id.asc()).offset((page - 1) * page_size).limit(page_size)))
    return {
        "records": [build_result_read(record) for record in records],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


def delete_eval_task(db: Session, task_id: int) -> bool:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        return False
    for annotation in db.scalars(select(ExplanationEvalRecord).where(ExplanationEvalRecord.taskId == task_id)):
        db.delete(annotation)
    for result in db.scalars(select(EvaluationResult).where(EvaluationResult.taskId == task_id)):
        db.delete(result)
    db.delete(task)
    db.commit()
    return True


def render_prompt(template: str, record: EvalDatasetRecord) -> str:
    replacements = {
        "axiom_text": record.axiomText or "",
        "context_info": record.contextInfo or "",
        "subject": record.subject or "",
        "predicate": record.predicate or "",
        "object": record.object or "",
    }
    rendered = template
    used_placeholder = False
    for key, value in replacements.items():
        for placeholder in (f"{{{key}}}", f"{{{key.upper()}}}", f"{{{{{key}}}}}", f"{{{{{key.upper()}}}}}"):
            if placeholder in rendered:
                used_placeholder = True
                rendered = rendered.replace(placeholder, value)

    if not used_placeholder:
        rendered = "\n\n".join(
            [
                rendered.strip(),
                "待判断公理：",
                replacements["axiom_text"],
                "上下文信息：",
                replacements["context_info"],
            ]
        )
    return rendered


def _append_error_remark(remark: Optional[str], error_message: str) -> str:
    current = (remark or "").strip()
    suffix = f"执行失败：{error_message[:180]}"
    if not current:
        return suffix
    return f"{current}；{suffix}"[:255]


def parse_model_response(raw_output: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    judgment_result = None
    predict_label = None
    explanation = None
    for pattern in JUDGMENT_PATTERNS:
        match = pattern.search(raw_output or "")
        if match:
            value = match.group(1).strip().lower()
            if value in {"正确", "correct"}:
                judgment_result = "正确"
                predict_label = 1
            elif value in {"错误", "incorrect"}:
                judgment_result = "错误"
                predict_label = 0
            break

    for pattern in EXPLANATION_PATTERNS:
        match = pattern.search(raw_output or "")
        if match:
            explanation = match.group(1).strip()
            break
    return judgment_result, predict_label, explanation


def calculate_metrics(db: Session, task_id: int) -> dict[str, Any]:
    rows = list(
        db.execute(
            select(EvaluationResult.trueLabel, EvaluationResult.predictLabel)
            .where(EvaluationResult.taskId == task_id)
            .where(EvaluationResult.trueLabel.is_not(None))
            .where(EvaluationResult.predictLabel.is_not(None))
        )
    )
    tp = fp = tn = fn = 0
    for true_label, predict_label in rows:
        if true_label == 1 and predict_label == 1:
            tp += 1
        elif true_label == 0 and predict_label == 1:
            fp += 1
        elif true_label == 0 and predict_label == 0:
            tn += 1
        elif true_label == 1 and predict_label == 0:
            fn += 1
    total = len(rows)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "evaluatedCount": total,
    }


def build_task_read(db: Session, task: EvaluationTask) -> dict[str, Any]:
    dataset = db.get(EvalDataset, task.datasetId) if task.datasetId else None
    model = db.get(ModelConfig, task.modelId) if task.modelId else None
    prompt = db.get(PromptTemplateConfig, task.promptId) if task.promptId else None
    return {
        "id": task.id,
        "taskName": task.taskName or task.name or "",
        "datasetId": task.datasetId,
        "modelId": task.modelId,
        "promptId": task.promptId,
        "taskStatus": task.taskStatus or "pending",
        "totalCount": task.totalCount or 0,
        "successCount": task.successCount or 0,
        "failCount": task.failCount or 0,
        "remark": task.remark,
        "createdTime": task.createdTime,
        "updatedTime": task.updatedTime,
        "datasetName": dataset.datasetName if dataset else None,
        "modelName": model.modelName if model else None,
        "promptName": prompt.templateName if prompt else None,
    }


def build_result_read(result: EvaluationResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "taskId": result.taskId,
        "datasetRecordId": result.datasetRecordId,
        "axiomType": result.axiomType,
        "axiomText": result.axiomText,
        "trueLabel": result.trueLabel,
        "predictLabel": result.predictLabel,
        "judgmentResult": result.judgmentResult,
        "explanation": result.explanation,
        "rawOutput": result.rawOutput,
        "runStatus": result.runStatus,
        "errorMessage": result.errorMessage,
        "createdTime": result.createdTime,
        "updatedTime": result.updatedTime,
    }
