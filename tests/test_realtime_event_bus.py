from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.event_bus import EventEnvelope, event_bus


def test_event_envelope_serializes_contract():
    event = EventEnvelope(
        event="ALERT_CREATED",
        warehouse_id="warehouse-1",
        data={"alert_id": "alt-123", "alert_level": "HIGH"},
    )

    payload = event.model_dump()
    assert payload["event"] == "ALERT_CREATED"
    assert payload["warehouse_id"] == "warehouse-1"
    assert payload["data"]["alert_id"] == "alt-123"
    assert "timestamp" in payload


def test_websocket_connects_without_token():
    client = TestClient(app)

    response = client.get("/api/v1/health")
    assert response.status_code == 200

    with client.websocket_connect("/api/v1/ws/events?warehouse_id=warehouse-1") as websocket:
        message = websocket.receive_json()
        assert message["event"] == "connection_ok"
        assert "connected" in message["data"]["message"].lower()


def test_websocket_emits_published_event():
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/events?warehouse_id=warehouse-1") as websocket:
        message = websocket.receive_json()
        assert message["event"] == "connection_ok"

        event_bus.publish(
            "INCIDENT_STATUS_CHANGED",
            {"incident_id": "INC-1", "from_status": "DETECTED", "to_status": "ALERTED"},
            warehouse_id="warehouse-1",
        )

        broadcast = websocket.receive_json()
        assert broadcast["event"] == "INCIDENT_STATUS_CHANGED"
        assert broadcast["data"]["incident_id"] == "INC-1"
        assert broadcast["warehouse_id"] == "warehouse-1"
