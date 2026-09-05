"""
Digital Twin Service for Warehouse Topology and Spatial State
"""
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.warehouse import Camera, Warehouse, Zone
from backend.app.schemas.digital_twin import (
    CameraTopology,
    DigitalTwinTopologyResponse,
    ZoneTopology,
)


class DigitalTwinService:
    @staticmethod
    async def get_warehouse_topology(
        db: AsyncSession,
        warehouse_id: Optional[str] = None,
    ) -> DigitalTwinTopologyResponse:
        query = select(Warehouse).options(selectinload(Warehouse.zones), selectinload(Warehouse.cameras))
        if warehouse_id:
            query = query.where(Warehouse.id == warehouse_id)

        result = await db.execute(query)
        wh = result.scalars().first()

        if not wh:
            # Return default template warehouse topology
            return DigitalTwinTopologyResponse(
                warehouse_id=warehouse_id or "WH-MAIN-01",
                warehouse_name="GuardianEye Model Warehouse Alpha",
                dimensions_meters=[120.0, 80.0, 12.0],
                zones=[
                    ZoneTopology(
                        zone_id="zone-1",
                        zone_code="DOCK_BAY_01",
                        zone_name="Inbound Loading Bay 01",
                        zone_type="LOADING_DOCK",
                        polygon_points=[[0.0, 0.0], [30.0, 0.0], [30.0, 25.0], [0.0, 25.0]],
                        risk_multiplier=1.4,
                    ),
                    ZoneTopology(
                        zone_id="zone-2",
                        zone_code="HIGH_RACK_01",
                        zone_name="High-Rack Storage Aisle 01",
                        zone_type="RACK_AISLE",
                        polygon_points=[[40.0, 10.0], [100.0, 10.0], [100.0, 40.0], [40.0, 40.0]],
                        risk_multiplier=1.6,
                    ),
                ],
                cameras=[
                    CameraTopology(
                        camera_id="cam-1",
                        camera_code="CAM-DOCK-01",
                        camera_name="Inbound Dock High-Angle",
                        position_xyz=[15.0, 2.0, 8.5],
                        coverage_zones=["DOCK_BAY_01"],
                    )
                ],
                active_entity_count=12,
            )

        zones_list = [
            ZoneTopology(
                zone_id=z.id,
                zone_code=z.zone_code,
                zone_name=z.zone_name,
                zone_type=z.zone_type,
                polygon_points=(
                    json.loads(z.polygon_coordinates)
                    if z.polygon_coordinates and z.polygon_coordinates.startswith("[")
                    else []
                ),
                risk_multiplier=z.risk_multiplier,
            )
            for z in wh.zones
        ]

        cams_list = [
            CameraTopology(
                camera_id=c.id,
                camera_code=c.camera_code,
                camera_name=c.camera_name,
                position_xyz=[10.0, 10.0, 6.0],
                coverage_zones=[c.zone_id] if c.zone_id else [],
            )
            for c in wh.cameras
        ]

        return DigitalTwinTopologyResponse(
            warehouse_id=wh.id,
            warehouse_name=wh.name,
            dimensions_meters=[wh.width_meters or 100.0, wh.length_meters or 80.0, 10.0],
            zones=zones_list,
            cameras=cams_list,
            active_entity_count=len(zones_list) * 4,
        )


digital_twin_service = DigitalTwinService()
