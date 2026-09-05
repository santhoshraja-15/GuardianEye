"""
Pydantic Schemas for Video Management and Processing Jobs
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class VideoBase(BaseModel):
    filename: str
    camera_id: Optional[str] = None


class VideoMetadataResponse(BaseModel):
    duration_seconds: float
    fps: float
    width: int
    height: int
    codec: str
    aspect_ratio: str
    total_frames: int
    file_size_bytes: int


class ProcessingJobResponse(BaseModel):
    id: str
    video_id: str
    job_status: str
    progress_percentage: float
    frames_processed: int
    total_frames: int
    inference_fps_achieved: float
    processing_time_seconds: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: str
    filename: str
    camera_id: Optional[str] = None
    storage_path: str
    file_size_bytes: int
    duration_seconds: float
    fps: float
    width: int
    height: int
    codec: str
    checksum_sha256: str
    status: str
    created_at: datetime
    updated_at: datetime
    processing_jobs: List[ProcessingJobResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class VideoUploadResponse(BaseModel):
    success: bool = True
    video: VideoResponse
    processing_job: ProcessingJobResponse
    message: str = "Video uploaded and queued for processing."
