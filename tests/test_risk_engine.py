"""
Level 16 & 17 Context Enrichment and Deterministic Risk Engine Tests
"""
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
)
from ai.context.context_enricher import ContextEnricher, ProductContext
from ai.risk.risk_engine import DeterministicRiskEngine
from ai.risk.risk_schemas import RiskLevel


def test_context_enricher_fragility_and_zones():
    """Verify context enrichment extracts correct zone and product multipliers"""
    catalog = {
        "SKU-GLASS-VASE": ProductContext(
            sku="SKU-GLASS-VASE",
            product_name="Fragile Glassware",
            category="Home & Living",
            fragility_rating=5,
            unit_value_usd=120.0,
            max_safe_drop_height_px=10.0,
        )
    }
    enricher = ContextEnricher(catalog=catalog)
    ctx = enricher.enrich(entity_id=1, sku_or_class="SKU-GLASS-VASE", zone_code="WET_FLOOR_DOCK", shift_hours=8.0)
    
    assert ctx.product.fragility_rating == 5
    assert ctx.zone_risk_multiplier == 2.0
    assert ctx.shift_fatigue_multiplier == 1.15


def test_deterministic_risk_score_calculation():
    """Verify deterministic mathematical calculation of risk score and critical categorization"""
    enricher = ContextEnricher()
    # High fragility electronic item in loading dock
    ctx = enricher.enrich(entity_id=1, zone_code="LOADING_DOCK")
    
    behaviour = DetectedBehaviour(
        behaviour_type=BehaviourType.B01_DROP,
        severity=BehaviourSeverity.HIGH,
        start_frame=10,
        end_frame=15,
        start_time_seconds=0.33,
        end_time_seconds=0.50,
        duration_seconds=0.17,
        confidence=0.95,
        description="Drop from elevated height",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_DROP_FREEFALL",
            primary_entity_id=1,
            primary_class="carton",
            fall_height_px=100.0,
            peak_velocity_px_s=35.0,
        ),
    )

    result = DeterministicRiskEngine.evaluate(behaviour, ctx)
    assert result.risk_score >= 80.0
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.is_actionable is True
    assert len(result.factors) >= 2
    assert result.breakdown.zone_multiplier == 1.4
