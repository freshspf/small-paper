from __future__ import annotations

from typing import Optional

from app.models.dataset import DatasetStatus
from app.schemas.common import APIBaseModel, TimestampRead


class DatasetCreate(APIBaseModel):
    name: str
    description: Optional[str] = None
    source: Optional[str] = None


class DatasetRead(TimestampRead):
    id: int
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    file_name: Optional[str] = None
    row_count: int
    status: DatasetStatus
    has_labels: bool
