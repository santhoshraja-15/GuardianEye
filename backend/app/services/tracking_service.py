"""
Tracking Service for Ingesting and Retrieving Entity Trajectories
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject
from backend.app.core.errors import NotFoundException
from backend.app.models.tracking import Track, TrackPoint


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
    def persist_frame_tracks(
        db: Session, video_id: str, frame_tracks: FrameTracks
    ):
        """
        Record current frame's active tracks and trajectory points in database
        """
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
            )
            db.add(pt)

        db.commit()


tracking_service = TrackingService()
