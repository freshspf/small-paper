from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.models.evaluation_job import EvaluationJobStatus
from app.schemas.common import APIBaseModel, ORMBaseModel, TimestampRead


class MockEvaluationCreate(APIBaseModel):
    dataset_id: int
    model_id: int
    prompt_template_id: int


class EvaluationResultRead(TimestampRead):
    id: int
    taskId: Optional[int] = None
    datasetRecordId: Optional[int] = None
    axiomType: Optional[str] = None
    axiomText: Optional[str] = None
    trueLabel: Optional[int] = None
    predictLabel: Optional[int] = None
    judgmentResult: Optional[str] = None
    rawOutput: Optional[str] = None
    runStatus: Optional[str] = None
    errorMessage: Optional[str] = None
    createdTime: Optional[datetime] = None
    updatedTime: Optional[datetime] = None
    evaluation_task_id: int
    dataset_record_id: int
    sample_id: Optional[str] = None
    axiom_type: Optional[str] = None
    axiom_text: Optional[str] = None
    predicted_label: Optional[int] = None
    judgment_result: Optional[str] = None
    explanation: Optional[str] = None
    raw_response: Optional[str] = None
    raw_output: Optional[str] = None
    response_time_ms: Optional[float] = None
    total_tokens: Optional[int] = None


class EvaluationTaskRead(TimestampRead):
    id: int
    taskName: Optional[str] = None
    datasetId: Optional[int] = None
    modelId: Optional[int] = None
    promptId: Optional[int] = None
    taskStatus: Optional[str] = None
    totalCount: Optional[int] = None
    successCount: Optional[int] = None
    failCount: Optional[int] = None
    remark: Optional[str] = None
    createdTime: Optional[datetime] = None
    updatedTime: Optional[datetime] = None
    dataset_id: int
    model_id: int
    prompt_template_id: int
    name: str
    status: EvaluationJobStatus
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class EvaluationTaskSummary(ORMBaseModel):
    id: int
    taskName: Optional[str] = None
    datasetId: Optional[int] = None
    modelId: Optional[int] = None
    promptId: Optional[int] = None
    taskStatus: Optional[str] = None
    totalCount: Optional[int] = None
    successCount: Optional[int] = None
    failCount: Optional[int] = None
    remark: Optional[str] = None
    createdTime: Optional[datetime] = None
    updatedTime: Optional[datetime] = None
    name: str
    status: EvaluationJobStatus
    dataset_id: int
    model_id: int
    prompt_template_id: int
    created_at: datetime
    updated_at: datetime


class MockEvaluationResponse(APIBaseModel):
    task: EvaluationTaskRead
    result_count: int
    preview_results: List[EvaluationResultRead]


class EvaluationMetrics(APIBaseModel):
    total: int
    accuracy: float
    precision: float
    recall: float
    f1: float


class EvaluationMetricsResponse(APIBaseModel):
    overall: EvaluationMetrics
    by_axiom_type: Dict[str, EvaluationMetrics]
