"""
Video Ingestion, Header Parsing, and Metadata Extraction Engine
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2


@dataclass
class VideoMetadata:
    filename: str
    file_path: str
    file_size_bytes: int
    duration_seconds: float
    fps: float
    total_frames: int
    width: int
    height: int
    codec: str
    aspect_ratio: str
    is_valid: bool
    error_message: Optional[str] = None


class VideoLoader:
    """
    High-performance video decoder and header metadata extractor
    with corrupt frame handling and stream validation.
    """

    @staticmethod
    def extract_metadata(file_path: str) -> VideoMetadata:
        """
        Extract video technical properties using OpenCV VideoCapture
        """
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            return VideoMetadata(
                filename=path_obj.name,
                file_path=str(path_obj),
                file_size_bytes=0,
                duration_seconds=0.0,
                fps=0.0,
                total_frames=0,
                width=0,
                height=0,
                codec="unknown",
                aspect_ratio="unknown",
                is_valid=False,
                error_message=f"Video file not found at {file_path}",
            )

        file_size = path_obj.stat().st_size
        if file_size == 0:
            return VideoMetadata(
                filename=path_obj.name,
                file_path=str(path_obj),
                file_size_bytes=0,
                duration_seconds=0.0,
                fps=0.0,
                total_frames=0,
                width=0,
                height=0,
                codec="unknown",
                aspect_ratio="unknown",
                is_valid=False,
                error_message="Video file is 0 bytes (empty file).",
            )

        cap = cv2.VideoCapture(str(path_obj))
        if not cap.isOpened():
            return VideoMetadata(
                filename=path_obj.name,
                file_path=str(path_obj),
                file_size_bytes=file_size,
                duration_seconds=0.0,
                fps=0.0,
                total_frames=0,
                width=0,
                height=0,
                codec="corrupt",
                aspect_ratio="unknown",
                is_valid=False,
                error_message="Failed to open video stream. Invalid codec or corrupt file header.",
            )

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip() or "h264"

            duration = (total_frames / fps) if fps > 0 else 0.0

            # Compute aspect ratio
            aspect_ratio = f"{width}:{height}"
            if width > 0 and height > 0:
                gcd_val = VideoLoader._gcd(width, height)
                aspect_ratio = f"{width // gcd_val}:{height // gcd_val}"

            # Quick frame read test to verify stream decodability
            ret, frame = cap.read()
            if not ret or frame is None:
                return VideoMetadata(
                    filename=path_obj.name,
                    file_path=str(path_obj),
                    file_size_bytes=file_size,
                    duration_seconds=duration,
                    fps=fps,
                    total_frames=total_frames,
                    width=width,
                    height=height,
                    codec=codec,
                    aspect_ratio=aspect_ratio,
                    is_valid=False,
                    error_message="Video header opened, but first frame decoding failed.",
                )

            return VideoMetadata(
                filename=path_obj.name,
                file_path=str(path_obj),
                file_size_bytes=file_size,
                duration_seconds=round(duration, 2),
                fps=round(fps, 2),
                total_frames=total_frames,
                width=width,
                height=height,
                codec=codec,
                aspect_ratio=aspect_ratio,
                is_valid=True,
            )

        finally:
            cap.release()

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a
