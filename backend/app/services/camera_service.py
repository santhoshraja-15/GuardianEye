"""
Camera Registry Service — CRUD for warehouse cameras.

Prior to this, no camera API existed at all (see architecture audit
section 5/10): cameras were reachable only as a read-only nested field
of /digital-twin/topology, with no way to create one, assign it to a
zone, or set its position/orientation for the Digital Twin's coverage
view. This is that missing surface.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.core.errors import NotFoundException
from backend.app.models.warehouse import Camera
from backend.app.schemas.camera import CameraCreate, CameraUpdate


class CameraService:
    @staticmethod
    def create_camera(db: Session, camera_in: CameraCreate) -> Camera:
        camera = Camera(
            warehouse_id=camera_in.warehouse_id,
            zone_id=camera_in.zone_id,
            name=camera_in.name,
            camera_code=camera_in.camera_code,
            rtsp_url=camera_in.rtsp_url,
            fps=camera_in.fps,
            resolution=camera_in.resolution,
            status=camera_in.status,
            is_positioned=False,
        )
        db.add(camera)
        db.commit()
        db.refresh(camera)
        return camera

    @staticmethod
    def list_cameras(db: Session, warehouse_id: Optional[str] = None) -> List[Camera]:
        query = db.query(Camera)
        if warehouse_id:
            query = query.filter(Camera.warehouse_id == warehouse_id)
        return query.all()

    @staticmethod
    def get_camera_by_id(db: Session, camera_id: str) -> Camera:
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if not camera:
            raise NotFoundException("Camera", camera_id)
        return camera

    @staticmethod
    def update_camera(db: Session, camera_id: str, camera_in: CameraUpdate) -> Camera:
        camera = CameraService.get_camera_by_id(db, camera_id)
        data = camera_in.model_dump(exclude_unset=True)
        position_fields = {"location_x", "location_y"}
        for field, value in data.items():
            setattr(camera, field, value)
        if position_fields & data.keys():
            camera.is_positioned = True
        db.commit()
        db.refresh(camera)
        return camera

    @staticmethod
    def delete_camera(db: Session, camera_id: str) -> None:
        camera = CameraService.get_camera_by_id(db, camera_id)
        db.delete(camera)
        db.commit()


camera_service = CameraService()
