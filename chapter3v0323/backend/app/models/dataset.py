from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class DatasetStatus(str, PyEnum):
    DRAFT = "draft"
    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_labels: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[DatasetStatus] = mapped_column(SQLEnum(DatasetStatus, name="dataset_status"), default=DatasetStatus.READY, nullable=False)

    records = relationship("DatasetRecord", back_populates="dataset", cascade="all, delete-orphan")
    evaluation_tasks = relationship("EvaluationTask", back_populates="dataset")
