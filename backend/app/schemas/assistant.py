"""
Pydantic Schemas for Grounded AI Assistant and Copilot
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitationReference(BaseModel):
    source_type: str  # INCIDENT, RISK_ASSESSMENT, ZONE, BEHAVIOUR_RULE
    source_id: str
    title: str
    confidence: float
    snippet: str


class AssistantQueryRequest(BaseModel):
    query: str
    warehouse_id: Optional[str] = None
    max_citations: int = 5


class AssistantQueryResponse(BaseModel):
    answer: str
    grounded_citations: List[CitationReference] = Field(default_factory=list)
    is_grounded: bool = True
    confidence: float = 0.95
    suggested_followups: List[str] = Field(default_factory=list)
