"""
Pydantic Schemas for Dashboard Analytics, Risk Heatmaps, and Operational Health
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HeatmapPoint(BaseModel):
    x_normalized: float
    y_normalized: float
    intensity: float  # 0.0 to 1.0
    zone_code: str
    incident_count: int


class BehaviourDistributionItem(BaseModel):
    behaviour_code: str
    count: int
    percentage: float
    avg_risk_score: float


class DashboardSummaryResponse(BaseModel):
    total_videos_processed: int
    total_incidents_detected: int
    critical_incidents: int
    open_alerts: int
    estimated_damage_loss_usd: float
    mean_time_to_acknowledge_seconds: float
    behaviour_distribution: List[BehaviourDistributionItem] = Field(default_factory=list)
    risk_heatmaps: List[HeatmapPoint] = Field(default_factory=list)
    operational_health_status: str  # OPTIMAL, DEGRADED, CRITICAL

    model_config = ConfigDict(from_attributes=True)
