"""
Digital Twin Service for Warehouse Topology and Spatial State

Rebuilt from a static-topology-only endpoint (see git history for the
previous version) into one that also reports real, currently-known
tracked entities and puts zones/cameras/entities on one shared 0-1
coordinate plane. Two fabrications this replaces:

  * active_entity_count used to be a literal `12` (no-warehouse
    fallback) or `len(zones) * 4` (real-warehouse path) — neither ever
    touched a Track row. It is now len(entities), a real count.
  * Cameras used to fall back to a hardcoded [10.0, 10.0, 5.0] position
    whenever location_x/y were their default 0.0 (a falsy-value bug,
    `location_x or 10.0`), so every never-positioned camera rendered
    stacked on one identical fake dot. Camera.is_positioned (an
    explicit flag, added alongside this rewrite) now distinguishes "at
    (0,0) because that's real" from "never positioned" honestly.

This is still not a full realtime digital twin — see
is_live_entity_count on the response and the module-level note below.
"""
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ai.spatial.coordinate_transform import normalize_zone_polygons
from backend.app.core.errors import NotFoundException
from backend.app.models.tracking import Track, TrackPoint
from backend.app.models.video import Video
from backend.app.models.warehouse import Camera, Warehouse, Zone
from backend.app.schemas.digital_twin import (
    CameraTopology,
    DigitalTwinTopologyResponse,
    EntityTopology,
    ZoneTopology,
)


class DigitalTwinService:
    @staticmethod
    def get_warehouse_topology(
        db: Session,
        warehouse_id: Optional[str] = None,
    ) -> DigitalTwinTopologyResponse:
        query = select(Warehouse).options(selectinload(Warehouse.zones), selectinload(Warehouse.cameras))
        if warehouse_id:
            query = query.where(Warehouse.id == warehouse_id)

        result = db.execute(query)
        wh = result.scalars().first()

        if not wh:
            # Previously this branch returned an entirely invented demo
            # warehouse (name, two zones, one camera — all fabricated).
            # Rule #42 in the spec is strict: no production fake/demo
            # positions. A genuinely warehouse-less system now gets an
            # honest 404 instead, matching every other *ById lookup in
            # this codebase (SpatialService.get_zone_by_id, etc.) — the
            # frontend renders its own "no warehouse configured" empty
            # state rather than being handed made-up geometry.
            raise NotFoundException("Warehouse", warehouse_id or "<any>")

        raw_polygons: Dict[str, List[Tuple[float, float]]] = {}
        for z in wh.zones:
            try:
                coords = json.loads(z.polygon_coordinates) if z.polygon_coordinates else []
                raw_polygons[z.id] = [(float(p[0]), float(p[1])) for p in coords if len(p) >= 2]
            except (ValueError, TypeError):
                raw_polygons[z.id] = []

        normalized_polygons = normalize_zone_polygons(raw_polygons) if any(raw_polygons.values()) else {}

        zones_list = [
            ZoneTopology(
                zone_id=z.id,
                zone_code=z.code,
                zone_name=z.name,
                zone_type=z.zone_type,
                polygon_points=[list(p) for p in raw_polygons.get(z.id, [])],
                normalized_polygon_points=[list(p) for p in normalized_polygons.get(z.id, [])],
                risk_multiplier=z.risk_weight,
                is_restricted=z.is_restricted,
            )
            for z in wh.zones
        ]

        width_m = wh.width_meters or 100.0
        length_m = wh.length_meters or 80.0

        cams_list = [
            CameraTopology(
                camera_id=c.id,
                camera_code=c.camera_code,
                camera_name=c.name,
                position_xyz=[c.location_x, c.location_y, c.location_z],
                # Cameras are positioned in warehouse-meters (their own
                # declared space, separate from the zone-authoring
                # plane) — normalized against the warehouse's own
                # physical footprint, not the zones' bounding box, since
                # the two coordinate spaces have no calibrated
                # relationship to each other yet (see
                # ai/spatial/coordinate_transform.py's module docstring
                # for why this is an honest simplification, not a
                # precise alignment claim).
                normalized_position=[
                    round(max(0.0, min(1.0, c.location_x / width_m)), 4),
                    round(max(0.0, min(1.0, c.location_y / length_m)), 4),
                ],
                # bool(...)/`or <default>` coercions: these columns were
                # added to an already-seeded cameras table via
                # schema_sync's additive ALTER TABLE, which has no DDL-
                # level default — existing rows read back as SQL NULL /
                # Python None until a camera is next updated through the
                # API, even though the ORM model declares a default for
                # any *new* row. None here means exactly what the
                # default would have meant ("never positioned", "no
                # orientation set"), so this coerces rather than letting
                # a stale row fail response validation.
                is_positioned=bool(c.is_positioned),
                orientation_degrees=c.orientation_degrees,
                fov_degrees=c.fov_degrees or 90.0,
                coverage_range_m=c.coverage_range_m or 15.0,
                coverage_zones=[c.zone_id] if c.zone_id else [],
                is_calibrated=c.calibration is not None and bool(c.calibration.homography_json),
                status=c.status,
            )
            for c in wh.cameras
        ]

        entities = DigitalTwinService._collect_real_entities(db, wh)

        return DigitalTwinTopologyResponse(
            warehouse_id=wh.id,
            warehouse_name=wh.name,
            dimensions_meters=[width_m, length_m, 10.0],
            zones=zones_list,
            cameras=cams_list,
            entities=entities,
            active_entity_count=len(entities),
            is_live_entity_count=False,
        )

    @staticmethod
    def _collect_real_entities(db: Session, wh: Warehouse) -> List[EntityTopology]:
        """One snapshot per camera — the most recently completed video
        attributed to it, and every one of that video's tracks' latest
        known position. Also folds in the most recently completed video
        with no camera assigned at all, but only when `wh` is the
        first/default warehouse — mirroring exactly how
        ai.pipeline_runner.process_video resolves an unassigned video's
        warehouse (falls back to `db.query(Warehouse).first()`), so
        this list matches what the rest of the backend actually
        attributed that video's incidents/behaviours to, instead of
        inventing a separate attribution rule just for this endpoint."""
        entities: List[EntityTopology] = []
        seen_video_ids: set = set()

        for cam in wh.cameras:
            latest_video = (
                db.query(Video)
                .filter(Video.camera_id == cam.id, Video.status == "COMPLETED")
                .order_by(Video.updated_at.desc())
                .first()
            )
            if not latest_video or latest_video.id in seen_video_ids:
                continue
            seen_video_ids.add(latest_video.id)
            entities.extend(DigitalTwinService._entities_from_video(db, latest_video, cam.id))

        first_warehouse = db.query(Warehouse).order_by(Warehouse.created_at.asc()).first()
        if first_warehouse and first_warehouse.id == wh.id:
            unassigned_video = (
                db.query(Video)
                .filter(Video.camera_id.is_(None), Video.status == "COMPLETED")
                .order_by(Video.updated_at.desc())
                .first()
            )
            if unassigned_video and unassigned_video.id not in seen_video_ids:
                entities.extend(DigitalTwinService._entities_from_video(db, unassigned_video, None))

        return entities

    @staticmethod
    def _entities_from_video(db: Session, video: Video, camera_id: Optional[str]) -> List[EntityTopology]:
        tracks = db.query(Track).filter(Track.video_id == video.id).all()
        out: List[EntityTopology] = []
        for track in tracks:
            latest_point = (
                db.query(TrackPoint)
                .filter(TrackPoint.track_id_fk == track.id)
                .order_by(TrackPoint.frame_number.desc())
                .first()
            )
            # normalized_x/y are only populated for points persisted
            # after the spatial-context wiring landed (see
            # tracking_service.persist_frame_tracks) — older rows from
            # before that stay silently excluded rather than rendered
            # at a guessed (0, 0).
            if not latest_point or latest_point.normalized_x is None:
                continue
            world_pos = None
            if latest_point.world_x is not None and latest_point.world_y is not None:
                world_pos = [latest_point.world_x, latest_point.world_y]
            out.append(
                EntityTopology(
                    track_id=track.track_id,
                    video_id=video.id,
                    camera_id=camera_id,
                    class_name=track.class_name,
                    normalized_position=[latest_point.normalized_x, latest_point.normalized_y],
                    zone_id=latest_point.zone_id,
                    world_position=world_pos,
                    world_position_quality=latest_point.world_position_quality,
                    confidence=latest_point.confidence,
                    last_seen_frame=track.last_frame,
                    last_seen_timestamp_seconds=latest_point.timestamp_seconds,
                )
            )
        return out


digital_twin_service = DigitalTwinService()
