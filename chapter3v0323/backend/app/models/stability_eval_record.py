from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, Text, func, text
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class StabilityEvalRecord(Base):
    __tablename__ = "stability_eval_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stabilityTaskId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    baseTaskId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    resultId: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    originalId: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    templateId: Mapped[int] = mapped_column(Integer, nullable=False)
    variantId: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    axiomType: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    originalText: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    perturbedText: Mapped[str] = mapped_column(Text, nullable=False)
    contextInfo: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    label: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    originalPredictLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    perturbedPredictLabel: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
    consistencyFlag: Mapped[Optional[int]] = mapped_column(TINYINT(1), nullable=True)
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
