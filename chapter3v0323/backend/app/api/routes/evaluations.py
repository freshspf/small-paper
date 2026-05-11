from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import (
    EvaluationMetricsResponse,
    EvaluationResultRead,
    EvaluationTaskRead,
    EvaluationTaskSummary,
    MockEvaluationCreate,
    MockEvaluationResponse,
)
from app.services import evaluation_service


router = APIRouter()


@router.get("/", response_model=List[EvaluationTaskSummary])
async def list_evaluation_tasks(db: Session = Depends(get_db)) -> List[EvaluationTaskSummary]:
    return evaluation_service.list_evaluation_tasks(db)


@router.post("/mock", response_model=MockEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def run_mock_evaluation(
    payload: MockEvaluationCreate,
    db: Session = Depends(get_db),
) -> MockEvaluationResponse:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Mock evaluation has been replaced. Use POST /api/v1/evaluations instead.",
    )


@router.post("/", response_model=MockEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def run_live_evaluation(
    payload: MockEvaluationCreate,
    db: Session = Depends(get_db),
) -> MockEvaluationResponse:
    try:
        task, results = evaluation_service.run_live_evaluation(
            db=db,
            dataset_id=payload.dataset_id,
            model_id=payload.model_id,
            prompt_template_id=payload.prompt_template_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MockEvaluationResponse(
        task=EvaluationTaskRead.model_validate(task),
        result_count=len(results),
        preview_results=[EvaluationResultRead.model_validate(item) for item in results[:20]],
    )


@router.get("/{task_id}", response_model=EvaluationTaskRead)
async def get_evaluation_task(task_id: int, db: Session = Depends(get_db)) -> EvaluationTaskRead:
    task = evaluation_service.get_evaluation_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation task not found")
    return task


@router.get("/{task_id}/results", response_model=List[EvaluationResultRead])
async def list_evaluation_results(task_id: int, db: Session = Depends(get_db)) -> List[EvaluationResultRead]:
    task = evaluation_service.get_evaluation_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation task not found")
    return evaluation_service.list_evaluation_results(db, task_id, limit=20)


@router.get("/{task_id}/metrics", response_model=EvaluationMetricsResponse)
async def get_evaluation_metrics(task_id: int, db: Session = Depends(get_db)) -> EvaluationMetricsResponse:
    try:
        metrics = evaluation_service.get_evaluation_metrics(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EvaluationMetricsResponse.model_validate(metrics)
