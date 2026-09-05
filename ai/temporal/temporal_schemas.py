"""
Data Models and Types for Temporal State Reasoning
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class TemporalState(str, Enum):
    IDLE = "IDLE"
    APPROACHING = "APPROACHING"
    CONTACT = "CONTACT"
    HOLDING = "HOLDING"
    MOVING = "MOVING"
    ACCELERATING = "ACCELERATING"
    RELEASED = "RELEASED"
    FALLING = "FALLING"
    DRAGGING = "DRAGGING"
    IMPACT = "IMPACT"
    STATIONARY = "STATIONARY"
    LOST = "LOST"
    REACQUIRED = "REACQUIRED"


@dataclass
class StateTransition:
    from_state: TemporalState
    to_state: TemporalState
    frame_index: int
    timestamp_seconds: float
    trigger_reason: str
    confidence: float


@dataclass
class EntityTemporalTimeline:
    track_id: int
    class_name: str
    current_state: TemporalState
    state_start_frame: int
    state_start_time_seconds: float
    current_state_duration_seconds: float
    state_history: List[StateTransition] = field(default_factory=list)
    state_sequence: List[str] = field(default_factory=list)
