"""
API Router for Digital Twin Topology
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.digital_twin import DigitalTwinTopologyResponse
from backend.app.services.digital_twin_service import digital_twin_service

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


@router.get("/topology", response_model=DigitalTwinTopologyResponse)
async def get_warehouse_digital_twin(
    warehouse_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve 2D/3D warehouse spatial topology, zones, and camera viewpoints."""
    return await digital_twin_service.get_warehouse_topology(db, warehouse_id=warehouse_id)
