"""
Video Ingestion and Video Management API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import SessionLocal, get_db
from backend.app.models.user import User
from backend.app.schemas.video import (
    ProcessingJobResponse,
    VideoMetadataResponse,
    VideoResponse,
    VideoUploadResponse,
)
from backend.app.services.video_service import VideoService

router = APIRouter()


def _run_bg_processing(job_id: str):
    with SessionLocal() as db:
        VideoService.process_video_job(db, job_id)


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Warehouse Video",
    description="Upload video footage (MP4, AVI, MOV) for AI perception, behaviour tracking, and risk analysis.",
)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoUploadResponse:
    video, job = await VideoService.ingest_video_file(db, file, camera_id=camera_id)
    if auto_process and job:
        background_tasks.add_task(_run_bg_processing, job.id)

    return VideoUploadResponse(
        success=True,
        video=video,
        processing_job=job,
        message="Video footage ingested, validated, and queued for AI intelligence processing.",
    )


@router.post(
    "/{video_id}/process",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI Video Processing",
    description="Dispatch video to the AI perception, tracking, behaviour, and risk pipeline.",
)
def process_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProcessingJobResponse:
    job = VideoService.create_or_get_pending_job(db, video_id)
    background_tasks.add_task(_run_bg_processing, job.id)
    return job


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


@router.get(
    "/{video_id}/stream",
    summary="Stream Video with Partial Range Support",
    description="Stream video bytes with HTTP 206 Range header support for seamless playback and seeking.",
)
def stream_video(
    video_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    import os
    from fastapi.responses import FileResponse, StreamingResponse
    from backend.app.services.storage_service import storage_service

    video = VideoService.get_video_by_id(db, video_id)
    file_path = storage_service.get_file_path(video.storage_path)

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(file_path, media_type="video/mp4", filename=video.filename)

    byte1, byte2 = 0, None
    m = range_header.replace("bytes=", "").split("-")
    if m[0]:
        byte1 = int(m[0])
    if len(m) > 1 and m[1]:
        byte2 = int(m[1])

    length = file_size - byte1 if byte2 is None else byte2 - byte1 + 1

    def file_iterator(start: int, chunk_length: int, chunk_size: int = 65536):
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_length
            while bytes_left > 0:
                read_size = min(chunk_size, bytes_left)
                data = f.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {byte1}-{byte1 + length - 1}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(file_iterator(byte1, length), status_code=206, headers=headers)

