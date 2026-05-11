from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvalTaskCreate(BaseModel):
    taskName: str = Field(min_length=1, max_length=100)
    datasetId: int
    modelId: int
    promptId: int
    remark: Optional[str] = Field(default=None, max_length=255)


class EvalTaskRead(BaseModel):
    id: int
    taskName: str
    datasetId: Optional[int] = None
    modelId: Optional[int] = None
    promptId: Optional[int] = None
    taskStatus: str
    totalCount: int
    successCount: int
    failCount: int
    remark: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime
    datasetName: Optional[str] = None
    modelName: Optional[str] = None
    promptName: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvalResultRead(BaseModel):
    id: int
    taskId: Optional[int] = None
    datasetRecordId: Optional[int] = None
    axiomType: Optional[str] = None
    axiomText: Optional[str] = None
    trueLabel: Optional[int] = None
    predictLabel: Optional[int] = None
    judgmentResult: Optional[str] = None
    explanation: Optional[str] = None
    rawOutput: Optional[str] = None
    runStatus: str
    errorMessage: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    evaluatedCount: int


class EvalTaskDetail(BaseModel):
    task: EvalTaskRead
    dataset: Optional[dict[str, Any]] = None
    model: Optional[dict[str, Any]] = None
    prompt: Optional[dict[str, Any]] = None
    metrics: EvalMetrics


class EvalResultPage(BaseModel):
    records: List[EvalResultRead]
    total: int
    page: int
    pageSize: int
