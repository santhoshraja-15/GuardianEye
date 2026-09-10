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
from ai.context.context_enricher import ContextEnricher
from ai.damage.damage_predictor import DamagePredictor
from ai.evidence.evidence_generator import EvidenceGenerator
from ai.interaction.interaction_detector import InteractionDetector
from ai.perception.yolo_detector import YOLODetector, detector as default_detector
from ai.prevention.prevention_engine import PreventionEngine
from ai.preprocessing.frame_extractor import FrameExtractor, ProcessedFrame
from ai.risk.risk_engine import DeterministicRiskEngine
from ai.risk.risk_schemas import RiskEvaluationResult, RiskLevel
from ai.spatial.coordinate_transform import normalize_zone_polygons
from ai.spatial.event_engine import ProximityEngine, SpatialEventCandidate, ZoneTransitionEngine
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
from backend.app.services.calibration_service import calibration_service
from backend.app.services.event_bus import event_bus
from backend.app.services.evidence_service import evidence_service
from backend.app.services.incident_service import IncidentService
from backend.app.services.spatial_event_service import spatial_event_service
from backend.app.services.storage_service import storage_service
from backend.app.services.tracking_service import SpatialContext, tracking_service


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
        """Load PolygonZones from DB (or instantiate default warehouse
        zones when none are configured), then normalize every polygon
        into a shared 0-1 plane.

        Zone.polygon_coordinates are authored in an arbitrary,
        undeclared plane (this project's seed data uses ~0-1000 units
        with no physical meaning) that is NOT the same space as a
        track's video-pixel position. Comparing them directly — which
        is what every zone-matching call site did before this method
        normalized its output — is the exact "video coordinates and
        world coordinates aren't explicitly separated" bug the spatial
        architecture audit flagged; two of the eight implemented
        behaviour rules (drag/wet-floor, zone-mismatch placement) and
        the new zone-transition/proximity event engines all rely on
        this method's output being safe to compare against a track's
        own normalize()'d position (see ai.spatial.coordinate_transform
        and behaviour_engine.evaluate_frame's docstring)."""
        query = db.query(Zone)
        if warehouse_id:
            query = query.filter(Zone.warehouse_id == warehouse_id)
        db_zones = query.all()

        raw_polygons: Dict[str, List[tuple]] = {}
        zone_meta: Dict[str, Zone] = {}
        if db_zones:
            for z in db_zones:
                try:
                    coords = json.loads(z.polygon_coordinates)
                    raw_polygons[z.code] = [(float(c[0]), float(c[1])) for c in coords]
                except Exception:
                    raw_polygons[z.code] = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]
                zone_meta[z.code] = z
        else:
            # Fallback default industrial zones — used only when the
            # warehouse has no zones configured at all.
            raw_polygons["LOADING_DOCK_01"] = [(0.0, 0.0), (1920.0, 0.0), (1920.0, 1080.0), (0.0, 1080.0)]
            raw_polygons["STAGING_BAY_01"] = [(200.0, 200.0), (800.0, 200.0), (800.0, 800.0), (200.0, 800.0)]

        normalized_polygons = normalize_zone_polygons(raw_polygons)

        zones: Dict[str, PolygonZone] = {}
        for code, normalized_polygon in normalized_polygons.items():
            z = zone_meta.get(code)
            if z is not None:
                zones[code] = PolygonZone(
                    zone_id=z.id,
                    zone_code=code,
                    points=[Point(x, y) for x, y in normalized_polygon],
                    zone_type=z.zone_type,
                    risk_multiplier=z.risk_weight,
                    is_restricted=z.is_restricted,
                )
            else:
                zones[code] = PolygonZone(
                    zone_id=f"zone-{code.lower()}",
                    zone_code=code,
                    points=[Point(x, y) for x, y in normalized_polygon],
                    zone_type="LOADING_DOCK" if "DOCK" in code else "STAGING_BAY",
                    risk_multiplier=1.4 if "DOCK" in code else 1.2,
                )

        return zones

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
        # No SKU master-data integration exists yet, so ContextEnricher falls
        # back to its built-in per-object-class profiles (see
        # ai/context/product_catalog.py) — passing no catalog override here
        # is deliberate, not an oversight.
        enricher = ContextEnricher()

        tracker = ByteTracker()
        fsm = TemporalStateMachine()
        zone_transition_engine = ZoneTransitionEngine()
        proximity_engine = ProximityEngine()

        # Resolved once per video, not re-fetched every frame: the
        # warehouse's declared physical footprint (for the honest
        # UNCALIBRATED_ESTIMATE world-position fallback) and this
        # camera's real homography if one has been calibrated (see
        # backend/app/services/calibration_service.py — this is the
        # spec's "MOST IMPORTANT architectural requirement": a real
        # video-pixel -> warehouse-meters transform, not a fabricated
        # one).
        warehouse_row = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first() if warehouse_id else None
        homography_matrix, reprojection_error_px = calibration_service.get_active_homography(db, camera_id)
        spatial_context = SpatialContext(
            video_width=float(video.width or 1920),
            video_height=float(video.height or 1080),
            warehouse_width_m=warehouse_row.width_meters if warehouse_row else None,
            warehouse_length_m=warehouse_row.length_meters if warehouse_row else None,
            zones=zones,
            homography_matrix=homography_matrix,
            reprojection_error_px=reprojection_error_px,
        )

        def _publish_spatial_event(candidate: SpatialEventCandidate, frame_idx: int, timestamp: float) -> None:
            event_row = spatial_event_service.create_event(
                db=db,
                video_id=video.id,
                event_type=candidate.event_type,
                severity=candidate.severity,
                frame_number=frame_idx,
                timestamp_seconds=timestamp,
                description=candidate.description,
                camera_id=camera_id,
                warehouse_id=warehouse_id,
                zone_id=candidate.zone_id,
                from_zone_id=candidate.from_zone_id,
                to_zone_id=candidate.to_zone_id,
                involved_track_ids=candidate.involved_track_ids,
                confidence=candidate.confidence,
            )
            event_bus.publish(
                event="SPATIAL_EVENT_CREATED",
                warehouse_id=warehouse_id,
                data={
                    "event_id": event_row.id,
                    "video_id": video.id,
                    "event_type": candidate.event_type,
                    "severity": candidate.severity,
                    "description": candidate.description,
                    "timestamp_seconds": timestamp,
                },
            )

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
        # Buffered separately from tracks_by_frame (which stays complete
        # for evidence generation): cleared after every periodic flush so
        # the end-of-loop "persist whatever's left" pass never re-writes
        # a frame that was already flushed to the DB — previously both
        # loops drew from the same dict, so any frame divisible by 15 was
        # persisted twice.
        pending_track_persistence: Dict[int, FrameTracks] = {}
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
                pending_track_persistence[frame_idx] = frame_tracks

                # 3. Interactions
                interactions = self.interaction_detector.detect_interactions(frame_tracks)

                # 4. Temporal FSM
                timelines = fsm.update(frame_tracks, interactions)

                # 5. Behaviour Intelligence
                behaviour_events = self.behaviour_engine.evaluate_frame(
                    frame_tracks, interactions, timelines, zones,
                    frame_width=spatial_context.video_width, frame_height=spatial_context.video_height,
                )

                # 5b. Generalized spatial events — zone transitions and
                # proximity warnings (additive stream, see
                # ai/spatial/event_engine.py and models/spatial_event.py;
                # does not touch BehaviourEvent/Incident at all).
                for track in frame_tracks.active_tracks:
                    transition = zone_transition_engine.evaluate(
                        track, zones, spatial_context.video_width, spatial_context.video_height
                    )
                    if transition:
                        _publish_spatial_event(transition, frame_idx, frame_tracks.timestamp_seconds)

                for proximity_candidate in proximity_engine.evaluate(
                    frame_tracks.active_tracks, spatial_context.video_width, spatial_context.video_height
                ):
                    _publish_spatial_event(proximity_candidate, frame_idx, frame_tracks.timestamp_seconds)

                # 6. Process Detected Behaviours
                for detected_b in behaviour_events.active_behaviours:
                    primary_id = detected_b.evidence.primary_entity_id

                    # Use the zone the behaviour engine actually resolved via
                    # point-in-polygon spatial matching (evidence.zone_code) —
                    # only a subset of rules (drag/wet-floor, zone-mismatch
                    # placement) currently resolve one; rules that don't yet
                    # do spatial matching fall back to the warehouse's first
                    # configured zone rather than silently attributing every
                    # incident to the same hardcoded dock, which corrupted
                    # zone heatmaps/hotspot analytics downstream.
                    zone_code = detected_b.evidence.zone_code
                    if not zone_code or zone_code not in zones:
                        zone_code = next(iter(zones), "LOADING_DOCK_01")
                    zone_id = zones[zone_code].zone_id if zone_code in zones else None

                    # 7. Context Enrichment — resolved from the actually
                    # detected object class (evidence.primary_class), not a
                    # single hardcoded SKU regardless of what was seen. No
                    # real SKU/barcode recognition exists in this pipeline,
                    # so this always resolves to a CLASS_DEFAULT profile
                    # today (see ai/context/product_catalog.py); the SKU
                    # catalog path stays wired up for whenever real product
                    # master data is integrated.
                    ctx = enricher.enrich(
                        entity_id=primary_id,
                        sku_or_class=detected_b.evidence.primary_class,
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
                    # Previously: likely_damage_type looked up a field name
                    # (`predicted_damage_type`) that doesn't exist on
                    # DamagePredictionResult, so getattr's fallback fired on
                    # every single event, silently persisting "ABRASION"
                    # regardless of what DamagePredictor actually classified.
                    # damage_status and the $-loss estimate were similarly
                    # discarded in favor of a constant / nothing at all.
                    # All three now persist DamagePredictor's real output.
                    damage_pred = DamagePrediction(
                        behaviour_event_id=b_event.id,
                        damage_probability=damage_res.damage_probability,
                        likely_damage_type=damage_res.likely_damage_type.value,
                        damage_status=damage_res.damage_status.value,
                        estimated_financial_loss_usd=damage_res.estimated_financial_loss_usd,
                        factors_json=json.dumps(damage_res.damage_factors),
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
                        # Event names are uppercase to match the contract
                        # the frontend RealtimeSocketManager actually
                        # listens for (frontend/src/services/realtime.ts)
                        # — this used to publish lowercase names that no
                        # production event name has ever matched, so the
                        # websocket carried traffic that reached zero
                        # frontend handlers (confirmed: the only place
                        # the lowercase form is asserted is this
                        # project's own test suite, not the frontend).
                        event_bus.publish(
                            event="INCIDENT_CREATED",
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
                                event="ALERT_CREATED",
                                warehouse_id=warehouse_id,
                                data={
                                    "alert_id": alert.id,
                                    "alert_level": alert.alert_level,
                                    "message": alert.message,
                                    "zone_id": zone_id,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                            )

                # Persist dense trajectory track points periodically —
                # every buffered frame since the last flush, not just the
                # single most-recent one (previously only 1-in-15 frames
                # was ever actually persisted here; the rest silently
                # waited for the end-of-loop pass below, which is exactly
                # why that pass existed and exactly why it re-persisted
                # frames this block had already written).
                if frames_count % 15 == 0:
                    for ft in pending_track_persistence.values():
                        tracking_service.persist_frame_tracks(db, video.id, ft, spatial_context)
                    pending_track_persistence.clear()

                # Periodic progress updates
                if frames_count % 10 == 0:
                    pct = min(99.0, round((frames_count / max(job.total_frames, 1)) * 100.0, 1))
                    job.frames_processed = frames_count
                    job.progress_percentage = pct
                    db.commit()

                    if progress_callback:
                        progress_callback(pct, frames_count, job.total_frames)

                    event_bus.publish(
                        event="VIDEO_PROGRESS",
                        warehouse_id=warehouse_id,
                        data={
                            "job_id": job.id,
                            "video_id": video.id,
                            "progress": pct,
                            "frames_processed": frames_count,
                            "total_frames": job.total_frames,
                        },
                    )

            # Persist whatever's left since the last periodic flush
            # (not every frame ever seen — tracks_by_frame stays intact
            # above for evidence generation, pending_track_persistence
            # is the separate, drained buffer; see its declaration).
            for ft in pending_track_persistence.values():
                tracking_service.persist_frame_tracks(db, video.id, ft, spatial_context)
            pending_track_persistence.clear()

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
                event="VIDEO_COMPLETED",
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
