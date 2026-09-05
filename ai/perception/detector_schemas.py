"""
Data Models and Types for Object Perception Detections
"""
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Detection:
    class_id: int
    class_name: str  # person, carton, pallet, trolley, forklift, equipment, loading_bay, floor, stack
    confidence: float
    bbox_xyxy: List[float]  # [x1, y1, x2, y2] in pixels
    bbox_normalized: List[float]  # [x1, y1, x2, y2] in 0.0 to 1.0 range
    centroid_xy: Tuple[float, float]  # (cx, cy)
    width_px: float
    height_px: float
    area_px: float


@dataclass
class FrameDetections:
    frame_index: int
    source_frame_number: int
    timestamp_seconds: float
    image_width: int
    image_height: int
    detections: List[Detection] = field(default_factory=list)
    inference_latency_ms: float = 0.0
