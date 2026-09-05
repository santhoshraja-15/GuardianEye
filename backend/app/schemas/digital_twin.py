"""
Pydantic Schemas for Digital Twin Warehouse Topology
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ZoneTopology(BaseModel):
    zone_id: str
    zone_code: str
    zone_name: str
    zone_type: str
    polygon_points: List[List[float]]
    risk_multiplier: float


class CameraTopology(BaseModel):
    camera_id: str
    camera_code: str
    camera_name: str
    position_xyz: List[float]
    coverage_zones: List[str]


class DigitalTwinTopologyResponse(BaseModel):
    warehouse_id: str
    warehouse_name: str
    dimensions_meters: List[float]  # [width, length, height]
    zones: List[ZoneTopology] = Field(default_factory=list)
    cameras: List[CameraTopology] = Field(default_factory=list)
    active_entity_count: int = 0
