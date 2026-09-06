"""
Data Models and Types for Entity Interactions
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple, Union


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
class InteractionEvent:
    event_id: str = ""
    interaction: Optional[SpatialInteraction] = None
    event_type: Optional[str] = None
    timestamp_seconds: float = 0.0
    severity: float = 0.0
    # Direct interaction attributes
    interaction_type: InteractionType = InteractionType.CONTACT
    source_track_id: int = 0
    source_class: str = ""
    target_track_id: int = 0
    target_class: str = ""
    confidence: float = 1.0
    distance_px: float = 0.0
    iou: float = 0.0
    relative_speed_px_per_sec: float = 0.0
    relative_velocity: Tuple[float, float] = (0.0, 0.0)
    start_frame: int = 0
    end_frame: int = 0
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.interaction is not None:
            if not self.source_track_id:
                self.source_track_id = self.interaction.source_track_id
            if not self.target_track_id:
                self.target_track_id = self.interaction.target_track_id
            if not self.source_class:
                self.source_class = self.interaction.source_class
            if not self.target_class:
                self.target_class = self.interaction.target_class
            if self.interaction_type == InteractionType.CONTACT and self.interaction.interaction_type:
                self.interaction_type = self.interaction.interaction_type
            if self.distance_px == 0.0:
                self.distance_px = self.interaction.distance_px
            if self.iou == 0.0:
                self.iou = self.interaction.iou
            if self.duration_seconds == 0.0:
                self.duration_seconds = self.interaction.duration_seconds
            if self.confidence == 1.0:
                self.confidence = self.interaction.confidence


@dataclass
class FrameInteractions:
    frame_index: int
    source_frame_number: int = 0
    timestamp_seconds: float = 0.0
    interactions: List[Union[SpatialInteraction, InteractionEvent, Any]] = field(default_factory=list)

