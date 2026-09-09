"""
Dataset Management and Model Registry API Endpoints
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.learning import Dataset, DatasetVersion, ModelArtifact, ModelEvaluation
from backend.app.models.user import User
from backend.app.schemas.learning import (
    DatasetResponse,
    DatasetVersionResponse,
    ModelArtifactResponse,
    ModelEvaluationResponse,
)

router = APIRouter()


class ApproveModelRequest(BaseModel):
    model_id: str
    decision: str = "APPROVED"  # APPROVED, REJECTED


@router.get(
    "/models",
    response_model=List[ModelArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="List Model Artifacts",
)
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ModelArtifactResponse]:
    return db.query(ModelArtifact).order_by(ModelArtifact.created_at.desc()).all()


@router.post(
    "/models/approve",
    response_model=ModelArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Model for Deployment",
)
def approve_model(
    req: ApproveModelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelArtifactResponse:
    model = db.query(ModelArtifact).filter(ModelArtifact.id == req.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {req.model_id} not found")

    model.status = req.decision
    model.approved_by = current_user.id
    model.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(model)
    return model


@router.get(
    "/datasets",
    response_model=List[DatasetResponse],
    status_code=status.HTTP_200_OK,
    summary="List Datasets",
)
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DatasetResponse]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.get(
    "/datasets/{dataset_id}/versions",
    response_model=List[DatasetVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Dataset Versions",
)
def list_dataset_versions(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DatasetVersionResponse]:
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.created_at.desc())
        .all()
    )


@router.get(
    "/evaluations",
    response_model=List[ModelEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Model Evaluations",
)
def list_evaluations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ModelEvaluationResponse]:
    return db.query(ModelEvaluation).order_by(ModelEvaluation.created_at.desc()).all()
