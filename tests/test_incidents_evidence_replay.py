"""
Level 20, 21, 22 Incident Management, Evidence Package, and Replay Tests
"""
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
)
from ai.evidence.evidence_generator import EvidenceGenerator
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState


def test_evidence_manifest_generation_and_hash():
    """Verify SHA-256 tamper-proof evidence manifest generation"""
    behaviour = DetectedBehaviour(
        behaviour_type=BehaviourType.B01_DROP,
        severity=BehaviourSeverity.HIGH,
        start_frame=1,
        end_frame=3,
        start_time_seconds=0.033,
        end_time_seconds=0.099,
        duration_seconds=0.066,
        confidence=0.95,
        description="Drop detected",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_DROP",
            primary_entity_id=1,
            primary_class="carton",
        ),
        keyframe_indices=[1, 3],
    )

    t1 = TrackedObject(
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
        velocity_xy=(0.0, 20.0),
        speed_px_per_sec=20.0,
        age_frames=1,
        hits=1,
        time_since_update=0,
    )
    ft1 = FrameTracks(frame_index=1, timestamp_seconds=0.033, active_tracks=[t1], lost_tracks=[], removed_tracks=[])
    ft3 = FrameTracks(frame_index=3, timestamp_seconds=0.099, active_tracks=[t1], lost_tracks=[], removed_tracks=[])

    tracks_by_frame = {1: ft1, 3: ft3}

    manifest = EvidenceGenerator.generate_manifest(
        incident_id="inc-123",
        video_id="vid-456",
        behaviour=behaviour,
        tracks_by_frame=tracks_by_frame,
    )

    assert manifest.incident_id == "inc-123"
    assert len(manifest.keyframes) == 2
    assert len(manifest.clip_sha256) == 64  # SHA-256 hex string length
    assert manifest.keyframes[0].overlay_boxes[0].is_primary is True
    assert manifest.keyframes[0].overlay_boxes[0].track_id == 1
