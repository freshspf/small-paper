from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.annotation import (
    AnnotationListResponse,
    AnnotationRead,
    AnnotationResultItem,
    AnnotationUpsert,
    ExplanationStatsResponse,
)
from app.services import annotation_service


router = APIRouter()


@router.get("/tasks/{task_id}/results", response_model=AnnotationListResponse)
async def list_task_results_for_annotation(task_id: int, db: Session = Depends(get_db)) -> AnnotationListResponse:
    try:
        results = annotation_service.list_task_results_for_annotation(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    items: List[AnnotationResultItem] = []
    for result in results:
        annotation = result.annotation_records[0] if result.annotation_records else None
        items.append(
            AnnotationResultItem(
                created_at=result.created_at,
                updated_at=result.updated_at,
                evaluation_result_id=result.id,
                sample_id=result.sample_id,
                axiom_type=result.axiom_type,
                axiom_text=result.axiom_text,
                judgment_result=result.judgment_result,
                explanation=result.explanation,
                raw_response=result.raw_response,
                annotation_id=annotation.id if annotation else None,
                explanation_label=annotation.explanation_label if annotation else None,
                annotation_reason=annotation.annotation_reason if annotation else None,
            )
        )

    return AnnotationListResponse(items=items)


@router.put("/results/{evaluation_result_id}", response_model=AnnotationRead)
async def upsert_annotation(
    evaluation_result_id: int,
    payload: AnnotationUpsert,
    db: Session = Depends(get_db),
) -> AnnotationRead:
    try:
        annotation = annotation_service.upsert_annotation(db, evaluation_result_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return annotation


@router.get("/results/{evaluation_result_id}", response_model=AnnotationRead)
async def get_annotation(evaluation_result_id: int, db: Session = Depends(get_db)) -> AnnotationRead:
    annotation = annotation_service.get_annotation(db, evaluation_result_id)
    if annotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    return annotation


@router.get("/stats", response_model=ExplanationStatsResponse)
async def get_explanation_stats(db: Session = Depends(get_db)) -> ExplanationStatsResponse:
    stats = annotation_service.get_explanation_stats(db)
    return ExplanationStatsResponse.model_validate(stats)
