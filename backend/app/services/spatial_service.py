"""
Spatial Zone Management and Spatial Reasoning Service
"""
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from ai.spatial.zone_geometry import SpatialGeometryEngine, ZoneDefinition
from backend.app.core.errors import NotFoundException, ValidationException
from backend.app.models.warehouse import Zone
from backend.app.schemas.spatial import ZoneCreate, ZoneUpdate


class SpatialService:
    """Manages warehouse polygon zones and geometric occupancy validation"""

    @staticmethod
    def create_zone(db: Session, zone_in: ZoneCreate) -> Zone:
        try:
            coords = json.loads(zone_in.polygon_coordinates)
            if not isinstance(coords, list) or len(coords) < 3:
                raise ValueError("Polygon must contain at least 3 coordinate pairs.")
        except Exception as e:
            raise ValidationException(f"Invalid polygon_coordinates JSON: {e}")

        zone = Zone(
            warehouse_id=zone_in.warehouse_id,
            name=zone_in.name,
            code=zone_in.code,
            zone_type=zone_in.zone_type.upper(),
            polygon_coordinates=zone_in.polygon_coordinates,
            risk_weight=zone_in.risk_weight,
            is_restricted=zone_in.is_restricted,
        )
        db.add(zone)
        db.commit()
        db.refresh(zone)
        return zone

    @staticmethod
    def list_zones(db: Session, warehouse_id: Optional[str] = None) -> List[Zone]:
        query = db.query(Zone)
        if warehouse_id:
            query = query.filter(Zone.warehouse_id == warehouse_id)
        return query.all()

    @staticmethod
    def get_zone_by_id(db: Session, zone_id: str) -> Zone:
        zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if not zone:
            raise NotFoundException("Zone", zone_id)
        return zone

    @staticmethod
    def get_zone_definitions(db: Session, warehouse_id: Optional[str] = None) -> List[ZoneDefinition]:
        zones = SpatialService.list_zones(db, warehouse_id=warehouse_id)
        definitions = []
        for z in zones:
            try:
                coords = json.loads(z.polygon_coordinates)
                poly = [(float(pt[0]), float(pt[1])) for pt in coords]
                definitions.append(
                    ZoneDefinition(
                        zone_id=z.id,
                        name=z.name,
                        zone_type=z.zone_type,
                        polygon=poly,
                        risk_weight=z.risk_weight,
                        is_restricted=z.is_restricted,
                    )
                )
            except Exception:
                continue
        return definitions


spatial_service = SpatialService()
