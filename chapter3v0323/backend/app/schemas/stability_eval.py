from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class StabilityEvalTaskRead(BaseModel):
    id: int
    baseTaskId: int
    axiomTypeScope: str
    templateCount: int
    taskStatus: str
    totalCount: int
    successCount: int
    failCount: int
    hardConsistency: Optional[Decimal] = None
    softConsistency: Optional[Decimal] = None
    remark: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime


class StabilityEvalRecordRead(BaseModel):
    id: int
    stabilityTaskId: int
    baseTaskId: int
    resultId: int
    originalId: str
    templateId: int
    variantId: str
    axiomType: str
    originalText: Optional[str] = None
    perturbedText: str
    contextInfo: Optional[str] = None
    label: Optional[int] = None
    originalPredictLabel: Optional[int] = None
    perturbedPredictLabel: Optional[int] = None
    consistencyFlag: Optional[int] = None
    runStatus: str
    errorMessage: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime


class StabilityEvalRecordPage(BaseModel):
    records: list[StabilityEvalRecordRead]
    total: int
    page: int
    pageSize: int
