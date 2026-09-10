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


class ComparisonMetric(BaseModel):
    """One metric compared across two time periods (e.g. today vs. yesterday)."""

    label: str
    period_a_label: str
    period_b_label: str
    period_a_value: float
    period_b_value: float
    absolute_change: float
    percent_change: Optional[float] = None
    direction: str  # INCREASED | DECREASED | STABLE


class WhatChangedSummary(BaseModel):
    """Structured "what changed" breakdown backing a comparative answer."""

    improved: List[str] = Field(default_factory=list)
    worsened: List[str] = Field(default_factory=list)
    new_items: List[str] = Field(default_factory=list)
    persistent: List[str] = Field(default_factory=list)
    most_significant_change: Optional[str] = None


class AssistantQueryResponse(BaseModel):
    answer: str
    grounded_citations: List[CitationReference] = Field(default_factory=list)
    is_grounded: bool = True
    confidence: float = 0.95
    suggested_followups: List[str] = Field(default_factory=list)

    # Present only for comparative/temporal answers ("compare today vs
    # yesterday", "what changed this shift?"). Left unset for every other
    # query so existing consumers see no shape change.
    period_a_label: Optional[str] = None
    period_b_label: Optional[str] = None
    comparison: Optional[List[ComparisonMetric]] = None
    what_changed: Optional[WhatChangedSummary] = None
    why_it_matters: Optional[str] = None
    recommended_action: Optional[str] = None
    data_available: bool = True
    llm_provider_used: Optional[str] = None
