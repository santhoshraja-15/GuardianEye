"""
Interaction and Behaviour Event ORM Entities
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.video import Video
    from backend.app.models.risk import RiskAssessment, DamagePrediction
    from backend.app.models.incident import Incident


class Interaction(Base):
    __tablename__ = "interactions"

    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    source_track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # APPROACHING, CONTACT, HOLDING, CARRYING, SEPARATED
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    min_distance_px: Mapped[float] = mapped_column(Float, default=0.0)
    max_iou: Mapped[float] = mapped_column(Float, default=0.0)


class BehaviourEvent(Base):
    __tablename__ = "behaviour_events"

    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    primary_track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    secondary_track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    behaviour_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # B01_DROP, B02_DRAG, B03_THROW, etc.
    behaviour_name: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    dna_sequence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON representation of state transitions
    dna_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of 32 float features
    status: Mapped[str] = mapped_column(String(50), default="DETECTED")

    video: Mapped["Video"] = relationship("Video", back_populates="behaviour_events")
    risk_assessment: Mapped[Optional["RiskAssessment"]] = relationship(
        "RiskAssessment", back_populates="behaviour_event", uselist=False, cascade="all, delete-orphan"
    )
    damage_prediction: Mapped[Optional["DamagePrediction"]] = relationship(
        "DamagePrediction", back_populates="behaviour_event", uselist=False, cascade="all, delete-orphan"
    )
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident", back_populates="behaviour_event", uselist=False, cascade="all, delete-orphan"
    )
