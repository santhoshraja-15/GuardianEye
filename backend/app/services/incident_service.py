"""
Incident Lifecycle Service for Case Management and Audit Trails
"""
from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from backend.app.models.incident import Incident, IncidentHistory
from backend.app.schemas.incident import IncidentCreateRequest, IncidentStatusUpdateRequest
from backend.app.services.event_bus import event_bus


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
    def create_incident(
        cls,
        db: Session,
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
        db.flush()

        initial_history = IncidentHistory(
            incident_id=incident.id,
            from_status="NONE",
            to_status="DETECTED",
            change_reason="System automated incident generation",
        )
        db.add(initial_history)
        db.commit()
        db.refresh(incident)
        return incident

    @classmethod
    def update_incident_status(
        cls,
        db: Session,
        req: IncidentStatusUpdateRequest,
        user_id: Optional[str] = None,
    ) -> Optional[Incident]:
        query = select(Incident).where(Incident.id == req.incident_id).options(selectinload(Incident.history))
        result = db.execute(query)
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
        db.commit()
        db.refresh(incident)

        # Previously this method never published anything — the
        # frontend's realtime router has always listened for
        # INCIDENT_STATUS_CHANGED (frontend/src/services/realtime.ts) but
        # nothing in the backend ever emitted it, so an incident's status
        # changing never invalidated any cached query in another open tab.
        event_bus.publish(
            event="INCIDENT_STATUS_CHANGED",
            warehouse_id=incident.warehouse_id,
            data={
                "incident_id": incident.id,
                "incident_code": incident.incident_code,
                "from_status": current_status,
                "to_status": new_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return incident

    @staticmethod
    def get_incident_by_id(
        db: Session,
        incident_id: str,
    ) -> Optional[Incident]:
        query = select(Incident).where(Incident.id == incident_id).options(selectinload(Incident.history))
        result = db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def list_incidents(
        db: Session,
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
        result = db.execute(query)
        return list(result.scalars().all())


incident_service = IncidentService()
