"""
Data Models and Types for Multi-Object Tracking
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class TrackState(str, Enum):
    NEW = "NEW"
    TRACKED = "TRACKED"
    LOST = "LOST"
    REMOVED = "REMOVED"


@dataclass
class TrackPointData:
    frame_index: int
    timestamp_seconds: float
    bbox_xyxy: List[float]
    centroid_xy: Tuple[float, float]
    velocity_xy: Tuple[float, float]
    speed_px_per_sec: float
    confidence: float
    zone_id: Optional[str] = None


@dataclass
class TrackedObject:
    track_id: int
    class_id: int
    class_name: str
    state: TrackState
    confidence: float
    current_bbox: List[float]
    current_centroid: Tuple[float, float]
    velocity_xy: Tuple[float, float] = (0.0, 0.0)
    speed_px_per_sec: float = 0.0
    direction_degrees: float = 0.0
    first_frame_index: int = 0
    last_frame_index: int = 0
    start_time_seconds: float = 0.0
    last_time_seconds: float = 0.0
    hits: int = 1
    age_frames: int = 0
    time_since_update: int = 0
    trajectory: List[TrackPointData] = field(default_factory=list)


@dataclass
class FrameTracks:
    frame_index: int
    source_frame_number: int
    timestamp_seconds: float
    active_tracks: List[TrackedObject] = field(default_factory=list)
    lost_tracks: List[TrackedObject] = field(default_factory=list)
