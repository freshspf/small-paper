from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_job import EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.explanation_annotation import AnnotationRecord
from app.models.llm_model import LLMModel
from app.schemas.annotation import AnnotationUpsert


def list_task_results_for_annotation(db: Session, task_id: int) -> list[EvaluationResult]:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        raise ValueError("Evaluation task not found")

    stmt = (
        select(EvaluationResult)
        .where(EvaluationResult.evaluation_task_id == task_id)
        .options(
            selectinload(EvaluationResult.dataset_record),
            selectinload(EvaluationResult.annotation_records),
        )
        .order_by(EvaluationResult.id.asc())
    )
    return list(db.scalars(stmt))


def upsert_annotation(
    db: Session,
    evaluation_result_id: int,
    payload: AnnotationUpsert,
) -> AnnotationRecord:
    result = db.get(EvaluationResult, evaluation_result_id)
    if result is None:
        raise ValueError("Evaluation result not found")

    stmt = select(AnnotationRecord).where(AnnotationRecord.evaluation_result_id == evaluation_result_id)
    annotation = db.execute(stmt).scalar_one_or_none()

    if annotation is None:
        annotation = AnnotationRecord(
            evaluation_result_id=evaluation_result_id,
            explanation_label=payload.explanation_label,
            annotation_reason=payload.annotation_reason,
        )
    else:
        annotation.explanation_label = payload.explanation_label
        annotation.annotation_reason = payload.annotation_reason

    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


def get_annotation(db: Session, evaluation_result_id: int) -> Optional[AnnotationRecord]:
    stmt = select(AnnotationRecord).where(AnnotationRecord.evaluation_result_id == evaluation_result_id)
    return db.execute(stmt).scalar_one_or_none()


def get_explanation_stats(db: Session) -> dict[str, object]:
    rows = list(
        db.execute(
            select(LLMModel.name, AnnotationRecord.explanation_label)
            .join(EvaluationTask, EvaluationTask.model_id == LLMModel.id)
            .join(EvaluationResult, EvaluationResult.evaluation_task_id == EvaluationTask.id)
            .join(AnnotationRecord, AnnotationRecord.evaluation_result_id == EvaluationResult.id)
        )
    )

    overall = _calculate_explanation_stats([label for _, label in rows])
    by_model: dict[str, dict[str, object]] = {}

    model_names = sorted({model_name for model_name, _ in rows})
    for model_name in model_names:
        labels = [label for current_model_name, label in rows if current_model_name == model_name]
        by_model[model_name] = _calculate_explanation_stats(labels)

    return {
        "overall": overall,
        "by_model": by_model,
    }


def _calculate_explanation_stats(labels: list[object]) -> dict[str, object]:
    total_annotations = len(labels)
    normalized_labels = [
        getattr(label, "value", label)
        for label in labels
    ]
    correct_count = sum(1 for label in normalized_labels if str(label) == "correct")
    hallucination_count = sum(1 for label in normalized_labels if str(label) == "hallucination")

    if total_annotations == 0:
        return {
            "total_annotations": 0,
            "correct_count": 0,
            "hallucination_count": 0,
            "explanation_accuracy": 0.0,
            "hallucination_rate": 0.0,
        }

    explanation_accuracy = correct_count / total_annotations
    hallucination_rate = hallucination_count / total_annotations

    return {
        "total_annotations": total_annotations,
        "correct_count": correct_count,
        "hallucination_count": hallucination_count,
        "explanation_accuracy": round(explanation_accuracy, 4),
        "hallucination_rate": round(hallucination_rate, 4),
    }
