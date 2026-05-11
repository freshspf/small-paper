from __future__ import annotations

from typing import List, Optional

from app.models.explanation_annotation import ExplanationLabel
from app.schemas.common import APIBaseModel, TimestampRead


class AnnotationUpsert(APIBaseModel):
    explanation_label: ExplanationLabel
    annotation_reason: Optional[str] = None


class AnnotationRead(TimestampRead):
    id: int
    evaluation_result_id: int
    explanation_label: ExplanationLabel
    annotation_reason: Optional[str] = None


class AnnotationResultItem(TimestampRead):
    evaluation_result_id: int
    sample_id: Optional[str] = None
    axiom_type: Optional[str] = None
    axiom_text: Optional[str] = None
    judgment_result: Optional[str] = None
    explanation: Optional[str] = None
    raw_response: Optional[str] = None
    annotation_id: Optional[int] = None
    explanation_label: Optional[ExplanationLabel] = None
    annotation_reason: Optional[str] = None


class AnnotationListResponse(APIBaseModel):
    items: List[AnnotationResultItem]


class ExplanationStats(APIBaseModel):
    total_annotations: int
    correct_count: int
    hallucination_count: int
    explanation_accuracy: float
    hallucination_rate: float


class ExplanationStatsResponse(APIBaseModel):
    overall: ExplanationStats
    by_model: dict[str, ExplanationStats]
