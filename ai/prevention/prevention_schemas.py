"""
Data Models and Types for Root Cause Analysis, Recommendations, and Counterfactual Simulation
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RootCauseCategory(str, Enum):
    PROCESS = "PROCESS"
    EQUIPMENT = "EQUIPMENT"
    CONGESTION = "CONGESTION"
    ERGONOMIC = "ERGONOMIC"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    UNKNOWN = "UNKNOWN"


class PreventionType(str, Enum):
    TRAINING = "TRAINING"
    EQUIPMENT_CHANGE = "EQUIPMENT_CHANGE"
    LAYOUT_MODIFICATION = "LAYOUT_MODIFICATION"
    PROCESS_RULE = "PROCESS_RULE"
    ENVIRONMENTAL_MAINTENANCE = "ENVIRONMENTAL_MAINTENANCE"


@dataclass
class RootCauseResult:
    cause_category: RootCauseCategory
    observed_facts: List[str]
    inferred_factors: List[str]
    confidence: float


@dataclass
class RecommendationResult:
    action_title: str
    description: str
    prevention_type: PreventionType
    estimated_risk_reduction_pct: float
    implementation_priority: str  # P0, P1, P2


@dataclass
class CounterfactualResult:
    observed_action: str
    observed_risk_score: float
    counterfactual_action: str
    simulated_risk_score: float
    risk_delta: float
    simulation_method: str = "DETERMINISTIC_PHYSICAL_MODEL"
