"""
Spatial Geometry and Point-in-Polygon Primitives

Zone *transition* detection (an entity crossing from one zone into
another) and proximity events live in ai/spatial/event_engine.py, which
is built on top of the primitives here — point_in_polygon,
distance_to_boundary, bbox_distance. This module only answers "is this
point inside this polygon / how far from its edge / how far from that
other box" — it holds no per-track state and emits no events itself.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Union
from ai.tracking.tracker_schemas import TrackedObject


@dataclass
class Point:
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class ZoneDefinition:
    zone_id: str
    name: str
    zone_type: str  # STORAGE, LOADING_BAY, DANGER, RESTRICTED, TRANSIT, STAGING
    polygon: List[Tuple[float, float]]  # List of (x, y) coordinates
    risk_weight: float = 1.0
    is_restricted: bool = False


@dataclass
class SpatialOccupancy:
    track_id: int
    class_name: str
    zone_id: str
    zone_name: str
    zone_type: str
    is_inside: bool
    distance_to_boundary_px: float
    is_restricted_violation: bool


@dataclass
class PolygonZone:
    name: str = ""
    polygon: List[Tuple[float, float]] = field(default_factory=list)
    zone_id: Optional[str] = None
    zone_code: Optional[str] = None
    zone_type: str = "GENERIC"
    points: Optional[List[Point]] = None
    risk_multiplier: float = 1.0
    risk_weight: float = 1.0
    is_restricted: bool = False

    def __post_init__(self):
        if not self.name and self.zone_code:
            self.name = self.zone_code
        elif not self.name and self.zone_id:
            self.name = self.zone_id
        if self.points and not self.polygon:
            self.polygon = [p.to_tuple() for p in self.points]
        elif self.polygon and not self.points:
            self.points = [Point(x, y) for x, y in self.polygon]

    def contains_point(self, point: Point | Tuple[float, float]) -> bool:
        pt = point.to_tuple() if isinstance(point, Point) else point
        return SpatialGeometryEngine.point_in_polygon(pt, self.polygon)


class ZoneEvaluator:
    """Evaluates spatial inclusion of points/tracks across polygon zones"""

    def __init__(self, zones: Optional[List[PolygonZone]] = None):
        self.zones = zones or []

    @staticmethod
    def is_point_inside(point: Point | Tuple[float, float], zone: PolygonZone | ZoneDefinition) -> bool:
        if isinstance(zone, PolygonZone):
            return zone.contains_point(point)
        pt = point.to_tuple() if isinstance(point, Point) else point
        return SpatialGeometryEngine.point_in_polygon(pt, zone.polygon)

    def evaluate(self, track: TrackedObject) -> List[PolygonZone]:
        centroid = getattr(track, "current_centroid", None) or getattr(track, "centroid_xy", (0.0, 0.0))
        pt = Point(centroid[0], centroid[1])
        return [zone for zone in self.zones if zone.contains_point(pt)]


class SpatialGeometryEngine:
    """
    Mathematical spatial geometry engine evaluating point-in-polygon ray casting,
    entity-to-zone boundary proximity, and inter-entity Euclidean distances.
    """

    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        """
        Ray-casting algorithm determining whether a point (x, y) lies inside a 2D polygon
        """
        x, y = point
        n = len(polygon)
        if n < 3:
            return False

        inside = False
        p1x, p1y = polygon[0]

        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def polygon_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Simple vertex-average centroid — sufficient for the roughly
        rectangular warehouse zones this app configures, and exact for any
        polygon when computing "where is this zone, roughly" rather than
        needing the area-weighted centroid of an irregular shape."""
        if not polygon:
            return (0.0, 0.0)
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    @staticmethod
    def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points"""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def _point_to_segment_distance(
        p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]
    ) -> float:
        """Shortest distance from point p to the segment a-b."""
        px, py = p
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
        proj_x, proj_y = ax + t * dx, ay + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    @staticmethod
    def distance_to_boundary(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> float:
        """Real shortest distance from a point to the polygon's boundary
        (minimum over every edge segment) — used to know how close an
        entity is to leaving/entering a zone, not just whether it
        already has. Returns 0.0 only for a degenerate (<2-vertex)
        polygon, never as a stand-in for "not computed"."""
        if len(polygon) < 2:
            return 0.0
        n = len(polygon)
        return min(
            SpatialGeometryEngine._point_to_segment_distance(point, polygon[i], polygon[(i + 1) % n])
            for i in range(n)
        )

    @staticmethod
    def bbox_distance(bbox1: List[float], bbox2: List[float]) -> float:
        """
        Calculate minimum distance between two non-overlapping bounding boxes.
        Returns 0.0 if bounding boxes intersect.
        """
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2

        left = x2_max < x1_min
        right = x1_max < x2_min
        bottom = y2_max < y1_min
        top = y1_max < y2_min

        if top and left:
            return SpatialGeometryEngine.euclidean_distance((x1_min, y1_max), (x2_max, y2_min))
        elif left and bottom:
            return SpatialGeometryEngine.euclidean_distance((x1_min, y1_min), (x2_max, y2_max))
        elif bottom and right:
            return SpatialGeometryEngine.euclidean_distance((x1_max, y1_min), (x2_min, y2_max))
        elif right and top:
            return SpatialGeometryEngine.euclidean_distance((x1_max, y1_max), (x2_min, y2_min))
        elif left:
            return x1_min - x2_max
        elif right:
            return x2_min - x1_max
        elif bottom:
            return y1_min - y2_max
        elif top:
            return y2_min - y1_max
        else:
            return 0.0  # Overlapping / Intersecting

    @staticmethod
    def evaluate_zones(
        track: TrackedObject, zones: List[ZoneDefinition]
    ) -> List[SpatialOccupancy]:
        """
        Evaluate which warehouse zones contain the tracked entity and detect safety violations
        """
        results: List[SpatialOccupancy] = []
        cx, cy = track.current_centroid

        for zone in zones:
            is_inside = SpatialGeometryEngine.point_in_polygon((cx, cy), zone.polygon)
            is_violation = is_inside and zone.is_restricted

            if is_inside:
                results.append(
                    SpatialOccupancy(
                        track_id=track.track_id,
                        class_name=track.class_name,
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        zone_type=zone.zone_type,
                        is_inside=True,
                        distance_to_boundary_px=SpatialGeometryEngine.distance_to_boundary((cx, cy), zone.polygon),
                        is_restricted_violation=is_violation,
                    )
                )

        return results


spatial_engine = SpatialGeometryEngine()
