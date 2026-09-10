"""
Tracking Service for Ingesting and Retrieving Entity Trajectories
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from ai.spatial.coordinate_transform import anchor_point, normalize, world_position
from ai.spatial.zone_geometry import Point, PolygonZone
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject
from backend.app.core.errors import NotFoundException
from backend.app.models.tracking import Track, TrackPoint


@dataclass
class SpatialContext:
    """Everything persist_frame_tracks needs to compute a track point's
    footpoint/normalized/zone/world position, bundled once per video
    rather than re-fetched or re-derived on every call. `zones` must
    already be in the same 0-1 normalized plane as a normalized video
    point (see ai.pipeline_runner._load_spatial_zones, which normalizes
    zone polygons against their own combined bounding box before
    anything else touches them — the fix for the video-pixel-vs-zone-
    plane mismatch documented in the architecture audit)."""

    video_width: float = 1920.0
    video_height: float = 1080.0
    warehouse_width_m: Optional[float] = None
    warehouse_length_m: Optional[float] = None
    zones: Dict[str, PolygonZone] = field(default_factory=dict)
    homography_matrix: Optional[List[List[float]]] = None
    reprojection_error_px: Optional[float] = None


class TrackingService:
    """
    Manages persistence and retrieval of multi-object tracks and
    dense trajectory histories.
    """

    @staticmethod
    def get_tracks_for_video(db: Session, video_id: str) -> List[Track]:
        return (
            db.query(Track)
            .filter(Track.video_id == video_id)
            .order_by(Track.first_frame.asc())
            .all()
        )

    @staticmethod
    def get_track_by_id(db: Session, video_id: str, track_id_num: int) -> Track:
        track = (
            db.query(Track)
            .filter(Track.video_id == video_id, Track.track_id == track_id_num)
            .first()
        )
        if not track:
            raise NotFoundException("Track", f"{video_id}:{track_id_num}")
        return track

    @staticmethod
    def _resolve_zone(anchor_norm: Tuple[float, float], zones: Dict[str, PolygonZone]) -> Optional[str]:
        pt = Point(anchor_norm[0], anchor_norm[1])
        for zone in zones.values():
            if zone.contains_point(pt):
                return zone.zone_id
        return None

    @staticmethod
    def persist_frame_tracks(
        db: Session,
        video_id: str,
        frame_tracks: FrameTracks,
        spatial_context: Optional[SpatialContext] = None,
    ):
        """
        Record current frame's active tracks and trajectory points in database.

        When a SpatialContext is supplied, each point also gets a real
        footpoint anchor (ground-contact point, not bbox center — see
        ai.spatial.coordinate_transform), a normalized 0-1 position, its
        actually-resolved zone (previously always NULL — the column
        existed but nothing ever wrote to it), and a best-effort world
        position honestly labeled CALIBRATED or UNCALIBRATED_ESTIMATE.
        """
        ctx = spatial_context or SpatialContext()

        for obj in frame_tracks.active_tracks:
            # Find or create track
            track = (
                db.query(Track)
                .filter(Track.video_id == video_id, Track.track_id == obj.track_id)
                .first()
            )
            if not track:
                track = Track(
                    video_id=video_id,
                    track_id=obj.track_id,
                    class_name=obj.class_name,
                    confidence=obj.confidence,
                    first_frame=obj.first_frame_index,
                    last_frame=obj.last_frame_index,
                    duration_seconds=max(0.0, obj.last_time_seconds - obj.start_time_seconds),
                    max_velocity=obj.speed_px_per_sec,
                )
                db.add(track)
                db.flush()
            else:
                track.last_frame = obj.last_frame_index
                track.duration_seconds = max(
                    0.0, obj.last_time_seconds - obj.start_time_seconds
                )
                track.max_velocity = max(track.max_velocity, obj.speed_px_per_sec)

            # Record point
            x1, y1, x2, y2 = obj.current_bbox
            cx, cy = obj.current_centroid
            vx, vy = obj.velocity_xy

            anchor_px = anchor_point(obj.current_bbox, obj.class_name) if obj.current_bbox else (cx, cy)
            anchor_norm = normalize(anchor_px, ctx.video_width, ctx.video_height)
            zone_id = TrackingService._resolve_zone(anchor_norm, ctx.zones) if ctx.zones else None
            world_xy, quality = world_position(
                anchor_norm,
                ctx.homography_matrix,
                ctx.warehouse_width_m,
                ctx.warehouse_length_m,
                ctx.reprojection_error_px,
            )

            pt = TrackPoint(
                track_id_fk=track.id,
                frame_number=frame_tracks.frame_index,
                timestamp_seconds=frame_tracks.timestamp_seconds,
                bbox_x1=x1,
                bbox_y1=y1,
                bbox_x2=x2,
                bbox_y2=y2,
                centroid_x=cx,
                centroid_y=cy,
                velocity_x=vx,
                velocity_y=vy,
                confidence=obj.confidence,
                zone_id=zone_id,
                anchor_x=anchor_px[0],
                anchor_y=anchor_px[1],
                normalized_x=anchor_norm[0],
                normalized_y=anchor_norm[1],
                world_x=world_xy[0],
                world_y=world_xy[1],
                world_position_quality=quality.status,
            )
            db.add(pt)

        db.commit()


tracking_service = TrackingService()
