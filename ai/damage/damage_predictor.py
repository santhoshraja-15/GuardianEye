"""
Damage Prediction Engine for Physical Impacts and Handling Anomalies
Calculates damage probabilities based on kinetic energy, drop heights, packaging fragility, and wet floor drag friction.
"""
from typing import List, Optional
from ai.behaviour.behaviour_schemas import BehaviourType, DetectedBehaviour
from ai.context.context_enricher import EnrichedBehaviourContext
from ai.damage.damage_schemas import DamagePredictionResult, DamageStatus, DamageType


class DamagePredictor:
    """Predicts damage likelihood and expected damage type using deterministic physical parameters."""

    @classmethod
    def predict(
        cls,
        behaviour: DetectedBehaviour,
        context: EnrichedBehaviourContext,
    ) -> DamagePredictionResult:
        b_type = behaviour.behaviour_type
        fragility = context.product.fragility_rating
        unit_val = context.product.unit_value_usd
        factors: List[str] = []

        prob = 0.1
        damage_type = DamageType.NO_OBSERVED_DAMAGE

        # 1. Drop evaluation
        if b_type == BehaviourType.B01_DROP:
            fall_h = behaviour.evidence.fall_height_px
            max_safe = context.product.max_safe_drop_height_px
            ratio = fall_h / max(10.0, max_safe)

            if ratio > 1.8:
                prob = min(0.95, 0.5 + 0.1 * fragility)
                damage_type = DamageType.STRUCTURAL_BREAKAGE if fragility >= 3 else DamageType.PACKAGING_DEFORMATION
                factors.append(f"Excessive drop height ({fall_h:.1f}px vs safe {max_safe:.1f}px)")
            elif ratio > 1.0:
                prob = min(0.75, 0.3 + 0.08 * fragility)
                damage_type = DamageType.PACKAGING_DEFORMATION
                factors.append("Moderate drop impact above threshold")
            else:
                prob = 0.25
                damage_type = DamageType.PACKAGING_DEFORMATION

        # 2. Drag & Wet Floor evaluation
        elif b_type in (BehaviourType.B02_DRAG, BehaviourType.B15_WET_FLOOR_DRAGGING):
            dur = behaviour.evidence.duration_seconds
            if b_type == BehaviourType.B15_WET_FLOOR_DRAGGING:
                prob = min(0.92, 0.45 + (0.1 * dur))
                damage_type = DamageType.MOISTURE_CONTAMINATION
                factors.append(f"Carton dragged on wet dock floor for {dur:.2f}s")
            else:
                prob = min(0.70, 0.25 + (0.05 * dur))
                damage_type = DamageType.SURFACE_ABRASION
                factors.append(f"Horizontal abrasive friction drag ({dur:.2f}s)")

        # 3. Throw evaluation
        elif b_type == BehaviourType.B03_THROW:
            prob = min(0.90, 0.4 + 0.1 * fragility)
            damage_type = DamageType.STRUCTURAL_BREAKAGE if fragility >= 3 else DamageType.PACKAGING_DEFORMATION
            factors.append("Ballistic throw impact shock")

        # 4. Stepping on carton evaluation
        elif b_type == BehaviourType.B11_STEPPING_ON_CARTON:
            prob = min(0.95, 0.6 + 0.08 * fragility)
            damage_type = DamageType.CRUSHING
            factors.append("Direct vertical foot pressure / weight load on carton")

        # 5. Stacking violation evaluation
        elif b_type in (BehaviourType.B05_IMPROPER_STACKING, BehaviourType.B06_UNSTABLE_STACK):
            prob = 0.45
            damage_type = DamageType.PACKAGING_DEFORMATION
            factors.append("Uneven compressive stack load")

        else:
            prob = 0.15
            damage_type = DamageType.NO_OBSERVED_DAMAGE

        prob = round(prob, 2)
        damage_status = DamageStatus.POTENTIAL_DAMAGE if prob >= 0.4 else DamageStatus.NOT_OBSERVED
        est_loss = round(unit_val * prob, 2)
        is_claim = prob >= 0.6 and est_loss >= 25.0

        return DamagePredictionResult(
            damage_probability=prob,
            likely_damage_type=damage_type,
            damage_status=damage_status,
            estimated_financial_loss_usd=est_loss,
            is_claim_eligible=is_claim,
            damage_factors=factors,
            confidence=0.92,
        )


damage_predictor = DamagePredictor()
