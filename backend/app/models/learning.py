"""
Human Review, Dataset Versioning, Model Registry, and Evaluation ORM Entities
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class HumanReview(Base):
    __tablename__ = "human_reviews"

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    reviewed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    review_outcome: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # CORRECT, INCORRECT, CHANGE_BEHAVIOUR, UNCERTAIN
    corrected_behaviour_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_curated_for_training: Mapped[bool] = mapped_column(default=False)


class Dataset(Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[str] = mapped_column(String(50), default="BEHAVIOUR_DETECTION")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., "v1.0.0"
    train_sample_count: Mapped[int] = mapped_column(Integer, default=0)
    val_sample_count: Mapped[int] = mapped_column(Integer, default=0)
    test_sample_count: Mapped[int] = mapped_column(Integer, default=0)
    manifest_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # YOLO_DETECTION, BEHAVIOUR_CLASSIFIER, DAMAGE_MODEL
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), default="PyTorch")
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="CANDIDATE", index=True
    )  # TRAINING, EVALUATION, CANDIDATE, APPROVED, REJECTED, RETIRED
    parameters_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("model_artifacts.id"), nullable=False, index=True)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("dataset_versions.id"), nullable=False, index=True)
    mAP_50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    behaviour_f1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    false_positive_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confusion_matrix_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
