"""
Interaction Query and Database Persistence Service
"""
from typing import List
from sqlalchemy.orm import Session
from ai.interaction.interaction_schemas import FrameInteractions
from backend.app.models.behaviour import Interaction


class InteractionService:
    """Manages recording and querying human-object-equipment interactions"""

    @staticmethod
    def get_interactions_for_video(db: Session, video_id: str) -> List[Interaction]:
        return (
            db.query(Interaction)
            .filter(Interaction.video_id == video_id)
            .order_by(Interaction.start_frame.asc())
            .all()
        )

    @staticmethod
    def persist_frame_interactions(
        db: Session, video_id: str, frame_interactions: FrameInteractions
    ):
        for item in frame_interactions.interactions:
            # Check if existing interaction can be extended
            existing = (
                db.query(Interaction)
                .filter(
                    Interaction.video_id == video_id,
                    Interaction.source_track_id == item.source_track_id,
                    Interaction.target_track_id == item.target_track_id,
                    Interaction.interaction_type == item.interaction_type.value,
                    Interaction.end_frame >= item.start_frame - 5,
                )
                .first()
            )

            if existing:
                existing.end_frame = item.current_frame
                existing.end_time_seconds = item.current_time_seconds
                existing.min_distance_px = min(existing.min_distance_px, item.distance_px)
                existing.max_iou = max(existing.max_iou, item.iou)
            else:
                new_int = Interaction(
                    video_id=video_id,
                    source_track_id=item.source_track_id,
                    target_track_id=item.target_track_id,
                    interaction_type=item.interaction_type.value,
                    start_frame=item.start_frame,
                    end_frame=item.current_frame,
                    start_time_seconds=item.start_time_seconds,
                    end_time_seconds=item.current_time_seconds,
                    min_distance_px=item.distance_px,
                    max_iou=item.iou,
                )
                db.add(new_int)

        db.commit()


interaction_service = InteractionService()
