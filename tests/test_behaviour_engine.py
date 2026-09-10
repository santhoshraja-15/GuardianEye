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


def test_b06_unstable_stack_severe_overhang():
    """Verify B06 fires (instead of B05) when the top box is mostly unsupported."""
    engine = BehaviourEngine()
    bottom = TrackedObject(
        track_id=30, class_name="carton", class_id=1, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 300.0, 200.0, 400.0], centroid_xy=(150.0, 350.0),
        width_px=100.0, height_px=100.0, area_px=10000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    top = TrackedObject(
        track_id=31, class_name="carton", class_id=1, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[175.0, 190.0, 275.0, 290.0], centroid_xy=(225.0, 240.0),
        width_px=100.0, height_px=100.0, area_px=10000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[bottom, top], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    unstable = [b for b in result.active_behaviours if b.behaviour_type == BehaviourType.B06_UNSTABLE_STACK]
    assert len(unstable) == 1
    assert unstable[0].severity == BehaviourSeverity.CRITICAL


def test_b06_unstable_stack_tall_single_stack():
    """Verify B06 fires from a single 'stack' track's own height:width aspect ratio."""
    engine = BehaviourEngine()
    stack = TrackedObject(
        track_id=40, class_name="stack", class_id=8, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 50.0, 150.0, 350.0], centroid_xy=(125.0, 200.0),
        width_px=50.0, height_px=300.0, area_px=15000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[stack], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    assert any(b.behaviour_type == BehaviourType.B06_UNSTABLE_STACK for b in result.active_behaviours)


def test_b09_pallet_misalignment():
    """Verify B09 when a load rests on a pallet with under 60% horizontal support."""
    engine = BehaviourEngine()
    pallet = TrackedObject(
        track_id=50, class_name="pallet", class_id=2, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 400.0, 300.0, 450.0], centroid_xy=(200.0, 425.0),
        width_px=200.0, height_px=50.0, area_px=10000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    load = TrackedObject(
        track_id=51, class_name="carton", class_id=1, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[250.0, 300.0, 400.0, 400.0], centroid_xy=(325.0, 350.0),
        width_px=150.0, height_px=100.0, area_px=15000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[pallet, load], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    assert any(b.behaviour_type == BehaviourType.B09_PALLET_MISALIGNMENT for b in result.active_behaviours)


def test_b17_overloading_pallet():
    """Verify B17 when 4+ separate loads rest on one pallet footprint."""
    engine = BehaviourEngine()
    pallet = TrackedObject(
        track_id=60, class_name="pallet", class_id=2, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 400.0, 400.0, 450.0], centroid_xy=(250.0, 425.0),
        width_px=300.0, height_px=50.0, area_px=15000.0,
        velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
    )
    loads = []
    for i in range(4):
        x1 = 110.0 + i * 70.0
        loads.append(
            TrackedObject(
                track_id=61 + i, class_name="carton", class_id=1, confidence=0.9, state=TrackState.CONFIRMED,
                bbox_xyxy=[x1, 340.0, x1 + 60.0, 400.0], centroid_xy=(x1 + 30.0, 370.0),
                width_px=60.0, height_px=60.0, area_px=3600.0,
                velocity_xy=(0.0, 0.0), speed_px_per_sec=0.0, age_frames=10, hits=10, time_since_update=0,
            )
        )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[pallet, *loads], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    assert any(b.behaviour_type == BehaviourType.B17_OVERLOADING_PALLET for b in result.active_behaviours)


def test_b20_collision_risk_converging_forklift():
    """Verify B20 when a forklift and person are close and closing fast."""
    engine = BehaviourEngine()
    forklift = TrackedObject(
        track_id=70, class_name="forklift", class_id=4, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 100.0, 200.0, 200.0], centroid_xy=(150.0, 150.0),
        width_px=100.0, height_px=100.0, area_px=10000.0,
        velocity_xy=(90.0, 0.0), speed_px_per_sec=90.0, age_frames=10, hits=10, time_since_update=0,
    )
    person = TrackedObject(
        track_id=71, class_name="person", class_id=0, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[250.0, 100.0, 300.0, 250.0], centroid_xy=(275.0, 150.0),
        width_px=50.0, height_px=150.0, area_px=7500.0,
        velocity_xy=(-20.0, 0.0), speed_px_per_sec=20.0, age_frames=10, hits=10, time_since_update=0,
    )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[forklift, person], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    collisions = [b for b in result.active_behaviours if b.behaviour_type == BehaviourType.B20_COLLISION_RISK]
    assert len(collisions) == 1
    assert collisions[0].severity == BehaviourSeverity.CRITICAL


def test_b20_no_collision_risk_when_diverging():
    """Verify B20 does not fire when two movers are moving apart, even if close."""
    engine = BehaviourEngine()
    forklift = TrackedObject(
        track_id=80, class_name="forklift", class_id=4, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[100.0, 100.0, 200.0, 200.0], centroid_xy=(150.0, 150.0),
        width_px=100.0, height_px=100.0, area_px=10000.0,
        velocity_xy=(-40.0, 0.0), speed_px_per_sec=40.0, age_frames=10, hits=10, time_since_update=0,
    )
    person = TrackedObject(
        track_id=81, class_name="person", class_id=0, confidence=0.9, state=TrackState.CONFIRMED,
        bbox_xyxy=[250.0, 100.0, 300.0, 250.0], centroid_xy=(275.0, 150.0),
        width_px=50.0, height_px=150.0, area_px=7500.0,
        velocity_xy=(5.0, 0.0), speed_px_per_sec=5.0, age_frames=10, hits=10, time_since_update=0,
    )
    frame_tracks = FrameTracks(frame_index=10, timestamp_seconds=0.33, active_tracks=[forklift, person], lost_tracks=[], removed_tracks=[])
    frame_interactions = FrameInteractions(frame_index=10, timestamp_seconds=0.33, interactions=[])

    result = engine.evaluate_frame(frame_tracks, frame_interactions, {})
    assert not any(b.behaviour_type == BehaviourType.B20_COLLISION_RISK for b in result.active_behaviours)
