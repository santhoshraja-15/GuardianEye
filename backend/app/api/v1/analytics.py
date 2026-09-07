"""
API Router for Analytics, Heatmaps, and Operational Intelligence
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.analytics import DashboardSummaryResponse
from backend.app.services.analytics_service import analytics_service

router = APIRouter(tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    warehouse_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve operational dashboard summary metrics and spatial risk heatmaps."""
    return analytics_service.get_dashboard_summary(db, warehouse_id=warehouse_id)
