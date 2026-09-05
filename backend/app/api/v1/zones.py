"""
Spatial Zone Management API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.spatial import ZoneCreate, ZoneResponse, ZoneUpdate
from backend.app.services.spatial_service import spatial_service

router = APIRouter()


@router.get(
    "/",
    response_model=List[ZoneResponse],
    status_code=status.HTTP_200_OK,
    summary="List Warehouse Zones",
    description="Retrieve all configured spatial zones with polygon boundaries.",
)
def list_zones(
    warehouse_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ZoneResponse]:
    return spatial_service.list_zones(db, warehouse_id=warehouse_id)


@router.post(
    "/",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Zone",
    description="Define a new warehouse polygon zone (Supervisor and Admin only).",
    dependencies=[Depends(require_roles(["Admin", "Supervisor"]))],
)
def create_zone(
    zone_in: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ZoneResponse:
    return spatial_service.create_zone(db, zone_in)


@router.get(
    "/{zone_id}",
    response_model=ZoneResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Zone By ID",
    description="Retrieve details and coordinates of a specific zone.",
)
def get_zone(
    zone_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ZoneResponse:
    return spatial_service.get_zone_by_id(db, zone_id)
