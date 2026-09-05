"""
Temporal Finite State Machine & Sequence Reasoning Engine
"""
from typing import Dict, List, Optional
from ai.interaction.interaction_schemas import FrameInteractions, InteractionType
from ai.temporal.temporal_schemas import (
    EntityTemporalTimeline,
    StateTransition,
    TemporalState,
)
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


class TemporalStateMachine:
    """
    Tracks and updates multi-frame temporal state machines for every active entity.
    Transitions through:
    IDLE -> APPROACHING -> CONTACT -> HOLDING -> MOVING -> RELEASED -> FALLING -> IMPACT -> STATIONARY
    and handles occlusion recovery (ACTIVE -> LOST -> REACQUIRED).
    """

    def __init__(self):
        # track_id -> EntityTemporalTimeline
        self.timelines: Dict[int, EntityTemporalTimeline] = {}

    def update(
        self,
        frame_tracks: FrameTracks,
        frame_interactions: FrameInteractions,
    ) -> Dict[int, EntityTemporalTimeline]:
        """
        Advance state machines for all active tracks based on motion, tracking status,
        and current interactions.
        """
        frame_idx = frame_tracks.frame_index
        timestamp = frame_tracks.timestamp_seconds

        # Map active interactions by entity ID
        interactions_by_track: Dict[int, List] = {}
        for item in frame_interactions.interactions:
            interactions_by_track.setdefault(item.source_track_id, []).append(item)
            interactions_by_track.setdefault(item.target_track_id, []).append(item)

        # 1. Process active tracks
        active_ids = set()
        for track in frame_tracks.active_tracks:
            active_ids.add(track.track_id)
            timeline = self._get_or_create_timeline(track, frame_idx, timestamp)
            self._evaluate_state_transition(
                timeline, track, interactions_by_track.get(track.track_id, []), frame_idx, timestamp
            )

        # 2. Process lost tracks (handle occlusion)
        for track in frame_tracks.lost_tracks:
            if track.track_id in self.timelines:
                timeline = self.timelines[track.track_id]
                if timeline.current_state != TemporalState.LOST:
                    self._transition(
                        timeline,
                        TemporalState.LOST,
                        frame_idx,
                        timestamp,
                        "Track temporarily lost / occluded",
                        confidence=0.85,
                    )

        return self.timelines

    def _get_or_create_timeline(
        self, track: TrackedObject, frame_idx: int, timestamp: float
    ) -> EntityTemporalTimeline:
        if track.track_id not in self.timelines:
            timeline = EntityTemporalTimeline(
                track_id=track.track_id,
                class_name=track.class_name,
                current_state=TemporalState.IDLE,
                state_start_frame=frame_idx,
                state_start_time_seconds=timestamp,
                current_state_duration_seconds=0.0,
                state_history=[],
                state_sequence=[TemporalState.IDLE.value],
            )
            self.timelines[track.track_id] = timeline
        return self.timelines[track.track_id]

    def _evaluate_state_transition(
        self,
        timeline: EntityTemporalTimeline,
        track: TrackedObject,
        interactions: List,
        frame_idx: int,
        timestamp: float,
    ):
        curr = timeline.current_state
        speed = track.speed_px_per_sec
        vy = track.velocity_xy[1]
        timeline.current_state_duration_seconds = max(0.0, timestamp - timeline.state_start_time_seconds)

        # Handle reacquisition from LOST state
        if curr == TemporalState.LOST:
            self._transition(
                timeline,
                TemporalState.REACQUIRED,
                frame_idx,
                timestamp,
                "Track successfully reacquired",
                confidence=0.90,
            )
            return

        has_holding = any(i.interaction_type == InteractionType.HOLDING for i in interactions)
        has_carrying = any(i.interaction_type == InteractionType.CARRYING for i in interactions)
        has_contact = any(i.interaction_type == InteractionType.CONTACT for i in interactions)
        has_approaching = any(i.interaction_type == InteractionType.APPROACHING for i in interactions)

        # State transition rules for Carton / Product
        if track.class_name in ("carton", "product"):
            if curr in (TemporalState.IDLE, TemporalState.STATIONARY, TemporalState.REACQUIRED):
                if has_holding or has_carrying:
                    self._transition(timeline, TemporalState.HOLDING, frame_idx, timestamp, "Person holding carton", 0.90)
                elif has_contact:
                    self._transition(timeline, TemporalState.CONTACT, frame_idx, timestamp, "Contact with person", 0.85)
                elif has_approaching:
                    self._transition(timeline, TemporalState.APPROACHING, frame_idx, timestamp, "Person approaching", 0.80)
                elif speed > 5.0:
                    self._transition(timeline, TemporalState.MOVING, frame_idx, timestamp, "Carton in motion", 0.80)

            elif curr in (TemporalState.CONTACT, TemporalState.HOLDING):
                if has_carrying or (speed > 15.0 and (has_holding or has_contact)):
                    self._transition(timeline, TemporalState.MOVING, frame_idx, timestamp, "Carton carried / moving", 0.90)
                elif not (has_holding or has_contact or has_carrying):
                    if vy > 12.0:  # Rapid downward descent
                        self._transition(timeline, TemporalState.FALLING, frame_idx, timestamp, "Released with downward velocity (Falling)", 0.92)
                    else:
                        self._transition(timeline, TemporalState.RELEASED, frame_idx, timestamp, "Released from hold", 0.85)

            elif curr == TemporalState.MOVING:
                if not (has_holding or has_contact or has_carrying):
                    if vy > 12.0:
                        self._transition(timeline, TemporalState.FALLING, frame_idx, timestamp, "Downward descent detected", 0.92)
                    else:
                        self._transition(timeline, TemporalState.RELEASED, frame_idx, timestamp, "Movement ended / released", 0.85)
                elif speed < 3.0 and not has_carrying:
                    self._transition(timeline, TemporalState.HOLDING, frame_idx, timestamp, "Stationary while held", 0.85)

            elif curr == TemporalState.FALLING:
                if speed < 5.0 or vy <= 0.0:  # Impact with floor / pallet
                    self._transition(timeline, TemporalState.IMPACT, frame_idx, timestamp, "Deceleration / Impact detected", 0.95)

            elif curr == TemporalState.IMPACT:
                if speed < 2.0:
                    self._transition(timeline, TemporalState.STATIONARY, frame_idx, timestamp, "Settled after impact", 0.90)

    def _transition(
        self,
        timeline: EntityTemporalTimeline,
        new_state: TemporalState,
        frame_idx: int,
        timestamp: float,
        reason: str,
        confidence: float,
    ):
        if timeline.current_state == new_state:
            return

        transition = StateTransition(
            from_state=timeline.current_state,
            to_state=new_state,
            frame_index=frame_idx,
            timestamp_seconds=timestamp,
            trigger_reason=reason,
            confidence=confidence,
        )
        timeline.state_history.append(transition)
        timeline.state_sequence.append(new_state.value)
        timeline.current_state = new_state
        timeline.state_start_frame = frame_idx
        timeline.state_start_time_seconds = timestamp
        timeline.current_state_duration_seconds = 0.0


temporal_state_machine = TemporalStateMachine()
