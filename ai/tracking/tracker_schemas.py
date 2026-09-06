"""
Data Models and Types for Multi-Object Tracking
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class TrackState(str, Enum):
    NEW = "NEW"
    TRACKED = "TRACKED"
    CONFIRMED = "CONFIRMED"
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
    current_bbox: List[float] = field(default_factory=list)
    current_centroid: Tuple[float, float] = (0.0, 0.0)
    bbox_xyxy: Optional[List[float]] = None
    centroid_xy: Optional[Tuple[float, float]] = None
    width_px: float = 0.0
    height_px: float = 0.0
    area_px: float = 0.0
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

    def __post_init__(self):
        if self.bbox_xyxy is not None and not self.current_bbox:
            self.current_bbox = self.bbox_xyxy
        elif self.current_bbox and self.bbox_xyxy is None:
            self.bbox_xyxy = self.current_bbox

        if self.centroid_xy is not None and self.current_centroid == (0.0, 0.0):
            self.current_centroid = self.centroid_xy
        elif self.current_centroid != (0.0, 0.0) and self.centroid_xy is None:
            self.centroid_xy = self.current_centroid

        if self.width_px == 0.0 and self.current_bbox and len(self.current_bbox) == 4:
            self.width_px = self.current_bbox[2] - self.current_bbox[0]
        if self.height_px == 0.0 and self.current_bbox and len(self.current_bbox) == 4:
            self.height_px = self.current_bbox[3] - self.current_bbox[1]
        if self.area_px == 0.0:
            self.area_px = self.width_px * self.height_px


@dataclass
class FrameTracks:
    frame_index: int
    source_frame_number: int = 0
    timestamp_seconds: float = 0.0
    active_tracks: List[TrackedObject] = field(default_factory=list)
    lost_tracks: List[TrackedObject] = field(default_factory=list)
    removed_tracks: List[TrackedObject] = field(default_factory=list)

