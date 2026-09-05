"""
Level 15 Behaviour DNA and Similarity Engine Tests
"""
from ai.behaviour.behaviour_dna import BehaviourDNAEncoder, DNASimilarityEngine
from ai.behaviour.behaviour_schemas import (
    BehaviourEvidence,
    BehaviourSeverity,
    BehaviourType,
    DetectedBehaviour,
)
from ai.temporal.temporal_schemas import EntityTemporalTimeline, StateTransition, TemporalState
from ai.tracking.tracker_schemas import TrackedObject, TrackState


def test_behaviour_dna_encoding():
    """Verify 32-dimensional Behaviour DNA vector generation and unit length"""
    timeline = EntityTemporalTimeline(
        track_id=1,
        class_name="carton",
        current_state=TemporalState.IMPACT,
        state_start_frame=5,
        state_start_time_seconds=0.15,
        current_state_duration_seconds=0.05,
        state_history=[
            StateTransition(TemporalState.HOLDING, TemporalState.FALLING, 3, 0.1, "Release", 0.9),
            StateTransition(TemporalState.FALLING, TemporalState.IMPACT, 5, 0.15, "Hit floor", 0.95),
        ],
        state_sequence=[TemporalState.HOLDING.value, TemporalState.FALLING.value, TemporalState.IMPACT.value],
    )

    track_history = [
        TrackedObject(
            track_id=1,
            class_name="carton",
            class_id=1,
            confidence=0.95,
            state=TrackState.CONFIRMED,
            bbox_xyxy=[100.0, 100.0 + i * 20.0, 200.0, 200.0 + i * 20.0],
            centroid_xy=(150.0, 150.0 + i * 20.0),
            width_px=100.0,
            height_px=100.0,
            area_px=10000.0,
            velocity_xy=(0.0, 20.0),
            speed_px_per_sec=20.0,
            age_frames=i + 1,
            hits=i + 1,
            time_since_update=0,
        )
        for i in range(5)
    ]

    behaviour = DetectedBehaviour(
        behaviour_type=BehaviourType.B01_DROP,
        severity=BehaviourSeverity.HIGH,
        start_frame=3,
        end_frame=5,
        start_time_seconds=0.1,
        end_time_seconds=0.15,
        duration_seconds=0.05,
        confidence=0.95,
        description="Drop detected",
        evidence=BehaviourEvidence(
            trigger_rule="RULE_DROP",
            primary_entity_id=1,
            primary_class="carton",
        ),
    )

    dna = BehaviourDNAEncoder.encode(timeline, track_history, behaviour, zone_risk_multiplier=1.2)
    assert len(dna.vector_32d) == 32
    assert dna.state_signature == "HOLDING->FALLING->IMPACT"
    # Unit length check (sum of squares approx 1.0)
    sq_sum = sum(x * x for x in dna.vector_32d)
    assert abs(sq_sum - 1.0) < 0.01


def test_dna_similarity_engine():
    """Verify Cosine Similarity and Euclidean distance between matching and distinct vectors"""
    vec_a = [0.0] * 32
    vec_a[0] = 0.5
    vec_a[25] = 0.866  # Drop signature

    vec_b = [0.0] * 32
    vec_b[0] = 0.48
    vec_b[25] = 0.877  # Similar drop

    vec_c = [0.0] * 32
    vec_c[1] = 0.9
    vec_c[27] = 0.435  # Throw signature

    sim_ab = DNASimilarityEngine.cosine_similarity(vec_a, vec_b)
    sim_ac = DNASimilarityEngine.cosine_similarity(vec_a, vec_c)
    dist_ab = DNASimilarityEngine.euclidean_distance(vec_a, vec_b)

    assert sim_ab > 0.98  # Highly similar
    assert sim_ac < 0.5   # Distinct behaviour
    assert dist_ab < 0.1
