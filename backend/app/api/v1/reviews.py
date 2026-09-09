"""
Human Review and Active Learning Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.incident import Incident, IncidentHistory
from backend.app.models.learning import HumanReview
from backend.app.models.user import User
from backend.app.schemas.learning import HumanReviewCreateRequest, HumanReviewResponse

router = APIRouter()


@router.post(
    "/",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Human Review",
    description="Submit reviewer verdict, notes, and curation flag for active learning.",
)
def submit_human_review(
    req: HumanReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HumanReviewResponse:
    incident = db.query(Incident).filter(Incident.id == req.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {req.incident_id} not found")

    review = HumanReview(
        incident_id=req.incident_id,
        reviewed_by=current_user.id,
        review_outcome=req.review_outcome,
        corrected_behaviour_code=req.corrected_behaviour_code,
        reviewer_notes=req.reviewer_notes,
        is_curated_for_training=req.is_curated_for_training,
    )
    db.add(review)

    # Transition incident status based on outcome
    if req.review_outcome == "CORRECT":
        incident.status = "CONFIRMED"
    elif req.review_outcome == "INCORRECT":
        incident.status = "REJECTED"
    elif req.review_outcome == "CHANGE_BEHAVIOUR":
        incident.status = "CONFIRMED"

    history = IncidentHistory(
        incident_id=incident.id,
        user_id=current_user.id,
        from_status="UNDER_REVIEW",
        to_status=incident.status,
        change_reason=f"Human Review Verdict: {req.review_outcome}. Notes: {req.reviewer_notes or 'None'}",
    )
    db.add(history)
    db.commit()
    db.refresh(review)

    return review


@router.get(
    "/incident/{incident_id}",
    response_model=List[HumanReviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Reviews for Incident",
)
def get_incident_reviews(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[HumanReviewResponse]:
    return (
        db.query(HumanReview)
        .filter(HumanReview.incident_id == incident_id)
        .order_by(HumanReview.created_at.desc())
        .all()
    )


@router.get(
    "/",
    response_model=List[HumanReviewResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Human Reviews",
)
def list_human_reviews(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[HumanReviewResponse]:
    return (
        db.query(HumanReview)
        .order_by(HumanReview.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
