from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptTemplateConfigBase(BaseModel):
    templateName: str = Field(min_length=1, max_length=50)
    taskType: str = Field(min_length=1, max_length=50)
    templateType: str = Field(min_length=1, max_length=30)
    layerName: Optional[str] = Field(default=None, max_length=50)
    templateContent: str = Field(min_length=1)
    switchCount: int = Field(default=0, ge=0, le=1)
    switchDomain: int = Field(default=0, ge=0, le=1)
    switchNaming: int = Field(default=0, ge=0, le=1)
    switchEntity: int = Field(default=0, ge=0, le=1)
    remark: Optional[str] = Field(default=None, max_length=255)
    status: int = Field(default=1, ge=0, le=1)


class PromptTemplateConfigCreate(PromptTemplateConfigBase):
    pass


class PromptTemplateConfigUpdate(BaseModel):
    templateName: Optional[str] = Field(default=None, min_length=1, max_length=50)
    taskType: Optional[str] = Field(default=None, min_length=1, max_length=50)
    templateType: Optional[str] = Field(default=None, min_length=1, max_length=30)
    layerName: Optional[str] = Field(default=None, max_length=50)
    templateContent: Optional[str] = Field(default=None, min_length=1)
    switchCount: Optional[int] = Field(default=None, ge=0, le=1)
    switchDomain: Optional[int] = Field(default=None, ge=0, le=1)
    switchNaming: Optional[int] = Field(default=None, ge=0, le=1)
    switchEntity: Optional[int] = Field(default=None, ge=0, le=1)
    remark: Optional[str] = Field(default=None, max_length=255)
    status: Optional[int] = Field(default=None, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")


class PromptTemplateConfigRead(PromptTemplateConfigBase):
    id: int
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True)
