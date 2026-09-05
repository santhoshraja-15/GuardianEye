"""
Level 18 & 19 Damage Intelligence and Alert Deduplication Tests
"""
import pytest
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
)
from ai.context.context_enricher import ContextEnricher, ProductContext
from ai.damage.damage_predictor import DamagePredictor
from ai.damage.damage_schemas import DamageStatus, DamageType
from backend.app.services.alert_service import AlertService


def test_damage_prediction_wet_floor_and_drop():
    """Verify damage predictor assigns correct damage types and probabilities"""
    catalog = {
        "SKU-DELICATE": ProductContext(
            sku="SKU-DELICATE",
            product_name="Optics Component",
            category="Electronics",
            fragility_rating=5,
            unit_value_usd=500.0,
            max_safe_drop_height_px=15.0,
        )
    }
    enricher = ContextEnricher(catalog=catalog)
    ctx = enricher.enrich(entity_id=1, sku_or_class="SKU-DELICATE", zone_code="WET_FLOOR_DOCK")

    # 1. Test Drop
    drop_event = DetectedBehaviour(
        behaviour_type=BehaviourType.B01_DROP,
        severity=BehaviourSeverity.CRITICAL,
        start_frame=1,
        end_frame=5,
        start_time_seconds=0.033,
        end_time_seconds=0.165,
        duration_seconds=0.132,
        confidence=0.95,
        description="Drop from height",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_DROP",
            primary_entity_id=1,
            primary_class="carton",
            fall_height_px=60.0,
        ),
    )
    res_drop = DamagePredictor.predict(drop_event, ctx)
    assert res_drop.damage_probability > 0.8
    assert res_drop.likely_damage_type == DamageType.STRUCTURAL_BREAKAGE
    assert res_drop.is_claim_eligible is True

    # 2. Test Wet floor drag
    wet_drag = DetectedBehaviour(
        behaviour_type=BehaviourType.B15_WET_FLOOR_DRAGGING,
        severity=BehaviourSeverity.HIGH,
        start_frame=1,
        end_frame=30,
        start_time_seconds=0.0,
        end_time_seconds=2.0,
        duration_seconds=2.0,
        confidence=0.90,
        description="Wet floor dragging",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_WET_DRAG",
            primary_entity_id=1,
            primary_class="carton",
            duration_seconds=2.0,
        ),
    )
    res_wet = DamagePredictor.predict(wet_drag, ctx)
    assert res_wet.likely_damage_type == DamageType.MOISTURE_CONTAMINATION
    assert res_wet.damage_status == DamageStatus.POTENTIAL_DAMAGE


def test_alert_deduplication():
    """Verify alert service suppresses duplicate alerts within time window"""
    service = AlertService(dedup_window_seconds=3.0)
    key = service.generate_dedup_key("video-123", 1, "B01_DROP")

    # First event -> not suppressed
    assert service.should_suppress_alert(key, current_time_sec=1.0) is False
    # Second event 1 second later -> suppressed
    assert service.should_suppress_alert(key, current_time_sec=2.0) is True
    # Third event 4 seconds later -> not suppressed
    assert service.should_suppress_alert(key, current_time_sec=5.5) is False
