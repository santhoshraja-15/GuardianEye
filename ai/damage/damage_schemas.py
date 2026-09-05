"""
Data Models and Types for Damage Intelligence & Physical Impact Modeling
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DamageType(str, Enum):
    PACKAGING_DEFORMATION = "PACKAGING_DEFORMATION"
    STRUCTURAL_BREAKAGE = "STRUCTURAL_BREAKAGE"
    SURFACE_ABRASION = "SURFACE_ABRASION"
    CRUSHING = "CRUSHING"
    MOISTURE_CONTAMINATION = "MOISTURE_CONTAMINATION"
    INTERNAL_COMPONENT_FAILURE = "INTERNAL_COMPONENT_FAILURE"
    NO_OBSERVED_DAMAGE = "NO_OBSERVED_DAMAGE"


class DamageStatus(str, Enum):
    NOT_OBSERVED = "NOT_OBSERVED"
    POTENTIAL_DAMAGE = "POTENTIAL_DAMAGE"
    CONFIRMED_BY_HUMAN = "CONFIRMED_BY_HUMAN"
    CONFIRMED_BY_EXTERNAL_SYSTEM = "CONFIRMED_BY_EXTERNAL_SYSTEM"


@dataclass
class DamagePredictionResult:
    damage_probability: float  # 0.0 to 1.0
    likely_damage_type: DamageType
    damage_status: DamageStatus
    estimated_financial_loss_usd: float
    is_claim_eligible: bool
    damage_factors: List[str]
    confidence: float
