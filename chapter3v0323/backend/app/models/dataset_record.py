from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class DatasetRecord(Base, TimestampMixin):
    __tablename__ = "dataset_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    sample_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    axiom_type: Mapped[str] = mapped_column(String(100), nullable=False)
    axiom_text: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    predicate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    object_value: Mapped[Optional[str]] = mapped_column("object", String(255), nullable=True)
    label: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dataset = relationship("Dataset", back_populates="records")
    evaluation_results = relationship("EvaluationResult", back_populates="dataset_record")

    @property
    def object(self) -> Optional[str]:
        return self.object_value
