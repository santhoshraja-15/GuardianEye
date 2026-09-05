"""
API Router for Incident Case Management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.incident import (
    IncidentCreateRequest,
    IncidentResponse,
    IncidentStatusUpdateRequest,
)
from backend.app.services.incident_service import incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    warehouse_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List incidents with filtering and pagination."""
    return await incident_service.list_incidents(
        db, warehouse_id=warehouse_id, severity=severity, status=status, limit=limit, offset=offset
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full incident details including audit history."""
    incident = await incident_service.get_incident_by_id(db, incident_id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return incident


@router.post("", response_model=IncidentResponse)
async def create_incident(
    payload: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new incident case."""
    return await incident_service.create_incident(db, req=payload)


@router.post("/status", response_model=IncidentResponse)
async def update_incident_status(
    payload: IncidentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition incident lifecycle status with audit reason."""
    try:
        updated = await incident_service.update_incident_status(db, req=payload, user_id=current_user.id)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{payload.incident_id}' not found",
            )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
