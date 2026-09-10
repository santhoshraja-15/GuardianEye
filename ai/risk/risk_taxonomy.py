"""
Centralized Behaviour Risk Taxonomy

Every behaviour type GuardianEye can classify gets one explicit, documented
risk profile here — DeterministicRiskEngine looks weights up from this
table rather than each behaviour silently inheriting an unexplained
neutral default. If a value below looks arbitrary, it's because it's a
judgment call encoded once, in one place, instead of an accidental gap.

`detection_status` is a deliberately honest field: nine of these twenty
behaviour types (the CORE_TEN below, minus one — see behaviour_engine.py)
currently have a real computer-vision detection rule wired up. The
remaining ones are fully specified here — severity, weight, confidence
threshold, recommended action — so risk *scoring* is complete and
consistent the moment a detection rule for them ships, but they cannot
fire from real video today. Reporting them as "IMPLEMENTED" would be a
fabricated capability claim; this table says so explicitly instead.
"""
from dataclasses import dataclass

from ai.behaviour.behaviour_schemas import BehaviourSeverity, BehaviourType


@dataclass(frozen=True)
class BehaviourRiskProfile:
    behaviour_type: BehaviourType
    base_severity: BehaviourSeverity
    risk_weight: float
    confidence_threshold: float
    recommended_action: str
    detection_status: str  # "IMPLEMENTED" | "PLANNED"


RISK_TAXONOMY = {
    BehaviourType.B01_DROP: BehaviourRiskProfile(
        BehaviourType.B01_DROP, BehaviourSeverity.HIGH, 1.20, 0.55,
        "Inspect the dropped item for internal damage before it moves further down the line.",
        "IMPLEMENTED",
    ),
    BehaviourType.B02_DRAG: BehaviourRiskProfile(
        BehaviourType.B02_DRAG, BehaviourSeverity.MEDIUM, 1.10, 0.50,
        "Provide a trolley or pallet jack at this station to eliminate floor-dragging.",
        "IMPLEMENTED",
    ),
    BehaviourType.B03_THROW: BehaviourRiskProfile(
        BehaviourType.B03_THROW, BehaviourSeverity.CRITICAL, 1.35, 0.55,
        "Coach the operator on controlled placement; ballistic handling has the highest breakage rate of any tracked behaviour.",
        "IMPLEMENTED",
    ),
    BehaviourType.B04_ROUGH_HANDLING: BehaviourRiskProfile(
        BehaviourType.B04_ROUGH_HANDLING, BehaviourSeverity.MEDIUM, 1.00, 0.50,
        "Review acceleration/deceleration force at this station against SOP handling limits.",
        "IMPLEMENTED",
    ),
    BehaviourType.B05_IMPROPER_STACKING: BehaviourRiskProfile(
        BehaviourType.B05_IMPROPER_STACKING, BehaviourSeverity.MEDIUM, 1.05, 0.50,
        "Enforce heavy-on-bottom stacking order and re-stack the affected pallet.",
        "IMPLEMENTED",
    ),
    BehaviourType.B06_UNSTABLE_STACK: BehaviourRiskProfile(
        BehaviourType.B06_UNSTABLE_STACK, BehaviourSeverity.HIGH, 1.15, 0.55,
        "Stabilize or reduce stack height before it progresses toward collapse.",
        "PLANNED",
    ),
    BehaviourType.B07_INCORRECT_PLACEMENT: BehaviourRiskProfile(
        BehaviourType.B07_INCORRECT_PLACEMENT, BehaviourSeverity.MEDIUM, 1.10, 0.50,
        "Relocate the item to its designated zone and reinforce zone-marking compliance.",
        "IMPLEMENTED",
    ),
    BehaviourType.B08_EQUIPMENT_MISUSE: BehaviourRiskProfile(
        BehaviourType.B08_EQUIPMENT_MISUSE, BehaviourSeverity.HIGH, 1.20, 0.55,
        "Retrain on correct equipment operating procedure for this task.",
        "PLANNED",
    ),
    BehaviourType.B09_PALLET_MISALIGNMENT: BehaviourRiskProfile(
        BehaviourType.B09_PALLET_MISALIGNMENT, BehaviourSeverity.MEDIUM, 1.10, 0.55,
        "Re-engage the forks fully and square the pallet before lifting.",
        "PLANNED",
    ),
    BehaviourType.B10_LOADING_SEQUENCE_VIOLATION: BehaviourRiskProfile(
        BehaviourType.B10_LOADING_SEQUENCE_VIOLATION, BehaviourSeverity.MEDIUM, 1.05, 0.55,
        "Secure the base tier fully before staging upper tiers.",
        "PLANNED",
    ),
    BehaviourType.B11_STEPPING_ON_CARTON: BehaviourRiskProfile(
        BehaviourType.B11_STEPPING_ON_CARTON, BehaviourSeverity.HIGH, 1.40, 0.55,
        "Provide approved step platforms; direct foot-loading on product has the highest crushing risk observed.",
        "IMPLEMENTED",
    ),
    BehaviourType.B12_KICKING_PRODUCT: BehaviourRiskProfile(
        BehaviourType.B12_KICKING_PRODUCT, BehaviourSeverity.HIGH, 1.30, 0.55,
        "This is a conduct issue, not a process gap — escalate directly to the floor supervisor.",
        "PLANNED",
    ),
    BehaviourType.B13_ROLLING_CARTON: BehaviourRiskProfile(
        BehaviourType.B13_ROLLING_CARTON, BehaviourSeverity.MEDIUM, 1.10, 0.50,
        "Use a conveyor or dolly instead of rolling cartons on their edge/corner.",
        "IMPLEMENTED",
    ),
    BehaviourType.B14_CRUSHING_UNDER_LOAD: BehaviourRiskProfile(
        BehaviourType.B14_CRUSHING_UNDER_LOAD, BehaviourSeverity.CRITICAL, 1.35, 0.55,
        "Immediately verify the compressive load limit for the base item's packaging class.",
        "PLANNED",
    ),
    BehaviourType.B15_WET_FLOOR_DRAGGING: BehaviourRiskProfile(
        BehaviourType.B15_WET_FLOOR_DRAGGING, BehaviourSeverity.HIGH, 1.30, 0.55,
        "Flag the floor condition for facilities and reroute traffic until it is dry.",
        "IMPLEMENTED",
    ),
    BehaviourType.B16_AISLE_OBSTRUCTION: BehaviourRiskProfile(
        BehaviourType.B16_AISLE_OBSTRUCTION, BehaviourSeverity.MEDIUM, 1.05, 0.50,
        "Clear the aisle — obstruction is both a handling and an evacuation-route risk.",
        "PLANNED",
    ),
    BehaviourType.B17_OVERLOADING_PALLET: BehaviourRiskProfile(
        BehaviourType.B17_OVERLOADING_PALLET, BehaviourSeverity.HIGH, 1.20, 0.55,
        "Split the load across pallets to stay within the rated weight limit.",
        "PLANNED",
    ),
    BehaviourType.B18_UNSECURED_TRANSIT: BehaviourRiskProfile(
        BehaviourType.B18_UNSECURED_TRANSIT, BehaviourSeverity.HIGH, 1.15, 0.55,
        "Apply load restraints before transit; shifting cargo is a leading cause of in-transit damage.",
        "PLANNED",
    ),
    BehaviourType.B19_IMPROPER_LIFTING_POSTURE: BehaviourRiskProfile(
        BehaviourType.B19_IMPROPER_LIFTING_POSTURE, BehaviourSeverity.LOW, 0.90, 0.50,
        "This is an ergonomic/operator-safety signal rather than a product-damage one — route to safety training, not quality review.",
        "PLANNED",
    ),
    BehaviourType.B20_COLLISION_RISK: BehaviourRiskProfile(
        BehaviourType.B20_COLLISION_RISK, BehaviourSeverity.CRITICAL, 1.30, 0.55,
        "Pedestrian/vehicle proximity breach — verify right-of-way signage and pedestrian barriers at this location.",
        "PLANNED",
    ),
}


def get_profile(behaviour_type: BehaviourType) -> BehaviourRiskProfile:
    """Every BehaviourType enum member has an entry — this never falls
    through to a silent default."""
    return RISK_TAXONOMY[behaviour_type]


def implemented_behaviour_types() -> list:
    return [bt for bt, profile in RISK_TAXONOMY.items() if profile.detection_status == "IMPLEMENTED"]


def planned_behaviour_types() -> list:
    return [bt for bt, profile in RISK_TAXONOMY.items() if profile.detection_status == "PLANNED"]
