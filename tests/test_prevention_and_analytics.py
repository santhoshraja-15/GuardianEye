"""
Level 23-26 Prevention, RCA, Counterfactuals and Analytics Tests
"""
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
)
from ai.context.context_enricher import ContextEnricher
from ai.prevention.prevention_engine import PreventionEngine
from ai.prevention.prevention_schemas import PreventionType, RootCauseCategory
from ai.risk.risk_engine import DeterministicRiskEngine


def test_root_cause_analysis_and_counterfactual():
    """Verify Root Cause Analysis categories and counterfactual simulation calculations"""
    enricher = ContextEnricher()
    ctx = enricher.enrich(entity_id=1, zone_code="WET_FLOOR_DOCK")

    behaviour = DetectedBehaviour(
        behaviour_type=BehaviourType.B15_WET_FLOOR_DRAGGING,
        severity=BehaviourSeverity.HIGH,
        start_frame=1,
        end_frame=30,
        start_time_seconds=0.0,
        end_time_seconds=2.0,
        duration_seconds=2.0,
        confidence=0.92,
        description="Carton dragged on wet floor",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_WET_DRAG",
            primary_entity_id=1,
            primary_class="carton",
            duration_seconds=2.0,
            peak_velocity_px_s=18.0,
        ),
    )

    rca = PreventionEngine.analyze_root_cause(behaviour, ctx)
    assert rca.cause_category == RootCauseCategory.ENVIRONMENTAL
    assert len(rca.observed_facts) >= 1

    recs = PreventionEngine.generate_recommendations(behaviour, ctx, rca)
    assert len(recs) >= 1
    assert recs[0].prevention_type == PreventionType.ENVIRONMENTAL_MAINTENANCE

    risk_eval = DeterministicRiskEngine.evaluate(behaviour, ctx)
    cf = PreventionEngine.simulate_counterfactual(behaviour, risk_eval, ctx)
    assert cf.risk_delta > 0.0
    assert cf.simulated_risk_score < cf.observed_risk_score
