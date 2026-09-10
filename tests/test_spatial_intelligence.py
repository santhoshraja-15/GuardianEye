"""
Tests for the Spatial Intelligence Engine rebuild — canonical coordinate
transform, camera calibration, zone-transition/proximity event
detection, and the Digital Twin's real (not fabricated) entity count.
Uses a throwaway in-memory SQLite session, same pattern as
test_analytics_service.py / test_temporal_intelligence.py.
"""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai.spatial.coordinate_transform import (
    anchor_point,
    normalize,
    normalize_zone_polygons,
    solve_homography,
    world_position,
)
from ai.spatial.event_engine import ProximityEngine, ZoneTransitionEngine
from ai.spatial.zone_geometry import PolygonZone, SpatialGeometryEngine
from ai.tracking.tracker_schemas import TrackedObject, TrackState
from backend.app.core.errors import NotFoundException
from backend.app.database.session import Base
from backend.app.models.calibration import Calibration  # noqa: F401
from backend.app.models.spatial_event import SpatialEvent  # noqa: F401
from backend.app.models.tracking import Track, TrackPoint  # noqa: F401
from backend.app.models.user import User  # noqa: F401
from backend.app.models.video import Video  # noqa: F401
from backend.app.models.warehouse import Camera, Warehouse, Zone  # noqa: F401
from backend.app.schemas.camera import CalibrationCreate, CalibrationPointPair
from backend.app.services.calibration_service import calibration_service
from backend.app.services.digital_twin_service import digital_twin_service


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _track(track_id, class_name, bbox, confidence=0.9):
    return TrackedObject(
        track_id=track_id,
        class_id=0,
        class_name=class_name,
        state=TrackState.TRACKED,
        confidence=confidence,
        current_bbox=bbox,
        current_centroid=((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2),
    )


# ── anchor point / normalization ──────────────────────────────────────

def test_anchor_point_uses_footpoint_for_people():
    # A 2m-tall bbox: bbox-center would misplace the person a full body-
    # height off from where they're actually standing.
    bbox = [100.0, 50.0, 140.0, 250.0]
    x, y = anchor_point(bbox, "person")
    assert x == pytest.approx(120.0)
    assert y == pytest.approx(250.0)  # bottom of bbox, not the 150.0 vertical midpoint


def test_anchor_point_uses_centroid_for_cartons():
    bbox = [100.0, 50.0, 140.0, 250.0]
    x, y = anchor_point(bbox, "carton")
    assert x == pytest.approx(120.0)
    assert y == pytest.approx(150.0)


def test_normalize_scales_by_frame_dimensions():
    assert normalize((960.0, 540.0), 1920.0, 1080.0) == pytest.approx((0.5, 0.5))
    # Out-of-frame points are clamped into 0-1, never negative or >1.
    assert normalize((-50.0, 5000.0), 1920.0, 1080.0) == (0.0, 1.0)


def test_normalize_zone_polygons_uses_combined_bounding_box():
    zones = {
        "A": [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        "B": [(100.0, 100.0), (200.0, 100.0), (200.0, 200.0), (100.0, 200.0)],
    }
    normalized = normalize_zone_polygons(zones)
    # Combined bbox is (0,0)-(200,200); zone A's corner (0,0) -> (0,0),
    # zone B's corner (200,200) -> (1,1).
    assert normalized["A"][0] == pytest.approx((0.0, 0.0))
    assert normalized["B"][2] == pytest.approx((1.0, 1.0))


# ── homography / world position ───────────────────────────────────────

def test_solve_homography_round_trips_a_simple_scale():
    # 4 correspondences describing "normalized video point * 10 = world
    # meters" — an exact, solvable relationship.
    source = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    world = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    matrix, error = solve_homography(source, world)
    assert matrix is not None
    assert error == pytest.approx(0.0, abs=1e-6)

    (wx, wy), quality = world_position((0.5, 0.5), matrix, None, None)
    assert wx == pytest.approx(5.0, abs=1e-6)
    assert wy == pytest.approx(5.0, abs=1e-6)
    assert quality.status == "CALIBRATED"


def test_solve_homography_refuses_fewer_than_four_points():
    matrix, error = solve_homography([(0.0, 0.0)], [(0.0, 0.0)])
    assert matrix is None
    assert error is None


def test_world_position_uncalibrated_fallback_is_labeled_honestly():
    (wx, wy), quality = world_position((0.5, 0.25), None, 100.0, 40.0)
    assert (wx, wy) == pytest.approx((50.0, 10.0))
    assert quality.status == "UNCALIBRATED_ESTIMATE"


def test_world_position_with_no_warehouse_extent_is_labeled_honestly():
    (wx, wy), quality = world_position((0.5, 0.5), None, None, None)
    assert quality.status == "NO_WAREHOUSE_EXTENT"


# ── distance_to_boundary (previously hardcoded 0.0) ───────────────────

def test_distance_to_boundary_is_a_real_measurement():
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    # Center of the square is 5 units from every edge.
    assert SpatialGeometryEngine.distance_to_boundary((5.0, 5.0), square) == pytest.approx(5.0)
    # A point sitting exactly on an edge is 0 away from it.
    assert SpatialGeometryEngine.distance_to_boundary((5.0, 0.0), square) == pytest.approx(0.0)


# ── zone transition engine ────────────────────────────────────────────

def _zone(zone_id, code, polygon, is_restricted=False):
    return PolygonZone(zone_id=zone_id, zone_code=code, polygon=polygon, is_restricted=is_restricted)


def test_zone_transition_enter_then_exit():
    zones = {"DOCK": _zone("z-dock", "DOCK", [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)])}
    engine = ZoneTransitionEngine()
    track = _track(1, "person", [40.0, 40.0, 60.0, 100.0])  # normalized ~ (0.05, 0.1) inside DOCK @ 1000x1000

    entered = engine.evaluate(track, zones, frame_width=1000.0, frame_height=1000.0)
    assert entered is not None
    assert entered.event_type == "ZONE_ENTERED"

    # Same position next frame -> no new event.
    assert engine.evaluate(track, zones, frame_width=1000.0, frame_height=1000.0) is None

    # Move outside the zone entirely.
    track_outside = _track(1, "person", [900.0, 900.0, 920.0, 980.0])
    exited = engine.evaluate(track_outside, zones, frame_width=1000.0, frame_height=1000.0)
    assert exited is not None
    assert exited.event_type == "ZONE_EXITED"


def test_zone_transition_restricted_zone_is_high_severity():
    zones = {
        "RESTRICTED": _zone(
            "z-r", "RESTRICTED", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], is_restricted=True
        )
    }
    engine = ZoneTransitionEngine()
    track = _track(2, "person", [400.0, 400.0, 420.0, 480.0])
    event = engine.evaluate(track, zones, frame_width=1000.0, frame_height=1000.0)
    assert event is not None
    assert event.severity == "HIGH"


def test_proximity_engine_fires_once_per_approach():
    engine = ProximityEngine()
    person = _track(1, "person", [500.0, 500.0, 520.0, 600.0])
    forklift_far = _track(2, "forklift", [10.0, 10.0, 60.0, 60.0])
    forklift_near = _track(2, "forklift", [505.0, 505.0, 555.0, 555.0])

    assert engine.evaluate([person, forklift_far], 1000.0, 1000.0) == []

    first = engine.evaluate([person, forklift_near], 1000.0, 1000.0)
    assert len(first) == 1
    assert first[0].event_type == "PROXIMITY_WARNING"

    # Still close next frame -> no repeat event.
    assert engine.evaluate([person, forklift_near], 1000.0, 1000.0) == []


# ── calibration service ────────────────────────────────────────────────

def _make_warehouse_with_camera(db):
    warehouse = Warehouse(name="WH Test", code="WH-T", width_meters=100.0, length_meters=80.0)
    db.add(warehouse)
    db.flush()
    camera = Camera(warehouse_id=warehouse.id, name="Cam 1", camera_code="CAM-T-01")
    db.add(camera)
    db.commit()
    return warehouse, camera


def test_calibration_service_solves_and_persists(db_session):
    _, camera = _make_warehouse_with_camera(db_session)
    points = [
        CalibrationPointPair(video_point=(0.0, 0.0), world_point=(0.0, 0.0)),
        CalibrationPointPair(video_point=(1.0, 0.0), world_point=(20.0, 0.0)),
        CalibrationPointPair(video_point=(1.0, 1.0), world_point=(20.0, 15.0)),
        CalibrationPointPair(video_point=(0.0, 1.0), world_point=(0.0, 15.0)),
    ]
    calibration = calibration_service.save_calibration(
        db_session, camera.id, CalibrationCreate(points=points), user_id=None
    )
    assert calibration.homography_json is not None
    assert calibration.reprojection_error < 0.01

    matrix, error = calibration_service.get_active_homography(db_session, camera.id)
    assert matrix is not None
    assert error < 0.01


def test_calibration_service_rejects_degenerate_points(db_session):
    from backend.app.core.errors import ValidationException

    _, camera = _make_warehouse_with_camera(db_session)
    # All 4 points identical -> no solvable homography.
    points = [CalibrationPointPair(video_point=(0.5, 0.5), world_point=(1.0, 1.0)) for _ in range(4)]
    with pytest.raises(ValidationException):
        calibration_service.save_calibration(db_session, camera.id, CalibrationCreate(points=points), user_id=None)


def test_uncalibrated_camera_returns_no_homography(db_session):
    _, camera = _make_warehouse_with_camera(db_session)
    matrix, error = calibration_service.get_active_homography(db_session, camera.id)
    assert matrix is None
    assert error is None


# ── digital twin: real entity count, not a fabricated constant ────────

def test_digital_twin_topology_raises_when_no_warehouse_exists(db_session):
    with pytest.raises(NotFoundException):
        digital_twin_service.get_warehouse_topology(db_session, warehouse_id="does-not-exist")


def test_digital_twin_active_entity_count_reflects_real_tracks(db_session):
    warehouse, camera = _make_warehouse_with_camera(db_session)
    video = Video(
        camera_id=camera.id, filename="v.mp4", storage_path="v.mp4", file_size_bytes=1,
        duration_seconds=5.0, fps=10, width=1000, height=1000, codec="h264",
        checksum_sha256="x", status="COMPLETED",
    )
    db_session.add(video)
    db_session.flush()

    for track_id in (1, 2, 3):
        track = Track(
            video_id=video.id, track_id=track_id, class_name="person", confidence=0.9,
            first_frame=0, last_frame=10, duration_seconds=1.0, max_velocity=5.0,
        )
        db_session.add(track)
        db_session.flush()
        db_session.add(
            TrackPoint(
                track_id_fk=track.id, frame_number=10, timestamp_seconds=1.0,
                bbox_x1=0.0, bbox_y1=0.0, bbox_x2=10.0, bbox_y2=10.0,
                centroid_x=5.0, centroid_y=5.0, confidence=0.9,
                anchor_x=5.0, anchor_y=10.0, normalized_x=0.05, normalized_y=0.1,
            )
        )
    db_session.commit()

    topology = digital_twin_service.get_warehouse_topology(db_session, warehouse_id=warehouse.id)

    # The real point: this number comes from counting actual TrackPoint
    # rows, not from a literal constant (12) or len(zones) * 4 — both
    # of which the previous implementation used regardless of what was
    # actually tracked.
    assert topology.active_entity_count == 3
    assert len(topology.entities) == 3
    assert topology.is_live_entity_count is False
    assert {e.track_id for e in topology.entities} == {1, 2, 3}
