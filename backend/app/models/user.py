"""
User, Role, RBAC, and Audit Trail ORM Entities
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated or JSON string

    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("roles.id"), nullable=True)

    role: Mapped[Optional[Role]] = relationship("Role", back_populates="users")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., "INCIDENT_STATUS_CHANGE"
    entity_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # "Incident", "Video"
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    before_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped[Optional[User]] = relationship("User", back_populates="audit_logs")
