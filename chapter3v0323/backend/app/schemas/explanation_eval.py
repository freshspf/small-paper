from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExplanationEvalUpsert(BaseModel):
    taskId: int
    resultId: int
    explanationCorrectLabel: Optional[int] = Field(default=None, ge=0, le=1)
    hallucinationLabel: Optional[int] = Field(default=None, ge=0, le=1)
    annotationRemark: Optional[str] = Field(default=None, max_length=255)


class ExplanationEvalRecordRead(BaseModel):
    id: Optional[int] = None
    taskId: int
    resultId: int
    explanationCorrectLabel: Optional[int] = None
    hallucinationLabel: Optional[int] = None
    annotationStatus: str
    annotationRemark: Optional[str] = None
    createdTime: Optional[datetime] = None
    updatedTime: Optional[datetime] = None


class ExplanationEvalItem(BaseModel):
    resultId: int
    taskId: int
    axiomType: Optional[str] = None
    axiomText: Optional[str] = None
    trueLabel: Optional[int] = None
    predictLabel: Optional[int] = None
    judgmentResult: Optional[str] = None
    explanation: Optional[str] = None
    rawOutput: Optional[str] = None
    runStatus: str
    annotation: ExplanationEvalRecordRead


class ExplanationEvalPage(BaseModel):
    records: list[ExplanationEvalItem]
    total: int
    page: int
    pageSize: int


class ExplanationEvalStats(BaseModel):
    correctCaseCount: int
    annotatedCount: int
    explanationCorrectCount: int
    hallucinationCount: int
    explanationAccuracy: float
    hallucinationRate: float
