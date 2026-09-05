"""
API Router for Evidence Packages
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.evidence import EvidencePackageResponse
from backend.app.services.evidence_service import evidence_service

router = APIRouter(prefix="/evidence", tags=["Evidence Packages"])


@router.get("/incident/{incident_id}", response_model=EvidencePackageResponse)
async def get_incident_evidence(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the cryptographic evidence package and visual overlays for an incident."""
    evidence = await evidence_service.get_evidence_by_incident(db, incident_id=incident_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence package for incident '{incident_id}' not found",
        )
    return evidence
