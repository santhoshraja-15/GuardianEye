"""
Temporal & Comparative Analytics Service

Reusable period-based aggregation over real incident/behaviour/risk data,
plus period-vs-period comparison (deltas, direction, "what changed").
Built once here so the assistant's comparative questions ("compare today
vs yesterday", "what changed this shift") and any future dashboard widget
share the same grounded computation instead of each hardcoding its own
query — per-question logic was exactly what produced the previous
keyword-branch assistant that couldn't generalize.

Nothing here fabricates a number: every metric is a real aggregate over
Incident / BehaviourEvent / RiskAssessment / DamagePrediction / Alert rows
for the requested time window. If a window contains zero rows the metrics
are honestly zero / None, not a plausible-looking placeholder.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.behaviour import BehaviourEvent
from backend.app.models.incident import Alert, Incident
from backend.app.models.risk import DamagePrediction, RiskAssessment
from backend.app.models.warehouse import Zone
from backend.app.services import shift_config


# ─── Time period resolution ──────────────────────────────────────────────

@dataclass(frozen=True)
class TimePeriod:
    start: datetime
    end: datetime
    label: str


# Recognized phrases, checked longest/most-specific first so "previous shift"
# doesn't get shadowed by a looser "shift" match, etc. Each resolver takes
# `now` and returns the period that phrase means *as of now*.
def _today(now: datetime) -> TimePeriod:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return TimePeriod(start, now, "Today")


def _yesterday(now: datetime) -> TimePeriod:
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=1)
    return TimePeriod(start, end, "Yesterday")


def _this_week(now: datetime) -> TimePeriod:
    start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    return TimePeriod(start, now, "Last 7 Days")


def _previous_week(now: datetime) -> TimePeriod:
    end = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=7)
    return TimePeriod(start, end, "The 7 Days Before That")


def _current_shift(now: datetime) -> TimePeriod:
    start, end, label = shift_config.current_shift_range(now)
    return TimePeriod(start, end, label)


def _previous_shift(now: datetime) -> TimePeriod:
    start, end, label = shift_config.previous_shift_range(now)
    return TimePeriod(start, end, label)


def _named_shift(code: str):
    def _resolve(now: datetime) -> Optional[TimePeriod]:
        resolved = shift_config.named_shift_range_today(now, code)
        if not resolved:
            return None
        start, end, label = resolved
        return TimePeriod(start, end, f"Today's {label}")
    return _resolve


# Ordered: first matching phrase wins, so check specific multi-word phrases
# before their single-word substrings.
_PHRASE_RESOLVERS: List[Tuple[str, "callable"]] = [
    ("previous shift", _previous_shift),
    ("last shift", _previous_shift),
    ("prior shift", _previous_shift),
    ("this shift", _current_shift),
    ("current shift", _current_shift),
    ("morning shift", _named_shift("MORNING")),
    ("morning", _named_shift("MORNING")),
    ("evening shift", _named_shift("EVENING")),
    ("evening", _named_shift("EVENING")),
    ("night shift", _named_shift("NIGHT")),
    ("overnight", _named_shift("NIGHT")),
    ("yesterday", _yesterday),
    ("last week", _previous_week),
    ("this week", _this_week),
    ("today", _today),
]


def resolve_period_phrase(phrase: str, now: datetime) -> Optional[TimePeriod]:
    """Resolve one recognized time-period phrase against `now`. None if unrecognized."""
    lowered = phrase.lower()
    for keyword, resolver in _PHRASE_RESOLVERS:
        if keyword in lowered:
            return resolver(now)
    return None


def find_period_phrases(query: str) -> List[str]:
    """Every recognized period phrase present in a query, in the order they appear."""
    lowered = query.lower()
    found: List[Tuple[int, str]] = []
    seen_spans: List[Tuple[int, int]] = []
    for keyword, _resolver in _PHRASE_RESOLVERS:
        idx = lowered.find(keyword)
        if idx == -1:
            continue
        # Skip if this keyword is a substring of an already-matched longer phrase at the same spot.
        if any(start <= idx < end for start, end in seen_spans):
            continue
        found.append((idx, keyword))
        seen_spans.append((idx, idx + len(keyword)))
    found.sort(key=lambda pair: pair[0])
    return [kw for _idx, kw in found]


# ─── Period metrics ──────────────────────────────────────────────────────

@dataclass
class PeriodMetrics:
    period: TimePeriod
    total_incidents: int = 0
    high_risk_incidents: int = 0
    critical_incidents: int = 0
    avg_risk_score: Optional[float] = None
    potential_damage_events: int = 0
    avg_response_seconds: Optional[float] = None
    behaviour_counts: Dict[str, int] = field(default_factory=dict)
    zone_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.total_incidents > 0


def compute_period_metrics(
    db: Session,
    period: TimePeriod,
    warehouse_id: Optional[str] = None,
) -> PeriodMetrics:
    """Every metric here is a real aggregate over rows created within [period.start, period.end)."""
    base_filter = [Incident.created_at >= period.start, Incident.created_at < period.end]
    if warehouse_id:
        base_filter.append(Incident.warehouse_id == warehouse_id)

    rows = (
        db.query(
            Incident.severity,
            BehaviourEvent.behaviour_code,
            Zone.code,
            RiskAssessment.risk_score,
        )
        .join(BehaviourEvent, Incident.behaviour_event_id == BehaviourEvent.id)
        .outerjoin(Zone, Incident.zone_id == Zone.id)
        .outerjoin(RiskAssessment, RiskAssessment.behaviour_event_id == BehaviourEvent.id)
        .filter(*base_filter)
        .all()
    )

    metrics = PeriodMetrics(period=period)
    metrics.total_incidents = len(rows)

    risk_scores: List[float] = []
    for severity, behaviour_code, zone_code, risk_score in rows:
        if severity == "HIGH":
            metrics.high_risk_incidents += 1
        elif severity == "CRITICAL":
            metrics.critical_incidents += 1
        if behaviour_code:
            metrics.behaviour_counts[behaviour_code] = metrics.behaviour_counts.get(behaviour_code, 0) + 1
        if zone_code:
            metrics.zone_counts[zone_code] = metrics.zone_counts.get(zone_code, 0) + 1
        if risk_score is not None:
            risk_scores.append(risk_score)

    if risk_scores:
        metrics.avg_risk_score = round(sum(risk_scores) / len(risk_scores), 1)

    metrics.potential_damage_events = (
        db.query(func.count(DamagePrediction.id))
        .join(BehaviourEvent, DamagePrediction.behaviour_event_id == BehaviourEvent.id)
        .join(Incident, Incident.behaviour_event_id == BehaviourEvent.id)
        .filter(
            DamagePrediction.damage_status == "POTENTIAL_DAMAGE",
            *base_filter,
        )
        .scalar()
        or 0
    )

    alert_filter = [Alert.created_at >= period.start, Alert.created_at < period.end, Alert.acknowledged_at.isnot(None)]
    acknowledged_alerts = db.query(Alert.created_at, Alert.acknowledged_at).filter(*alert_filter).all()
    if acknowledged_alerts:
        deltas = [
            (ack - created).total_seconds()
            for created, ack in acknowledged_alerts
            if ack is not None and created is not None
        ]
        if deltas:
            metrics.avg_response_seconds = round(sum(deltas) / len(deltas), 1)

    return metrics


# ─── Comparison ──────────────────────────────────────────────────────────

@dataclass
class MetricDelta:
    label: str
    period_a_value: float
    period_b_value: float
    absolute_change: float
    percent_change: Optional[float]
    direction: str  # "INCREASED" | "DECREASED" | "STABLE"


def _delta(label: str, a_value: Optional[float], b_value: Optional[float]) -> Optional[MetricDelta]:
    if a_value is None and b_value is None:
        return None
    a = a_value or 0.0
    b = b_value or 0.0
    change = round(b - a, 1)
    pct = round((change / a) * 100.0, 1) if a else None
    direction = "STABLE" if abs(change) < 0.05 else ("INCREASED" if change > 0 else "DECREASED")
    return MetricDelta(label=label, period_a_value=a, period_b_value=b, absolute_change=change, percent_change=pct, direction=direction)


@dataclass
class CategoryDelta:
    """A single behaviour code's or zone code's count across two periods."""
    key: str
    period_a_count: int
    period_b_count: int
    change: int


@dataclass
class WhatChanged:
    improved: List[str] = field(default_factory=list)
    worsened: List[str] = field(default_factory=list)
    new_items: List[str] = field(default_factory=list)
    persistent: List[str] = field(default_factory=list)
    most_significant_change: Optional[str] = None


@dataclass
class PeriodComparisonResult:
    period_a: TimePeriod
    period_b: TimePeriod
    metrics_a: PeriodMetrics
    metrics_b: PeriodMetrics
    overall: List[MetricDelta]
    behaviour_deltas: List[CategoryDelta]
    zone_deltas: List[CategoryDelta]
    what_changed: WhatChanged
    recommended_action: str
    data_available: bool


def _category_deltas(a_counts: Dict[str, int], b_counts: Dict[str, int]) -> List[CategoryDelta]:
    keys = set(a_counts) | set(b_counts)
    deltas = [
        CategoryDelta(key=k, period_a_count=a_counts.get(k, 0), period_b_count=b_counts.get(k, 0), change=b_counts.get(k, 0) - a_counts.get(k, 0))
        for k in keys
    ]
    deltas.sort(key=lambda d: abs(d.change), reverse=True)
    return deltas


def compare_periods(
    db: Session,
    period_a: TimePeriod,
    period_b: TimePeriod,
    warehouse_id: Optional[str] = None,
) -> PeriodComparisonResult:
    """Period B is treated as the "current"/later period being explained relative to A."""
    metrics_a = compute_period_metrics(db, period_a, warehouse_id)
    metrics_b = compute_period_metrics(db, period_b, warehouse_id)

    overall = [
        d for d in [
            _delta("Total incidents", metrics_a.total_incidents, metrics_b.total_incidents),
            _delta("High-risk incidents", metrics_a.high_risk_incidents, metrics_b.high_risk_incidents),
            _delta("Critical incidents", metrics_a.critical_incidents, metrics_b.critical_incidents),
            _delta("Average risk score", metrics_a.avg_risk_score, metrics_b.avg_risk_score),
            _delta("Potential damage events", metrics_a.potential_damage_events, metrics_b.potential_damage_events),
            _delta("Avg. response time (s)", metrics_a.avg_response_seconds, metrics_b.avg_response_seconds),
        ]
        if d is not None
    ]

    behaviour_deltas = _category_deltas(metrics_a.behaviour_counts, metrics_b.behaviour_counts)
    zone_deltas = _category_deltas(metrics_a.zone_counts, metrics_b.zone_counts)

    what_changed = WhatChanged()
    for d in behaviour_deltas:
        if d.period_a_count == 0 and d.period_b_count > 0:
            what_changed.new_items.append(f"{d.key} ({d.period_b_count} new occurrence(s))")
        elif d.change < 0:
            what_changed.improved.append(f"{d.key} decreased by {abs(d.change)}")
        elif d.change > 0:
            what_changed.worsened.append(f"{d.key} increased by {d.change}")
        elif d.period_a_count > 0 and d.period_b_count > 0:
            what_changed.persistent.append(f"{d.key} remained steady at {d.period_b_count}")

    for d in zone_deltas:
        if d.period_a_count == 0 and d.period_b_count > 0:
            what_changed.new_items.append(f"Zone {d.key} ({d.period_b_count} new incident(s))")

    most_significant = None
    all_deltas = behaviour_deltas + zone_deltas
    if all_deltas:
        top = max(all_deltas, key=lambda d: abs(d.change))
        if top.change != 0:
            direction = "increased" if top.change > 0 else "decreased"
            most_significant = f"{top.key} {direction} the most ({top.period_a_count} -> {top.period_b_count})"
    what_changed.most_significant_change = most_significant

    data_available = metrics_a.has_data or metrics_b.has_data
    if not data_available:
        recommended_action = (
            f"No incidents were recorded in either {period_a.label} or {period_b.label} — "
            "there isn't enough data yet to recommend an action."
        )
    elif what_changed.worsened:
        worst_behaviour = max(
            (d for d in behaviour_deltas if d.change > 0), key=lambda d: d.change, default=None
        )
        if worst_behaviour:
            recommended_action = (
                f"Review handling practice for {worst_behaviour.key.replace('_', ' ').title()} — "
                f"it rose from {worst_behaviour.period_a_count} to {worst_behaviour.period_b_count} occurrence(s) "
                f"and was the largest driver of change."
            )
        else:
            recommended_action = "Risk increased overall — review recent incidents for a common cause."
    elif what_changed.improved:
        recommended_action = "Handling discipline is trending in the right direction — reinforce whatever changed to sustain it."
    else:
        recommended_action = "No material change between the two periods — no corrective action indicated."

    return PeriodComparisonResult(
        period_a=period_a,
        period_b=period_b,
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        overall=overall,
        behaviour_deltas=behaviour_deltas,
        zone_deltas=zone_deltas,
        what_changed=what_changed,
        recommended_action=recommended_action,
        data_available=data_available,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def daily_buckets(now: datetime, num_days: int = 7) -> List[TimePeriod]:
    """The last `num_days` full calendar days plus today-so-far, oldest
    first — the shared "risk trend" series definition used by both the
    dashboard chart and anything else that wants a real day-by-day view,
    instead of each caller inventing its own fake week."""
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    buckets: List[TimePeriod] = []
    for i in range(num_days - 1, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = min(day_start + timedelta(days=1), now) if i == 0 else day_start + timedelta(days=1)
        label = day_start.strftime("%a %b %d")
        buckets.append(TimePeriod(day_start, day_end, label))
    return buckets


def compute_series(
    db: Session,
    periods: List[TimePeriod],
    warehouse_id: Optional[str] = None,
) -> List[PeriodMetrics]:
    """Real per-bucket metrics for a list of periods (e.g. daily_buckets()) —
    one query per bucket, same aggregation compute_period_metrics always
    uses, so a trend chart and a single-period answer can never disagree
    about what "average risk" or "incident count" means."""
    return [compute_period_metrics(db, period, warehouse_id) for period in periods]
