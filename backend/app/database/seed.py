"""
GuardianEye Database Master Seeder
Populates core roles, administrators, warehouses, spatial zones, cameras,
product catalog, ML model registry, and catalogs the 7 real warehouse sample videos.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import get_password_hash
from backend.app.database.session import Base, SessionLocal, engine
from backend.app.models.learning import Dataset, DatasetVersion, ModelArtifact, ModelEvaluation
from backend.app.models.product import Product, ProductCategory
from backend.app.models.user import Role, User
from backend.app.models.video import ProcessingJob, Video
from backend.app.models.warehouse import Camera, Warehouse, Zone
from ai.preprocessing.video_loader import VideoLoader


def seed_database(db: Optional[Session] = None):
    Base.metadata.create_all(bind=engine)

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        logger.info("Seeding GuardianEye Core Database...")

        # 1. Seed Roles
        roles_data = [
            ("Admin", "System Administrator with unrestricted access", "*"),
            ("Supervisor", "Warehouse Operations Supervisor managing live alerts and reviews", "read,write,review,ack"),
            ("Safety_Officer", "Safety compliance and incident investigation officer", "read,review,report,export"),
            ("Analyst", "Operations and risk analytics viewer", "read,analytics,export"),
            ("Operator", "Live terminal display operator", "read,ack"),
        ]
        roles_map = {}
        for name, desc, perms in roles_data:
            role = db.query(Role).filter(Role.name == name).first()
            if not role:
                role = Role(name=name, description=desc, permissions=perms)
                db.add(role)
                db.flush()
            roles_map[name] = role

        # 2. Seed Default Users
        users_data = [
            ("admin@guardianeye.ai", "Admin User", "Admin", "Admin@123456"),
            ("supervisor@guardianeye.ai", "Sarah Supervisor", "Supervisor", "Supervisor@123456"),
            ("operator@guardianeye.ai", "Oliver Operator", "Operator", "Operator@123456"),
            ("safety@guardianeye.ai", "Dave Safety Officer", "Safety_Officer", "Safety@123456"),
            ("auditor@guardianeye.ai", "Audrey Auditor", "Analyst", "Auditor@123456"),
            ("admin@guardianeye.io", "Admin User", "Admin", "Admin@123456"),
            ("supervisor@guardianeye.io", "Sarah Supervisor", "Supervisor", "Supervisor@123456"),
            ("safety@guardianeye.io", "Dave Safety Officer", "Safety_Officer", "Safety@123456"),
        ]
        for email, full_name, role_name, password in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name=full_name,
                    role_id=roles_map[role_name].id,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            else:
                user.hashed_password = get_password_hash(password)
                user.is_active = True
                db.flush()

        # 3. Seed Master Warehouse
        warehouse = db.query(Warehouse).filter(Warehouse.code == "WH-CENTRAL-01").first()
        if not warehouse:
            warehouse = Warehouse(
                name="North Central Logistics Hub",
                code="WH-CENTRAL-01",
                location="1000 Industrial Parkway, Chicago, IL",
                width_meters=120.0,
                length_meters=80.0,
                is_active=True,
            )
            db.add(warehouse)
            db.flush()

        # 4. Seed Spatial Zones
        zones_data = [
            (
                "LOADING_DOCK_01",
                "Dock Loading Bay 01",
                "LOADING_BAY",
                1.4,
                "[[0.0, 0.0], [500.0, 0.0], [500.0, 400.0], [0.0, 400.0]]",
            ),
            (
                "STAGING_BAY_01",
                "Inbound Staging Bay 01",
                "STAGING",
                1.2,
                "[[500.0, 0.0], [1000.0, 0.0], [1000.0, 400.0], [500.0, 400.0]]",
            ),
            (
                "HIGH_RACK_AISLE_3",
                "High Rack Storage Aisle 03",
                "STORAGE",
                1.6,
                "[[0.0, 400.0], [600.0, 400.0], [600.0, 1000.0], [0.0, 1000.0]]",
            ),
            (
                "AISLE_04_TRANSIT",
                "Main Transit Corridor Aisle 04",
                "TRANSIT",
                1.1,
                "[[600.0, 400.0], [1000.0, 400.0], [1000.0, 1000.0], [600.0, 1000.0]]",
            ),
        ]
        zones_map = {}
        for code, name, z_type, weight, coords in zones_data:
            zone = db.query(Zone).filter(Zone.code == code, Zone.warehouse_id == warehouse.id).first()
            if not zone:
                zone = Zone(
                    warehouse_id=warehouse.id,
                    code=code,
                    name=name,
                    zone_type=z_type,
                    risk_weight=weight,
                    polygon_coordinates=coords,
                    is_restricted=False,
                )
                db.add(zone)
                db.flush()
            zones_map[code] = zone

        # 5. Seed Cameras
        cameras_data = [
            ("CAM-DOCK-01", "Dock Bay 01 Telemetry Camera", "rtsp://10.0.1.101/live", "LOADING_DOCK_01"),
            ("CAM-STAGING-01", "Inbound Staging Camera 01", "rtsp://10.0.1.102/live", "STAGING_BAY_01"),
            ("CAM-RACK-03", "High Rack Aisle 03 Overhead Camera", "rtsp://10.0.1.103/live", "HIGH_RACK_AISLE_3"),
            ("CAM-AISLE-04", "Transit Aisle 04 Surveillance Camera", "rtsp://10.0.1.104/live", "AISLE_04_TRANSIT"),
        ]
        cameras_map = {}
        for cam_code, name, url, zone_code in cameras_data:
            camera = db.query(Camera).filter(Camera.camera_code == cam_code, Camera.warehouse_id == warehouse.id).first()
            if not camera:
                camera = Camera(
                    warehouse_id=warehouse.id,
                    zone_id=zones_map[zone_code].id,
                    camera_code=cam_code,
                    name=name,
                    rtsp_url=url,
                    fps=30,
                    resolution="1920x1080",
                    status="ONLINE",
                )
                db.add(camera)
                db.flush()
            cameras_map[cam_code] = camera

        # 6. Seed Product Categories & Products
        categories_data = [
            ("Packaging & General Goods", 0.4, 40.0, 150.0, "Standard packaging"),
            ("Electronics & Sensors", 0.9, 15.0, 30.0, "High fragility electronics"),
            ("Heavy Furniture & Fixtures", 0.6, 20.0, 300.0, "Industrial furniture"),
            ("Precision Glassware", 0.95, 10.0, 20.0, "Fragile lab glass"),
        ]
        cat_map = {}
        for cat_name, frag, drop_h, stack_w, desc in categories_data:
            cat = db.query(ProductCategory).filter(ProductCategory.name == cat_name).first()
            if not cat:
                cat = ProductCategory(
                    name=cat_name,
                    fragility_index=frag,
                    max_drop_height_cm=drop_h,
                    max_stack_weight_kg=stack_w,
                    description=desc,
                )
                db.add(cat)
                db.flush()
            cat_map[cat_name] = cat

        products_data = [
            ("SKU-CARTON-STD", "Standard Corrugated Packaging Carton", "Packaging & General Goods", 5.0, "45x30x50", False),
            ("SKU-OPTICS", "Precision Industrial Laser & Optical Sensor", "Electronics & Sensors", 1.2, "20x15x15", True),
            ("SKU-HEAVY-FURNITURE", "Industrial Steel Storage Cabinet", "Heavy Furniture & Fixtures", 65.0, "120x60x180", True),
            ("SKU-GLASSWARE", "Laboratory Precision Glassware Set", "Precision Glassware", 3.5, "30x30x30", True),
        ]
        for sku, name, cat_name, wt, dims, frag in products_data:
            prod = db.query(Product).filter(Product.sku == sku).first()
            if not prod:
                prod = Product(
                    sku=sku,
                    name=name,
                    category_id=cat_map[cat_name].id,
                    weight_kg=wt,
                    dimensions_cm=dims,
                    is_fragile=frag,
                )
                db.add(prod)
                db.flush()

        # 7. Seed Model Registry & Datasets
        models_data = [
            ("YOLOv8-Warehouse-Perception", "YOLO_DETECTION", "v1.2.0", "PyTorch", "models/detection/yolov8n.pt", "APPROVED"),
            ("Temporal-FSM-Behaviour-Engine", "BEHAVIOUR_CLASSIFIER", "v2.1.0", "RuleFSM", "ai/behaviour/behaviour_engine.py", "APPROVED"),
            ("DamageNet-Physical-Risk", "DAMAGE_MODEL", "v1.4.0", "DeterministicMath", "ai/risk/risk_engine.py", "APPROVED"),
        ]
        for name, m_type, ver, fw, path, stat in models_data:
            mod = db.query(ModelArtifact).filter(ModelArtifact.name == name, ModelArtifact.version == ver).first()
            if not mod:
                mod = ModelArtifact(
                    name=name,
                    model_type=m_type,
                    version=ver,
                    framework=fw,
                    artifact_path=path,
                    status=stat,
                )
                db.add(mod)
                db.flush()

        dataset = db.query(Dataset).filter(Dataset.name == "Warehouse-Real-Scenarios-Golden").first()
        if not dataset:
            dataset = Dataset(
                name="Warehouse-Real-Scenarios-Golden",
                description="Golden benchmark warehouse operational dataset containing real CCTV footage",
                dataset_type="BEHAVIOUR_DETECTION",
            )
            db.add(dataset)
            db.flush()

            ver = DatasetVersion(
                dataset_id=dataset.id,
                version_tag="v1.0.0-GOLDEN",
                train_sample_count=5,
                val_sample_count=1,
                test_sample_count=1,
                manifest_checksum="a8f93e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f",
                manifest_json=json.dumps({"total_videos": 7, "split": "GOLDEN"}),
            )
            db.add(ver)
            db.flush()

        # 8. Ingest Sample Videos
        sample_dir = Path("./Sample videos").resolve()
        storage_video_dir = Path("./storage/videos").resolve()
        storage_video_dir.mkdir(parents=True, exist_ok=True)

        if sample_dir.exists():
            for sample_file in sample_dir.glob("*.mp4"):
                dest_file = storage_video_dir / sample_file.name
                if not dest_file.exists():
                    shutil.copy(str(sample_file), str(dest_file))

                rel_storage_path = f"videos/{sample_file.name}"
                existing_video = db.query(Video).filter(Video.filename == sample_file.name).first()

                if not existing_video:
                    meta = VideoLoader.extract_metadata(str(dest_file))
                    duration = meta.duration_seconds if meta.is_valid else 15.0
                    fps = meta.fps if meta.is_valid else 30.0
                    w = meta.width if meta.is_valid else 1920
                    h = meta.height if meta.is_valid else 1080
                    total_f = meta.total_frames if meta.is_valid else int(duration * fps)

                    cam_id = cameras_map["CAM-DOCK-01"].id

                    video = Video(
                        camera_id=cam_id,
                        filename=sample_file.name,
                        storage_path=rel_storage_path,
                        file_size_bytes=sample_file.stat().st_size,
                        duration_seconds=round(duration, 2),
                        fps=round(fps, 2),
                        width=w,
                        height=h,
                        codec="H264",
                        checksum_sha256="sample-checksum",
                        status="QUEUED",
                    )
                    db.add(video)
                    db.flush()

                    job = ProcessingJob(
                        video_id=video.id,
                        job_status="PENDING",
                        progress_percentage=0.0,
                        frames_processed=0,
                        total_frames=total_f,
                    )
                    db.add(job)
                    db.flush()

        db.commit()
        logger.info("GuardianEye database seeded successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}", exc_info=True)
        raise
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    seed_database()
