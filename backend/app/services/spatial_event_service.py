"""
Persistence and retrieval for generalized SpatialEvents (zone
transitions, proximity warnings — see models/spatial_event.py).
"""
import json
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.app.models.spatial_event import SpatialEvent
from backend.app.schemas.spatial_event import SpatialEventResponse


class SpatialEventService:
    @staticmethod
    def create_event(
        db: Session,
        video_id: str,
        event_type: str,
        severity: str,
        frame_number: int,
        timestamp_seconds: float,
        description: str,
        camera_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        from_zone_id: Optional[str] = None,
        to_zone_id: Optional[str] = None,
        involved_track_ids: Optional[List[int]] = None,
        confidence: float = 1.0,
    ) -> SpatialEvent:
        event = SpatialEvent(
            video_id=video_id,
            camera_id=camera_id,
            warehouse_id=warehouse_id,
            event_type=event_type,
            severity=severity,
            frame_number=frame_number,
            timestamp_seconds=timestamp_seconds,
            zone_id=zone_id,
            from_zone_id=from_zone_id,
            to_zone_id=to_zone_id,
            involved_track_ids_json=json.dumps(involved_track_ids or []),
            confidence=confidence,
            description=description,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_events(
        db: Session,
        video_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        camera_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SpatialEvent]:
        query = db.query(SpatialEvent).order_by(SpatialEvent.created_at.desc())
        if video_id:
            query = query.filter(SpatialEvent.video_id == video_id)
        if zone_id:
            query = query.filter(SpatialEvent.zone_id == zone_id)
        if camera_id:
            query = query.filter(SpatialEvent.camera_id == camera_id)
        if event_type:
            query = query.filter(SpatialEvent.event_type == event_type)
        if severity:
            query = query.filter(SpatialEvent.severity == severity)
        return query.offset(offset).limit(limit).all()

    @staticmethod
    def to_response(event: SpatialEvent) -> SpatialEventResponse:
        try:
            track_ids = json.loads(event.involved_track_ids_json)
        except (ValueError, TypeError):
            track_ids = []
        return SpatialEventResponse(
            id=event.id,
            video_id=event.video_id,
            camera_id=event.camera_id,
            warehouse_id=event.warehouse_id,
            event_type=event.event_type,
            severity=event.severity,
            frame_number=event.frame_number,
            timestamp_seconds=event.timestamp_seconds,
            zone_id=event.zone_id,
            from_zone_id=event.from_zone_id,
            to_zone_id=event.to_zone_id,
            involved_track_ids=track_ids,
            confidence=event.confidence,
            description=event.description,
            created_at=event.created_at,
        )


spatial_event_service = SpatialEventService()
