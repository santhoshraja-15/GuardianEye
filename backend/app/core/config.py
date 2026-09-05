"""
GuardianEye Application Settings & Environment Configuration
"""
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 1. Project & Environment
    PROJECT_NAME: str = "GuardianEye"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # 2. Security & Auth
    SECRET_KEY: str = "default-dev-secret-key-change-in-production-guardianeye-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 3. CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    # 4. Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "guardian"
    POSTGRES_PASSWORD: str = "guardian_password"
    POSTGRES_DB: str = "guardian_eye"
    DATABASE_URL: str = "postgresql+psycopg://guardian:guardian_password@localhost:5432/guardian_eye"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    # 5. Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 6. Object Storage
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage/data"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "guardian-eye-evidence"
    MINIO_USE_SSL: bool = False

    # 7. AI & Computer Vision
    YOLO_MODEL_PATH: str = "./models/detection/yolov8n.pt"
    YOLO_DEVICE: str = "cpu"  # cpu or cuda
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.35
    IOU_THRESHOLD: float = 0.45
    INFERENCE_FPS: int = 10
    MAX_TRACK_AGE_FRAMES: int = 30
    MIN_TRACK_HITS: int = 3

    # 8. Risk & Alerts
    RISK_THRESHOLD_LOW: float = 25.0
    RISK_THRESHOLD_MEDIUM: float = 50.0
    RISK_THRESHOLD_HIGH: float = 75.0
    RISK_THRESHOLD_CRITICAL: float = 90.0
    ALERT_COOLDOWN_SECONDS: float = 10.0
    AUTO_EVIDENCE_GENERATION: bool = True

    # 9. LLM / AI Assistant
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # 10. Logging & Monitoring
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090


settings = Settings()
