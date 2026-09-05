"""
Level 12 Human-Object-Equipment Interaction Engine Verification Tests
"""
from ai.interaction.interaction_detector import InteractionDetector
from ai.interaction.interaction_schemas import InteractionType
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


def test_person_carton_holding_and_carrying_interaction():
    """Verify holding and carrying interaction detection between person and carton"""
    detector = InteractionDetector()

    # Person track
    person = TrackedObject(
        track_id=1,
        class_id=0,
        class_name="person",
        state=TrackState.TRACKED,
        confidence=0.92,
        current_bbox=[100.0, 100.0, 200.0, 300.0],
        current_centroid=(150.0, 200.0),
        velocity_xy=(20.0, 0.0),
        speed_px_per_sec=20.0,
    )

    # Carton carried by person (close proximity, overlapping bbox, matching velocity)
    carton = TrackedObject(
        track_id=2,
        class_id=1,
        class_name="carton",
        state=TrackState.TRACKED,
        confidence=0.88,
        current_bbox=[120.0, 180.0, 180.0, 240.0],
        current_centroid=(150.0, 210.0),
        velocity_xy=(19.0, 0.0),
        speed_px_per_sec=19.0,
    )

    frame_tracks = FrameTracks(
        frame_index=0,
        source_frame_number=0,
        timestamp_seconds=0.0,
        active_tracks=[person, carton],
    )

    result = detector.detect_interactions(frame_tracks)
    assert len(result.interactions) == 1
    interaction = result.interactions[0]
    assert interaction.interaction_type in (
        InteractionType.CARRYING,
        InteractionType.HOLDING,
    )
    assert interaction.source_track_id == 1
    assert interaction.target_track_id == 2


def test_equipment_person_collision_risk_interaction():
    """Verify collision risk detection between moving forklift and nearby person"""
    detector = InteractionDetector()

    forklift = TrackedObject(
        track_id=5,
        class_id=4,
        class_name="forklift",
        state=TrackState.TRACKED,
        confidence=0.95,
        current_bbox=[300.0, 300.0, 500.0, 500.0],
        current_centroid=(400.0, 400.0),
        speed_px_per_sec=45.0,
    )

    pedestrian = TrackedObject(
        track_id=8,
        class_id=0,
        class_name="person",
        state=TrackState.TRACKED,
        confidence=0.91,
        current_bbox=[480.0, 350.0, 550.0, 480.0],
        current_centroid=(515.0, 415.0),
        speed_px_per_sec=10.0,
    )

    frame_tracks = FrameTracks(
        frame_index=10,
        source_frame_number=30,
        timestamp_seconds=1.0,
        active_tracks=[forklift, pedestrian],
    )

    result = detector.detect_interactions(frame_tracks)
    assert len(result.interactions) == 1
    interaction = result.interactions[0]
    assert interaction.interaction_type == InteractionType.COLLISION_RISK
