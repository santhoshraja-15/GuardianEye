"""
Level 14 Behaviour Intelligence Engine Tests
"""
from ai.behaviour.behaviour_engine import BehaviourEngine
from ai.behaviour.behaviour_schemas import BehaviourType, BehaviourSeverity
from ai.interaction.interaction_schemas import FrameInteractions, InteractionEvent, InteractionType
from ai.spatial.zone_geometry import Point, PolygonZone
from ai.temporal.temporal_schemas import EntityTemporalTimeline, StateTransition, TemporalState
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


def test_b01_drop_detection():
    """Verify B01 Drop detection when timeline transitions through falling/impact"""
    engine = BehaviourEngine()
    carton = TrackedObject(
        track_id=1,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 300.0, 200.0, 400.0],
        centroid_xy=(150.0, 350.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(0.0, 30.0),
        speed_px_per_sec=30.0,
        age_frames=10,
        hits=10,
        time_since_update=0,
    )
    timeline = EntityTemporalTimeline(
        track_id=1,
        class_name="carton",
        current_state=TemporalState.IMPACT,
        state_start_frame=5,
        state_start_time_seconds=0.15,
        current_state_duration_seconds=0.05,
        state_history=[],
        state_sequence=[TemporalState.HOLDING.value, TemporalState.FALLING.value, TemporalState.IMPACT.value],
    )

    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[carton], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])
    
    result = engine.evaluate_frame(frame_tracks, frame_interactions, {1: timeline})
    assert len(result.active_behaviours) == 1
    assert result.active_behaviours[0].behaviour_type == BehaviourType.B01_DROP
    assert result.active_behaviours[0].severity in (BehaviourSeverity.HIGH, BehaviourSeverity.CRITICAL)


def test_b02_drag_detection():
    """Verify B02 Drag detection when carton moves horizontally while held/contacted on floor"""
    engine = BehaviourEngine()
    carton = TrackedObject(
        track_id=2,
        class_name="carton",
        class_id=1,
        confidence=0.92,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[200.0, 400.0, 300.0, 500.0],
        centroid_xy=(250.0, 450.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(20.0, 1.0),
        speed_px_per_sec=20.0,
        age_frames=12,
        hits=12,
        time_since_update=0,
    )
    timeline = EntityTemporalTimeline(
        track_id=2,
        class_name="carton",
        current_state=TemporalState.MOVING,
        state_start_frame=8,
        state_start_time_seconds=0.25,
        current_state_duration_seconds=0.1,
        state_history=[],
        state_sequence=[TemporalState.HOLDING.value, TemporalState.MOVING.value],
    )
    contact_interaction = InteractionEvent(
        interaction_type=InteractionType.CONTACT,
        source_track_id=100,
        target_track_id=2,
        source_class="person",
        target_class="carton",
        confidence=0.90,
        distance_px=5.0,
        iou=0.3,
        relative_speed_px_per_sec=20.0,
        start_frame=8,
        end_frame=12,
        duration_seconds=0.15,
    )

    frame_tracks = FrameTracks(frame_index=12, timestamp_seconds=0.4, active_tracks=[carton], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=12, timestamp_seconds=0.4, interactions=[contact_interaction])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {2: timeline})
    assert len(result.active_behaviours) >= 1
    assert any(b.behaviour_type == BehaviourType.B02_DRAG for b in result.active_behaviours)


def test_b03_throw_detection():
    """Verify B03 Throw detection when package moves at high ballistic speed without hold"""
    engine = BehaviourEngine()
    carton = TrackedObject(
        track_id=3,
        class_name="carton",
        class_id=1,
        confidence=0.93,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[200.0, 200.0, 300.0, 300.0],
        centroid_xy=(250.0, 250.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(45.0, 10.0),
        speed_px_per_sec=46.0,
        age_frames=15,
        hits=15,
        time_since_update=0,
    )
    timeline = EntityTemporalTimeline(
        track_id=3,
        class_name="carton",
        current_state=TemporalState.MOVING,
        state_start_frame=10,
        state_start_time_seconds=0.3,
        current_state_duration_seconds=0.15,
        state_history=[],
        state_sequence=[TemporalState.RELEASED.value, TemporalState.MOVING.value],
    )

    frame_tracks = FrameTracks(frame_index=15, timestamp_seconds=0.5, active_tracks=[carton], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=15, timestamp_seconds=0.5, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {3: timeline})
    assert len(result.active_behaviours) == 1
    assert result.active_behaviours[0].behaviour_type == BehaviourType.B03_THROW
    assert result.active_behaviours[0].severity == BehaviourSeverity.CRITICAL


def test_b11_stepping_on_carton():
    """Verify B11 Stepping on carton detection"""
    engine = BehaviourEngine()
    person = TrackedObject(
        track_id=10,
        class_name="person",
        class_id=0,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 50.0, 180.0, 210.0],
        centroid_xy=(140.0, 130.0),
        width_px=80.0,
        height_px=160.0,
        area_px=12800.0,
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=20,
        hits=20,
        time_since_update=0,
    )
    carton = TrackedObject(
        track_id=20,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[90.0, 200.0, 200.0, 280.0],
        centroid_xy=(145.0, 240.0),
        width_px=110.0,
        height_px=80.0,
        area_px=8800.0,
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=20,
        hits=20,
        time_since_update=0,
    )
    stepping_interaction = InteractionEvent(
        interaction_type=InteractionType.CONTACT,
        source_track_id=10,
        target_track_id=20,
        source_class="person",
        target_class="carton",
        confidence=0.95,
        distance_px=0.0,
        iou=0.25,
        relative_speed_px_per_sec=0.0,
        start_frame=15,
        end_frame=20,
        duration_seconds=0.16,
    )

    frame_tracks = FrameTracks(frame_index=20, timestamp_seconds=0.66, active_tracks=[person, carton], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=20, timestamp_seconds=0.66, interactions=[stepping_interaction])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    assert len(result.active_behaviours) == 1
    assert result.active_behaviours[0].behaviour_type == BehaviourType.B11_STEPPING_ON_CARTON
    assert result.active_behaviours[0].severity == BehaviourSeverity.CRITICAL
