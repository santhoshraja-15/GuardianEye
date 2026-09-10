"""
Spatial Events API — zone transitions and proximity warnings.

Additive alongside /incidents and /alerts (see models/spatial_event.py
for why this is a separate stream), so the Digital Twin and Live
Streams timeline have real, queryable events for things that aren't
one of the 8 implemented behaviour-detection rules.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.spatial_event import SpatialEventResponse
from backend.app.services.spatial_event_service import spatial_event_service

router = APIRouter()


@router.get(
    "/",
    response_model=List[SpatialEventResponse],
    summary="List Spatial Events",
    description="Zone transitions and proximity warnings, optionally filtered.",
)
def list_events(
    video_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SpatialEventResponse]:
    events = spatial_event_service.list_events(
        db,
        video_id=video_id,
        zone_id=zone_id,
        camera_id=camera_id,
        event_type=event_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return [spatial_event_service.to_response(e) for e in events]
