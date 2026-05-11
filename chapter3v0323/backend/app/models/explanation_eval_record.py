from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ExplanationEvalRecord(Base):
    __tablename__ = "explanation_eval_record"
    __table_args__ = (
        UniqueConstraint("taskId", "resultId", name="uq_explanation_eval_task_result"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    resultId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    explanationCorrectLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    hallucinationLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    annotationStatus: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False, index=True)
    annotationRemark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
