"""
Data Models and Schemas for Deterministic Risk Engine
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskFormulaBreakdown:
    base_severity_score: float
    height_risk_component: float
    velocity_risk_component: float
    fragility_multiplier: float
    zone_multiplier: float
    shift_fatigue_multiplier: float
    raw_computed_score: float
    final_score_clamped: float


@dataclass
class RiskEvaluationResult:
    risk_score: float  # 0.0 to 100.0
    risk_level: RiskLevel
    breakdown: RiskFormulaBreakdown
    factors: List[str]
    is_actionable: bool
    recommended_action: str
