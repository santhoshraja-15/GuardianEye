"""
Warehouse, Zone, and Camera Topology ORM Entities
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.video import Video


class Warehouse(Base):
    __tablename__ = "warehouses"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    width_meters: Mapped[float] = mapped_column(Float, default=100.0)
    length_meters: Mapped[float] = mapped_column(Float, default=150.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    zones: Mapped[List["Zone"]] = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="warehouse", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    zone_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="STORAGE"
    )  # STORAGE, LOADING_BAY, DANGER, RESTRICTED, TRANSIT, STAGING
    polygon_coordinates: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON serialized list of [x, y] coordinates
    risk_weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)

    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="zones")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="zone")


class Camera(Base):
    __tablename__ = "cameras"

    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    camera_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    rtsp_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_x: Mapped[float] = mapped_column(Float, default=0.0)
    location_y: Mapped[float] = mapped_column(Float, default=0.0)
    location_z: Mapped[float] = mapped_column(Float, default=5.0)  # Mounting height in meters
    fps: Mapped[int] = mapped_column(Integer, default=30)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080")
    status: Mapped[str] = mapped_column(String(20), default="ONLINE")  # ONLINE, OFFLINE, DEGRADED

    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="cameras")
    zone: Mapped[Optional[Zone]] = relationship("Zone", back_populates="cameras")
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="camera")
