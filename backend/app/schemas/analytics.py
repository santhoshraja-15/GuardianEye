"""
Pydantic Schemas for Dashboard Analytics, Risk Heatmaps, and Operational Health

Every field here is either a direct measurement, a documented deterministic
calculation over real rows, or explicitly Optional/None when the
underlying data doesn't exist yet — none of these are placeholder values
dressed up to look measured. See analytics_service.py for exactly how each
one is computed, and `provenance` for a human-readable summary of method +
data source per metric.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HeatmapPoint(BaseModel):
    x_normalized: float
    y_normalized: float
    intensity: float  # 0.0 to 1.0 — this zone's incident count relative to the busiest zone
    zone_code: str
    zone_name: str
    incident_count: int


class BehaviourDistributionItem(BaseModel):
    behaviour_code: str
    count: int
    percentage: float
    # None when no risk assessment rows exist for this behaviour code yet —
    # never a plausible-looking guess in place of real data.
    avg_risk_score: Optional[float] = None


class RiskTrendPoint(BaseModel):
    label: str
    period_start: datetime
    period_end: datetime
    total_incidents: int
    avg_risk_score: Optional[float] = None


class RiskTrendComparison(BaseModel):
    """Current shift vs. previous shift, computed by the same
    temporal_analytics_service the assistant's "what changed this shift"
    answers use — the dashboard and the assistant cannot disagree about
    this number because they call the same function."""

    period_a_label: str
    period_b_label: str
    period_a_avg_risk: Optional[float] = None
    period_b_avg_risk: Optional[float] = None
    direction: Optional[str] = None  # INCREASED | DECREASED | STABLE
    percent_change: Optional[float] = None
    data_available: bool


class AnalyticsProvenance(BaseModel):
    """Human-readable "how was this computed" for the KPIs most likely to
    be challenged — deliberately plain strings rather than a generic
    metadata blob, so this reads directly in a tooltip or footer."""

    avg_risk_score_method: str
    damage_exposure_method: str
    heatmap_method: str
    response_time_method: str
    generated_at: datetime


class DashboardSummaryResponse(BaseModel):
    total_videos_processed: int
    total_incidents_detected: int
    critical_incidents: int
    open_alerts: int

    # Kept for backward compatibility with existing consumers of this field
    # name — its value is now potential_damage_exposure_usd (a real SUM,
    # not a formula), never a fabricated constant-per-incident guess.
    estimated_damage_loss_usd: float
    potential_damage_exposure_usd: float
    confirmed_damage_cost_usd: float

    # None when there are zero acknowledged alerts to average — never a
    # constant standing in for "we haven't measured this."
    mean_time_to_acknowledge_seconds: Optional[float] = None

    behaviour_distribution: List[BehaviourDistributionItem] = Field(default_factory=list)
    risk_heatmaps: List[HeatmapPoint] = Field(default_factory=list)
    operational_health_status: str  # OPTIMAL, DEGRADED, CRITICAL

    risk_trend_daily: List[RiskTrendPoint] = Field(default_factory=list)
    risk_trend_shift: Optional[RiskTrendComparison] = None
    provenance: Optional[AnalyticsProvenance] = None

    model_config = ConfigDict(from_attributes=True)
