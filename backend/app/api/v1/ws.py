"""Realtime websocket stream for GuardianEye operational events (Open Access Mode)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.event_bus import connection_manager

router = APIRouter()


@router.websocket("/events")
async def event_stream(websocket: WebSocket, token: Optional[str] = None, warehouse_id: Optional[str] = None):
    """Open a websocket subscription for warehouse events without authentication requirements.

    Emits a connection_ok event and subsequently broadcasts status or alert events for the warehouse.
    """
    await websocket.accept()

    wh_id = warehouse_id or "WH-CENTRAL-01"
    connection_manager.register(wh_id, websocket)
    await websocket.send_json(
        {
            "event": "connection_ok",
            "warehouse_id": wh_id,
            "data": {"message": "Connected to GuardianEye event stream", "warehouse_id": wh_id},
        }
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.unregister(wh_id, websocket)
