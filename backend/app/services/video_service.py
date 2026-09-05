"""
Video Ingestion and Job Lifecycle Domain Service Logic
"""
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ai.preprocessing.video_loader import VideoLoader
from backend.app.core.errors import NotFoundException, ValidationException, VideoProcessingException
from backend.app.models.video import ProcessingJob, Video
from backend.app.services.storage_service import storage_service


class VideoService:
    """
    Manages video intake, metadata extraction, database records,
    and asynchronous processing job scheduling.
    """

    @staticmethod
    async def ingest_video_file(
        db: Session,
        upload_file: UploadFile,
        camera_id: Optional[str] = None,
    ) -> Tuple[Video, ProcessingJob]:
        """
        Stream uploaded video to storage, parse metadata, and create Video + Job records
        """
        # 1. Save file to storage
        rel_path, abs_path, file_size, checksum = await storage_service.save_upload_file(
            upload_file, category="videos"
        )

        # 2. Extract video technical properties
        metadata = VideoLoader.extract_metadata(abs_path)
        if not metadata.is_valid:
            # Clean up unreadable file
            storage_service.delete_file(rel_path)
            raise ValidationException(
                f"Invalid or corrupted video stream: {metadata.error_message}"
            )

        # 3. Create Video DB Record
        video = Video(
            camera_id=camera_id,
            filename=upload_file.filename,
            storage_path=rel_path,
            file_size_bytes=file_size,
            duration_seconds=metadata.duration_seconds,
            fps=metadata.fps,
            width=metadata.width,
            height=metadata.height,
            codec=metadata.codec,
            checksum_sha256=checksum,
            status="QUEUED",
        )
        db.add(video)
        db.flush()

        # 4. Create Initial Processing Job Record
        job = ProcessingJob(
            video_id=video.id,
            job_status="PENDING",
            progress_percentage=0.0,
            frames_processed=0,
            total_frames=metadata.total_frames,
        )
        db.add(job)
        db.commit()
        db.refresh(video)
        db.refresh(job)

        return video, job

    @staticmethod
    def get_video_by_id(db: Session, video_id: str) -> Video:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise NotFoundException("Video", video_id)
        return video

    @staticmethod
    def list_videos(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Video]:
        query = db.query(Video)
        if status:
            query = query.filter(Video.status == status.upper())
        return query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_jobs_for_video(db: Session, video_id: str) -> List[ProcessingJob]:
        VideoService.get_video_by_id(db, video_id)
        return (
            db.query(ProcessingJob)
            .filter(ProcessingJob.video_id == video_id)
            .order_by(ProcessingJob.created_at.desc())
            .all()
        )
