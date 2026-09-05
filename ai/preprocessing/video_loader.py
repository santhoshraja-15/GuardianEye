"""
Video Ingestion, Header Parsing, and Metadata Extraction Engine
"""
from dataclasses import dataclass
import math
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2
import numpy as np


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
    with corrupt frame handling, stream validation, and thumbnail generation.
    """

    @staticmethod
    def extract_metadata(file_path: str) -> VideoMetadata:
        """
        Extract video technical properties using OpenCV VideoCapture.
        Handles zero-byte files, non-existent paths, unindexed streams, and invalid codecs safely.
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

        try:
            file_size = path_obj.stat().st_size
        except Exception as e:
            file_size = 0

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
            # Safe property extraction handling NaN / Inf / negative values
            raw_fps = cap.get(cv2.CAP_PROP_FPS)
            fps = float(raw_fps) if (raw_fps and not math.isnan(raw_fps) and not math.isinf(raw_fps) and raw_fps > 0) else 30.0

            raw_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            total_frames = int(raw_frames) if (raw_frames and not math.isnan(raw_frames) and not math.isinf(raw_frames) and raw_frames > 0) else 0

            raw_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            width = int(raw_w) if (raw_w and not math.isnan(raw_w) and not math.isinf(raw_w) and raw_w > 0) else 0

            raw_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            height = int(raw_h) if (raw_h and not math.isnan(raw_h) and not math.isinf(raw_h) and raw_h > 0) else 0

            # Safe fourcc codec decoding
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "h264"
            if fourcc_int > 0:
                chars = []
                for i in range(4):
                    c = (fourcc_int >> (8 * i)) & 0xFF
                    if 32 <= c <= 126:  # printable ASCII
                        chars.append(chr(c))
                if chars:
                    decoded = "".join(chars).strip()
                    if decoded:
                        codec = decoded

            # Quick frame read test to verify stream decodability
            ret, frame = cap.read()
            if not ret or frame is None:
                duration = (total_frames / fps) if (fps > 0 and total_frames > 0) else 0.0
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
                    aspect_ratio="unknown",
                    is_valid=False,
                    error_message="Video header opened, but first frame decoding failed.",
                )

            # If width or height were 0 from header, grab from decoded frame
            if width <= 0 or height <= 0:
                height, width = frame.shape[:2]

            duration = (total_frames / fps) if (fps > 0 and total_frames > 0) else 0.0

            # Compute simplified aspect ratio
            aspect_ratio = f"{width}:{height}"
            if width > 0 and height > 0:
                gcd_val = VideoLoader._gcd(width, height)
                if gcd_val > 0:
                    aspect_ratio = f"{width // gcd_val}:{height // gcd_val}"

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
    def extract_thumbnail(file_path: str, output_image_path: str, timestamp_sec: float = 0.0) -> bool:
        """Extract a single representative snapshot frame as JPEG/PNG."""
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return False

        try:
            if timestamp_sec > 0:
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
            ret, frame = cap.read()
            if ret and frame is not None:
                os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
                return cv2.imwrite(output_image_path, frame)
            return False
        finally:
            cap.release()

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a
