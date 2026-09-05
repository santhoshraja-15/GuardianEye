"""
GuardianEye Main FastAPI Application Entrypoint
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.errors import (
    GuardianEyeException,
    guardian_eye_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from backend.app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown routines
    """
    # 1. Startup
    setup_logging()
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"Loaded config: DB={settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}, AI_DEVICE={settings.YOLO_DEVICE}")
    yield
    # 2. Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME} cleanly.")


def create_application() -> FastAPI:
    """Application factory for GuardianEye FastAPI instance"""
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} API",
        description="AI-Powered Warehouse Behaviour, Risk, Damage Prevention & Operational Intelligence Platform",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # 1. Security & CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Global Exception Handlers
    app.add_exception_handler(GuardianEyeException, guardian_eye_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 3. Mount API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # 4. Root Health / Liveness
    @app.get("/health", tags=["Root"])
    async def root_health():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_application()
