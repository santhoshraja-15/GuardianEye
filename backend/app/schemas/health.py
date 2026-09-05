"""
Pydantic Schemas for System & Subsystem Health Probes
"""
from datetime import datetime
from typing import Dict, Literal
from pydantic import BaseModel, Field


class SubsystemHealth(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy", "disabled"]
    latency_ms: float = Field(default=0.0, description="Response latency in milliseconds")
    details: Dict[str, str] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    environment: str
    timestamp: datetime
    subsystems: Dict[str, SubsystemHealth] = Field(
        default_factory=lambda: {
            "database": SubsystemHealth(status="healthy", latency_ms=1.2),
            "redis": SubsystemHealth(status="healthy", latency_ms=0.8),
            "storage": SubsystemHealth(status="healthy", latency_ms=2.1),
            "ai_engine": SubsystemHealth(status="healthy", latency_ms=5.4),
        }
    )
