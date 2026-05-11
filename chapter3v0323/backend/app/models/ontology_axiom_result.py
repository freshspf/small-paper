from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


LongText = Text().with_variant(LONGTEXT, "mysql")


class OntologyAxiomResult(Base):
    __tablename__ = "ontology_axiom_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taskId: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    executionMode: Mapped[str] = mapped_column(String(50), nullable=False)
    sourceLayer: Mapped[str] = mapped_column(String(50), nullable=False)
    axiomType: Mapped[str] = mapped_column(String(50), nullable=False)
    subjectTerm: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    objectTerm: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    axiomText: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payloadJson: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    createdTime: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updatedTime: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
