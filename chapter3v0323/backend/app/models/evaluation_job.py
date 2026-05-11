from __future__ import annotations

from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, TIMESTAMP, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class EvaluationJobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EvaluationTask(Base, TimestampMixin):
    __tablename__ = "evaluation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskName: Mapped[str] = mapped_column(String(100), server_default="", nullable=False)
    datasetId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    modelId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    promptId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    taskStatus: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False, index=True)
    totalCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    successCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    failCount: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
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
    dataset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    model_id: Mapped[Optional[int]] = mapped_column(ForeignKey("llm_models.id"), nullable=True)
    prompt_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("prompt_templates.id"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[EvaluationJobStatus]] = mapped_column(
        SQLEnum(EvaluationJobStatus, name="evaluation_job_status"),
        default=EvaluationJobStatus.PENDING,
        nullable=True,
    )
    started_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    finished_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    dataset = relationship("Dataset", back_populates="evaluation_tasks")
    model = relationship("LLMModel", back_populates="evaluation_tasks")
    prompt_template = relationship("PromptTemplate", back_populates="evaluation_tasks")
    results = relationship("EvaluationResult", back_populates="evaluation_task")


EvaluationJob = EvaluationTask
