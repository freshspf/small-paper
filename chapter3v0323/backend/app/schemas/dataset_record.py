from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict

from app.schemas.common import TimestampRead


class DatasetRecordRead(TimestampRead):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    sample_id: str
    axiom_type: str
    axiom_text: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    label: Optional[int] = None
    source: Optional[str] = None
    context_info: Optional[str] = None
