"""
Camera Calibration ORM Entity

Persists the point correspondences an administrator supplied (video
pixel positions <-> real warehouse meters) and the homography solved
from them (see ai/spatial/coordinate_transform.solve_homography), so a
camera's world-space transform survives a restart and is computed once,
not re-derived on every request.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base

if TYPE_CHECKING:
    from backend.app.models.warehouse import Camera


class Calibration(Base):
    __tablename__ = "calibrations"

    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id"), nullable=False, unique=True, index=True
    )
    # JSON list of [x, y] normalized (0-1) video points the operator clicked.
    source_points_json: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON list of [x, y] warehouse-meter points the operator entered,
    # positionally corresponding to source_points_json.
    world_points_json: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON 3x3 homography matrix solved from the two point sets above via
    # cv2.findHomography — None if fewer than 4 correspondences were given
    # or the solve failed (never a guessed/identity matrix standing in).
    homography_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Mean reprojection error (in normalized-video units) of the solved
    # homography against the operator's own reference points — the
    # calibration's own honest accuracy self-report (spec section 40).
    reprojection_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calibrated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="calibration")
