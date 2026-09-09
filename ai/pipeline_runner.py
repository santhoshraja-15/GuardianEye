"""
Master AI Pipeline Runner and Orchestrator
Executes the full GuardianEye intelligence pipeline from raw video frames to
perception, tracking, behaviour intelligence, deterministic risk quantification,
damage prediction, incident creation, deduplicated alerts, cryptographic evidence
packages, and real-time event broadcasting.
"""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import cv2
import numpy as np
from sqlalchemy.orm import Session

from ai.behaviour.behaviour_dna import BehaviourDNAEncoder
from ai.behaviour.behaviour_engine import BehaviourEngine
from ai.behaviour.behaviour_schemas import BehaviourType, DetectedBehaviour
from ai.context.context_enricher import ContextEnricher, ProductContext
from ai.damage.damage_predictor import DamagePredictor
from ai.evidence.evidence_generator import EvidenceGenerator
from ai.interaction.interaction_detector import InteractionDetector
from ai.perception.yolo_detector import YOLODetector, detector as default_detector
from ai.prevention.prevention_engine import PreventionEngine
from ai.preprocessing.frame_extractor import FrameExtractor, ProcessedFrame
from ai.risk.risk_engine import DeterministicRiskEngine
from ai.risk.risk_schemas import RiskEvaluationResult, RiskLevel
from ai.spatial.zone_geometry import Point, PolygonZone
from ai.temporal.state_machine import TemporalStateMachine
from ai.tracking.byte_tracker import ByteTracker
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.behaviour import BehaviourEvent
from backend.app.models.evidence import EvidencePackage, Recommendation, RootCause
from backend.app.models.incident import Alert, Incident, IncidentHistory
from backend.app.models.risk import DamagePrediction, RiskAssessment
from backend.app.models.video import ProcessingJob, Video
from backend.app.models.warehouse import Camera, Warehouse, Zone
from backend.app.schemas.incident import IncidentCreateRequest
from backend.app.services.alert_service import alert_service
from backend.app.services.behaviour_service import behaviour_service
from backend.app.services.event_bus import event_bus
from backend.app.services.evidence_service import evidence_service
from backend.app.services.incident_service import IncidentService
from backend.app.services.storage_service import storage_service
from backend.app.services.tracking_service import tracking_service


class AIPipelineOrchestrator:
    """
    End-to-End AI Video Analysis Pipeline.
    """

    def __init__(
        self,
        target_fps: Optional[int] = None,
        detector: Optional[YOLODetector] = None,
    ):
        self.target_fps = target_fps or settings.INFERENCE_FPS
        self.extractor = FrameExtractor(target_fps=self.target_fps)
        self.detector = detector or default_detector
        self.behaviour_engine = BehaviourEngine()
        self.interaction_detector = InteractionDetector(distance_threshold_px=100.0)

    def _load_spatial_zones(self, db: Session, warehouse_id: Optional[str] = None) -> Dict[str, PolygonZone]:
        """Load PolygonZones from DB or instantiate default warehouse zones."""
        query = db.query(Zone)
        if warehouse_id:
            query = query.filter(Zone.warehouse_id == warehouse_id)
        db_zones = query.all()

        zones: Dict[str, PolygonZone] = {}
        if db_zones:
            for z in db_zones:
                try:
                    coords = json.loads(z.polygon_coordinates)
                    points = [Point(c[0], c[1]) for c in coords]
                except Exception:
                    points = [Point(0.0, 0.0), Point(1000.0, 0.0), Point(1000.0, 1000.0), Point(0.0, 1000.0)]
                zones[z.code] = PolygonZone(
                    zone_id=z.id,
                    zone_code=z.code,
                    points=points,
                    zone_type=z.zone_type,
                    risk_multiplier=z.risk_weight,
                )
        else:
            # Fallback default industrial zones
            zones["LOADING_DOCK_01"] = PolygonZone(
                zone_id="zone-dock-1",
                zone_code="LOADING_DOCK_01",
                points=[Point(0.0, 0.0), Point(1920.0, 0.0), Point(1920.0, 1080.0), Point(0.0, 1080.0)],
                zone_type="LOADING_DOCK",
                risk_multiplier=1.4,
            )
            zones["STAGING_BAY_01"] = PolygonZone(
                zone_id="zone-staging-1",
                zone_code="STAGING_BAY_01",
                points=[Point(200.0, 200.0), Point(800.0, 200.0), Point(800.0, 800.0), Point(200.0, 800.0)],
                zone_type="STAGING_BAY",
                risk_multiplier=1.2,
            )

        return zones

    def _load_product_catalog(self) -> Dict[str, ProductContext]:
        """Provide standard SKU catalog with physical fragility definitions."""
        return {
            "SKU-CARTON-STD": ProductContext(
                sku="SKU-CARTON-STD",
                product_name="Standard Packaging Carton",
                category="General Goods",
                fragility_rating=3,
                unit_value_usd=120.0,
                max_safe_drop_height_px=25.0,
            ),
            "SKU-OPTICS": ProductContext(
                sku="SKU-OPTICS",
                product_name="Precision Industrial Optics",
                category="Electronics & Optics",
                fragility_rating=5,
                unit_value_usd=850.0,
                max_safe_drop_height_px=15.0,
            ),
            "SKU-HEAVY-FURNITURE": ProductContext(
                sku="SKU-HEAVY-FURNITURE",
                product_name="Heavy Cabinet / Furniture",
                category="Heavy Goods",
                fragility_rating=4,
                unit_value_usd=450.0,
                max_safe_drop_height_px=10.0,
            ),
        }

    def process_video(
        self,
        db: Session,
        job_id: str,
        progress_callback: Optional[Callable[[float, int, int], None]] = None,
    ) -> bool:
        """
        Execute full end-to-end video pipeline.
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Processing job {job_id} not found.")
            return False

        video = job.video
        if not video:
            logger.error(f"Video for job {job_id} not found.")
            return False

        # Mark job running
        job.job_status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        video.status = "PROCESSING"
        db.commit()

        # Resolve warehouse & camera associations
        warehouse_id = None
        camera_id = video.camera_id
        if camera_id:
            cam = db.query(Camera).filter(Camera.id == camera_id).first()
            if cam:
                warehouse_id = cam.warehouse_id

        if not warehouse_id:
            default_wh = db.query(Warehouse).first()
            if default_wh:
                warehouse_id = default_wh.id

        zones = self._load_spatial_zones(db, warehouse_id)
        catalog = self._load_product_catalog()
        enricher = ContextEnricher(catalog=catalog)

        tracker = ByteTracker()
        fsm = TemporalStateMachine()

        abs_video_path = storage_service.get_file_path(video.storage_path)
        if not abs_video_path.exists():
            job.job_status = "FAILED"
            job.error_message = f"Video file not found at {abs_video_path}"
            job.completed_at = datetime.now(timezone.utc)
            video.status = "FAILED"
            db.commit()
            return False

        start_time = datetime.now(timezone.utc)
        frames_count = 0
        tracks_by_frame: Dict[int, FrameTracks] = {}
        detected_incidents: List[str] = []

        try:
            for frame in self.extractor.extract_frames(str(abs_video_path)):
                frames_count += 1
                frame_idx = frame.frame_index

                # 1. Perception (YOLO / Rule-based entity detection)
                frame_dets = self.detector.detect(frame)

                # 2. Tracking (ByteTrack)
                frame_tracks = tracker.update(frame_dets)
                tracks_by_frame[frame_idx] = frame_tracks

                # 3. Interactions
                interactions = self.interaction_detector.detect_interactions(frame_tracks)

                # 4. Temporal FSM
                timelines = fsm.update(frame_tracks, interactions)

                # 5. Behaviour Intelligence
                behaviour_events = self.behaviour_engine.evaluate_frame(
                    frame_tracks, interactions, timelines, zones
                )

                # 6. Process Detected Behaviours
                for detected_b in behaviour_events.active_behaviours:
                    primary_id = detected_b.evidence.primary_entity_id
                    zone_code = "LOADING_DOCK_01"
                    zone_id = None

                    # Find matching zone from DB
                    if zone_code in zones:
                        zone_id = zones[zone_code].zone_id

                    # 7. Context Enrichment
                    ctx = enricher.enrich(
                        entity_id=primary_id,
                        sku_or_class="SKU-CARTON-STD",
                        zone_code=zone_code,
                    )

                    # 8. Deterministic Risk Calculation
                    risk_res = DeterministicRiskEngine.evaluate(detected_b, ctx)

                    # 9. Damage Prediction
                    damage_res = DamagePredictor.predict(detected_b, ctx)

                    # Persist Behaviour Event
                    b_event = behaviour_service.create_behaviour_event(
                        db=db,
                        video_id=video.id,
                        behaviour=detected_b,
                        zone_id=zone_id,
                    )

                    # Persist Risk Assessment
                    risk_assessment = RiskAssessment(
                        behaviour_event_id=b_event.id,
                        risk_score=risk_res.risk_score,
                        risk_level=risk_res.risk_level.value,
                        confidence=detected_b.confidence,
                        factors_breakdown=json.dumps(risk_res.factors),
                        explanation=detected_b.description,
                        calculated_by="DETERMINISTIC_ENGINE",
                    )
                    db.add(risk_assessment)

                    # Persist Damage Prediction
                    damage_pred = DamagePrediction(
                        behaviour_event_id=b_event.id,
                        damage_probability=damage_res.damage_probability,
                        likely_damage_type=getattr(damage_res, "predicted_damage_type", "ABRASION") or "ABRASION",
                        damage_status="POTENTIAL_DAMAGE",
                        factors_json=json.dumps([]),
                    )
                    db.add(damage_pred)
                    db.commit()

                    # 10. Incident Creation (if actionable or score >= 40.0)
                    if risk_res.is_actionable or risk_res.risk_score >= 40.0:
                        inc_req = IncidentCreateRequest(
                            behaviour_event_id=b_event.id,
                            warehouse_id=warehouse_id or "wh-default",
                            zone_id=zone_id,
                            camera_id=camera_id,
                            title=f"{detected_b.behaviour_type.value.replace('_', ' ').title()} Anomaly",
                            summary=(
                                f"Detected {detected_b.description} with risk score {risk_res.risk_score:.1f} "
                                f"({risk_res.risk_level.value}) and estimated loss ${damage_res.estimated_financial_loss_usd:.2f}."
                            ),
                            severity=risk_res.risk_level.value,
                        )
                        incident = IncidentService.create_incident(db, inc_req)
                        detected_incidents.append(incident.id)

                        # 11. Alert Generation (with deduplication)
                        alert = alert_service.create_alert_if_actionable(
                            db=db,
                            video_id=video.id,
                            behaviour_event_id=b_event.id,
                            behaviour=detected_b,
                            risk=risk_res,
                            zone_id=zone_id,
                        )

                        # Save snapshot image for evidence
                        snapshot_dir = storage_service.local_dir / "snapshots"
                        snapshot_dir.mkdir(parents=True, exist_ok=True)
                        snapshot_filename = f"{video.id}_incident_{incident.id}.jpg"
                        snapshot_path = snapshot_dir / snapshot_filename
                        cv2.imwrite(str(snapshot_path), frame.image_bgr)
                        rel_snapshot_path = f"/storage/snapshots/{snapshot_filename}"

                        # 12. SHA-256 Tamper-Proof Evidence Package Manifest
                        manifest = EvidenceGenerator.generate_manifest(
                            incident_id=incident.id,
                            video_id=video.id,
                            behaviour=detected_b,
                            tracks_by_frame=tracks_by_frame,
                            clip_path=f"/storage/{video.storage_path}",
                            snapshot_path=rel_snapshot_path,
                        )
                        evidence_service.create_evidence_package(db, incident.id, manifest)

                        # 13. Root Cause Analysis & Prevention Recommendations
                        root_cause = PreventionEngine.analyze_root_cause(detected_b, ctx)
                        rc_record = RootCause(
                            incident_id=incident.id,
                            cause_category=root_cause.cause_category.value,
                            observed_factors=json.dumps(root_cause.observed_facts),
                            inferred_factors=json.dumps(root_cause.inferred_factors),
                            confidence=root_cause.confidence,
                        )
                        db.add(rc_record)

                        recommendations = PreventionEngine.generate_recommendations(
                            detected_b, ctx, root_cause
                        )
                        for r in recommendations:
                            rec_record = Recommendation(
                                incident_id=incident.id,
                                action_title=r.action_title,
                                description=r.description,
                                prevention_type=r.prevention_type.value,
                                estimated_risk_reduction_pct=r.estimated_risk_reduction_pct,
                                status="PROPOSED",
                            )
                            db.add(rec_record)
                        db.commit()

                        # 14. Real-time WebSocket Broadcast
                        event_bus.publish(
                            event="incident_created",
                            warehouse_id=warehouse_id,
                            data={
                                "incident_id": incident.id,
                                "incident_code": incident.incident_code,
                                "title": incident.title,
                                "severity": incident.severity,
                                "risk_score": risk_res.risk_score,
                                "behaviour": detected_b.behaviour_type.value,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                        if alert:
                            event_bus.publish(
                                event="alert_created",
                                warehouse_id=warehouse_id,
                                data={
                                    "alert_id": alert.id,
                                    "alert_level": alert.alert_level,
                                    "message": alert.message,
                                    "zone_id": zone_id,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                            )

                # Persist dense trajectory track points periodically
                if frames_count % 15 == 0:
                    tracking_service.persist_frame_tracks(db, video.id, frame_tracks)

                # Periodic progress updates
                if frames_count % 10 == 0:
                    pct = min(99.0, round((frames_count / max(job.total_frames, 1)) * 100.0, 1))
                    job.frames_processed = frames_count
                    job.progress_percentage = pct
                    db.commit()

                    if progress_callback:
                        progress_callback(pct, frames_count, job.total_frames)

                    event_bus.publish(
                        event="video_progress",
                        warehouse_id=warehouse_id,
                        data={
                            "job_id": job.id,
                            "video_id": video.id,
                            "progress": pct,
                            "frames_processed": frames_count,
                            "total_frames": job.total_frames,
                        },
                    )

            # Persist remaining tracks
            for ft in tracks_by_frame.values():
                tracking_service.persist_frame_tracks(db, video.id, ft)

            # Mark job complete
            elapsed_sec = max(0.001, (datetime.now(timezone.utc) - start_time).total_seconds())
            fps_achieved = round(frames_count / elapsed_sec, 2)

            job.job_status = "COMPLETED"
            job.progress_percentage = 100.0
            job.frames_processed = frames_count
            job.processing_time_seconds = round(elapsed_sec, 2)
            job.inference_fps_achieved = fps_achieved
            job.completed_at = datetime.now(timezone.utc)
            video.status = "COMPLETED"
            db.commit()

            event_bus.publish(
                event="video_completed",
                warehouse_id=warehouse_id,
                data={
                    "job_id": job.id,
                    "video_id": video.id,
                    "total_frames": frames_count,
                    "incidents_count": len(detected_incidents),
                    "fps_achieved": fps_achieved,
                },
            )

            logger.info(
                f"Successfully processed video {video.id} ({frames_count} frames, {len(detected_incidents)} incidents) in {elapsed_sec:.2f}s ({fps_achieved} FPS)"
            )
            return True

        except Exception as e:
            elapsed_sec = (datetime.now(timezone.utc) - start_time).total_seconds()
            job.job_status = "FAILED"
            job.error_message = str(e)
            job.processing_time_seconds = round(elapsed_sec, 2)
            job.completed_at = datetime.now(timezone.utc)
            video.status = "FAILED"
            db.commit()

            logger.error(f"Pipeline failure on video {video.id}: {e}", exc_info=True)
            return False


pipeline_orchestrator = AIPipelineOrchestrator()
