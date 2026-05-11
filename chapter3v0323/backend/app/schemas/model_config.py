from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelConfigBase(BaseModel):
    modelName: str = Field(min_length=1, max_length=50)
    modelCode: str = Field(min_length=1, max_length=100)
    apiUrl: str = Field(min_length=1, max_length=255)
    apiKey: str = Field(min_length=1, max_length=255)
    temperature: float = Field(default=0.00, ge=0, le=9.99)
    maxTokens: int = Field(default=4096, ge=1)
    status: int = Field(default=1, ge=0, le=1)


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    modelName: Optional[str] = Field(default=None, min_length=1, max_length=50)
    modelCode: Optional[str] = Field(default=None, min_length=1, max_length=100)
    apiUrl: Optional[str] = Field(default=None, min_length=1, max_length=255)
    apiKey: Optional[str] = Field(default=None, min_length=1, max_length=255)
    temperature: Optional[float] = Field(default=None, ge=0, le=9.99)
    maxTokens: Optional[int] = Field(default=None, ge=1)
    status: Optional[int] = Field(default=None, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")


class ModelConfigRead(ModelConfigBase):
    id: int
    createdTime: datetime
    updatedTime: datetime

    model_config = ConfigDict(from_attributes=True)
