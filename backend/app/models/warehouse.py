"""
Warehouse, Zone, and Camera Topology ORM Entities
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.video import Video
    from backend.app.models.calibration import Calibration


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
    # location_x/y default to 0.0 (an existing NOT NULL column — can't be
    # relaxed to nullable without a real migration, see schema_sync.py's
    # additive-only limits) which used to be silently treated as "unset"
    # via a truthy-check fallback (`location_x or 10.0`) that clobbered a
    # deliberate (0, 0) position and, worse, collapsed every never-
    # positioned camera onto one identical fake point. is_positioned is
    # the honest, explicit flag for "has an admin actually placed this
    # camera" — 0.0 is then just a real coordinate like any other.
    is_positioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # 2D top-down orientation (degrees, 0=+X axis, clockwise) and field of
    # view (degrees) for a simple coverage-cone in the Digital Twin. Not a
    # full 3D pan/tilt/roll model — the twin itself is a 2D floor plan, so
    # a full 3D lens model would be precision the rendering can't use.
    orientation_degrees: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fov_degrees: Mapped[float] = mapped_column(Float, default=90.0)
    coverage_range_m: Mapped[float] = mapped_column(Float, default=15.0)
    fps: Mapped[int] = mapped_column(Integer, default=30)
    resolution: Mapped[str] = mapped_column(String(20), default="1920x1080")
    status: Mapped[str] = mapped_column(String(20), default="ONLINE")  # ONLINE, OFFLINE, DEGRADED

    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="cameras")
    zone: Mapped[Optional[Zone]] = relationship("Zone", back_populates="cameras")
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="camera")
    calibration: Mapped[Optional["Calibration"]] = relationship(
        "Calibration", back_populates="camera", uselist=False, cascade="all, delete-orphan"
    )
