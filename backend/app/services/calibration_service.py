"""
Camera Calibration Service

Solves and persists a per-camera homography from operator-supplied
point correspondences (see ai/spatial/coordinate_transform.solve_homography
for the actual math). This is the "MOST IMPORTANT architectural
requirement" from the spec: without this, there is no honest way to
place a tracked entity's video-pixel position on the warehouse map —
before this service existed, that transform simply did not exist
anywhere in the codebase (confirmed by a repo-wide grep for
homography/calibration/perspective — zero hits).
"""
from datetime import datetime, timezone
import json
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from ai.spatial.coordinate_transform import solve_homography
from backend.app.core.errors import NotFoundException, ValidationException
from backend.app.models.calibration import Calibration
from backend.app.schemas.camera import CalibrationCreate


class CalibrationService:
    @staticmethod
    def save_calibration(db: Session, camera_id: str, calibration_in: CalibrationCreate, user_id: Optional[str]) -> Calibration:
        source_points: List[Tuple[float, float]] = [tuple(p.video_point) for p in calibration_in.points]
        world_points: List[Tuple[float, float]] = [tuple(p.world_point) for p in calibration_in.points]

        matrix, error = solve_homography(source_points, world_points)
        if matrix is None:
            raise ValidationException(
                "Could not solve a homography from the supplied points — need at least 4 "
                "non-degenerate (video_point, world_point) correspondences."
            )

        existing = db.query(Calibration).filter(Calibration.camera_id == camera_id).first()
        if existing:
            existing.source_points_json = json.dumps(source_points)
            existing.world_points_json = json.dumps(world_points)
            existing.homography_json = json.dumps(matrix)
            existing.reprojection_error = error
            existing.is_active = True
            existing.calibrated_by = user_id
            existing.calibrated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        calibration = Calibration(
            camera_id=camera_id,
            source_points_json=json.dumps(source_points),
            world_points_json=json.dumps(world_points),
            homography_json=json.dumps(matrix),
            reprojection_error=error,
            is_active=True,
            calibrated_by=user_id,
            calibrated_at=datetime.now(timezone.utc),
        )
        db.add(calibration)
        db.commit()
        db.refresh(calibration)
        return calibration

    @staticmethod
    def get_calibration(db: Session, camera_id: str) -> Calibration:
        calibration = db.query(Calibration).filter(Calibration.camera_id == camera_id).first()
        if not calibration:
            raise NotFoundException("Calibration", camera_id)
        return calibration

    @staticmethod
    def get_active_homography(db: Session, camera_id: Optional[str]) -> Tuple[Optional[List[List[float]]], Optional[float]]:
        """Best-effort lookup used by the pipeline/tracking layer — never
        raises; returns (None, None) for an uncalibrated or unspecified
        camera so callers fall back to the honest UNCALIBRATED_ESTIMATE
        path in coordinate_transform.world_position."""
        if not camera_id:
            return None, None
        calibration = (
            db.query(Calibration)
            .filter(Calibration.camera_id == camera_id, Calibration.is_active.is_(True))
            .first()
        )
        if not calibration or not calibration.homography_json:
            return None, None
        try:
            return json.loads(calibration.homography_json), calibration.reprojection_error
        except (ValueError, TypeError):
            return None, None


calibration_service = CalibrationService()
