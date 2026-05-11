from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class EvalDatasetRecord(Base):
    __tablename__ = "eval_dataset_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    datasetId: Mapped[int] = mapped_column(
        ForeignKey("eval_dataset.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    axiomType: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    predicate: Mapped[str] = mapped_column(String(100), nullable=False)
    object: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    axiomText: Mapped[str] = mapped_column(Text, nullable=False)
    negativeStrategy: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subjectContext: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectContext: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contextInfo: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
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

    dataset = relationship("EvalDataset", back_populates="records")
