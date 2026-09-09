"""
Asynchronous Video Processing Worker Orchestrator
"""
import time
from datetime import datetime, timezone
from typing import Callable, Optional
from sqlalchemy.orm import Session
from ai.pipeline_runner import pipeline_orchestrator
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
        Execute full end-to-end AI perception, tracking, behaviour, risk, and incident pipeline
        """
        return pipeline_orchestrator.process_video(db=db, job_id=job_id)


video_worker = VideoProcessingWorker()
