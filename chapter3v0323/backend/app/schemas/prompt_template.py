from __future__ import annotations

from typing import Optional

from app.models.prompt_template import PromptTemplateType
from app.schemas.common import APIBaseModel, TimestampRead


class PromptTemplateBase(APIBaseModel):
    name: str
    template_type: PromptTemplateType
    content: str
    description: Optional[str] = None
    is_active: bool = True


class PromptTemplateCreate(PromptTemplateBase):
    is_builtin: bool = False
    is_default: bool = False


class PromptTemplateUpdate(APIBaseModel):
    name: Optional[str] = None
    template_type: Optional[PromptTemplateType] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class PromptTemplateRead(TimestampRead):
    id: int
    name: str
    template_type: PromptTemplateType
    content: str
    description: Optional[str] = None
    is_builtin: bool
    is_default: bool
    is_active: bool
