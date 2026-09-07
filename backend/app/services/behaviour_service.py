"""
Behaviour Event Service for Database Persistence and Querying
"""
import json
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ai.behaviour.behaviour_schemas import DetectedBehaviour
from backend.app.models.behaviour import BehaviourEvent


class BehaviourService:
    @staticmethod
    def create_behaviour_event(
        db: Session,
        video_id: str,
        behaviour: DetectedBehaviour,
        zone_id: Optional[str] = None,
    ) -> BehaviourEvent:
        event = BehaviourEvent(
            video_id=video_id,
            zone_id=zone_id,
            primary_track_id=behaviour.evidence.primary_entity_id,
            secondary_track_id=behaviour.evidence.secondary_entity_id,
            behaviour_code=behaviour.behaviour_type.value,
            behaviour_name=behaviour.description,
            confidence=behaviour.confidence,
            start_frame=behaviour.start_frame,
            end_frame=behaviour.end_frame,
            start_time_seconds=behaviour.start_time_seconds,
            end_time_seconds=behaviour.end_time_seconds,
            duration_seconds=behaviour.duration_seconds,
            dna_sequence=json.dumps(behaviour.keyframe_indices),
            status="DETECTED",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_behaviour_events_by_video(
        db: Session,
        video_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BehaviourEvent]:
        query = (
            select(BehaviourEvent)
            .where(BehaviourEvent.video_id == video_id)
            .order_by(BehaviourEvent.start_time_seconds.asc())
            .offset(offset)
            .limit(limit)
        )
        result = db.execute(query)
        return list(result.scalars().all())


behaviour_service = BehaviourService()
