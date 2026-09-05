"""
Level 11 Spatial Geometry & Zone Intelligence Verification Tests
"""
from ai.spatial.zone_geometry import SpatialGeometryEngine, ZoneDefinition
from ai.tracking.tracker_schemas import TrackedObject, TrackState


def test_point_in_polygon_ray_casting():
    """Verify point-in-polygon ray casting algorithm"""
    # Square polygon [0,0] to [100,100]
    polygon = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]

    # Point inside
    assert SpatialGeometryEngine.point_in_polygon((50.0, 50.0), polygon) is True
    # Point on outer perimeter
    assert SpatialGeometryEngine.point_in_polygon((150.0, 50.0), polygon) is False
    assert SpatialGeometryEngine.point_in_polygon((-10.0, 50.0), polygon) is False


def test_bbox_distance_and_euclidean_distance():
    """Verify minimum distance calculation between non-overlapping bounding boxes"""
    bbox1 = [0.0, 0.0, 10.0, 10.0]
    bbox2 = [20.0, 0.0, 30.0, 10.0]

    # Distance should be 20 - 10 = 10
    dist = SpatialGeometryEngine.bbox_distance(bbox1, bbox2)
    assert dist == 10.0

    # Overlapping boxes have 0 distance
    bbox3 = [5.0, 5.0, 15.0, 15.0]
    assert SpatialGeometryEngine.bbox_distance(bbox1, bbox3) == 0.0


def test_evaluate_zones_and_restricted_violations():
    """Verify zone occupancy evaluation and restricted violation detection"""
    zone_safe = ZoneDefinition(
        zone_id="z-storage-01",
        name="Storage A",
        zone_type="STORAGE",
        polygon=[(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)],
        is_restricted=False,
    )
    zone_danger = ZoneDefinition(
        zone_id="z-danger-01",
        name="Forklift Transit High-Risk",
        zone_type="DANGER",
        polygon=[(300.0, 300.0), (500.0, 300.0), (500.0, 500.0), (300.0, 500.0)],
        is_restricted=True,
    )

    track_inside_danger = TrackedObject(
        track_id=10,
        class_id=0,
        class_name="person",
        state=TrackState.TRACKED,
        confidence=0.92,
        current_bbox=[350.0, 350.0, 400.0, 450.0],
        current_centroid=(375.0, 400.0),
    )

    occupancy = SpatialGeometryEngine.evaluate_zones(
        track_inside_danger, [zone_safe, zone_danger]
    )
    assert len(occupancy) == 1
    assert occupancy[0].zone_name == "Forklift Transit High-Risk"
    assert occupancy[0].is_restricted_violation is True
