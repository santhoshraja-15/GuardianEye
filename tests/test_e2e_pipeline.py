"""
Complete End-to-End Integration & Golden Control Pipeline Benchmark Test
Tests the full GuardianEye intelligence pipeline from perception to prevention.
"""
import numpy as np
import pytest
from ai.behaviour.behaviour_dna import BehaviourDNAEncoder
from ai.behaviour.behaviour_engine import BehaviourEngine
from ai.behaviour.behaviour_schemas import BehaviourType
from ai.context.context_enricher import ContextEnricher, ProductContext
from ai.damage.damage_predictor import DamagePredictor
from ai.evidence.evidence_generator import EvidenceGenerator
from ai.interaction.interaction_detector import InteractionDetector
from ai.perception.detector_schemas import Detection, FrameDetections
from ai.prevention.prevention_engine import PreventionEngine
from ai.risk.risk_engine import DeterministicRiskEngine
from ai.risk.risk_schemas import RiskLevel
from ai.spatial.zone_geometry import Point, PolygonZone
from ai.temporal.state_machine import TemporalStateMachine
from ai.temporal.temporal_schemas import TemporalState
from ai.tracking.byte_tracker import ByteTracker
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject, TrackState
from backend.app.core.audit_logger import AuditLogger
from backend.app.services.alert_service import AlertService


def test_complete_e2e_guardianeye_pipeline():
    """
    Execute full end-to-end simulation of a real warehouse incident:
    High-value fragile item dropped in a high-risk loading dock.
    """
    # 1. Perception & Detections (Frame 1: Person holding carton)
    det_person = Detection(
        class_id=0,
        class_name="person",
        confidence=0.96,
        bbox_xyxy=[100.0, 50.0, 180.0, 250.0],
        bbox_normalized=[0.1, 0.05, 0.18, 0.25],
        centroid_xy=(140.0, 150.0),
        width_px=80.0,
        height_px=200.0,
        area_px=16000.0,
    )
    det_carton = Detection(
        class_id=1,
        class_name="carton",
        confidence=0.94,
        bbox_xyxy=[120.0, 150.0, 200.0, 230.0],
        bbox_normalized=[0.12, 0.15, 0.20, 0.23],
        centroid_xy=(160.0, 190.0),
        width_px=80.0,
        height_px=80.0,
        area_px=6400.0,
    )

    frame_dets = FrameDetections(
        frame_index=1,
        source_frame_number=1,
        timestamp_seconds=0.033,
        image_width=1000,
        image_height=1000,
        detections=[det_person, det_carton],
        inference_latency_ms=12.5,
    )
    assert len(frame_dets.detections) == 2

    # 2. Tracking (ByteTrack multi-frame updates)
    tracker = ByteTracker()
    frame_tracks_1 = tracker.update(frame_dets)
    assert len(frame_tracks_1.active_tracks) == 2

    # 3. Spatial Zones
    dock_zone = PolygonZone(
        zone_id="zone-dock-1",
        zone_code="LOADING_DOCK_01",
        points=[Point(0.0, 0.0), Point(500.0, 0.0), Point(500.0, 500.0), Point(0.0, 500.0)],
        zone_type="LOADING_DOCK",
        risk_multiplier=1.4,
    )

    # 4. Interaction Engine
    interaction_detector = InteractionDetector(distance_threshold_px=80.0)
    interactions_1 = interaction_detector.detect_interactions(frame_tracks_1)
    assert len(interactions_1.interactions) >= 1

    # 5. Temporal State Machine
    fsm = TemporalStateMachine()
    timelines = fsm.update(frame_tracks_1, interactions_1)
    # Carton entity is recognized and tracked
    carton_track = [t for t in frame_tracks_1.active_tracks if t.class_name == "carton"][0]
    carton_id = carton_track.track_id
    assert carton_id in timelines

    # Simulate Drop sequence (Frame 2: falling, Frame 3: impact)
    carton_falling = TrackedObject(
        track_id=carton_id,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[120.0, 250.0, 200.0, 330.0],
        centroid_xy=(160.0, 290.0),
        width_px=80.0,
        height_px=80.0,
        area_px=6400.0,
        velocity_xy=(0.0, 35.0),
        speed_px_per_sec=35.0,
        age_frames=2,
        hits=2,
        time_since_update=0,
    )
    frame_tracks_2 = FrameTracks(
        frame_index=2, timestamp_seconds=0.066, active_tracks=[carton_falling], lost_tracks=[], removed_tracks=[]
    )
    interactions_2 = interaction_detector.detect_interactions(frame_tracks_2)
    fsm.update(frame_tracks_2, interactions_2)

    carton_impact = TrackedObject(
        track_id=carton_id,
        class_name="carton",
        class_id=1,
        confidence=0.95,
        state=TrackState.CONFIRMED,
        bbox_xyxy=[120.0, 450.0, 200.0, 530.0],
        centroid_xy=(160.0, 490.0),
        width_px=80.0,
        height_px=80.0,
        area_px=6400.0,
        velocity_xy=(0.0, 0.0),
        speed_px_per_sec=0.0,
        age_frames=3,
        hits=3,
        time_since_update=0,
    )
    frame_tracks_3 = FrameTracks(
        frame_index=3, timestamp_seconds=0.099, active_tracks=[carton_impact], lost_tracks=[], removed_tracks=[]
    )
    interactions_3 = interaction_detector.detect_interactions(frame_tracks_3)
    timelines = fsm.update(frame_tracks_3, interactions_3)

    # 6. Behaviour Intelligence Engine
    behaviour_engine = BehaviourEngine()
    behaviours = behaviour_engine.evaluate_frame(
        frame_tracks_3, interactions_3, timelines, zones={"LOADING_DOCK_01": dock_zone}
    )
    assert len(behaviours.active_behaviours) == 1
    detected_b = behaviours.active_behaviours[0]
    assert detected_b.behaviour_type == BehaviourType.B01_DROP

    # 7. Behaviour DNA (32D Vector)
    dna = BehaviourDNAEncoder.encode(
        timeline=timelines[carton_id],
        track_history=[carton_track, carton_falling, carton_impact],
        behaviour=detected_b,
        zone_risk_multiplier=1.4,
    )
    assert len(dna.vector_32d) == 32

    # 8. Context Enrichment (Fragile Glass / Electronics)
    catalog = {
        "SKU-OPTICS": ProductContext(
            sku="SKU-OPTICS",
            product_name="Precision Industrial Sensor",
            category="Optics & Sensors",
            fragility_rating=5,
            unit_value_usd=850.0,
            max_safe_drop_height_px=15.0,
        )
    }
    enricher = ContextEnricher(catalog=catalog)
    ctx = enricher.enrich(entity_id=carton_id, sku_or_class="SKU-OPTICS", zone_code="LOADING_DOCK_01")
    assert ctx.product.fragility_rating == 5
    assert ctx.zone_risk_multiplier == 1.4

    # 9. Deterministic Mathematical Risk Engine
    risk_result = DeterministicRiskEngine.evaluate(detected_b, ctx)
    assert risk_result.risk_score >= 80.0
    assert risk_result.risk_level == RiskLevel.CRITICAL
    assert risk_result.is_actionable is True

    # 10. Damage Prediction Engine
    damage_result = DamagePredictor.predict(detected_b, ctx)
    assert damage_result.damage_probability >= 0.8
    assert damage_result.estimated_financial_loss_usd > 500.0

    # 11. Alert Deduplication
    alert_service = AlertService()
    dedup_key = alert_service.generate_dedup_key("vid-101", carton_id, detected_b.behaviour_type.value)
    assert alert_service.should_suppress_alert(dedup_key, 0.099) is False
    assert alert_service.should_suppress_alert(dedup_key, 1.000) is True  # Deduplicated within 5s window

    # 12. Evidence Package Generator (SHA-256 Checksums)
    manifest = EvidenceGenerator.generate_manifest(
        incident_id="INC-GOLDEN-01",
        video_id="vid-101",
        behaviour=detected_b,
        tracks_by_frame={1: frame_tracks_1, 2: frame_tracks_2, 3: frame_tracks_3},
    )
    assert len(manifest.clip_sha256) == 64
    assert len(manifest.keyframes) >= 1

    # 13. Root Cause Analysis & Prevention
    rca = PreventionEngine.analyze_root_cause(detected_b, ctx)
    recs = PreventionEngine.generate_recommendations(detected_b, ctx, rca)
    cf = PreventionEngine.simulate_counterfactual(detected_b, risk_result, ctx)
    assert len(recs) >= 1
    assert cf.risk_delta > 50.0  # Significant simulated safety risk reduction

    # 14. Compliance Audit Logger
    audit_record = AuditLogger.log_action(
        user_id="USER-TEST",
        action="INCIDENT_RESOLVED",
        resource_type="INCIDENT",
        resource_id="INC-GOLDEN-01",
        details={"risk_score": risk_result.risk_score, "resolution": "Operator retrained"},
    )
    assert "sha256_hash" in audit_record
