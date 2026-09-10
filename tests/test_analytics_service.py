"""
Tests for the rewritten analytics_service.py — every KPI it returns must be
a real aggregate over a controlled in-memory dataset, never a formula or
constant standing in for measured data. Uses a throwaway in-memory SQLite
session, same pattern as test_temporal_intelligence.py.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.models.behaviour import BehaviourEvent  # noqa: F401
from backend.app.models.incident import Alert, Incident  # noqa: F401
from backend.app.models.risk import DamagePrediction, RiskAssessment  # noqa: F401
from backend.app.models.user import User  # noqa: F401
from backend.app.models.video import ProcessingJob, Video  # noqa: F401
from backend.app.models.warehouse import Camera, Warehouse, Zone  # noqa: F401
from backend.app.services.analytics_service import AnalyticsService


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_zone(db, *, warehouse_id, code, name, polygon):
    zone = Zone(
        warehouse_id=warehouse_id, code=code, name=name, zone_type="STORAGE",
        polygon_coordinates=json.dumps(polygon), risk_weight=1.2,
    )
    db.add(zone)
    db.commit()
    return zone


def _make_incident(db, *, created_at, severity, behaviour_code, zone_id=None, risk_score=None, damage=None):
    video = Video(
        camera_id=None, filename="v.mp4", storage_path="v.mp4", file_size_bytes=1,
        duration_seconds=1.0, fps=10, width=100, height=100, codec="h264",
        checksum_sha256="x", status="COMPLETED",
    )
    db.add(video)
    db.flush()

    event = BehaviourEvent(
        video_id=video.id, zone_id=zone_id, primary_track_id=1,
        behaviour_code=behaviour_code, behaviour_name=behaviour_code,
        confidence=0.9, start_frame=0, end_frame=1,
        start_time_seconds=0.0, end_time_seconds=1.0, duration_seconds=1.0,
        dna_sequence="[]", created_at=created_at,
    )
    db.add(event)
    db.flush()

    if risk_score is not None:
        db.add(RiskAssessment(
            behaviour_event_id=event.id, risk_score=risk_score, risk_level=severity,
            confidence=0.9, factors_breakdown="[]", explanation="test", created_at=created_at,
        ))

    incident = Incident(
        incident_code=f"INC-{event.id[:8]}", behaviour_event_id=event.id,
        warehouse_id="wh-1", zone_id=zone_id, title="Test Incident",
        summary="test", severity=severity, created_at=created_at,
    )
    db.add(incident)

    if damage is not None:
        db.add(DamagePrediction(
            behaviour_event_id=event.id,
            damage_probability=damage.get("probability", 0.5),
            likely_damage_type=damage.get("type", "PACKAGING_DEFORMATION"),
            damage_status=damage.get("status", "POTENTIAL_DAMAGE"),
            estimated_financial_loss_usd=damage.get("loss_usd"),
            factors_json="[]",
            created_at=created_at,
        ))

    db.commit()
    return incident


def test_empty_database_returns_honest_nones_not_fabricated_values(db_session):
    summary = AnalyticsService.get_dashboard_summary(db_session)

    assert summary.total_incidents_detected == 0
    assert summary.behaviour_distribution == []
    assert summary.risk_heatmaps == []
    assert summary.mean_time_to_acknowledge_seconds is None
    assert summary.estimated_damage_loss_usd == 0.0
    assert summary.confirmed_damage_cost_usd == 0.0
    assert summary.risk_trend_shift.data_available is False


def test_avg_risk_score_is_a_real_average_per_behaviour(db_session):
    now = datetime.now(timezone.utc)
    _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP", risk_score=90.0)
    _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP", risk_score=70.0)
    _make_incident(db_session, created_at=now, severity="MEDIUM", behaviour_code="B02_DRAG", risk_score=None)

    summary = AnalyticsService.get_dashboard_summary(db_session)
    by_code = {d.behaviour_code: d for d in summary.behaviour_distribution}

    assert by_code["B01_DROP"].avg_risk_score == 80.0  # (90+70)/2, not a constant
    assert by_code["B02_DRAG"].avg_risk_score is None  # no RiskAssessment row exists for it


def test_damage_totals_split_confirmed_vs_potential_and_ignore_null_legacy_rows(db_session):
    now = datetime.now(timezone.utc)
    _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP",
                    damage={"loss_usd": 100.0, "status": "POTENTIAL_DAMAGE"})
    _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP",
                    damage={"loss_usd": 50.0, "status": "CONFIRMED_BY_HUMAN"})
    # Legacy-style row with no persisted loss estimate (column added after it was created).
    _make_incident(db_session, created_at=now, severity="LOW", behaviour_code="B02_DRAG",
                    damage={"loss_usd": None, "status": "POTENTIAL_DAMAGE"})

    summary = AnalyticsService.get_dashboard_summary(db_session)

    assert summary.potential_damage_exposure_usd == 100.0  # the NULL row contributes 0, not an error
    assert summary.confirmed_damage_cost_usd == 50.0
    assert summary.estimated_damage_loss_usd == summary.potential_damage_exposure_usd


def test_mean_acknowledge_seconds_is_real_average_of_actual_alerts(db_session):
    now = datetime.now(timezone.utc)
    db_session.add(Alert(
        behaviour_event_id="be-1", alert_level="HIGH", message="m", deduplication_key="k1",
        status="ACKNOWLEDGED", created_at=now, acknowledged_at=now + timedelta(seconds=30),
    ))
    db_session.add(Alert(
        behaviour_event_id="be-2", alert_level="HIGH", message="m", deduplication_key="k2",
        status="ACKNOWLEDGED", created_at=now, acknowledged_at=now + timedelta(seconds=90),
    ))
    db_session.add(Alert(
        behaviour_event_id="be-3", alert_level="HIGH", message="m", deduplication_key="k3",
        status="OPEN", created_at=now, acknowledged_at=None,
    ))
    db_session.commit()

    summary = AnalyticsService.get_dashboard_summary(db_session)
    assert summary.mean_time_to_acknowledge_seconds == 60.0  # (30+90)/2, unacknowledged alert excluded


def test_heatmap_positions_are_real_zone_geometry_not_arbitrary_constants(db_session):
    warehouse = Warehouse(name="WH", code="WH-1", width_meters=120.0, length_meters=80.0)
    db_session.add(warehouse)
    db_session.commit()

    zone_a = _make_zone(
        db_session, warehouse_id=warehouse.id, code="BAY_01", name="Bay 01",
        polygon=[[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]],
    )
    zone_b = _make_zone(
        db_session, warehouse_id=warehouse.id, code="BAY_02", name="Bay 02",
        polygon=[[100.0, 0.0], [200.0, 0.0], [200.0, 100.0], [100.0, 100.0]],
    )

    now = datetime.now(timezone.utc)
    for _ in range(3):
        _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP", zone_id=zone_a.id)
    _make_incident(db_session, created_at=now, severity="LOW", behaviour_code="B02_DRAG", zone_id=zone_b.id)

    summary = AnalyticsService.get_dashboard_summary(db_session)
    by_code = {p.zone_code: p for p in summary.risk_heatmaps}

    # Zone A's polygon centroid is (50, 50); combined bbox across both zones
    # is x:[0,200] y:[0,100] -> normalized (0.25, 0.5).
    assert by_code["BAY_01"].x_normalized == pytest.approx(0.25)
    assert by_code["BAY_01"].y_normalized == pytest.approx(0.5)
    assert by_code["BAY_01"].incident_count == 3
    assert by_code["BAY_01"].intensity == 1.0  # busiest zone
    assert by_code["BAY_02"].incident_count == 1
    assert by_code["BAY_02"].intensity == pytest.approx(1 / 3, abs=0.001)  # rounded to 3dp by the service


def test_daily_trend_and_shift_trend_reuse_temporal_analytics_service(db_session):
    now = datetime.now(timezone.utc)
    _make_incident(db_session, created_at=now, severity="HIGH", behaviour_code="B01_DROP", risk_score=80.0)

    summary = AnalyticsService.get_dashboard_summary(db_session)

    assert len(summary.risk_trend_daily) == 7
    assert summary.risk_trend_daily[-1].total_incidents == 1  # today's bucket, last in the list
    assert summary.risk_trend_shift is not None
    assert summary.provenance is not None
    assert "AVG(risk_assessments.risk_score)" in summary.provenance.avg_risk_score_method

    # Only "now" has an incident, so the previous shift has zero risk data.
    # A manufactured "-100% decreased" trend must not appear just because
    # the missing side defaults to 0 internally.
    trend = summary.risk_trend_shift
    assert trend.data_available is False
    assert trend.direction is None
    assert trend.percent_change is None
