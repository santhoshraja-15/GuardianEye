"""
Human Review, Dataset, and Model Registry Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HumanReviewCreateRequest(BaseModel):
    incident_id: str
    review_outcome: str = Field(..., description="CORRECT, INCORRECT, CHANGE_BEHAVIOUR, UNCERTAIN")
    corrected_behaviour_code: Optional[str] = None
    reviewer_notes: Optional[str] = None
    is_curated_for_training: bool = False


class HumanReviewResponse(BaseModel):
    id: str
    incident_id: str
    reviewed_by: str
    review_outcome: str
    corrected_behaviour_code: Optional[str] = None
    reviewer_notes: Optional[str] = None
    is_curated_for_training: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    dataset_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_tag: str
    train_sample_count: int
    val_sample_count: int
    test_sample_count: int
    manifest_checksum: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelArtifactResponse(BaseModel):
    id: str
    name: str
    model_type: str
    version: str
    framework: str
    artifact_path: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelEvaluationResponse(BaseModel):
    id: str
    model_id: str
    dataset_version_id: str
    mAP_50: Optional[float] = None
    behaviour_f1: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    false_positive_rate: Optional[float] = None
    evaluation_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
