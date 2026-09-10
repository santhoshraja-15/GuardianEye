"""
Canonical Spatial Coordinate Transformation Layer

    VIDEO PIXEL SPACE  →  NORMALIZED SPACE (0-1)  →  ZONE-PLANE SPACE  →  WORLD SPACE (meters)

This is the single place in the codebase that converts a detection's
bounding box into a spatial anchor point and carries that point through
every coordinate space GuardianEye uses. Before this module existed,
each consumer (behaviour zone-matching, the digital-twin service, the
frontend map) picked its own ad-hoc combination of raw pixel centroid,
"meters", and an arbitrary 0-1000 zone-authoring plane, compared them
directly, and produced spatially wrong results (see the anchor-point and
zone-plane sections of the architecture audit). Every consumer should
call through here instead of re-deriving any of this math locally.

Anchor point convention (spec-mandated): the anchor is the object's
ground-contact point, not the bounding-box center. A tall person
standing at floor position (x, y) does not visually "float" at their
own vertical midpoint — using bbox center for a 2m-tall bounding box
would place them ~1m off from their true floor position. Bottom-center
of the bbox is the standard, well-understood approximation of this.

Coordinate spaces, precisely:

  * VIDEO PIXEL   — raw detector/tracker output, in the source video's
                    own pixel grid (0..video.width, 0..video.height).
  * NORMALIZED    — pixel / (frame_width, frame_height), always 0..1
                    regardless of source resolution. This is what makes
                    a 848x478 clip and a 1920x1080 clip comparable.
  * ZONE-PLANE     — the coordinate system Zone.polygon_coordinates are
                    authored in. This project's seeded zones use an
                    arbitrary but *consistent* ~0-1000 authoring plane
                    (see backend/app/database/seed.py) that has no
                    declared physical extent — it is a layout plane, not
                    meters. Comparing a zone polygon in this plane
                    against a raw video-pixel point is the exact bug
                    documented in the architecture audit (zone
                    attribution for B02/B07/B15 compared incompatible
                    spaces). Going through NORMALIZED first makes the
                    comparison valid regardless of each zone's own
                    authored scale, by normalizing the zone-plane
                    against its own bounding box — the same technique
                    analytics_service._real_heatmap already uses for the
                    dashboard heatmap. This module is that technique,
                    factored out so every consumer (analytics, digital
                    twin, zone-matching) shares one implementation
                    instead of three that could quietly drift apart.
  * WORLD (meters) — only meaningful once a camera has a real
                    calibration (a homography solved from operator-
                    supplied point correspondences, see
                    backend/app/services/calibration_service.py). Until
                    a camera is calibrated, callers get an explicit
                    UNCALIBRATED_ESTIMATE quality flag alongside a
                    best-effort linear estimate — never a silently
                    fabricated precise-looking coordinate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

Point2D = Tuple[float, float]

# Anchor-point rule per entity class. "bottom_center" is the footpoint
# (ground-contact) convention; "centroid" is used for classes where the
# bounding box roughly already tracks the object's own resting point
# (a fallen/rolling carton, a pallet) rather than a tall standing body.
_FOOTPOINT_CLASSES = {
    "person": "bottom_center",
    "forklift": "bottom_center",
    "trolley": "bottom_center",
    "equipment": "bottom_center",
}
_DEFAULT_ANCHOR_MODE = "centroid"


@dataclass
class CalibrationQuality:
    """How much to trust a world-space position. Never hide this from a
    caller that renders it — an uncalibrated estimate rendered with the
    same visual confidence as a calibrated one is a trust problem, not
    a polish problem (spec section 34)."""

    status: str  # "CALIBRATED" | "UNCALIBRATED_ESTIMATE" | "NO_WAREHOUSE_EXTENT"
    reprojection_error_px: Optional[float] = None


def anchor_point(bbox_xyxy: Sequence[float], class_name: str) -> Point2D:
    """The object's ground-contact point in video pixel space.

    People/forklifts/trolleys/equipment: bottom-center of the bbox — the
    point where the entity actually touches the floor, so a tall bbox
    doesn't drag the reported position toward the entity's own vertical
    midpoint. Everything else (cartons, pallets, generic classes):
    bbox centroid, which is already a reasonable stand-in for a mostly
    box-shaped object's own footprint center.
    """
    x1, y1, x2, y2 = bbox_xyxy[0], bbox_xyxy[1], bbox_xyxy[2], bbox_xyxy[3]
    mode = _FOOTPOINT_CLASSES.get(class_name, _DEFAULT_ANCHOR_MODE)
    if mode == "bottom_center":
        return ((x1 + x2) / 2.0, max(y1, y2))
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def normalize(point: Point2D, frame_width: float, frame_height: float) -> Point2D:
    """Video pixel point -> 0..1 normalized, independent of source resolution."""
    w = frame_width if frame_width and frame_width > 0 else 1.0
    h = frame_height if frame_height and frame_height > 0 else 1.0
    return (
        max(0.0, min(1.0, point[0] / w)),
        max(0.0, min(1.0, point[1] / h)),
    )


def zone_plane_bounds(zone_polygons: Sequence[Sequence[Point2D]]) -> Tuple[float, float, float, float]:
    """Bounding box (min_x, max_x, min_y, max_y) of every configured
    zone's own vertices — the zone-authoring plane's real extent, since
    nothing declares it explicitly. Falls back to a unit box when there
    are no zones at all (an empty warehouse has no plane to normalize
    against, not a "1000x1000" one)."""
    all_points = [pt for poly in zone_polygons for pt in poly]
    if not all_points:
        return (0.0, 1.0, 0.0, 1.0)
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x - min_x <= 0:
        max_x = min_x + 1.0
    if max_y - min_y <= 0:
        max_y = min_y + 1.0
    return (min_x, max_x, min_y, max_y)


def normalize_zone_polygons(
    zone_polygons: dict,
) -> dict:
    """Convenience wrapper around zone_plane_bounds +
    zone_plane_point_to_normalized: given {code: [(x,y), ...]} in the
    zone-authoring plane, returns the same shape normalized to 0-1
    against the combined bounding box of every polygon. This is the one
    implementation every consumer that needs "zones on a 0-1 plane"
    should call — analytics_service (dashboard heatmap),
    digital_twin_service (twin map), and ai.pipeline_runner
    (zone-matching for behaviour/event detection) all use this same
    function rather than three independent reimplementations that could
    quietly drift apart."""
    bounds = zone_plane_bounds(list(zone_polygons.values()))
    return {
        code: [zone_plane_point_to_normalized(p, bounds) for p in polygon]
        for code, polygon in zone_polygons.items()
    }


def zone_plane_point_to_normalized(
    point: Point2D, bounds: Tuple[float, float, float, float]
) -> Point2D:
    """A point already in zone-authoring-plane units -> 0..1, normalized
    against that plane's own bounding box (see module docstring)."""
    min_x, max_x, min_y, max_y = bounds
    return (
        max(0.0, min(1.0, (point[0] - min_x) / (max_x - min_x))),
        max(0.0, min(1.0, (point[1] - min_y) / (max_y - min_y))),
    )


def normalized_video_point_to_zone_plane(
    normalized_point: Point2D, bounds: Tuple[float, float, float, float]
) -> Point2D:
    """A 0..1 normalized VIDEO point -> a point in the zone-authoring
    plane's own units, so it can be compared with
    ai.spatial.zone_geometry.point_in_polygon against raw zone
    polygons. This is the missing link that made zone-matching compare
    incompatible spaces: a track's normalized position is scaled up
    into the same units the zone polygons were authored in, rather than
    comparing raw video pixels against them directly."""
    min_x, max_x, min_y, max_y = bounds
    return (
        min_x + normalized_point[0] * (max_x - min_x),
        min_y + normalized_point[1] * (max_y - min_y),
    )


def world_position(
    normalized_point: Point2D,
    homography_matrix: Optional[List[List[float]]],
    warehouse_width_m: Optional[float],
    warehouse_length_m: Optional[float],
    reprojection_error_px: Optional[float] = None,
) -> Tuple[Point2D, CalibrationQuality]:
    """Best available real-world (meters) position for a normalized
    video point.

    If the camera has a real homography (see calibration_service, which
    solves one from operator-supplied point correspondences via
    cv2.findHomography), apply it — this is the only path that can
    honestly be labeled CALIBRATED.

    Otherwise, fall back to a linear estimate against the warehouse's
    declared physical footprint (width_meters/length_meters) — this is
    NOT a real perspective-correct transform (it assumes the camera's
    normalized frame maps linearly onto the whole warehouse floor,
    which is only roughly true for a top-down or wide establishing
    shot), so it is always returned with an UNCALIBRATED_ESTIMATE
    quality flag rather than presented as equivalent to a calibrated
    position.
    """
    if homography_matrix:
        try:
            import numpy as np
            import cv2

            h = np.array(homography_matrix, dtype="float64")
            src = np.array([[[normalized_point[0], normalized_point[1]]]], dtype="float64")
            dst = cv2.perspectiveTransform(src, h)
            wx, wy = float(dst[0][0][0]), float(dst[0][0][1])
            return (wx, wy), CalibrationQuality(
                status="CALIBRATED", reprojection_error_px=reprojection_error_px
            )
        except Exception:
            pass  # fall through to the uncalibrated estimate below

    if not warehouse_width_m or not warehouse_length_m:
        return (normalized_point[0], normalized_point[1]), CalibrationQuality(
            status="NO_WAREHOUSE_EXTENT"
        )

    return (
        (normalized_point[0] * warehouse_width_m, normalized_point[1] * warehouse_length_m),
        CalibrationQuality(status="UNCALIBRATED_ESTIMATE"),
    )


def solve_homography(
    source_points: Sequence[Point2D], world_points: Sequence[Point2D]
) -> Tuple[Optional[List[List[float]]], Optional[float]]:
    """Solve a homography from >=4 (normalized video point, world meters
    point) correspondences via cv2.findHomography, and report the mean
    reprojection error in the source (normalized-video) unit as an
    honest calibration-quality number. Returns (None, None) if fewer
    than 4 points are given or the solve fails — never a guessed
    matrix."""
    if len(source_points) < 4 or len(world_points) < 4 or len(source_points) != len(world_points):
        return None, None

    import numpy as np
    import cv2

    src = np.array(source_points, dtype="float64")
    dst = np.array(world_points, dtype="float64")
    matrix, _ = cv2.findHomography(src, dst, method=0)
    if matrix is None:
        return None, None

    # Reprojection error: transform every source point through the
    # solved homography and compare against the operator-supplied world
    # point they were meant to land on.
    projected = cv2.perspectiveTransform(src.reshape(-1, 1, 2), matrix).reshape(-1, 2)
    errors = [
        ((projected[i][0] - dst[i][0]) ** 2 + (projected[i][1] - dst[i][1]) ** 2) ** 0.5
        for i in range(len(dst))
    ]
    mean_error = sum(errors) / len(errors)
    return matrix.tolist(), round(float(mean_error), 4)
