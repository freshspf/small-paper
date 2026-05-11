from __future__ import annotations

from typing import Optional

from app.schemas.common import APIBaseModel, TimestampRead


class LLMModelBase(APIBaseModel):
    name: str
    provider: Optional[str] = None
    api_key: str
    base_url: str
    model_name: str
    is_default: bool = False


class LLMModelCreate(LLMModelBase):
    pass


class LLMModelUpdate(APIBaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_default: Optional[bool] = None


class LLMModelRead(TimestampRead):
    id: int
    name: str
    provider: Optional[str] = None
    api_key: str
    base_url: str
    model_name: str
    is_default: bool
