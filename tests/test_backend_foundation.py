"""
Level 02 Backend Foundation Verification Tests
"""
from datetime import datetime, timezone
from backend.app.core.config import Settings
from backend.app.core.errors import (
    APIErrorResponse,
    NotFoundException,
    ValidationException,
    GuardianEyeException,
)
from backend.app.schemas.health import HealthResponse, SubsystemHealth


def test_settings_initialization():
    """Verify Settings initializes with all default and derived properties"""
    test_settings = Settings(
        PROJECT_NAME="GuardianEyeTest",
        ENVIRONMENT="test",
        DEBUG=False,
    )
    assert test_settings.PROJECT_NAME == "GuardianEyeTest"
    assert test_settings.ENVIRONMENT == "test"
    assert test_settings.API_V1_STR == "/api/v1"
    assert test_settings.JWT_ALGORITHM == "HS256"
    assert isinstance(test_settings.BACKEND_CORS_ORIGINS, list)


def test_custom_exception_hierarchy():
    """Verify custom domain exceptions instantiate with structured details"""
    nf_exc = NotFoundException("Video", "vid-12345")
    assert nf_exc.status_code == 404
    assert nf_exc.code == "RESOURCE_NOT_FOUND"
    assert "vid-12345" in nf_exc.message
    assert nf_exc.details == {"resource": "Video", "id": "vid-12345"}

    val_exc = ValidationException("Invalid frame format", {"expected": "RGB"})
    assert val_exc.status_code == 422
    assert val_exc.code == "VALIDATION_FAILED"
    assert val_exc.details["expected"] == "RGB"


def test_health_schema_validation():
    """Verify HealthResponse Pydantic schema validation"""
    health = HealthResponse(
        status="healthy",
        version="1.0.0",
        environment="test",
        timestamp=datetime.now(timezone.utc),
        subsystems={
            "database": SubsystemHealth(status="healthy", latency_ms=1.5),
            "ai_engine": SubsystemHealth(status="healthy", latency_ms=4.2),
        },
    )
    assert health.status == "healthy"
    assert "database" in health.subsystems
    assert health.subsystems["database"].latency_ms == 1.5
