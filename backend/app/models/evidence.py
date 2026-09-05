"""
Evidence Package, Root Cause, Recommendation, and Counterfactual ORM Entities
"""
from typing import Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class EvidencePackage(Base):
    __tablename__ = "evidence_packages"

    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), nullable=False, unique=True, index=True
    )
    snapshot_path: Mapped[str] = mapped_column(String(500), nullable=False)
    clip_path: Mapped[str] = mapped_column(String(500), nullable=False)
    pre_event_seconds: Mapped[float] = mapped_column(Float, default=3.0)
    post_event_seconds: Mapped[float] = mapped_column(Float, default=3.0)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    overlay_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON representation of bounding boxes, tracks & states

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence_package")


class RootCause(Base):
    __tablename__ = "root_causes"

    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id"), nullable=False, unique=True, index=True
    )
    cause_category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PROCESS, EQUIPMENT, CONGESTION, ERGONOMIC, INFRASTRUCTURE, UNKNOWN
    observed_factors: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of facts
    inferred_factors: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of inferences
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="root_cause")


class Recommendation(Base):
    __tablename__ = "recommendations"

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    action_title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prevention_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # TRAINING, EQUIPMENT_CHANGE, LAYOUT_MODIFICATION, PROCESS_RULE
    estimated_risk_reduction_pct: Mapped[float] = mapped_column(Float, default=50.0)
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED")  # PROPOSED, ACCEPTED, IMPLEMENTED, REJECTED

    incident: Mapped["Incident"] = relationship("Incident", back_populates="recommendations")


class CounterfactualAnalysis(Base):
    __tablename__ = "counterfactual_analyses"

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    observed_action: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    counterfactual_action: Mapped[str] = mapped_column(String(255), nullable=False)
    simulated_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_delta: Mapped[float] = mapped_column(Float, nullable=False)
    simulation_method: Mapped[str] = mapped_column(String(50), default="DETERMINISTIC_MODEL")
