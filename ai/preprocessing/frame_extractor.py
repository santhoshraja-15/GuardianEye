"""
Decoupled Frame Extraction, Temporal Sampling, and Image Normalization
"""
import time
from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class ProcessedFrame:
    frame_index: int
    source_frame_number: int
    timestamp_seconds: float
    image_bgr: np.ndarray
    image_rgb: np.ndarray
    original_width: int
    original_height: int


class FrameExtractor:
    """
    Decoupled frame extraction engine that samples frames from video streams
    at a specified target inference FPS (e.g., 10 FPS from a 30 FPS source),
    calculates exact timestamps, and normalizes image arrays.
    """

    def __init__(self, target_fps: int = 10):
        self.target_fps = target_fps

    def extract_frames(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        target_size: Optional[Tuple[int, int]] = None,
    ) -> Generator[ProcessedFrame, None, None]:
        """
        Generator yielding ProcessedFrame instances with decoupled temporal subsampling
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video stream at: {video_path}")

        try:
            source_fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
            total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0

            # Determine frame skip interval
            if self.target_fps >= source_fps:
                step = 1
            else:
                step = max(1, round(source_fps / self.target_fps))

            frame_count = 0
            sampled_index = 0

            while cap.isOpened():
                ret, frame_bgr = cap.read()
                if not ret or frame_bgr is None:
                    break

                if frame_count % step == 0:
                    timestamp_sec = round(frame_count / source_fps, 3)

                    # Resize if requested
                    if target_size:
                        resized_bgr = cv2.resize(frame_bgr, target_size)
                    else:
                        resized_bgr = frame_bgr

                    # Color conversion BGR -> RGB
                    frame_rgb = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)

                    yield ProcessedFrame(
                        frame_index=sampled_index,
                        source_frame_number=frame_count,
                        timestamp_seconds=timestamp_sec,
                        image_bgr=resized_bgr,
                        image_rgb=frame_rgb,
                        original_width=width,
                        original_height=height,
                    )

                    sampled_index += 1
                    if max_frames and sampled_index >= max_frames:
                        break

                frame_count += 1

        finally:
            cap.release()

    @staticmethod
    def create_batch(
        frames: List[ProcessedFrame],
    ) -> Tuple[np.ndarray, List[float], List[int]]:
        """
        Stack a list of ProcessedFrames into an RGB batch array (N, H, W, C)
        along with timestamps and frame indices.
        """
        batch_images = np.stack([f.image_rgb for f in frames], axis=0)
        timestamps = [f.timestamp_seconds for f in frames]
        indices = [f.frame_index for f in frames]
        return batch_images, timestamps, indices
