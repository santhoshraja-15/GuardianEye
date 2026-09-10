"""
Generalized Spatial Event ORM Entity

BehaviourEvent/Incident (backend/app/models/behaviour.py,
backend/app/models/incident.py) are deliberately left untouched — that
1:1 chain is load-bearing for the existing incident/alert/evidence/
prevention workflow and Incident.behaviour_event_id is a non-nullable
unique FK, so it can only ever represent one of the 8 implemented
computer-vision behaviour rules.

SpatialEvent is an additive, separate stream for events that are real
but aren't a "behaviour" in that sense — a zone crossing, a person
lingering near a forklift, unusual congestion. These don't need to
become Incidents to be useful: they're surfaced through their own API
(/api/v1/events) and their own websocket channel (SPATIAL_EVENT_CREATED)
for the Digital Twin / Live Streams timeline. Nothing here is hardcoded
per the spec's event examples — only zone-transition and proximity
detection are actually implemented (see ai/spatial/event_engine.py);
event_type is a free string precisely so more real detectors can be
added later without a schema change.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.session import Base


class SpatialEvent(Base):
    __tablename__ = "spatial_events"

    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), nullable=False, index=True)
    camera_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cameras.id"), nullable=True, index=True)
    warehouse_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("warehouses.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # ZONE_ENTERED, ZONE_EXITED, PROXIMITY_WARNING, ...
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW", index=True)
    frame_number: Mapped[int] = mapped_column(default=0)
    timestamp_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    from_zone_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    to_zone_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    # JSON list of tracker track_id ints involved (1 for a zone crossing,
    # 2 for a proximity pair).
    involved_track_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
