"""
Data Models and Types for Entity Interactions
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class InteractionType(str, Enum):
    APPROACHING = "APPROACHING"
    CONTACT = "CONTACT"
    HOLDING = "HOLDING"
    CARRYING = "CARRYING"
    SEPARATED = "SEPARATED"
    STACKED_ON = "STACKED_ON"
    NEAR_EQUIPMENT = "NEAR_EQUIPMENT"
    COLLISION_RISK = "COLLISION_RISK"
    FLOOR_CONTACT = "FLOOR_CONTACT"


@dataclass
class SpatialInteraction:
    interaction_id: str
    source_track_id: int
    source_class: str
    target_track_id: int
    target_class: str
    interaction_type: InteractionType
    distance_px: float
    iou: float
    relative_velocity: Tuple[float, float]
    start_frame: int
    current_frame: int
    start_time_seconds: float
    current_time_seconds: float
    duration_seconds: float
    confidence: float


@dataclass
class FrameInteractions:
    frame_index: int
    source_frame_number: int
    timestamp_seconds: float
    interactions: List[SpatialInteraction] = field(default_factory=list)
