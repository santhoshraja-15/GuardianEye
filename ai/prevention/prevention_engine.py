"""
Prevention Intelligence Engine
Performs Root Cause Analysis (RCA), generates corrective action recommendations, and runs counterfactual simulations.
"""
from typing import List, Optional, Tuple
from ai.behaviour.behaviour_schemas import BehaviourType, DetectedBehaviour
from ai.context.context_enricher import EnrichedBehaviourContext
from ai.prevention.prevention_schemas import (
    CounterfactualResult,
    PreventionType,
    RecommendationResult,
    RootCauseCategory,
    RootCauseResult,
)
from ai.risk.risk_schemas import RiskEvaluationResult


class PreventionEngine:
    """Deterministic prevention, RCA, and counterfactual simulation engine."""

    @classmethod
    def analyze_root_cause(
        cls,
        behaviour: DetectedBehaviour,
        context: EnrichedBehaviourContext,
    ) -> RootCauseResult:
        b_type = behaviour.behaviour_type
        observed = []
        inferred = []
        cat = RootCauseCategory.PROCESS
        conf = 0.90

        if b_type == BehaviourType.B15_WET_FLOOR_DRAGGING or "WET" in context.zone_code.upper():
            cat = RootCauseCategory.ENVIRONMENTAL
            observed.append(f"Carton dragged in wet floor zone '{context.zone_code}'.")
            inferred.append("Facility drainage or spill cleanup protocol overdue.")
            conf = 0.95

        elif b_type in (BehaviourType.B01_DROP, BehaviourType.B03_THROW, BehaviourType.B04_ROUGH_HANDLING):
            cat = RootCauseCategory.ERGONOMIC
            observed.append(f"High-velocity manipulation ({behaviour.evidence.peak_velocity_px_s:.1f} px/s).")
            if context.shift_fatigue_multiplier > 1.0:
                inferred.append("Shift duration fatigue contributing to hurried manual handling.")
            else:
                inferred.append("Lack of two-handed lifting technique or operator ergonomic strain.")

        elif b_type in (BehaviourType.B05_IMPROPER_STACKING, BehaviourType.B06_UNSTABLE_STACK):
            cat = RootCauseCategory.PROCESS
            observed.append("Stack overhang exceeds stability threshold.")
            inferred.append("Insufficient palletization guideline adherence / lack of stacking jig.")

        elif b_type in (BehaviourType.B07_INCORRECT_PLACEMENT, BehaviourType.B16_AISLE_OBSTRUCTION):
            cat = RootCauseCategory.CONGESTION
            observed.append(f"Entity placed in aisle / pathway '{context.zone_code}'.")
            inferred.append("Inbound buffer staging capacity reached, causing overflow into pathways.")

        else:
            cat = RootCauseCategory.PROCESS
            observed.append(f"Behaviour {b_type.value} recorded.")
            inferred.append("Standard operating procedure deviation.")

        return RootCauseResult(
            cause_category=cat,
            observed_facts=observed,
            inferred_factors=inferred,
            confidence=conf,
        )

    @classmethod
    def generate_recommendations(
        cls,
        behaviour: DetectedBehaviour,
        context: EnrichedBehaviourContext,
        root_cause: RootCauseResult,
    ) -> List[RecommendationResult]:
        recs: List[RecommendationResult] = []

        if root_cause.cause_category == RootCauseCategory.ENVIRONMENTAL:
            recs.append(
                RecommendationResult(
                    action_title="Immediate Dock Floor Spill Remediation",
                    description="Dispatch sanitation team to dry floor zone and install anti-slip matting.",
                    prevention_type=PreventionType.ENVIRONMENTAL_MAINTENANCE,
                    estimated_risk_reduction_pct=85.0,
                    implementation_priority="P0",
                )
            )

        if root_cause.cause_category == RootCauseCategory.ERGONOMIC:
            recs.append(
                RecommendationResult(
                    action_title="Ergonomic Handling Refresher & Mechanical Lift Aid",
                    description="Provide vacuum lift assist or team lift protocol for packages exceeding 15kg.",
                    prevention_type=PreventionType.TRAINING,
                    estimated_risk_reduction_pct=70.0,
                    implementation_priority="P1",
                )
            )

        if root_cause.cause_category == RootCauseCategory.PROCESS:
            recs.append(
                RecommendationResult(
                    action_title="Enforce Interlocking Pallet Stacking Pattern",
                    description="Update SOP to require interlocking brick stacking pattern and max 4-tier height.",
                    prevention_type=PreventionType.PROCESS_RULE,
                    estimated_risk_reduction_pct=65.0,
                    implementation_priority="P1",
                )
            )

        if root_cause.cause_category == RootCauseCategory.CONGESTION:
            recs.append(
                RecommendationResult(
                    action_title="Re-design Staging Buffer Demarcation",
                    description="Repaint floor buffer boundaries and add LiDAR warning sensors in transit aisles.",
                    prevention_type=PreventionType.LAYOUT_MODIFICATION,
                    estimated_risk_reduction_pct=60.0,
                    implementation_priority="P2",
                )
            )

        return recs

    @classmethod
    def simulate_counterfactual(
        cls,
        behaviour: DetectedBehaviour,
        risk: RiskEvaluationResult,
        context: EnrichedBehaviourContext,
    ) -> CounterfactualResult:
        observed_act = behaviour.description
        obs_score = risk.risk_score

        if behaviour.behaviour_type in (BehaviourType.B01_DROP, BehaviourType.B03_THROW):
            cf_action = "Operator placed package directly onto conveyor/pallet using two-handed controlled motion (< 5 px/s)."
            sim_score = max(10.0, obs_score * 0.18)
        elif behaviour.behaviour_type in (BehaviourType.B02_DRAG, BehaviourType.B15_WET_FLOOR_DRAGGING):
            cf_action = "Operator transported package on hand-truck or roller trolley instead of dragging on floor."
            sim_score = max(12.0, obs_score * 0.20)
        elif behaviour.behaviour_type == BehaviourType.B11_STEPPING_ON_CARTON:
            cf_action = "Operator utilized portable safety step platform instead of standing on product packaging."
            sim_score = 5.0
        else:
            cf_action = "Operator followed standard operating procedure with recommended safety clearance."
            sim_score = max(15.0, obs_score * 0.25)

        sim_score = round(sim_score, 1)
        delta = round(obs_score - sim_score, 1)

        return CounterfactualResult(
            observed_action=observed_act,
            observed_risk_score=obs_score,
            counterfactual_action=cf_action,
            simulated_risk_score=sim_score,
            risk_delta=delta,
            simulation_method="DETERMINISTIC_PHYSICAL_MODEL",
        )


prevention_engine = PreventionEngine()
