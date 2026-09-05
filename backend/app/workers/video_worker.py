"""
Asynchronous Video Processing Worker Orchestrator
"""
import time
from datetime import datetime, timezone
from typing import Callable, Optional
from sqlalchemy.orm import Session
from ai.preprocessing.frame_extractor import FrameExtractor, ProcessedFrame
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.video import ProcessingJob, Video
from backend.app.services.storage_service import storage_service


class VideoProcessingWorker:
    """
    Worker pipeline orchestrating video decoding, decoupled frame extraction,
    and delegating frames to the AI computer vision pipeline while updating
    database job progress.
    """

    def __init__(self, target_fps: Optional[int] = None):
        self.target_fps = target_fps or settings.INFERENCE_FPS
        self.extractor = FrameExtractor(target_fps=self.target_fps)

    def process_video_job(
        self,
        db: Session,
        job_id: str,
        frame_callback: Optional[Callable[[ProcessedFrame], None]] = None,
    ) -> bool:
        """
        Execute frame extraction loop for a processing job, computing throughput FPS
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Processing job {job_id} not found.")
            return False

        video = job.video
        job.job_status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        video.status = "PROCESSING"
        db.commit()

        start_time = time.time()
        frames_count = 0

        try:
            abs_video_path = storage_service.get_file_path(video.storage_path)

            for frame in self.extractor.extract_frames(str(abs_video_path)):
                # Dispatch frame to AI inference callback if provided
                if frame_callback:
                    frame_callback(frame)

                frames_count += 1

                # Update progress periodically
                if frames_count % 30 == 0 and job.total_frames > 0:
                    job.frames_processed = frames_count
                    job.progress_percentage = min(
                        99.0, round((frame.source_frame_number / job.total_frames) * 100, 1)
                    )
                    db.commit()

            # Mark completed
            elapsed_sec = max(0.001, time.time() - start_time)
            fps_achieved = round(frames_count / elapsed_sec, 2)

            job.job_status = "COMPLETED"
            job.progress_percentage = 100.0
            job.frames_processed = frames_count
            job.processing_time_seconds = round(elapsed_sec, 2)
            job.inference_fps_achieved = fps_achieved
            job.completed_at = datetime.now(timezone.utc)
            video.status = "COMPLETED"
            db.commit()

            logger.info(
                f"Completed video processing job {job_id}: {frames_count} frames in {elapsed_sec:.2f}s ({fps_achieved} FPS)"
            )
            return True

        except Exception as e:
            elapsed_sec = time.time() - start_time
            job.job_status = "FAILED"
            job.error_message = str(e)
            job.processing_time_seconds = round(elapsed_sec, 2)
            job.completed_at = datetime.now(timezone.utc)
            video.status = "FAILED"
            db.commit()

            logger.error(f"Video processing job {job_id} failed: {e}", exc_info=True)
            return False


video_worker = VideoProcessingWorker()
