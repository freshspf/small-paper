from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, TIMESTAMP, Text, func, text
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class EvaluationResult(Base, TimestampMixin):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    datasetRecordId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    axiomType: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    axiomText: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trueLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    predictLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    judgmentResult: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    evaluation_task_id: Mapped[Optional[int]] = mapped_column(
        "evaluation_job_id",
        ForeignKey("evaluation_tasks.id"),
        nullable=True,
        index=True,
    )
    dataset_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_records.id"), nullable=True, index=True)
    predicted_label: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    judgment_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rawOutput: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    runStatus: Mapped[str] = mapped_column(String(20), server_default="success", nullable=False, index=True)
    errorMessage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    evaluation_task = relationship("EvaluationTask", back_populates="results")
    dataset_record = relationship("DatasetRecord", back_populates="evaluation_results")
    @property
    def sample_id(self) -> Optional[str]:
        if self.dataset_record is None:
            return None
        return self.dataset_record.sample_id

    @property
    def axiom_type(self) -> Optional[str]:
        if self.dataset_record is None:
            return None
        return self.dataset_record.axiom_type

    @property
    def axiom_text(self) -> Optional[str]:
        if self.dataset_record is None:
            return None
        return self.dataset_record.axiom_text
