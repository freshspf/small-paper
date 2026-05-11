from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.eval_dataset_record import EvalDatasetRecord
from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.model_config import ModelConfig
from app.models.prompt_template_config import PromptTemplateConfig
from app.models.stability_eval_record import StabilityEvalRecord
from app.models.stability_eval_task import StabilityEvalTask
from app.services.eval_task_service import parse_model_response
from app.services.model_call_service import call_openai_compatible_model


SUPPORTED_AXIOM_TYPES = ("subClassOf", "subPropertyOf", "domain", "range")

PERTURBATION_TEMPLATES: dict[str, list[str]] = {
    "subClassOf": [
        "{subject} ⊑ {object}",
        "{subject} is a subclass of {object}",
        "Every instance of {subject} is also an instance of {object}",
        "If x is a {subject}, then x is also an {object}",
        "The class {subject} is included in the class {object}",
    ],
    "subPropertyOf": [
        "{subject} ⊑ {object}",
        "{subject} is a subproperty of {object}",
        "If two entities are related by {subject}, they are also related by {object}",
        "If x {subject} y, then x {object} y",
        "The property {subject} is included in the property {object}",
    ],
    "domain": [
        "domain({subject}) = {object}",
        "The domain of {subject} is {object}",
        "If an entity uses the property {subject} as subject, it should belong to {object}",
        "If x {subject} y, then x is an instance of {object}",
        "The subject of property {subject} must belong to class {object}",
    ],
    "range": [
        "range({subject}) = {object}",
        "The range of {subject} is {object}",
        "If an entity appears as the object of {subject}, it should belong to {object}",
        "If x {subject} y, then y is an instance of {object}",
        "The object of property {subject} must belong to class {object}",
    ],
}


def get_perturbation_templates() -> dict[str, list[dict[str, Any]]]:
    return {
        axiom_type: [
            {"templateId": index + 1, "templateText": template}
            for index, template in enumerate(templates)
        ]
        for axiom_type, templates in PERTURBATION_TEMPLATES.items()
    }


def create_stability_eval_task(db: Session, base_task_id: int) -> StabilityEvalTask:
    base_task = db.get(EvaluationTask, base_task_id)
    if base_task is None:
        raise ValueError("原评估任务不存在")
    if base_task.taskStatus not in {"success", "completed"}:
        raise ValueError("只有已完成的评估任务可以进行稳定性评估")

    base_results = _load_base_results(db, base_task_id)
    if not base_results:
        raise ValueError("原评估任务没有可用于稳定性评估的成功结果")

    task = StabilityEvalTask(
        baseTaskId=base_task_id,
        axiomTypeScope=",".join(SUPPORTED_AXIOM_TYPES),
        templateCount=5,
        taskStatus="running",
        totalCount=len(base_results) * 5,
        successCount=0,
        failCount=0,
        hardConsistency=None,
        softConsistency=None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def stop_stability_eval_task(db: Session, stability_task_id: int) -> StabilityEvalTask:
    task = db.get(StabilityEvalTask, stability_task_id)
    if task is None:
        raise ValueError("稳定性评估任务不存在")
    if task.taskStatus not in {"running", "stopping"}:
        raise ValueError("只有评估中的稳定性任务可以停止")

    task.taskStatus = "stopping"
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def run_stability_eval_background(stability_task_id: int) -> None:
    with SessionLocal() as db:
        execute_stability_eval_task(db, stability_task_id)


def execute_stability_eval_task(db: Session, stability_task_id: int) -> None:
    task = db.get(StabilityEvalTask, stability_task_id)
    if task is None:
        return

    base_task = db.get(EvaluationTask, task.baseTaskId)
    if base_task is None:
        _mark_task_failed(db, task, "原评估任务不存在")
        return

    model = db.get(ModelConfig, base_task.modelId) if base_task.modelId else None
    prompt = db.get(PromptTemplateConfig, base_task.promptId) if base_task.promptId else None
    if model is None or prompt is None:
        _mark_task_failed(db, task, "原任务缺少模型配置或提示词模板")
        return

    for record in db.scalars(select(StabilityEvalRecord).where(StabilityEvalRecord.stabilityTaskId == task.id)):
        db.delete(record)
    db.commit()

    base_results = _load_base_results(db, task.baseTaskId)
    success_count = 0
    fail_count = 0
    for result in base_results:
        subject, object_value, context_info = _resolve_subject_object_context(db, result)
        templates = PERTURBATION_TEMPLATES.get(result.axiomType or "", [])
        for template_id, template_text in enumerate(templates, start=1):
            db.refresh(task)
            if task.taskStatus == "stopping":
                task.taskStatus = "stopped"
                db.add(task)
                db.commit()
                return

            variant_id = f"{result.id}_tpl{template_id}"
            perturbed_text = template_text.format(subject=subject, object=object_value)
            run_status = "success"
            error_message = None
            perturbed_predict_label = None

            try:
                prompt_text = render_stability_prompt(prompt.templateContent, perturbed_text, context_info)
                raw_output, _, _ = call_openai_compatible_model(model, prompt_text)
                _, perturbed_predict_label, _ = parse_model_response(raw_output)
                if perturbed_predict_label is None:
                    run_status = "failed"
                    error_message = "模型输出未解析出判断结果"
            except Exception as exc:
                run_status = "failed"
                error_message = str(exc)[:255]

            if run_status == "success":
                success_count += 1
            else:
                fail_count += 1

            consistency_flag = (
                1
                if run_status == "success"
                and result.predictLabel is not None
                and perturbed_predict_label == result.predictLabel
                else 0
            )
            db.add(
                StabilityEvalRecord(
                    stabilityTaskId=task.id,
                    baseTaskId=task.baseTaskId,
                    resultId=result.id,
                    originalId=str(result.id),
                    templateId=template_id,
                    variantId=variant_id,
                    axiomType=result.axiomType or "",
                    originalText=result.axiomText,
                    perturbedText=perturbed_text,
                    contextInfo=context_info,
                    label=result.trueLabel,
                    originalPredictLabel=result.predictLabel,
                    perturbedPredictLabel=perturbed_predict_label,
                    consistencyFlag=consistency_flag,
                    runStatus=run_status,
                    errorMessage=error_message,
                )
            )
            task.successCount = success_count
            task.failCount = fail_count
            db.add(task)
            db.commit()

    hard_consistency, soft_consistency = calculate_consistency(db, task.id)
    task.hardConsistency = Decimal(str(round(hard_consistency, 4)))
    task.softConsistency = Decimal(str(round(soft_consistency, 4)))
    db.refresh(task)
    if task.taskStatus == "stopping":
        task.taskStatus = "stopped"
    else:
        task.taskStatus = "success" if fail_count == 0 else "completed"
    task.successCount = success_count
    task.failCount = fail_count
    db.add(task)
    db.commit()


def list_stability_tasks(db: Session, base_task_id: int) -> list[dict[str, Any]]:
    tasks = list(
        db.scalars(
            select(StabilityEvalTask)
            .where(StabilityEvalTask.baseTaskId == base_task_id)
            .order_by(StabilityEvalTask.createdTime.desc(), StabilityEvalTask.id.desc())
        )
    )
    return [build_task_read(task) for task in tasks]


def get_stability_task_detail(db: Session, stability_task_id: int) -> Optional[dict[str, Any]]:
    task = db.get(StabilityEvalTask, stability_task_id)
    if task is None:
        return None
    return build_task_read(task)


def list_stability_records(db: Session, stability_task_id: int, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(StabilityEvalRecord).where(StabilityEvalRecord.stabilityTaskId == stability_task_id)
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    records = list(
        db.scalars(
            stmt.order_by(StabilityEvalRecord.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "records": [build_record_read(record) for record in records],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


def list_perturbed_dataset(db: Session, stability_task_id: int) -> list[dict[str, Any]]:
    records = list(
        db.scalars(
            select(StabilityEvalRecord)
            .where(StabilityEvalRecord.stabilityTaskId == stability_task_id)
            .order_by(StabilityEvalRecord.originalId.asc(), StabilityEvalRecord.templateId.asc())
        )
    )
    return [
        {
            "original_id": record.originalId,
            "template_id": record.templateId,
            "variant_id": record.variantId,
            "axiom_type": record.axiomType,
            "axiom_text": record.perturbedText,
            "context_info": record.contextInfo,
            "label": record.label,
        }
        for record in records
    ]


def calculate_consistency(db: Session, stability_task_id: int) -> tuple[float, float]:
    records = list(db.scalars(select(StabilityEvalRecord).where(StabilityEvalRecord.stabilityTaskId == stability_task_id)))
    by_original: dict[str, list[StabilityEvalRecord]] = defaultdict(list)
    for record in records:
        by_original[record.originalId].append(record)
    if not by_original:
        return 0.0, 0.0

    hard_ok = 0
    variance_sum = 0.0
    for grouped_records in by_original.values():
        all_success = all(record.runStatus == "success" and record.perturbedPredictLabel is not None for record in grouped_records)
        original_label = grouped_records[0].originalPredictLabel
        if all_success and all(record.perturbedPredictLabel == original_label for record in grouped_records):
            hard_ok += 1

        values = [float(record.perturbedPredictLabel or 0) for record in grouped_records]
        mean_value = sum(values) / len(values)
        variance_sum += sum((value - mean_value) ** 2 for value in values) / len(values)

    return hard_ok / len(by_original), variance_sum / len(by_original)


def render_stability_prompt(template: str, perturbed_text: str, context_info: str) -> str:
    rendered = template
    used_placeholder = False
    replacements = {
        "axiom_text": perturbed_text,
        "context_info": context_info,
    }
    for key, value in replacements.items():
        for placeholder in (f"{{{key}}}", f"{{{key.upper()}}}", f"{{{{{key}}}}}", f"{{{{{key.upper()}}}}}"):
            if placeholder in rendered:
                used_placeholder = True
                rendered = rendered.replace(placeholder, value)

    if not used_placeholder:
        rendered = "\n\n".join([rendered.strip(), "待判断公理：", perturbed_text, "上下文信息：", context_info])
    return rendered


def build_task_read(task: StabilityEvalTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "baseTaskId": task.baseTaskId,
        "axiomTypeScope": task.axiomTypeScope,
        "templateCount": task.templateCount,
        "taskStatus": task.taskStatus,
        "totalCount": task.totalCount,
        "successCount": task.successCount,
        "failCount": task.failCount,
        "hardConsistency": float(task.hardConsistency) if task.hardConsistency is not None else None,
        "softConsistency": float(task.softConsistency) if task.softConsistency is not None else None,
        "remark": task.remark,
        "createdTime": task.createdTime,
        "updatedTime": task.updatedTime,
    }


def build_record_read(record: StabilityEvalRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "stabilityTaskId": record.stabilityTaskId,
        "baseTaskId": record.baseTaskId,
        "resultId": record.resultId,
        "originalId": record.originalId,
        "templateId": record.templateId,
        "variantId": record.variantId,
        "axiomType": record.axiomType,
        "originalText": record.originalText,
        "perturbedText": record.perturbedText,
        "contextInfo": record.contextInfo,
        "label": record.label,
        "originalPredictLabel": record.originalPredictLabel,
        "perturbedPredictLabel": record.perturbedPredictLabel,
        "consistencyFlag": record.consistencyFlag,
        "runStatus": record.runStatus,
        "errorMessage": record.errorMessage,
        "createdTime": record.createdTime,
        "updatedTime": record.updatedTime,
    }


def _load_base_results(db: Session, base_task_id: int) -> list[EvaluationResult]:
    return list(
        db.scalars(
            select(EvaluationResult)
            .where(EvaluationResult.taskId == base_task_id)
            .where(EvaluationResult.runStatus == "success")
            .where(EvaluationResult.axiomType.in_(SUPPORTED_AXIOM_TYPES))
            .order_by(EvaluationResult.id.asc())
        )
    )


def _resolve_subject_object_context(db: Session, result: EvaluationResult) -> tuple[str, str, str]:
    record = db.get(EvalDatasetRecord, result.datasetRecordId) if result.datasetRecordId else None
    if record is not None:
        return record.subject or "", record.object or "", record.contextInfo or ""

    subject, object_value = _parse_subject_object(result.axiomText or "")
    return subject, object_value, ""


def _parse_subject_object(axiom_text: str) -> tuple[str, str]:
    if "⊑" in axiom_text:
        left, right = axiom_text.split("⊑", 1)
        return left.strip(), right.strip()
    match = re.search(r"(?:domain|range)\(([^)]+)\)\s*=\s*(.+)", axiom_text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    parts = re.split(r"\s+", axiom_text.strip())
    if len(parts) >= 3:
        return parts[0], parts[-1]
    return axiom_text.strip(), ""


def _mark_task_failed(db: Session, task: StabilityEvalTask, message: str) -> None:
    task.taskStatus = "failed"
    task.remark = message[:255]
    db.add(task)
    db.commit()
