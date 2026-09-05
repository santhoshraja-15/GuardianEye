"""
Level 04 Authentication and Server-Side RBAC Verification Tests
"""
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.app.schemas.auth import LoginRequest, Token, UserCreate


def test_password_hashing_and_verification():
    """Verify bcrypt password hashing and verification"""
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_and_refresh_token_lifecycle():
    """Verify JWT access and refresh token generation, claims, and decoding"""
    user_id = "usr-test-uuid-999"
    role = "Safety_Officer"

    access_token = create_access_token(subject=user_id, role=role)
    assert isinstance(access_token, str)

    payload = decode_token(access_token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"

    refresh_token = create_refresh_token(subject=user_id)
    refresh_payload = decode_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"


def test_auth_schemas_validation():
    """Verify auth request and response schema validations"""
    user_in = UserCreate(
        email="supervisor@guardianeye.ai",
        password="SecurePassword2026!",
        full_name="Sarah Connor",
        role_name="Supervisor",
    )
    assert user_in.email == "supervisor@guardianeye.ai"
    assert user_in.role_name == "Supervisor"

    login_req = LoginRequest(
        email="supervisor@guardianeye.ai",
        password="SecurePassword2026!",
    )
    assert login_req.email == "supervisor@guardianeye.ai"
