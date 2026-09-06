"""
Risk Assessment, Damage Prediction, and Predictive Risk ORM Entities
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.behaviour import BehaviourEvent


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    behaviour_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("behaviour_events.id"), nullable=False, unique=True, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 0.0 to 100.0
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    factors_breakdown: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of factors
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    calculated_by: Mapped[str] = mapped_column(String(50), default="DETERMINISTIC_ENGINE")

    behaviour_event: Mapped["BehaviourEvent"] = relationship(
        "BehaviourEvent", back_populates="risk_assessment"
    )


class DamagePrediction(Base):
    __tablename__ = "damage_predictions"

    behaviour_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("behaviour_events.id"), nullable=False, unique=True, index=True
    )
    damage_probability: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 0.0 to 1.0
    likely_damage_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PACKAGING_DEFORMATION, BREAKAGE, ABRASION, CRUSHING, UNKNOWN
    damage_status: Mapped[str] = mapped_column(
        String(50), default="POTENTIAL_DAMAGE", index=True
    )  # NOT_OBSERVED, POTENTIAL_DAMAGE, CONFIRMED_BY_HUMAN, CONFIRMED_BY_EXTERNAL_SYSTEM
    factors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    behaviour_event: Mapped["BehaviourEvent"] = relationship(
        "BehaviourEvent", back_populates="damage_prediction"
    )


class PredictiveRisk(Base):
    __tablename__ = "predictive_risks"

    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    forecast_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_incident_rate: Mapped[float] = mapped_column(Float, default=0.0)
    risk_trend: Mapped[str] = mapped_column(String(20), default="STABLE")  # INCREASING, STABLE, DECREASING
    top_predicted_behaviours: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
