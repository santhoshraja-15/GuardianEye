"""
API Router for Risk Assessments
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.risk import RiskAssessmentResponse
from backend.app.services.risk_service import risk_service

router = APIRouter(prefix="/risks", tags=["Risk Assessments"])


@router.get("/event/{behaviour_event_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment_for_event(
    behaviour_event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the deterministic risk assessment for a specific behaviour event."""
    assessment = await risk_service.get_risk_assessment_by_event(db, behaviour_event_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk assessment for event '{behaviour_event_id}' not found",
        )
    factors = []
    try:
        factors = json.loads(assessment.factors_breakdown)
    except Exception:
        factors = []

    return RiskAssessmentResponse(
        id=assessment.id,
        behaviour_event_id=assessment.behaviour_event_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        is_actionable=assessment.risk_score >= 60.0,
        recommended_action=assessment.explanation,
        factors=factors,
    )
