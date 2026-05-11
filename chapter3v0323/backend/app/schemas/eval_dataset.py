from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvalDatasetRead(BaseModel):
    id: int
    datasetName: str
    fileName: str
    recordCount: int
    remark: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalDatasetRecordRead(BaseModel):
    id: int
    datasetId: int
    axiomType: str
    subject: str
    predicate: str
    object: str
    label: int
    source: str
    axiomText: str
    negativeStrategy: Optional[str] = None
    subjectContext: Optional[str] = None
    objectContext: Optional[str] = None
    contextInfo: Optional[str] = None
    contextSummary: Optional[str] = None
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalDatasetUploadResult(BaseModel):
    dataset: EvalDatasetRead
    totalCount: int
    successCount: int
    failedCount: int
    errors: List[str] = Field(default_factory=list)


class EvalDatasetRecordPage(BaseModel):
    records: List[EvalDatasetRecordRead]
    total: int
    page: int
    pageSize: int
