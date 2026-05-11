from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.evaluation_job import EvaluationJobStatus, EvaluationTask
from app.models.evaluation_result import EvaluationResult
from app.models.llm_model import LLMModel
from app.models.prompt_template import PromptTemplate


JUDGMENT_PATTERNS = [
    re.compile(r"Judgment Result\s*[:：]\s*\[?(Correct|Incorrect)\]?", re.IGNORECASE),
    re.compile(r"判断结果\s*[:：]\s*\[?(正确|错误)\]?"),
]
EXPLANATION_PATTERNS = [
    re.compile(r"Explanation\s*[:：]\s*(.+)", re.IGNORECASE | re.DOTALL),
    re.compile(r"解释\s*[:：]\s*(.+)", re.DOTALL),
]


def list_evaluation_tasks(db: Session) -> list[EvaluationTask]:
    stmt = select(EvaluationTask).order_by(EvaluationTask.created_at.desc())
    return list(db.scalars(stmt))


def get_evaluation_task(db: Session, task_id: int) -> Optional[EvaluationTask]:
    return db.get(EvaluationTask, task_id)


def list_evaluation_results(db: Session, task_id: int, limit: Optional[int] = None) -> list[EvaluationResult]:
    stmt = (
        select(EvaluationResult)
        .where(EvaluationResult.evaluation_task_id == task_id)
        .order_by(EvaluationResult.id.asc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def get_evaluation_metrics(db: Session, task_id: int) -> dict[str, object]:
    task = db.get(EvaluationTask, task_id)
    if task is None:
        raise ValueError("Evaluation task not found")

    rows = list(
        db.execute(
            select(
                DatasetRecord.axiom_type,
                DatasetRecord.label,
                EvaluationResult.predicted_label,
            )
            .join(EvaluationResult, EvaluationResult.dataset_record_id == DatasetRecord.id)
            .where(EvaluationResult.evaluation_task_id == task_id)
            .order_by(EvaluationResult.id.asc())
        )
    )

    valid_rows = [
        {
            "axiom_type": axiom_type,
            "true_label": true_label,
            "predicted_label": predicted_label,
        }
        for axiom_type, true_label, predicted_label in rows
        if true_label is not None and predicted_label is not None
    ]

    overall = _calculate_metrics(valid_rows)
    by_axiom_type: dict[str, dict[str, object]] = {}

    axiom_types = sorted({row["axiom_type"] for row in valid_rows})
    for axiom_type in axiom_types:
        axiom_rows = [row for row in valid_rows if row["axiom_type"] == axiom_type]
        by_axiom_type[axiom_type] = _calculate_metrics(axiom_rows)

    return {
        "overall": overall,
        "by_axiom_type": by_axiom_type,
    }


def run_live_evaluation(
    db: Session,
    dataset_id: int,
    model_id: int,
    prompt_template_id: int,
) -> tuple[EvaluationTask, list[EvaluationResult]]:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise ValueError("Dataset not found")

    model = db.get(LLMModel, model_id)
    if model is None:
        raise ValueError("Model not found")

    prompt_template = db.get(PromptTemplate, prompt_template_id)
    if prompt_template is None:
        raise ValueError("Prompt template not found")

    records = list(
        db.scalars(
            select(DatasetRecord)
            .where(DatasetRecord.dataset_id == dataset_id)
            .order_by(DatasetRecord.id.asc())
        )
    )
    if not records:
        raise ValueError("Dataset has no records")

    task = EvaluationTask(
        dataset_id=dataset_id,
        model_id=model_id,
        prompt_template_id=prompt_template_id,
        name=f"{dataset.name} / {model.name} / {prompt_template.name}",
        status=EvaluationJobStatus.RUNNING,
        started_at=_now_str(),
        taskName=f"{dataset.name} / {model.name} / {prompt_template.name}",
        taskStatus=EvaluationJobStatus.RUNNING.value,
        totalCount=len(records),
        successCount=0,
        failCount=0,
    )
    db.add(task)
    db.flush()

    created_results: list[EvaluationResult] = []

    for record in records:
        prompt = render_prompt(prompt_template.content, record.axiom_text, record.context_info)
        try:
            raw_response, total_tokens, response_time_ms = call_openai_compatible_model(
                base_url=model.base_url,
                api_key=model.api_key,
                model_name=model.model_name,
                prompt=prompt,
            )
            run_status = "success"
            error_message = None
        except Exception as exc:
            raw_response = f"LLM request failed: {exc}"
            total_tokens = None
            response_time_ms = None
            run_status = "failed"
            error_message = str(exc)[:255]

        judgment_result, predicted_label, explanation = parse_model_response(raw_response)

        result = EvaluationResult(
            evaluation_task_id=task.id,
            dataset_record_id=record.id,
            taskId=task.id,
            datasetRecordId=record.id,
            axiomType=record.axiom_type,
            axiomText=record.axiom_text,
            trueLabel=record.label,
            predictLabel=predicted_label,
            predicted_label=predicted_label,
            judgmentResult=judgment_result,
            judgment_result=judgment_result,
            explanation=explanation,
            rawOutput=raw_response,
            runStatus=run_status,
            errorMessage=error_message,
            raw_response=raw_response,
            raw_output=raw_response,
            response_time_ms=response_time_ms,
            total_tokens=total_tokens,
        )
        db.add(result)
        created_results.append(result)

    task.status = EvaluationJobStatus.SUCCEEDED
    task.taskStatus = EvaluationJobStatus.SUCCEEDED.value
    task.successCount = len(created_results)
    task.failCount = 0
    task.finished_at = _now_str()
    db.add(task)
    db.commit()
    db.refresh(task)

    for result in created_results[:20]:
        db.refresh(result)

    return task, created_results


def run_mock_evaluation(
    db: Session,
    dataset_id: int,
    model_id: int,
    prompt_template_id: int,
) -> tuple[EvaluationTask, list[EvaluationResult]]:
    raise NotImplementedError("Mock evaluation has been deprecated. Use the live evaluation endpoint.")


def render_prompt(template: str, axiom_text: str, context_info: Optional[str]) -> str:
    rendered = template.replace("{axiom_text}", axiom_text)
    rendered = rendered.replace("{context_info}", context_info or "无")
    if "{context_info}" not in template and context_info:
        rendered = f"{rendered}\n\n上下文信息：\n{context_info}"
    return rendered


def call_openai_compatible_model(
    base_url: str,
    api_key: str,
    model_name: str,
    prompt: str,
) -> tuple[str, Optional[int], Optional[float]]:
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response_json = json.loads(response_body)
    content = extract_message_content(response_json)
    total_tokens = response_json.get("usage", {}).get("total_tokens")
    return content, total_tokens, elapsed_ms


def extract_message_content(response_json: dict) -> str:
    choices = response_json.get("choices") or []
    if not choices:
        return json.dumps(response_json, ensure_ascii=False)

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part).strip()

    return str(content)


def parse_model_response(raw_response: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    judgment_result: Optional[str] = None
    predicted_label: Optional[int] = None
    explanation: Optional[str] = None

    for pattern in JUDGMENT_PATTERNS:
        match = pattern.search(raw_response)
        if match:
            value = match.group(1).strip().lower()
            if value in {"correct", "正确"}:
                judgment_result = "Correct"
                predicted_label = 1
            elif value in {"incorrect", "错误"}:
                judgment_result = "Incorrect"
                predicted_label = 0
            break

    for pattern in EXPLANATION_PATTERNS:
        match = pattern.search(raw_response)
        if match:
            explanation = match.group(1).strip()
            break

    return judgment_result, predicted_label, explanation


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _calculate_metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    if total == 0:
        return {
            "total": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    tp = fp = tn = fn = 0
    for row in rows:
        true_label = _normalize_binary_label(row["true_label"])
        predicted_label = _normalize_binary_label(row["predicted_label"])

        if true_label is None or predicted_label is None:
            continue

        if true_label == 1 and predicted_label == 1:
            tp += 1
        elif true_label == 0 and predicted_label == 1:
            fp += 1
        elif true_label == 0 and predicted_label == 0:
            tn += 1
        elif true_label == 1 and predicted_label == 0:
            fn += 1

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "total": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _normalize_binary_label(value: object) -> Optional[int]:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    try:
        numeric = float(normalized)
    except ValueError:
        lowered = normalized.lower()
        if lowered in {"correct", "true", "yes"}:
            return 1
        if lowered in {"incorrect", "false", "no"}:
            return 0
        return None

    if numeric == 1.0:
        return 1
    if numeric == 0.0:
        return 0
    return None
