"""
GuardianEye Custom Exceptions & Standardized Error Handling
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class GuardianEyeException(Exception):
    """Base exception for all domain-specific GuardianEye errors"""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(GuardianEyeException):
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} with id '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": str(resource_id)},
        )


class ValidationException(GuardianEyeException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationException(GuardianEyeException):
    def __init__(self, message: str = "Authentication failed or token is invalid."):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(GuardianEyeException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class VideoProcessingException(GuardianEyeException):
    def __init__(self, message: str, video_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="VIDEO_PROCESSING_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"video_id": video_id} if video_id else {},
        )


async def guardian_eye_exception_handler(request: Request, exc: GuardianEyeException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred processing your request.",
                "details": {"type": type(exc).__name__},
            },
        },
    )
