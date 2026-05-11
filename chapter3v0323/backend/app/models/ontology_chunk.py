from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


LongText = Text().with_variant(LONGTEXT, "mysql")


class OntologyChunk(Base):
    __tablename__ = "ontology_chunk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskId: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    chunkId: Mapped[str] = mapped_column(String(100), nullable=False)
    chunkIndex: Mapped[int] = mapped_column(Integer, nullable=False)
    sectionTitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pageStart: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pageEnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunkText: Mapped[str] = mapped_column(LongText, nullable=False)
    createdTime: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updatedTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
