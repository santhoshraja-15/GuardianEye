"""
Multi-Object Tracking and Trajectory Point ORM Entities
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.video import Video


class Track(Base):
    __tablename__ = "tracks"

    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # Tracker persistent ID
    class_name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # person, carton, pallet, trolley, forklift, equipment
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    first_frame: Mapped[int] = mapped_column(Integer, default=0)
    last_frame: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    max_velocity: Mapped[float] = mapped_column(Float, default=0.0)  # px/sec
    trajectory_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON summary

    video: Mapped["Video"] = relationship("Video", back_populates="tracks")
    track_points: Mapped[List["TrackPoint"]] = relationship(
        "TrackPoint", back_populates="track", cascade="all, delete-orphan"
    )


class TrackPoint(Base):
    __tablename__ = "track_points"

    track_id_fk: Mapped[str] = mapped_column(String(36), ForeignKey("tracks.id"), nullable=False, index=True)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x2: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y2: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_x: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_y: Mapped[float] = mapped_column(Float, nullable=False)
    velocity_x: Mapped[float] = mapped_column(Float, default=0.0)
    velocity_y: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    track: Mapped[Track] = relationship("Track", back_populates="track_points")
