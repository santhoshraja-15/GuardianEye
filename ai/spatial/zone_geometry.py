"""
Spatial Geometry, Point-in-Polygon, and Zone Transition Engine
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from ai.tracking.tracker_schemas import TrackedObject


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
