"""
Incident Replay Service for Timeline Reconstruction
"""
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.evidence import EvidencePackage
from backend.app.models.incident import Incident
from backend.app.schemas.replay import IncidentReplayResponse, ReplayKeyframe, ReplayKeyframeBox


class ReplayService:
    @staticmethod
    async def get_incident_replay(
        db: AsyncSession,
        incident_id: str,
    ) -> Optional[IncidentReplayResponse]:
        query = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(selectinload(Incident.evidence_package), selectinload(Incident.behaviour_event))
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        if not incident or not incident.evidence_package:
            return None

        pkg = incident.evidence_package
        keyframes_list = []
        try:
            raw_overlay = json.loads(pkg.overlay_data)
            for item in raw_overlay:
                boxes = [
                    ReplayKeyframeBox(
                        track_id=b.get("track_id", 0),
                        class_name=b.get("class_name", "object"),
                        bbox_xyxy=b.get("bbox_xyxy", [0, 0, 0, 0]),
                        state_label=b.get("state_label", "ANOMALY"),
                        is_primary=b.get("is_primary", False),
                    )
                    for b in item.get("overlay_boxes", [])
                ]
                keyframes_list.append(
                    ReplayKeyframe(
                        frame_index=item.get("frame_index", 0),
                        timestamp_seconds=item.get("timestamp_seconds", 0.0),
                        image_url=item.get("image_path", ""),
                        sha256_hash=item.get("sha256_hash", ""),
                        boxes=boxes,
                    )
                )
        except Exception:
            keyframes_list = []

        return IncidentReplayResponse(
            incident_id=incident.id,
            video_id=incident.behaviour_event.video_id if incident.behaviour_event else "",
            behaviour_code=incident.behaviour_event.behaviour_code if incident.behaviour_event else "UNKNOWN",
            clip_url=pkg.clip_path,
            snapshot_url=pkg.snapshot_path,
            sha256_checksum=pkg.sha256_checksum,
            duration_seconds=(
                incident.behaviour_event.duration_seconds if incident.behaviour_event else 0.0
            ),
            keyframes=keyframes_list,
        )


replay_service = ReplayService()
