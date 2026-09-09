"""
Prevention Studio, SOP Rules, and Root Cause Analysis Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.evidence import Recommendation, RootCause
from backend.app.models.user import User
from backend.app.schemas.prevention import (
    PreventionRuleResponse,
    RecommendationResponse,
    RootCauseResponse,
)

router = APIRouter()

CORE_SOP_RULES: List[PreventionRuleResponse] = [
    PreventionRuleResponse(
        behaviour_code="B01_DROP",
        rule_name="Free-Fall & Sudden Drop Prevention",
        description="Immediate detection of unconstrained vertical acceleration (> 25 px/s) followed by ground impact.",
        risk_category="PHYSICAL_SAFETY",
        severity_default="CRITICAL",
        sop_citation="SOP-WH-B01: Controlled Cargo Descent Standards",
        detection_threshold_description="Vertical drop distance > 30px, deceleration delta > 20 px/s²",
    ),
    PreventionRuleResponse(
        behaviour_code="B02_DRAG",
        rule_name="Floor Dragging & Abrasion Prevention",
        description="Continuous horizontal displacement of carton without lifting or wheeled conveyance.",
        risk_category="EQUIPMENT_MISUSE",
        severity_default="HIGH",
        sop_citation="SOP-WH-B02: Mechanical Trolley & Pallet Jack Mandate",
        detection_threshold_description="Continuous ground contact sliding > 1.5 seconds",
    ),
    PreventionRuleResponse(
        behaviour_code="B03_THROW",
        rule_name="Parcel Throwing & Ballistic Ejection",
        description="Parabolic trajectory flight with entity speed exceeding 30 px/s without human contact.",
        risk_category="PHYSICAL_SAFETY",
        severity_default="CRITICAL",
        sop_citation="SOP-WH-B03: Zero-Tolerance Ballistic Handling",
        detection_threshold_description="Disengagement during velocity peak, in-flight time > 0.3s",
    ),
    PreventionRuleResponse(
        behaviour_code="B04_TILT",
        rule_name="Excessive Tilt & Incline Anomaly",
        description="Product tilt angle exceeding 45 degrees relative to gravity axis.",
        risk_category="PROCESS_COMPLIANCE",
        severity_default="MEDIUM",
        sop_citation="SOP-WH-B04: Upright Orientation Protocol for Sensitive Goods",
        detection_threshold_description="Aspect ratio deformation or bounding box orientation delta > 40°",
    ),
    PreventionRuleResponse(
        behaviour_code="B05_COLLISION",
        rule_name="Vehicle & Pedestrian Collision Hazard",
        description="Forklift / industrial vehicle proximity violation with pedestrian or fragile stack.",
        risk_category="CRITICAL_SAFETY",
        severity_default="CRITICAL",
        sop_citation="SOP-WH-B05: Dynamic 3-Meter Safety Exclusion Perimeter",
        detection_threshold_description="Centroid distance < 80px, closing velocity > 15 px/s",
    ),
    PreventionRuleResponse(
        behaviour_code="B11_STEPPING_ON_CARTON",
        rule_name="Product Stepping & Crush Hazard",
        description="Worker body weight applied directly onto cartons or lower pallet tiers.",
        risk_category="PHYSICAL_SAFETY",
        severity_default="CRITICAL",
        sop_citation="SOP-WH-B11: Mandatory Safety Step Stool & Ladder Usage",
        detection_threshold_description="Person lower bounding box resting on carton upper bound > 0.8s",
    ),
    PreventionRuleResponse(
        behaviour_code="B12_OVERSTACKING",
        rule_name="Unstable Overstacking & Height Limit",
        description="Stack height exceeding maximum permissible tiers or severe lateral overhang.",
        risk_category="INFRASTRUCTURE",
        severity_default="HIGH",
        sop_citation="SOP-WH-B12: Tier Limits & Overhang Constraints",
        detection_threshold_description="Vertical bounding box aspect ratio > 3.0, centroid drift > 15%",
    ),
    PreventionRuleResponse(
        behaviour_code="B13_ROLLING",
        rule_name="Carton Rolling & Tumbling",
        description="Repetitive end-over-end flipping or tumbling across the warehouse floor.",
        risk_category="EQUIPMENT_MISUSE",
        severity_default="HIGH",
        sop_citation="SOP-WH-B13: Continuous Upright Transport Protocol",
        detection_threshold_description="Consecutive aspect ratio inversions with horizontal displacement",
    ),
    PreventionRuleResponse(
        behaviour_code="B15_WET_FLOOR_DRAGGING",
        rule_name="Wet Dock Floor Dragging & Moisture Ingress",
        description="Dragging cartons across moist dock plates or spilled floor zones.",
        risk_category="ENVIRONMENTAL",
        severity_default="CRITICAL",
        sop_citation="SOP-WH-B15: Wet Dock Surface Isolation and Anti-Slip Protocols",
        detection_threshold_description="Entity dragging detected within zone marked with moisture multiplier > 1.2",
    ),
]


@router.get(
    "/rules",
    response_model=List[PreventionRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Prevention SOP Rules",
    description="Retrieve all configured warehouse safety scenarios, risk categories, and SOP citations.",
)
def get_prevention_rules(
    current_user: User = Depends(get_current_user),
) -> List[PreventionRuleResponse]:
    return CORE_SOP_RULES


@router.get(
    "/recommendations",
    response_model=List[RecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Corrective Action Recommendations",
)
def list_recommendations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RecommendationResponse]:
    return (
        db.query(Recommendation)
        .order_by(Recommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/root-causes",
    response_model=List[RootCauseResponse],
    status_code=status.HTTP_200_OK,
    summary="List Root Cause Analyses",
)
def list_root_causes(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RootCauseResponse]:
    return (
        db.query(RootCause)
        .order_by(RootCause.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
