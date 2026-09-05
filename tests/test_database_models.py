"""
Level 03 Database Models & Relational Integrity Verification Tests
"""
from backend.app.database.session import Base
from backend.app.models.user import User, Role, AuditLog
from backend.app.models.warehouse import Warehouse, Zone, Camera
from backend.app.models.product import ProductCategory, Product, Equipment
from backend.app.models.video import Video, ProcessingJob
from backend.app.models.tracking import Track, TrackPoint
from backend.app.models.behaviour import Interaction, BehaviourEvent
from backend.app.models.risk import RiskAssessment, DamagePrediction, PredictiveRisk
from backend.app.models.incident import Alert, Incident, IncidentHistory
from backend.app.models.evidence import (
    EvidencePackage,
    RootCause,
    Recommendation,
    CounterfactualAnalysis,
)
from backend.app.models.learning import (
    HumanReview,
    Dataset,
    DatasetVersion,
    ModelArtifact,
    ModelEvaluation,
)


def test_database_model_table_names():
    """Verify all ORM models declare proper table names"""
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"
    assert Warehouse.__tablename__ == "warehouses"
    assert Zone.__tablename__ == "zones"
    assert Camera.__tablename__ == "cameras"
    assert Product.__tablename__ == "products"
    assert Video.__tablename__ == "videos"
    assert ProcessingJob.__tablename__ == "processing_jobs"
    assert Track.__tablename__ == "tracks"
    assert TrackPoint.__tablename__ == "track_points"
    assert Interaction.__tablename__ == "interactions"
    assert BehaviourEvent.__tablename__ == "behaviour_events"
    assert RiskAssessment.__tablename__ == "risk_assessments"
    assert DamagePrediction.__tablename__ == "damage_predictions"
    assert Alert.__tablename__ == "alerts"
    assert Incident.__tablename__ == "incidents"
    assert EvidencePackage.__tablename__ == "evidence_packages"
    assert RootCause.__tablename__ == "root_causes"
    assert Recommendation.__tablename__ == "recommendations"
    assert CounterfactualAnalysis.__tablename__ == "counterfactual_analyses"
    assert HumanReview.__tablename__ == "human_reviews"
    assert Dataset.__tablename__ == "datasets"
    assert ModelArtifact.__tablename__ == "model_artifacts"


def test_model_instantiation_and_defaults():
    """Verify entities instantiate with UUIDs and default fields"""
    warehouse = Warehouse(
        name="Main Fulfillment Center",
        code="WH-01",
        location="Zone B, Industrial Park",
    )
    assert warehouse.id is not None
    assert warehouse.is_active is True
    assert warehouse.width_meters == 100.0

    zone = Zone(
        warehouse_id=warehouse.id,
        name="Loading Bay Alpha",
        code="LB-01",
        zone_type="LOADING_BAY",
        polygon_coordinates="[[0, 0], [10, 0], [10, 10], [0, 10]]",
    )
    assert zone.zone_type == "LOADING_BAY"
    assert zone.risk_weight == 1.0


def test_behaviour_and_risk_relationship_mapping():
    """Verify behavioural event and risk assessment model relations"""
    event = BehaviourEvent(
        video_id="vid-001",
        primary_track_id=1,
        behaviour_code="B01_DROP",
        behaviour_name="Product Drop",
        confidence=0.92,
        start_frame=120,
        end_frame=150,
        start_time_seconds=4.0,
        end_time_seconds=5.0,
        duration_seconds=1.0,
        dna_sequence="['APPROACH', 'LIFT', 'SEPARATED', 'DROP', 'IMPACT']",
    )
    assert event.behaviour_code == "B01_DROP"
    assert event.confidence == 0.92

    risk = RiskAssessment(
        behaviour_event_id=event.id,
        risk_score=85.0,
        risk_level="HIGH",
        confidence=0.90,
        factors_breakdown="[{'factor': 'impact_height', 'score': 30}]",
        explanation="Product dropped from height > 1.2m onto hard concrete surface.",
    )
    assert risk.risk_score == 85.0
    assert risk.risk_level == "HIGH"
