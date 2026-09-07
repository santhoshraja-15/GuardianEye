"""
API Router for Grounded AI Copilot and Assistant
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from backend.app.services.assistant_service import assistant_service

router = APIRouter(tags=["Assistant Copilot"])


@router.post("/chat", response_model=AssistantQueryResponse)
async def chat_with_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query the grounded warehouse safety copilot with strict citation provenance."""
    return assistant_service.process_query(db, req=payload)
