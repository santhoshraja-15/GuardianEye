"""
Alert and Incident Management ORM Entities
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.behaviour import BehaviourEvent
    from backend.app.models.evidence import EvidencePackage, RootCause, Recommendation


class Alert(Base):
    __tablename__ = "alerts"

    behaviour_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("behaviour_events.id"), nullable=False, index=True
    )
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="OPEN", index=True
    )  # OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, DISMISSED
    deduplication_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    incident_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    behaviour_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("behaviour_events.id"), nullable=False, unique=True, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    camera_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(50), default="DETECTED", index=True
    )  # DETECTED, ALERTED, ACKNOWLEDGED, UNDER_REVIEW, CONFIRMED, REJECTED, ACTION_TAKEN, RESOLVED
    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    behaviour_event: Mapped["BehaviourEvent"] = relationship("BehaviourEvent", back_populates="incident")
    evidence_package: Mapped[Optional["EvidencePackage"]] = relationship(
        "EvidencePackage", back_populates="incident", uselist=False, cascade="all, delete-orphan"
    )
    root_cause: Mapped[Optional["RootCause"]] = relationship(
        "RootCause", back_populates="incident", uselist=False, cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="incident", cascade="all, delete-orphan"
    )
    history: Mapped[List["IncidentHistory"]] = relationship(
        "IncidentHistory", back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentHistory(Base):
    __tablename__ = "incident_histories"

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    from_status: Mapped[str] = mapped_column(String(50), nullable=False)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)

    incident: Mapped[Incident] = relationship("Incident", back_populates="history")
