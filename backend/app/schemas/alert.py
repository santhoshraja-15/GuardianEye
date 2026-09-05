"""
Pydantic Schemas for Real-time Alerts and Notifications
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    id: str
    behaviour_event_id: str
    zone_id: Optional[str] = None
    alert_level: str
    message: str
    status: str
    deduplication_key: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeRequest(BaseModel):
    alert_id: str
    comment: Optional[str] = None
