"""
Pydantic Schemas for Risk Assessments
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskBreakdownResponse(BaseModel):
    base_severity_score: float
    height_risk_component: float
    velocity_risk_component: float
    fragility_multiplier: float
    zone_multiplier: float
    shift_fatigue_multiplier: float
    raw_computed_score: float
    final_score_clamped: float


class RiskAssessmentResponse(BaseModel):
    id: Optional[str] = None
    behaviour_event_id: Optional[str] = None
    risk_score: float
    risk_level: str
    is_actionable: bool
    recommended_action: str
    factors: List[str] = Field(default_factory=list)
    breakdown: Optional[RiskBreakdownResponse] = None

    model_config = ConfigDict(from_attributes=True)
