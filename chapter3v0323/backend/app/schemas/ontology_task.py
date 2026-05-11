from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class OntologyTaskCreate(BaseModel):
    taskName: str = Field(min_length=1, max_length=100)
    taskType: str = Field(default="configuration_optimization", min_length=1, max_length=50)
    modelId: int = Field(gt=0)
    promptId: int = Field(gt=0)
    domainType: str = Field(min_length=1, max_length=50)
    switchCount: int = Field(default=0, ge=0, le=1)
    switchDomain: int = Field(default=0, ge=0, le=1)
    switchNaming: int = Field(default=0, ge=0, le=1)
    switchEntityDefinition: int = Field(default=0, ge=0, le=1)
    inputText: str = Field(min_length=1)
    remark: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class OntologyBaselineCreate(BaseModel):
    taskName: str = Field(min_length=1, max_length=100)
    modelId: int = Field(gt=0)
    promptId: int = Field(gt=0)
    domainType: str = Field(min_length=1, max_length=50)
    domainSwitch: int = Field(default=1, ge=0, le=1)
    chunkMetadataSwitch: int = Field(default=1, ge=0, le=1)
    remark: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class OntologyLayeredCreate(BaseModel):
    taskName: str = Field(min_length=1, max_length=100)
    modelId: int = Field(gt=0)
    semanticPromptId: int = Field(gt=0)
    termPromptId: int = Field(gt=0)
    conceptPromptId: int = Field(gt=0)
    domainType: str = Field(min_length=1, max_length=50)
    domainSwitch: int = Field(default=1, ge=0, le=1)
    chunkMetadataSwitch: int = Field(default=1, ge=0, le=1)
    remark: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class OntologyTaskRead(BaseModel):
    id: int
    taskName: str
    taskType: str
    executionMode: Optional[str] = None
    modelId: int
    promptId: int
    semanticPromptId: Optional[int] = None
    termPromptId: Optional[int] = None
    conceptPromptId: Optional[int] = None
    domainType: str
    domainSwitch: int = 0
    chunkMetadataSwitch: int = 1
    inputType: Optional[str] = None
    fileName: Optional[str] = None
    filePath: Optional[str] = None
    totalChunkCount: int = 0
    successCount: int = 0
    failCount: int = 0
    switchCount: int
    switchDomain: int
    switchNaming: int
    switchEntityDefinition: int
    inputText: Optional[str]
    finalPrompt: Optional[str]
    outputContent: Optional[str]
    mergedOutput: Optional[str] = None
    taskStatus: str
    errorMessage: Optional[str]
    remark: Optional[str]
    createdTime: datetime
    updatedTime: datetime
    modelName: Optional[str] = None
    promptName: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OntologyChunkRead(BaseModel):
    id: int
    taskId: int
    chunkId: str
    chunkIndex: int
    sectionTitle: Optional[str]
    pageStart: Optional[int]
    pageEnd: Optional[int]
    chunkText: str
    createdTime: datetime
    updatedTime: datetime
    resultId: Optional[int] = None
    runStatus: Optional[str] = None
    errorMessage: Optional[str] = None
    classCount: int = 0
    propertyCount: int = 0
    subClassOfCount: int = 0
    subPropertyOfCount: int = 0
    domainCount: int = 0
    rangeCount: int = 0

    model_config = ConfigDict(from_attributes=True)


class OntologyChunkDetail(BaseModel):
    chunk: dict[str, Any]
    result: Optional[dict[str, Any]]


class OntologyTaskStats(BaseModel):
    totalChunkCount: int
    successCount: int
    failCount: int
    classCount: int
    propertyCount: int
    subClassOfCount: int
    subPropertyOfCount: int
    domainCount: int
    rangeCount: int
