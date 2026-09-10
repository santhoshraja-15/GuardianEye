"""
Camera Registry and Calibration API Endpoints

Previously there was no camera API at all — cameras were reachable only
as a read-only nested field of GET /digital-twin/topology, with no way
to create, position, or calibrate one (architecture audit sections 5
and 10). This is that missing surface: CRUD for cameras, plus the
calibration workflow the spec calls "the MOST IMPORTANT architectural
requirement" (video pixel <-> warehouse-meter point correspondences ->
homography).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.camera import (
    CalibrationCreate,
    CalibrationResponse,
    CameraCreate,
    CameraResponse,
    CameraUpdate,
)
from backend.app.services.calibration_service import calibration_service
from backend.app.services.camera_service import camera_service

router = APIRouter()


def _to_camera_response(camera) -> CameraResponse:
    return CameraResponse(
        id=camera.id,
        warehouse_id=camera.warehouse_id,
        zone_id=camera.zone_id,
        name=camera.name,
        camera_code=camera.camera_code,
        rtsp_url=camera.rtsp_url,
        fps=camera.fps,
        resolution=camera.resolution,
        status=camera.status,
        location_x=camera.location_x,
        location_y=camera.location_y,
        location_z=camera.location_z,
        # See the matching comment in digital_twin_service.py: these
        # columns were added via an additive ALTER TABLE with no DDL
        # default, so a pre-existing row reads back as None until next
        # updated through this API.
        is_positioned=bool(camera.is_positioned),
        orientation_degrees=camera.orientation_degrees,
        fov_degrees=camera.fov_degrees or 90.0,
        coverage_range_m=camera.coverage_range_m or 15.0,
        is_calibrated=camera.calibration is not None and bool(camera.calibration.homography_json),
        created_at=camera.created_at,
        updated_at=camera.updated_at,
    )


@router.get(
    "/",
    response_model=List[CameraResponse],
    summary="List Cameras",
    description="Retrieve every registered camera, optionally filtered by warehouse.",
)
def list_cameras(
    warehouse_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CameraResponse]:
    return [_to_camera_response(c) for c in camera_service.list_cameras(db, warehouse_id=warehouse_id)]


@router.post(
    "/",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Camera",
    description="Register a new camera against a warehouse (position/calibration set separately).",
)
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    return _to_camera_response(camera_service.create_camera(db, camera_in))


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get Camera By ID",
)
def get_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    return _to_camera_response(camera_service.get_camera_by_id(db, camera_id))


@router.patch(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Update Camera",
    description="Update a camera's zone/position/orientation/FOV/status.",
)
def update_camera(
    camera_id: str,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CameraResponse:
    return _to_camera_response(camera_service.update_camera(db, camera_id, camera_in))


@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Camera",
)
def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    camera_service.delete_camera(db, camera_id)


@router.post(
    "/{camera_id}/calibration",
    response_model=CalibrationResponse,
    summary="Calibrate Camera",
    description=(
        "Solve and persist a homography from >=4 (normalized video point, warehouse-meter point) "
        "correspondences. Returns the solved matrix and its own reprojection-error self-report — "
        "never a matrix that couldn't actually be solved."
    ),
)
def calibrate_camera(
    camera_id: str,
    calibration_in: CalibrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalibrationResponse:
    calibration = calibration_service.save_calibration(db, camera_id, calibration_in, user_id=current_user.id)
    return CalibrationResponse(
        camera_id=calibration.camera_id,
        source_points=_loads_points(calibration.source_points_json),
        world_points=_loads_points(calibration.world_points_json),
        homography_matrix=_loads_matrix(calibration.homography_json),
        reprojection_error=calibration.reprojection_error,
        is_active=calibration.is_active,
        calibrated_at=calibration.calibrated_at,
    )


@router.get(
    "/{camera_id}/calibration",
    response_model=CalibrationResponse,
    summary="Get Camera Calibration",
)
def get_camera_calibration(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalibrationResponse:
    calibration = calibration_service.get_calibration(db, camera_id)
    return CalibrationResponse(
        camera_id=calibration.camera_id,
        source_points=_loads_points(calibration.source_points_json),
        world_points=_loads_points(calibration.world_points_json),
        homography_matrix=_loads_matrix(calibration.homography_json),
        reprojection_error=calibration.reprojection_error,
        is_active=calibration.is_active,
        calibrated_at=calibration.calibrated_at,
    )


def _loads_points(raw: str):
    import json

    return [tuple(p) for p in json.loads(raw)]


def _loads_matrix(raw):
    import json

    return json.loads(raw) if raw else None
