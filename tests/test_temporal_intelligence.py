"""
Tests for the configurable shift-definition layer, the reusable temporal/
comparative analytics service, and the assistant's comparative-intent
routing built on top of them.

Uses a throwaway in-memory SQLite session (not the app's configured DB) so
these tests never touch or depend on real seeded demo data.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.models.behaviour import BehaviourEvent  # noqa: F401 - registers table
from backend.app.models.incident import Alert, Incident  # noqa: F401
from backend.app.models.risk import DamagePrediction, RiskAssessment  # noqa: F401
from backend.app.models.user import User  # noqa: F401 - FK target for User-referencing tables
from backend.app.models.video import ProcessingJob, Video  # noqa: F401
from backend.app.models.warehouse import Camera, Warehouse, Zone  # noqa: F401
from backend.app.schemas.assistant import AssistantQueryRequest
from backend.app.services import shift_config as sc
from backend.app.services import temporal_analytics_service as tas
from backend.app.services.assistant_service import AssistantService


# ─── Shift config (pure datetime logic, no DB) ───────────────────────────

def _dt(hour, minute=0, day=15):
    return datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc)


def test_get_shift_for_datetime_covers_all_hours():
    for hour in range(24):
        shift = sc.get_shift_for_datetime(_dt(hour))
        assert shift.code in {"MORNING", "EVENING", "NIGHT"}


def test_current_shift_range_clips_to_now():
    now = _dt(10, 30)  # mid-morning shift (06:00-14:00)
    start, end, label = sc.current_shift_range(now)
    assert start == _dt(6)
    assert end == now
    assert label == "Morning Shift"


def test_current_shift_range_handles_wrapping_night_shift_after_midnight():
    now = _dt(2, 15, day=16)  # 02:15 - inside a night shift that started the day before
    start, end, label = sc.current_shift_range(now)
    assert start == _dt(22, 0, day=15)
    assert end == now
    assert label == "Night Shift"


def test_previous_shift_range_wraps_to_night_before_morning():
    now = _dt(9)  # currently morning shift
    start, end, label = sc.previous_shift_range(now)
    assert end == _dt(6)  # exactly when morning started
    assert start == _dt(22, 0, day=14)  # night shift is 8 hours
    assert "Night" in label


def test_named_shift_today_future_shift_returns_unclipped_zero_window():
    now = _dt(8)  # before evening shift starts
    start, end, label = sc.named_shift_range_today(now, "EVENING")
    assert start == _dt(14)
    assert end == _dt(22)  # not clipped to `now` since it hasn't started
    assert label == "Evening Shift"


def test_named_shift_night_during_early_morning_tail_anchors_to_previous_day():
    now = _dt(3, day=16)  # 03:00 - still inside last night's Night shift
    start, end, label = sc.named_shift_range_today(now, "NIGHT")
    assert start == _dt(22, 0, day=15)
    assert end == now


# ─── Period phrase resolution (pure) ──────────────────────────────────────

def test_find_period_phrases_orders_by_position_in_text():
    phrases = tas.find_period_phrases("compare today vs yesterday")
    assert phrases == ["today", "yesterday"]


def test_find_period_phrases_prefers_longer_specific_phrase():
    phrases = tas.find_period_phrases("what changed this shift compared with the previous shift")
    assert phrases == ["this shift", "previous shift"]


def test_resolve_period_phrase_yesterday_is_full_day_before_today():
    now = _dt(15)
    period = tas.resolve_period_phrase("yesterday", now)
    assert period.start == _dt(0, day=14)
    assert period.end == _dt(0, day=15)


# ─── DB-backed period metrics & comparison ───────────────────────────────

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_incident(db, *, created_at, severity, behaviour_code, zone_id=None, risk_score=None):
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
            confidence=0.9, factors_breakdown="[]", explanation="test",
            created_at=created_at,
        ))

    incident = Incident(
        incident_code=f"INC-{event.id[:8]}", behaviour_event_id=event.id,
        warehouse_id="wh-1", zone_id=zone_id, title="Test Incident",
        summary="test", severity=severity, created_at=created_at,
    )
    db.add(incident)
    db.commit()
    return incident


def test_compute_period_metrics_aggregates_real_rows_only(db_session):
    today = datetime(2026, 9, 15, 10, tzinfo=timezone.utc)
    yesterday_ts = today - timedelta(days=1)

    _make_incident(db_session, created_at=today, severity="CRITICAL", behaviour_code="B01_DROP", risk_score=90.0)
    _make_incident(db_session, created_at=today, severity="HIGH", behaviour_code="B02_DRAG", risk_score=70.0)
    _make_incident(db_session, created_at=yesterday_ts, severity="HIGH", behaviour_code="B01_DROP", risk_score=60.0)

    today_period = tas.TimePeriod(today.replace(hour=0), today + timedelta(hours=1), "Today")
    metrics = tas.compute_period_metrics(db_session, today_period)

    assert metrics.total_incidents == 2
    assert metrics.critical_incidents == 1
    assert metrics.high_risk_incidents == 1
    assert metrics.avg_risk_score == 80.0  # (90 + 70) / 2
    assert metrics.behaviour_counts == {"B01_DROP": 1, "B02_DRAG": 1}


def test_compute_period_metrics_empty_window_is_honestly_empty(db_session):
    period = tas.TimePeriod(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        "Empty",
    )
    metrics = tas.compute_period_metrics(db_session, period)
    assert metrics.total_incidents == 0
    assert metrics.avg_risk_score is None
    assert metrics.has_data is False


def test_compare_periods_computes_real_deltas_and_flags_worsening(db_session):
    yesterday = datetime(2026, 9, 14, 10, tzinfo=timezone.utc)
    today = datetime(2026, 9, 15, 10, tzinfo=timezone.utc)

    _make_incident(db_session, created_at=yesterday, severity="HIGH", behaviour_code="B02_DRAG", risk_score=50.0)
    for _ in range(3):
        _make_incident(db_session, created_at=today, severity="HIGH", behaviour_code="B02_DRAG", risk_score=80.0)

    period_a = tas.TimePeriod(yesterday.replace(hour=0), yesterday.replace(hour=23, minute=59), "Yesterday")
    period_b = tas.TimePeriod(today.replace(hour=0), today.replace(hour=23, minute=59), "Today")

    result = tas.compare_periods(db_session, period_a, period_b)

    assert result.data_available is True
    total_delta = next(d for d in result.overall if d.label == "Total incidents")
    assert total_delta.period_a_value == 1
    assert total_delta.period_b_value == 3
    assert total_delta.direction == "INCREASED"

    drag_delta = next(d for d in result.behaviour_deltas if d.key == "B02_DRAG")
    assert drag_delta.change == 2
    assert "B02_DRAG" in result.what_changed.worsened[0]
    assert result.what_changed.most_significant_change is not None
    assert "review" in result.recommended_action.lower() or "b02_drag" in result.recommended_action.lower()


def test_compare_periods_with_no_data_in_either_window_is_explicit(db_session):
    period_a = tas.TimePeriod(datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2020, 1, 2, tzinfo=timezone.utc), "A")
    period_b = tas.TimePeriod(datetime(2020, 1, 3, tzinfo=timezone.utc), datetime(2020, 1, 4, tzinfo=timezone.utc), "B")
    result = tas.compare_periods(db_session, period_a, period_b)
    assert result.data_available is False
    assert "not enough data" in result.recommended_action.lower() or "no incidents" in result.recommended_action.lower()


# ─── Assistant comparative-intent end-to-end ─────────────────────────────

def test_assistant_answers_comparison_question_with_real_numbers(db_session, monkeypatch):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    today = datetime.now(timezone.utc)

    _make_incident(db_session, created_at=yesterday, severity="HIGH", behaviour_code="B02_DRAG", risk_score=50.0)
    _make_incident(db_session, created_at=today, severity="CRITICAL", behaviour_code="B01_DROP", risk_score=95.0)
    _make_incident(db_session, created_at=today, severity="CRITICAL", behaviour_code="B01_DROP", risk_score=90.0)

    req = AssistantQueryRequest(query="Compare today vs yesterday")
    resp = AssistantService.process_query(db_session, req)

    assert resp.data_available is True
    assert resp.comparison is not None and len(resp.comparison) > 0
    assert resp.period_a_label == "Yesterday"
    assert resp.period_b_label == "Today"
    total_metric = next(m for m in resp.comparison if m.label == "Total incidents")
    assert total_metric.period_a_value == 1
    assert total_metric.period_b_value == 2
    assert resp.recommended_action is not None
    assert resp.llm_provider_used == "mock"  # no API key configured in this environment


def test_assistant_what_changed_this_shift_is_grounded_not_fabricated(db_session):
    req = AssistantQueryRequest(query="What changed this shift?")
    resp = AssistantService.process_query(db_session, req)

    # No data exists in this isolated DB for "this shift" or "previous shift" -
    # the assistant must say so rather than inventing a plausible-looking number.
    assert resp.data_available is False
    assert resp.is_grounded is True


def test_non_comparative_question_still_uses_existing_branch_shape(db_session):
    """Regression guard: a plain zone question must be completely unaffected
    by the new comparative-intent routing."""
    req = AssistantQueryRequest(query="Which loading bay has the highest risk?")
    resp = AssistantService.process_query(db_session, req)

    assert resp.comparison is None
    assert resp.what_changed is None
    assert resp.answer  # existing zone-branch answer text still produced
