"""
Data Models and Types for Behaviour Intelligence Engine
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class BehaviourType(str, Enum):
    # Core 10 Scenarios (B01 - B10)
    B01_DROP = "B01_DROP"
    B02_DRAG = "B02_DRAG"
    B03_THROW = "B03_THROW"
    B04_ROUGH_HANDLING = "B04_ROUGH_HANDLING"
    B05_IMPROPER_STACKING = "B05_IMPROPER_STACKING"
    B06_UNSTABLE_STACK = "B06_UNSTABLE_STACK"
    B07_INCORRECT_PLACEMENT = "B07_INCORRECT_PLACEMENT"
    B08_EQUIPMENT_MISUSE = "B08_EQUIPMENT_MISUSE"
    B09_PALLET_MISALIGNMENT = "B09_PALLET_MISALIGNMENT"
    B10_LOADING_SEQUENCE_VIOLATION = "B10_LOADING_SEQUENCE_VIOLATION"

    # Extended Scenarios (B11 - B20)
    B11_STEPPING_ON_CARTON = "B11_STEPPING_ON_CARTON"
    B12_KICKING_PRODUCT = "B12_KICKING_PRODUCT"
    B13_ROLLING_CARTON = "B13_ROLLING_CARTON"
    B14_CRUSHING_UNDER_LOAD = "B14_CRUSHING_UNDER_LOAD"
    B15_WET_FLOOR_DRAGGING = "B15_WET_FLOOR_DRAGGING"
    B16_AISLE_OBSTRUCTION = "B16_AISLE_OBSTRUCTION"
    B17_OVERLOADING_PALLET = "B17_OVERLOADING_PALLET"
    B18_UNSECURED_TRANSIT = "B18_UNSECURED_TRANSIT"
    B19_IMPROPER_LIFTING_POSTURE = "B19_IMPROPER_LIFTING_POSTURE"
    B20_COLLISION_RISK = "B20_COLLISION_RISK"


class BehaviourSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class BehaviourEvidence:
    trigger_rule: str
    primary_entity_id: int
    primary_class: str
    secondary_entity_id: Optional[int] = None
    secondary_class: Optional[str] = None
    peak_velocity_px_s: float = 0.0
    impact_deceleration: float = 0.0
    fall_height_px: float = 0.0
    duration_seconds: float = 0.0
    zone_code: Optional[str] = None
    spatial_overlap_iou: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectedBehaviour:
    behaviour_type: BehaviourType
    severity: BehaviourSeverity
    start_frame: int
    end_frame: int
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    confidence: float
    description: str
    evidence: BehaviourEvidence
    keyframe_indices: List[int] = field(default_factory=list)


@dataclass
class FrameBehaviours:
    frame_index: int
    timestamp_seconds: float
    active_behaviours: List[DetectedBehaviour] = field(default_factory=list)
