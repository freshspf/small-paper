from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


LongText = Text().with_variant(LONGTEXT, "mysql")


class OntologyTask(Base):
    __tablename__ = "ontology_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskName: Mapped[str] = mapped_column(String(100), nullable=False)
    taskType: Mapped[str] = mapped_column(String(50), nullable=False)
    executionMode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    modelId: Mapped[int] = mapped_column(Integer, nullable=False)
    promptId: Mapped[int] = mapped_column(Integer, nullable=False)
    semanticPromptId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    termPromptId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    conceptPromptId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    domainType: Mapped[str] = mapped_column(String(50), nullable=False)
    domainSwitch: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunkMetadataSwitch: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    inputType: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fileName: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filePath: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    totalChunkCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchDomain: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchNaming: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    switchEntityDefinition: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inputText: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    finalPrompt: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    outputContent: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    mergedOutput: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    taskStatus: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    errorMessage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    createdTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updatedTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
