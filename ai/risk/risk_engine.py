"""
Deterministic Mathematical Risk Engine for Warehouse Operations
Calculates auditable risk scores (0-100) using physical parameters, fragility, and zone risks.
"""
from ai.behaviour.behaviour_schemas import BehaviourSeverity, DetectedBehaviour
from ai.context.context_enricher import EnrichedBehaviourContext
from ai.risk.risk_schemas import RiskEvaluationResult, RiskFormulaBreakdown, RiskLevel
from ai.risk.risk_taxonomy import RISK_TAXONOMY, get_profile


class DeterministicRiskEngine:
    """
    Evaluates operational risk using deterministic formulas:
    Score = Clamp( (Base * W_base + (Height / MaxSafeHeight) * W_h + (Speed / SpeedLimit) * W_spd) * Fragility_mult * Zone_mult * Fatigue_mult )
    """

    BASE_SEVERITY_SCORES = {
        BehaviourSeverity.LOW: 20.0,
        BehaviourSeverity.MEDIUM: 45.0,
        BehaviourSeverity.HIGH: 70.0,
        BehaviourSeverity.CRITICAL: 90.0,
    }

    # Sourced from the centralized taxonomy (ai/risk/risk_taxonomy.py) so
    # every one of the 20 behaviour types has an explicit, documented
    # weight — none silently inherit an unexplained 1.0 default.
    BEHAVIOUR_BASE_WEIGHTS = {bt: profile.risk_weight for bt, profile in RISK_TAXONOMY.items()}

    @classmethod
    def evaluate(
        cls,
        behaviour: DetectedBehaviour,
        context: EnrichedBehaviourContext,
    ) -> RiskEvaluationResult:
        factors = []
        profile = get_profile(behaviour.behaviour_type)
        base_score = cls.BASE_SEVERITY_SCORES.get(behaviour.severity, 40.0)
        weighted_base = base_score * profile.risk_weight

        if behaviour.confidence < profile.confidence_threshold:
            factors.append(
                f"Detection confidence ({behaviour.confidence:.2f}) is below the "
                f"{profile.confidence_threshold:.2f} threshold typically required for this behaviour type — "
                "treat as lower-certainty until reviewed."
            )

        # 1. Height risk component
        fall_height = behaviour.evidence.fall_height_px
        safe_height = max(10.0, context.product.max_safe_drop_height_px)
        height_ratio = min(2.5, fall_height / safe_height) if fall_height > 0 else 0.0
        height_component = height_ratio * 15.0
        if height_ratio > 1.0:
            factors.append(f"Fall height ({fall_height:.1f}px) exceeded safe limit ({safe_height:.1f}px)")

        # 2. Velocity risk component
        peak_spd = behaviour.evidence.peak_velocity_px_s
        safe_spd = 25.0
        speed_ratio = min(2.5, peak_spd / safe_spd) if peak_spd > 0 else 0.0
        speed_component = speed_ratio * 10.0
        if speed_ratio > 1.2:
            factors.append(f"Peak velocity ({peak_spd:.1f} px/s) exceeded standard threshold")

        # 3. Fragility multiplier: rating 1 -> 0.9x, rating 3 -> 1.1x, rating 5 -> 1.5x
        fragility_mult = 0.8 + (context.product.fragility_rating * 0.14)
        if context.product.fragility_rating >= 4:
            factors.append(f"High-fragility item: {context.product.product_name} (Rating: {context.product.fragility_rating}/5)")

        # 4. Zone & Shift Multipliers
        zone_mult = context.zone_risk_multiplier
        if zone_mult > 1.0:
            factors.append(f"High-risk zone modifier applied: {context.zone_code} ({zone_mult}x)")

        shift_mult = context.shift_fatigue_multiplier
        if shift_mult > 1.0:
            factors.append("Extended shift fatigue factor (+15%)")

        raw_score = (weighted_base + height_component + speed_component) * (fragility_mult * 0.5 + 0.5) * zone_mult * shift_mult
        final_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Categorize Risk Level
        if final_score >= 80.0:
            risk_level = RiskLevel.CRITICAL
            rec = "IMMEDIATE INTERVENTION: Stop operation, inspect package for internal/structural damage, alert floor supervisor."
        elif final_score >= 60.0:
            risk_level = RiskLevel.HIGH
            rec = "SUPERVISOR REVIEW: Flag incident, log SKU for quality inspection before customer dispatch."
        elif final_score >= 35.0:
            risk_level = RiskLevel.MEDIUM
            rec = "PROCESS ADVISORY: Notify operator of handling violation, log for coaching."
        else:
            risk_level = RiskLevel.LOW
            rec = "INFORMATIONAL: Routine telemetry logged."

        # Layer the behaviour-specific guidance (ai/risk/risk_taxonomy.py)
        # under the severity-tier action above, rather than a single
        # generic sentence for every behaviour at a given score band.
        rec = f"{rec} {profile.recommended_action}"

        breakdown = RiskFormulaBreakdown(
            base_severity_score=round(weighted_base, 2),
            height_risk_component=round(height_component, 2),
            velocity_risk_component=round(speed_component, 2),
            fragility_multiplier=round(fragility_mult, 2),
            zone_multiplier=round(zone_mult, 2),
            shift_fatigue_multiplier=round(shift_mult, 2),
            raw_computed_score=round(raw_score, 2),
            final_score_clamped=final_score,
        )

        return RiskEvaluationResult(
            risk_score=final_score,
            risk_level=risk_level,
            breakdown=breakdown,
            factors=factors,
            is_actionable=final_score >= 60.0,
            recommended_action=rec,
        )


risk_engine = DeterministicRiskEngine()
