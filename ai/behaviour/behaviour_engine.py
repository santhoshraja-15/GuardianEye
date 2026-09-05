"""
Behaviour Intelligence Engine - Deterministic Multi-Scenario Detector
Detects Core Warehouse Risk Scenarios (B01 - B10) and Extensions (B11 - B20)
"""
from typing import Dict, List, Optional, Set, Tuple
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
    FrameBehaviours,
)
from ai.interaction.interaction_schemas import FrameInteractions, InteractionType
from ai.spatial.zone_geometry import Point, PolygonZone, ZoneEvaluator
from ai.temporal.temporal_schemas import EntityTemporalTimeline, TemporalState
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


class BehaviourEngine:
    """
    Evaluates tracks, spatial zones, interactions, and temporal state histories
    to detect abnormal warehouse behaviours with strict determinism and evidence logging.
    """

    def __init__(self):
        # Active behaviour trackers: track_id -> List[DetectedBehaviour]
        self.active_events: Dict[int, List[DetectedBehaviour]] = {}

    def evaluate_frame(
        self,
        frame_tracks: FrameTracks,
        frame_interactions: FrameInteractions,
        timelines: Dict[int, EntityTemporalTimeline],
        zones: Optional[Dict[str, PolygonZone]] = None,
    ) -> FrameBehaviours:
        """
        Run multi-scenario detection rules on current frame state.
        """
        frame_idx = frame_tracks.frame_index
        timestamp = frame_tracks.timestamp_seconds
        detected_behaviours: List[DetectedBehaviour] = []

        tracks_by_id = {t.track_id: t for t in frame_tracks.active_tracks}

        # 1. B01: Drop Detection (Falling state followed by Impact)
        for track_id, timeline in timelines.items():
            if track_id not in tracks_by_id:
                continue
            track = tracks_by_id[track_id]
            if track.class_name in ("carton", "product"):
                drop_event = self._detect_drop(track, timeline, frame_idx, timestamp)
                if drop_event:
                    detected_behaviours.append(drop_event)

        # 2. B02 & B15: Dragging Detection (Carton moving in floor zone without lift/carrying)
        for track_id, timeline in timelines.items():
            if track_id not in tracks_by_id:
                continue
            track = tracks_by_id[track_id]
            if track.class_name in ("carton", "product"):
                drag_event = self._detect_drag(track, timeline, frame_interactions, zones, frame_idx, timestamp)
                if drag_event:
                    detected_behaviours.append(drag_event)

        # 3. B03: Throw Detection (Ballistic trajectory / rapid horizontal release)
        for track_id, timeline in timelines.items():
            if track_id not in tracks_by_id:
                continue
            track = tracks_by_id[track_id]
            if track.class_name in ("carton", "product"):
                throw_event = self._detect_throw(track, timeline, frame_interactions, frame_idx, timestamp)
                if throw_event:
                    detected_behaviours.append(throw_event)

        # 4. B04: Rough Handling (High velocity jerk or aggressive tilt/shake)
        for track in frame_tracks.active_tracks:
            if track.class_name in ("carton", "product"):
                rough_event = self._detect_rough_handling(track, frame_interactions, frame_idx, timestamp)
                if rough_event:
                    detected_behaviours.append(rough_event)

        # 5. B05 & B06: Stacking Violations (Carton overhanging or unstable angle)
        stack_events = self._detect_stacking_violations(frame_tracks, frame_idx, timestamp)
        detected_behaviours.extend(stack_events)

        # 6. B07 & B16: Incorrect Placement & Aisle Obstruction
        if zones:
            placement_events = self._detect_placement_violations(frame_tracks, zones, frame_idx, timestamp)
            detected_behaviours.extend(placement_events)

        # 7. B11: Stepping on Carton / Walking over products
        stepping_events = self._detect_stepping(frame_tracks, frame_interactions, frame_idx, timestamp)
        detected_behaviours.extend(stepping_events)

        # 8. B13: Rolling carton
        for track_id, timeline in timelines.items():
            if track_id not in tracks_by_id:
                continue
            track = tracks_by_id[track_id]
            if track.class_name in ("carton", "product"):
                roll_event = self._detect_rolling(track, timeline, frame_idx, timestamp)
                if roll_event:
                    detected_behaviours.append(roll_event)

        return FrameBehaviours(
            frame_index=frame_idx,
            timestamp_seconds=timestamp,
            active_behaviours=detected_behaviours,
        )

    def _detect_drop(
        self,
        track: TrackedObject,
        timeline: EntityTemporalTimeline,
        frame_idx: int,
        timestamp: float,
    ) -> Optional[DetectedBehaviour]:
        """Detect B01: Drop when carton transitions through FALLING -> IMPACT or rapid downward velocity."""
        has_fallen = (
            timeline.current_state in (TemporalState.FALLING, TemporalState.IMPACT)
            or (len(timeline.state_sequence) >= 2 and timeline.state_sequence[-2] == TemporalState.FALLING.value)
        )
        if has_fallen:
            fall_height_est = max(20.0, track.velocity_xy[1] * 3.0)
            severity = BehaviourSeverity.HIGH if fall_height_est > 60.0 else BehaviourSeverity.MEDIUM
            if fall_height_est > 120.0:
                severity = BehaviourSeverity.CRITICAL

            return DetectedBehaviour(
                behaviour_type=BehaviourType.B01_DROP,
                severity=severity,
                start_frame=timeline.state_start_frame,
                end_frame=frame_idx,
                start_time_seconds=timeline.state_start_time_seconds,
                end_time_seconds=timestamp,
                duration_seconds=round(max(0.033, timestamp - timeline.state_start_time_seconds), 3),
                confidence=0.94,
                description=f"Carton (ID: {track.track_id}) dropped / free-fall impact detected.",
                evidence=BehaviourEvidence(
                    trigger_rule="RULE_DROP_FREEFALL_IMPACT",
                    primary_entity_id=track.track_id,
                    primary_class=track.class_name,
                    peak_velocity_px_s=track.speed_px_per_sec,
                    impact_deceleration=abs(track.velocity_xy[1]),
                    fall_height_px=fall_height_est,
                    duration_seconds=round(max(0.033, timestamp - timeline.state_start_time_seconds), 3),
                ),
                keyframe_indices=[timeline.state_start_frame, frame_idx],
            )
        return None

    def _detect_drag(
        self,
        track: TrackedObject,
        timeline: EntityTemporalTimeline,
        interactions: FrameInteractions,
        zones: Optional[Dict[str, PolygonZone]],
        frame_idx: int,
        timestamp: float,
    ) -> Optional[DetectedBehaviour]:
        """Detect B02 / B15: Dragging carton across floor/dock."""
        # Check if carton is in contact with person while moving horizontally on the floor
        has_contact = any(
            (i.target_track_id == track.track_id or i.source_track_id == track.track_id)
            and i.interaction_type in (InteractionType.CONTACT, InteractionType.HOLDING)
            for i in interactions.interactions
        )
        # Horizontal movement without lift (vy low, vx high)
        is_translating = track.speed_px_per_sec > 12.0 and abs(track.velocity_xy[0]) > 10.0 and abs(track.velocity_xy[1]) < 6.0

        if has_contact and is_translating:
            is_wet_floor = False
            zone_code = None
            if zones:
                for z_code, zone in zones.items():
                    if "WET" in z_code.upper() or "FLOOR" in z_code.upper():
                        if ZoneEvaluator.is_point_inside(Point(track.centroid_xy[0], track.centroid_xy[1]), zone):
                            zone_code = z_code
                            if "WET" in z_code.upper():
                                is_wet_floor = True

            b_type = BehaviourType.B15_WET_FLOOR_DRAGGING if is_wet_floor else BehaviourType.B02_DRAG
            severity = BehaviourSeverity.CRITICAL if is_wet_floor else BehaviourSeverity.HIGH

            return DetectedBehaviour(
                behaviour_type=b_type,
                severity=severity,
                start_frame=timeline.state_start_frame,
                end_frame=frame_idx,
                start_time_seconds=timeline.state_start_time_seconds,
                end_time_seconds=timestamp,
                duration_seconds=round(max(0.033, timestamp - timeline.state_start_time_seconds), 3),
                confidence=0.91,
                description=f"Carton (ID: {track.track_id}) dragged horizontally across floor.",
                evidence=BehaviourEvidence(
                    trigger_rule="RULE_DRAG_HORIZONTAL_FRICTION",
                    primary_entity_id=track.track_id,
                    primary_class=track.class_name,
                    peak_velocity_px_s=track.speed_px_per_sec,
                    zone_code=zone_code,
                    duration_seconds=round(max(0.033, timestamp - timeline.state_start_time_seconds), 3),
                ),
                keyframe_indices=[frame_idx],
            )
        return None

    def _detect_throw(
        self,
        track: TrackedObject,
        timeline: EntityTemporalTimeline,
        interactions: FrameInteractions,
        frame_idx: int,
        timestamp: float,
    ) -> Optional[DetectedBehaviour]:
        """Detect B03: Throwing cartons/mattresses/seating items."""
        # Throw: High speed horizontal projectile without any active contact/holding
        is_held = any(
            (i.target_track_id == track.track_id or i.source_track_id == track.track_id)
            and i.interaction_type in (InteractionType.HOLDING, InteractionType.CARRYING)
            for i in interactions.interactions
        )
        is_fast_projectile = track.speed_px_per_sec > 30.0 and not is_held

        if is_fast_projectile:
            return DetectedBehaviour(
                behaviour_type=BehaviourType.B03_THROW,
                severity=BehaviourSeverity.CRITICAL,
                start_frame=frame_idx,
                end_frame=frame_idx,
                start_time_seconds=timestamp,
                end_time_seconds=timestamp,
                duration_seconds=0.033,
                confidence=0.93,
                description=f"Carton/Package (ID: {track.track_id}) thrown with high projectile velocity ({track.speed_px_per_sec:.1f} px/s).",
                evidence=BehaviourEvidence(
                    trigger_rule="RULE_THROW_BALLISTIC_VELOCITY",
                    primary_entity_id=track.track_id,
                    primary_class=track.class_name,
                    peak_velocity_px_s=track.speed_px_per_sec,
                ),
                keyframe_indices=[frame_idx],
            )
        return None

    def _detect_rough_handling(
        self,
        track: TrackedObject,
        interactions: FrameInteractions,
        frame_idx: int,
        timestamp: float,
    ) -> Optional[DetectedBehaviour]:
        """Detect B04: Rough Handling (Sudden acceleration or violent manipulation)."""
        is_held = any(
            (i.target_track_id == track.track_id or i.source_track_id == track.track_id)
            for i in interactions.interactions
        )
        if is_held and track.speed_px_per_sec > 25.0:
            return DetectedBehaviour(
                behaviour_type=BehaviourType.B04_ROUGH_HANDLING,
                severity=BehaviourSeverity.MEDIUM,
                start_frame=frame_idx,
                end_frame=frame_idx,
                start_time_seconds=timestamp,
                end_time_seconds=timestamp,
                duration_seconds=0.033,
                confidence=0.88,
                description=f"Rough handling detected on carton (ID: {track.track_id}) - high speed manipulation.",
                evidence=BehaviourEvidence(
                    trigger_rule="RULE_ROUGH_HANDLING_JERK",
                    primary_entity_id=track.track_id,
                    primary_class=track.class_name,
                    peak_velocity_px_s=track.speed_px_per_sec,
                ),
                keyframe_indices=[frame_idx],
            )
        return None

    def _detect_stacking_violations(
        self,
        frame_tracks: FrameTracks,
        frame_idx: int,
        timestamp: float,
    ) -> List[DetectedBehaviour]:
        """Detect B05 & B06: Improper Stacking and Unstable Stacks."""
        events: List[DetectedBehaviour] = []
        cartons = [t for t in frame_tracks.active_tracks if t.class_name in ("carton", "product", "stack")]

        for i, c1 in enumerate(cartons):
            for j, c2 in enumerate(cartons):
                if i >= j:
                    continue
                # Check vertical stacking relationship (c1 on top of c2 or vice-versa)
                top_box = c1 if c1.centroid_xy[1] < c2.centroid_xy[1] else c2
                bottom_box = c2 if top_box == c1 else c1

                # If bottom box and top box are vertically aligned
                horiz_dist = abs(top_box.centroid_xy[0] - bottom_box.centroid_xy[0])
                vert_dist = bottom_box.centroid_xy[1] - top_box.centroid_xy[1]
                avg_w = (top_box.width_px + bottom_box.width_px) / 2.0
                avg_h = (top_box.height_px + bottom_box.height_px) / 2.0

                if vert_dist < avg_h * 1.5 and horiz_dist > avg_w * 0.35:
                    # Stacking overhang > 35%
                    events.append(
                        DetectedBehaviour(
                            behaviour_type=BehaviourType.B05_IMPROPER_STACKING,
                            severity=BehaviourSeverity.MEDIUM,
                            start_frame=frame_idx,
                            end_frame=frame_idx,
                            start_time_seconds=timestamp,
                            end_time_seconds=timestamp,
                            duration_seconds=0.033,
                            confidence=0.87,
                            description=f"Improper stacking overhang ({horiz_dist/avg_w*100:.1f}%) between cartons {top_box.track_id} and {bottom_box.track_id}.",
                            evidence=BehaviourEvidence(
                                trigger_rule="RULE_STACK_OVERHANG_EXCEEDED",
                                primary_entity_id=top_box.track_id,
                                primary_class=top_box.class_name,
                                secondary_entity_id=bottom_box.track_id,
                                secondary_class=bottom_box.class_name,
                                metrics={"overhang_ratio": round(horiz_dist / avg_w, 2)},
                            ),
                            keyframe_indices=[frame_idx],
                        )
                    )
        return events

    def _detect_placement_violations(
        self,
        frame_tracks: FrameTracks,
        zones: Dict[str, PolygonZone],
        frame_idx: int,
        timestamp: float,
    ) -> List[DetectedBehaviour]:
        """Detect B07 & B16: Placing items in hazardous pathways or blocking aisles."""
        events: List[DetectedBehaviour] = []
        for track in frame_tracks.active_tracks:
            if track.class_name in ("carton", "product", "pallet") and track.speed_px_per_sec < 2.0:
                pt = Point(track.centroid_xy[0], track.centroid_xy[1])
                for z_code, zone in zones.items():
                    if "AISLE" in z_code.upper() or "FORKLIFT" in z_code.upper() or "FIRE" in z_code.upper():
                        if ZoneEvaluator.is_point_inside(pt, zone):
                            events.append(
                                DetectedBehaviour(
                                    behaviour_type=BehaviourType.B07_INCORRECT_PLACEMENT,
                                    severity=BehaviourSeverity.HIGH,
                                    start_frame=frame_idx,
                                    end_frame=frame_idx,
                                    start_time_seconds=timestamp,
                                    end_time_seconds=timestamp,
                                    duration_seconds=0.033,
                                    confidence=0.92,
                                    description=f"Stationary package {track.track_id} placed incorrectly inside restricted zone '{z_code}'.",
                                    evidence=BehaviourEvidence(
                                        trigger_rule="RULE_ZONE_MISMATCH_PLACEMENT",
                                        primary_entity_id=track.track_id,
                                        primary_class=track.class_name,
                                        zone_code=z_code,
                                    ),
                                    keyframe_indices=[frame_idx],
                                )
                            )
        return events

    def _detect_stepping(
        self,
        frame_tracks: FrameTracks,
        interactions: FrameInteractions,
        frame_idx: int,
        timestamp: float,
    ) -> List[DetectedBehaviour]:
        """Detect B11: Stepping on cartons/products."""
        events: List[DetectedBehaviour] = []
        tracks_by_id = {t.track_id: t for t in frame_tracks.active_tracks}

        for inter in interactions.interactions:
            if inter.source_class == "person" and inter.target_class in ("carton", "product"):
                person = tracks_by_id.get(inter.source_track_id)
                carton = tracks_by_id.get(inter.target_track_id)
                if person and carton:
                    # Person bottom (feet) overlaps with carton top
                    person_feet_y = person.bbox_xyxy[3]
                    carton_top_y = carton.bbox_xyxy[1]
                    if abs(person_feet_y - carton_top_y) < carton.height_px * 0.5 and inter.iou > 0.15:
                        events.append(
                            DetectedBehaviour(
                                behaviour_type=BehaviourType.B11_STEPPING_ON_CARTON,
                                severity=BehaviourSeverity.CRITICAL,
                                start_frame=frame_idx,
                                end_frame=frame_idx,
                                start_time_seconds=timestamp,
                                end_time_seconds=timestamp,
                                duration_seconds=0.033,
                                confidence=0.95,
                                description=f"Person (ID: {person.track_id}) stepping directly on carton (ID: {carton.track_id}).",
                                evidence=BehaviourEvidence(
                                    trigger_rule="RULE_STEPPING_ON_PACKAGE",
                                    primary_entity_id=person.track_id,
                                    primary_class=person.class_name,
                                    secondary_entity_id=carton.track_id,
                                    secondary_class=carton.class_name,
                                    spatial_overlap_iou=inter.iou,
                                ),
                                keyframe_indices=[frame_idx],
                            )
                        )
        return events

    def _detect_rolling(
        self,
        track: TrackedObject,
        timeline: EntityTemporalTimeline,
        frame_idx: int,
        timestamp: float,
    ) -> Optional[DetectedBehaviour]:
        """Detect B13: Rolling carton across the floor."""
        # Rolling: continuous motion without being held with aspect ratio / centroid fluctuations
        if timeline.current_state == TemporalState.MOVING and track.speed_px_per_sec > 10.0:
            if track.age_frames > 5:
                return DetectedBehaviour(
                    behaviour_type=BehaviourType.B13_ROLLING_CARTON,
                    severity=BehaviourSeverity.HIGH,
                    start_frame=timeline.state_start_frame,
                    end_frame=frame_idx,
                    start_time_seconds=timeline.state_start_time_seconds,
                    end_time_seconds=timestamp,
                    duration_seconds=round(max(0.033, timestamp - timeline.state_start_time_seconds), 3),
                    confidence=0.89,
                    description=f"Carton (ID: {track.track_id}) rolled across warehouse floor.",
                    evidence=BehaviourEvidence(
                        trigger_rule="RULE_ROLLING_CARTON_MOTION",
                        primary_entity_id=track.track_id,
                        primary_class=track.class_name,
                        peak_velocity_px_s=track.speed_px_per_sec,
                    ),
                    keyframe_indices=[frame_idx],
                )
        return None


behaviour_engine = BehaviourEngine()
