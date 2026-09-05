"""
Video Ingestion and Video Management API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.video import (
    ProcessingJobResponse,
    VideoMetadataResponse,
    VideoResponse,
    VideoUploadResponse,
)
from backend.app.services.video_service import VideoService

router = APIRouter()


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Warehouse Video",
    description="Upload video footage (MP4, AVI, MOV) for AI perception, behaviour tracking, and risk analysis.",
)
async def upload_video(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoUploadResponse:
    video, job = await VideoService.ingest_video_file(db, file, camera_id=camera_id)
    return VideoUploadResponse(
        success=True,
        video=video,
        processing_job=job,
        message="Video footage ingested, validated, and queued for AI intelligence processing.",
    )


@router.get(
    "/",
    response_model=List[VideoResponse],
    status_code=status.HTTP_200_OK,
    summary="List Videos",
    description="List all ingested warehouse videos with status filters.",
)
def list_videos(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VideoResponse]:
    return VideoService.list_videos(db, skip=skip, limit=limit, status=status)


@router.get(
    "/{video_id}",
    response_model=VideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Video By ID",
    description="Retrieve specific video metadata and processing history.",
)
def get_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoResponse:
    return VideoService.get_video_by_id(db, video_id)


@router.get(
    "/{video_id}/jobs",
    response_model=List[ProcessingJobResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Video Processing Jobs",
    description="Retrieve all execution jobs and processing progress for a video.",
)
def get_video_jobs(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ProcessingJobResponse]:
    return VideoService.get_jobs_for_video(db, video_id)
