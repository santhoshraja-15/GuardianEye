"""
Pydantic Schemas for Incident Lifecycle and Case Management
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IncidentCreateRequest(BaseModel):
    behaviour_event_id: str
    warehouse_id: str
    zone_id: Optional[str] = None
    camera_id: Optional[str] = None
    title: str
    summary: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class IncidentStatusUpdateRequest(BaseModel):
    incident_id: str
    new_status: str  # DETECTED, ALERTED, ACKNOWLEDGED, UNDER_REVIEW, CONFIRMED, REJECTED, ACTION_TAKEN, RESOLVED
    change_reason: str
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class IncidentHistoryResponse(BaseModel):
    id: str
    from_status: str
    to_status: str
    change_reason: str
    user_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: str
    incident_code: str
    behaviour_event_id: str
    warehouse_id: str
    zone_id: Optional[str] = None
    camera_id: Optional[str] = None
    title: str
    summary: str
    severity: str
    status: str
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    history: List[IncidentHistoryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
