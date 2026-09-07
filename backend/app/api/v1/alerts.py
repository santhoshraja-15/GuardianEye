"""
API Router for Real-time Alerts
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.alert import AlertAcknowledgeRequest, AlertResponse
from backend.app.services.alert_service import alert_service

router = APIRouter(tags=["Alerts"])


@router.get("", response_model=List[AlertResponse])
async def list_active_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List currently active alerts (OPEN and ACKNOWLEDGED)."""
    return alert_service.get_active_alerts(db, limit=limit)


@router.post("/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    payload: AlertAcknowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an active alert."""
    alert = alert_service.acknowledge_alert(db, alert_id=payload.alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id '{payload.alert_id}' not found",
        )
    return alert
