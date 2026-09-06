"""
Spatial Geometry, Point-in-Polygon, and Zone Transition Engine
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
    entity-to-zone proximity, inter-entity Euclidean distances, and zone transition events.
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
    def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points"""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return math.sqrt(dx * dx + dy * dy)

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
                        distance_to_boundary_px=0.0,
                        is_restricted_violation=is_violation,
                    )
                )

        return results


spatial_engine = SpatialGeometryEngine()
