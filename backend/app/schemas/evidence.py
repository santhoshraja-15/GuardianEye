"""
Pydantic Schemas for Evidence Packages
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidencePackageResponse(BaseModel):
    id: str
    incident_id: str
    snapshot_path: str
    clip_path: str
    pre_event_seconds: float
    post_event_seconds: float
    sha256_checksum: str
    overlay_data: str

    model_config = ConfigDict(from_attributes=True)
