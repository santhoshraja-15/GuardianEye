"""
Video and Processing Job ORM Entities
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class Video(Base):
    __tablename__ = "videos"

    camera_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    fps: Mapped[float] = mapped_column(Float, default=30.0)
    width: Mapped[int] = mapped_column(Integer, default=1920)
    height: Mapped[int] = mapped_column(Integer, default=1080)
    codec: Mapped[str] = mapped_column(String(50), default="h264")
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="UPLOADED", index=True
    )  # UPLOADED, QUEUED, PROCESSING, COMPLETED, FAILED

    camera: Mapped[Optional["Camera"]] = relationship("Camera", back_populates="videos")
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="video", cascade="all, delete-orphan"
    )
    tracks: Mapped[List["Track"]] = relationship("Track", back_populates="video", cascade="all, delete-orphan")
    behaviour_events: Mapped[List["BehaviourEvent"]] = relationship(
        "BehaviourEvent", back_populates="video", cascade="all, delete-orphan"
    )


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    job_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", index=True
    )  # PENDING, RUNNING, COMPLETED, FAILED, RETRYING
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    frames_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    inference_fps_achieved: Mapped[float] = mapped_column(Float, default=0.0)
    processing_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    video: Mapped[Video] = relationship("Video", back_populates="processing_jobs")
