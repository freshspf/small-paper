from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.eval_dataset import EvalDataset
from app.models.evaluation_job import EvaluationTask
from app.models.model_config import ModelConfig
from app.models.prompt_template_config import PromptTemplateConfig
from app.models.stability_eval_task import StabilityEvalTask
from app.services import eval_task_service, explanation_eval_service, stability_eval_service


def get_eval_report(db: Session, task_id: int) -> Optional[dict[str, Any]]:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        return None

    dataset = db.get(EvalDataset, task.datasetId) if task.datasetId else None
    model = db.get(ModelConfig, task.modelId) if task.modelId else None
    prompt = db.get(PromptTemplateConfig, task.promptId) if task.promptId else None
    classification = eval_task_service.calculate_metrics(db, task_id)
    explanation = explanation_eval_service.get_explanation_eval_stats(db, task_id)
    stability_task = _get_latest_stability_task(db, task_id)
    stability = _build_stability_summary(stability_task)

    return {
        "taskInfo": {
            "id": task.id,
            "taskName": task.taskName or task.name or "",
            "datasetName": dataset.datasetName if dataset else None,
            "modelName": model.modelName if model else None,
            "promptName": prompt.templateName if prompt else None,
            "createdTime": task.createdTime,
            "taskStatus": task.taskStatus,
        },
        "classification": {
            "totalCount": task.totalCount or 0,
            "successCount": task.successCount or 0,
            "failCount": task.failCount or 0,
            "accuracy": classification["accuracy"],
            "precision": classification["precision"],
            "recall": classification["recall"],
            "f1": classification["f1"],
        },
        "explanation": explanation,
        "stability": stability,
        "charts": {
            "classification": [
                {"name": "Accuracy", "value": classification["accuracy"]},
                {"name": "Precision", "value": classification["precision"]},
                {"name": "Recall", "value": classification["recall"]},
                {"name": "F1", "value": classification["f1"]},
            ],
            "explanation": [
                {"name": "解释正确率", "value": explanation["explanationAccuracy"]},
                {"name": "幻觉率", "value": explanation["hallucinationRate"]},
            ],
            "stability": [
                {"name": "硬一致性", "value": stability["hardConsistency"] or 0.0},
                {"name": "软一致性", "value": stability["softConsistency"] or 0.0},
            ],
        },
    }


def _get_latest_stability_task(db: Session, task_id: int) -> Optional[StabilityEvalTask]:
    return db.scalar(
        select(StabilityEvalTask)
        .where(StabilityEvalTask.baseTaskId == task_id)
        .order_by(StabilityEvalTask.createdTime.desc(), StabilityEvalTask.id.desc())
        .limit(1)
    )


def _build_stability_summary(task: Optional[StabilityEvalTask]) -> dict[str, Any]:
    if task is None:
        return {
            "hasData": False,
            "stabilityTaskId": None,
            "taskStatus": "none",
            "totalCount": 0,
            "successCount": 0,
            "failCount": 0,
            "hardConsistency": 0.0,
            "softConsistency": 0.0,
        }

    return {
        "hasData": True,
        "stabilityTaskId": task.id,
        "taskStatus": task.taskStatus,
        "totalCount": task.totalCount or 0,
        "successCount": task.successCount or 0,
        "failCount": task.failCount or 0,
        "hardConsistency": float(task.hardConsistency) if task.hardConsistency is not None else 0.0,
        "softConsistency": float(task.softConsistency) if task.softConsistency is not None else 0.0,
    }
