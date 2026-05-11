from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.explanation_eval_record import ExplanationEvalRecord
from app.schemas.explanation_eval import ExplanationEvalUpsert


def list_explanation_eval_items(
    db: Session,
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    annotation_status: Optional[str] = None,
) -> dict[str, Any]:
    _ensure_task_exists(db, task_id)
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    stmt = (
        select(EvaluationResult, ExplanationEvalRecord)
        .outerjoin(
            ExplanationEvalRecord,
            and_(
                ExplanationEvalRecord.taskId == EvaluationResult.taskId,
                ExplanationEvalRecord.resultId == EvaluationResult.id,
            ),
        )
        .where(_correct_result_condition(task_id))
    )
    if annotation_status:
        if annotation_status == "pending":
            stmt = stmt.where(
                (ExplanationEvalRecord.id.is_(None))
                | (ExplanationEvalRecord.annotationStatus == "pending")
            )
        else:
            stmt = stmt.where(ExplanationEvalRecord.annotationStatus == annotation_status)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = list(
        db.execute(
            stmt.order_by(EvaluationResult.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )

    return {
        "records": [_build_item(result, annotation) for result, annotation in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


def get_explanation_eval_detail(db: Session, result_id: int) -> Optional[dict[str, Any]]:
    result = db.get(EvaluationResult, result_id)
    if result is None:
        return None
    if not _is_correct_result(result):
        return None

    annotation = db.scalar(
        select(ExplanationEvalRecord).where(
            ExplanationEvalRecord.taskId == result.taskId,
            ExplanationEvalRecord.resultId == result.id,
        )
    )
    return _build_item(result, annotation)


def upsert_explanation_eval_record(db: Session, payload: ExplanationEvalUpsert) -> ExplanationEvalRecord:
    task = _ensure_task_exists(db, payload.taskId)
    result = db.get(EvaluationResult, payload.resultId)
    if result is None or result.taskId != task.id:
        raise ValueError("评估结果不存在或不属于该任务")
    if not _is_correct_result(result):
        raise ValueError("只有判断正确且执行成功的样本可以进行解释能力标注")

    annotation = db.scalar(
        select(ExplanationEvalRecord).where(
            ExplanationEvalRecord.taskId == payload.taskId,
            ExplanationEvalRecord.resultId == payload.resultId,
        )
    )
    if annotation is None:
        annotation = ExplanationEvalRecord(
            taskId=payload.taskId,
            resultId=payload.resultId,
        )

    annotation.explanationCorrectLabel = payload.explanationCorrectLabel
    annotation.hallucinationLabel = payload.hallucinationLabel
    annotation.annotationRemark = payload.annotationRemark
    annotation.annotationStatus = "completed" if (
        payload.explanationCorrectLabel is not None and payload.hallucinationLabel is not None
    ) else "pending"
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


def get_explanation_eval_stats(db: Session, task_id: int) -> dict[str, Any]:
    _ensure_task_exists(db, task_id)
    correct_case_count = int(
        db.scalar(
            select(func.count()).select_from(EvaluationResult).where(_correct_result_condition(task_id))
        )
        or 0
    )

    correct_annotations = _correct_annotation_select(task_id)
    annotated_count = int(db.scalar(select(func.count()).select_from(correct_annotations.where(ExplanationEvalRecord.annotationStatus == "completed").subquery())) or 0)
    explanation_correct_count = int(db.scalar(select(func.count()).select_from(correct_annotations.where(ExplanationEvalRecord.explanationCorrectLabel == 1).subquery())) or 0)
    hallucination_count = int(db.scalar(select(func.count()).select_from(correct_annotations.where(ExplanationEvalRecord.hallucinationLabel == 1).subquery())) or 0)

    return {
        "correctCaseCount": correct_case_count,
        "annotatedCount": annotated_count,
        "explanationCorrectCount": explanation_correct_count,
        "hallucinationCount": hallucination_count,
        "explanationAccuracy": round(explanation_correct_count / correct_case_count, 4) if correct_case_count else 0.0,
        "hallucinationRate": round(hallucination_count / correct_case_count, 4) if correct_case_count else 0.0,
    }


def build_annotation_read(annotation: ExplanationEvalRecord) -> dict[str, Any]:
    return {
        "id": annotation.id,
        "taskId": annotation.taskId,
        "resultId": annotation.resultId,
        "explanationCorrectLabel": annotation.explanationCorrectLabel,
        "hallucinationLabel": annotation.hallucinationLabel,
        "annotationStatus": annotation.annotationStatus,
        "annotationRemark": annotation.annotationRemark,
        "createdTime": annotation.createdTime,
        "updatedTime": annotation.updatedTime,
    }


def _ensure_task_exists(db: Session, task_id: int) -> EvaluationTask:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        raise ValueError("评估任务不存在")
    return task


def _correct_result_condition(task_id: int):
    return (
        (EvaluationResult.taskId == task_id)
        & (EvaluationResult.runStatus == "success")
        & (EvaluationResult.trueLabel.is_not(None))
        & (EvaluationResult.predictLabel.is_not(None))
        & (EvaluationResult.trueLabel == EvaluationResult.predictLabel)
    )


def _correct_annotation_select(task_id: int):
    return (
        select(ExplanationEvalRecord.id)
        .join(EvaluationResult, EvaluationResult.id == ExplanationEvalRecord.resultId)
        .where(ExplanationEvalRecord.taskId == task_id)
        .where(_correct_result_condition(task_id))
    )


def _is_correct_result(result: EvaluationResult) -> bool:
    return (
        result.runStatus == "success"
        and result.trueLabel is not None
        and result.predictLabel is not None
        and result.trueLabel == result.predictLabel
    )


def _build_item(result: EvaluationResult, annotation: Optional[ExplanationEvalRecord]) -> dict[str, Any]:
    annotation_data = (
        build_annotation_read(annotation)
        if annotation is not None
        else {
            "id": None,
            "taskId": result.taskId or 0,
            "resultId": result.id,
            "explanationCorrectLabel": None,
            "hallucinationLabel": None,
            "annotationStatus": "pending",
            "annotationRemark": None,
            "createdTime": None,
            "updatedTime": None,
        }
    )
    return {
        "resultId": result.id,
        "taskId": result.taskId or 0,
        "axiomType": result.axiomType,
        "axiomText": result.axiomText,
        "trueLabel": result.trueLabel,
        "predictLabel": result.predictLabel,
        "judgmentResult": result.judgmentResult,
        "explanation": result.explanation,
        "rawOutput": result.rawOutput,
        "runStatus": result.runStatus,
        "annotation": annotation_data,
    }
