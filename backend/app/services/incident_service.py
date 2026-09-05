"""
Incident Lifecycle Service for Case Management and Audit Trails
"""
from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.incident import Incident, IncidentHistory
from backend.app.schemas.incident import IncidentCreateRequest, IncidentStatusUpdateRequest


class IncidentService:
    ALLOWED_TRANSITIONS = {
        "DETECTED": ["ALERTED", "ACKNOWLEDGED", "UNDER_REVIEW", "REJECTED"],
        "ALERTED": ["ACKNOWLEDGED", "UNDER_REVIEW", "REJECTED"],
        "ACKNOWLEDGED": ["UNDER_REVIEW", "CONFIRMED", "REJECTED"],
        "UNDER_REVIEW": ["CONFIRMED", "REJECTED", "ACTION_TAKEN"],
        "CONFIRMED": ["ACTION_TAKEN", "RESOLVED"],
        "REJECTED": ["UNDER_REVIEW"],
        "ACTION_TAKEN": ["RESOLVED"],
        "RESOLVED": ["UNDER_REVIEW"],
    }

    @classmethod
    async def create_incident(
        cls,
        db: AsyncSession,
        req: IncidentCreateRequest,
    ) -> Incident:
        code = f"INC-{uuid.uuid4().hex[:8].upper()}"
        incident = Incident(
            incident_code=code,
            behaviour_event_id=req.behaviour_event_id,
            warehouse_id=req.warehouse_id,
            zone_id=req.zone_id,
            camera_id=req.camera_id,
            title=req.title,
            summary=req.summary,
            severity=req.severity,
            status="DETECTED",
        )
        db.add(incident)
        await db.flush()

        initial_history = IncidentHistory(
            incident_id=incident.id,
            from_status="NONE",
            to_status="DETECTED",
            change_reason="System automated incident generation",
        )
        db.add(initial_history)
        await db.commit()
        await db.refresh(incident)
        return incident

    @classmethod
    async def update_incident_status(
        cls,
        db: AsyncSession,
        req: IncidentStatusUpdateRequest,
        user_id: Optional[str] = None,
    ) -> Optional[Incident]:
        query = select(Incident).where(Incident.id == req.incident_id).options(selectinload(Incident.history))
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        if not incident:
            return None

        current_status = incident.status
        new_status = req.new_status

        # Validate lifecycle transition
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed and new_status != current_status:
            raise ValueError(f"Invalid lifecycle transition from '{current_status}' to '{new_status}'")

        incident.status = new_status
        if req.assigned_to:
            incident.assigned_to = req.assigned_to
        if req.resolution_notes:
            incident.resolution_notes = req.resolution_notes
        if new_status == "RESOLVED":
            incident.resolved_at = datetime.now(timezone.utc)

        history_entry = IncidentHistory(
            incident_id=incident.id,
            user_id=user_id,
            from_status=current_status,
            to_status=new_status,
            change_reason=req.change_reason,
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def get_incident_by_id(
        db: AsyncSession,
        incident_id: str,
    ) -> Optional[Incident]:
        query = select(Incident).where(Incident.id == incident_id).options(selectinload(Incident.history))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        warehouse_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Incident]:
        query = select(Incident).options(selectinload(Incident.history)).order_by(Incident.created_at.desc())
        if warehouse_id:
            query = query.where(Incident.warehouse_id == warehouse_id)
        if severity:
            query = query.where(Incident.severity == severity)
        if status:
            query = query.where(Incident.status == status)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


incident_service = IncidentService()
