"""
Level 13 Temporal State Machine & Sequence Reasoning Tests
"""
from ai.interaction.interaction_schemas import FrameInteractions, InteractionEvent, InteractionType
from ai.temporal.state_machine import TemporalStateMachine
from ai.temporal.temporal_schemas import EntityTemporalTimeline, TemporalState
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


def test_temporal_timeline_initialization():
    """Verify temporal state machine initializes timeline in IDLE state"""
    fsm = TemporalStateMachine()
    track = TrackedObject(
        track_id=1,
        class_name="carton",
        class_id=1,
        confidence=0.92,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 100.0, 200.0, 200.0],
        centroid_xy=(150.0, 150.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=1,
        hits=1,
        time_since_update=0,
    )
    frame_tracks = FrameTracks(
        frame_index=0,
        timestamp_seconds=0.0,
        active_tracks=[track],
        lost_tracks=[],
        removed_tracks=[],
    )
    frame_interactions = FrameInteractions(
        frame_index=0,
        timestamp_seconds=0.0,
        interactions=[],
    )

    timelines = fsm.update(frame_tracks, frame_interactions)
    assert 1 in timelines
    assert timelines[1].current_state == TemporalState.IDLE
    assert timelines[1].class_name == "carton"


def test_temporal_holding_and_falling_transition():
    """Verify state sequence transitions: IDLE -> HOLDING -> FALLING -> IMPACT -> STATIONARY"""
    fsm = TemporalStateMachine()
    
    # 1. Carton in contact / held by person (track_id 10)
    carton_track = TrackedObject(
        track_id=1,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 100.0, 200.0, 200.0],
        centroid_xy=(150.0, 150.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=1,
        hits=1,
        time_since_update=0,
    )
    interaction = InteractionEvent(
        interaction_type=InteractionType.HOLDING,
        source_track_id=10,
        target_track_id=1,
        source_class="person",
        target_class="carton",
        confidence=0.92,
        distance_px=5.0,
        iou=0.45,
        relative_speed_px_per_sec=0.0,
        start_frame=1,
        end_frame=1,
        duration_seconds=0.033,
    )
    
    fsm.update(
        FrameTracks(frame_index=1, timestamp_seconds=0.033, active_tracks=[carton_track], lost_tracks=[], removed_tracks=[]),
        FrameInteractions(frame_index=1, timestamp_seconds=0.033, interactions=[interaction]),
    )
    assert fsm.timelines[1].current_state == TemporalState.HOLDING

    # 2. Release with downward velocity (Falling)
    carton_falling = TrackedObject(
        track_id=1,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 150.0, 200.0, 250.0],
        centroid_xy=(150.0, 200.0),
        width_px=100.0,
        height_px=100.0,
        area_px=10000.0,
        velocity_xy=(0.0, 25.0),
        speed_px_per_sec=25.0,
        age_frames=2,
        hits=2,
        time_since_update=0,
    )
    fsm.update(
        FrameTracks(frame_index=2, timestamp_seconds=0.066, active_tracks=[carton_falling], lost_tracks=[], removed_tracks=[]),
        FrameInteractions(frame_index=2, timestamp_seconds=0.066, interactions=[]),
    )
    assert fsm.timelines[1].current_state == TemporalState.FALLING

    # 3. Sudden stop / deceleration (Impact)
    carton_impact = TrackedObject(
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
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=1.0,
        age_frames=3,
        hits=3,
        time_since_update=0,
    )
    fsm.update(
        FrameTracks(frame_index=3, timestamp_seconds=0.099, active_tracks=[carton_impact], lost_tracks=[], removed_tracks=[]),
        FrameInteractions(frame_index=3, timestamp_seconds=0.099, interactions=[]),
    )
    assert fsm.timelines[1].current_state == TemporalState.IMPACT

    # 4. Stationary settled
    carton_settled = TrackedObject(
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
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=4,
        hits=4,
        time_since_update=0,
    )
    fsm.update(
        FrameTracks(frame_index=4, timestamp_seconds=0.132, active_tracks=[carton_settled], lost_tracks=[], removed_tracks=[]),
        FrameInteractions(frame_index=4, timestamp_seconds=0.132, interactions=[]),
    )
    assert fsm.timelines[1].current_state == TemporalState.STATIONARY
    assert len(fsm.timelines[1].state_history) == 4
