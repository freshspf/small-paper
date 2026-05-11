from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class ExplanationLabel(str, PyEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    HALLUCINATION = "hallucination"


class AnnotationRecord(Base, TimestampMixin):
    __tablename__ = "annotation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_result_id: Mapped[int] = mapped_column(ForeignKey("evaluation_results.id"), nullable=False, index=True)
    explanation_label: Mapped[ExplanationLabel] = mapped_column(
        SQLEnum(ExplanationLabel, name="explanation_label"),
        nullable=False,
    )
    annotation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evaluation_result = relationship("EvaluationResult", back_populates="annotation_records")


ExplanationAnnotation = AnnotationRecord
