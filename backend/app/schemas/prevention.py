"""
Prevention Studio and SOP Rules Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PreventionRuleResponse(BaseModel):
    behaviour_code: str
    rule_name: str
    description: str
    risk_category: str
    severity_default: str
    sop_citation: str
    detection_threshold_description: str


class RecommendationResponse(BaseModel):
    id: str
    incident_id: str
    action_title: str
    description: str
    prevention_type: str
    estimated_risk_reduction_pct: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RootCauseResponse(BaseModel):
    id: str
    incident_id: str
    cause_category: str
    observed_factors: str
    inferred_factors: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
