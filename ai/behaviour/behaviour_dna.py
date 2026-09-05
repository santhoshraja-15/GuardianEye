"""
Behaviour DNA Encoder & Anomaly Similarity Engine
Encodes entity movement, temporal state transitions, and interaction kinematics into a 32-dimensional normalized feature vector.
"""
from dataclasses import dataclass, field
import json
import math
from typing import Dict, List, Optional, Tuple
import numpy as np
from ai.behaviour.behaviour_schemas import DetectedBehaviour
from ai.temporal.temporal_schemas import EntityTemporalTimeline, TemporalState
from ai.tracking.tracker_schemas import TrackedObject


@dataclass
class BehaviourDNA:
    vector_32d: List[float]
    state_signature: str
    feature_labels: List[str]
    magnitude: float


class BehaviourDNAEncoder:
    """
    Constructs a 32-dimensional normalized Behaviour DNA vector:
    [0:5]   - Velocity kinematics: (mean speed, peak speed, acceleration, horizontal bias, vertical bias)
    [5:10]  - State durations: (idle_ratio, hold_ratio, move_ratio, fall_ratio, impact_ratio)
    [10:15] - Interaction kinetics: (contact_ratio, min_distance, max_iou, multi_entity_flag, interaction_count)
    [15:20] - Spatial context: (zone_risk_weight, edge_proximity, floor_contact, elevation_change, total_displacement)
    [20:25] - Transition dynamics: (num_transitions, oscillation_score, jerk_metric, sudden_stop_flag, lost_frames_ratio)
    [25:32] - Anomaly fingerprints: (drop_metric, drag_metric, throw_metric, step_metric, rough_metric, tilt_angle, reserved)
    """

    FEATURE_NAMES = [
        "mean_speed", "peak_speed", "acceleration", "horizontal_bias", "vertical_bias",
        "idle_ratio", "hold_ratio", "move_ratio", "fall_ratio", "impact_ratio",
        "contact_ratio", "min_distance", "max_iou", "multi_entity_flag", "interaction_count",
        "zone_risk_weight", "edge_proximity", "floor_contact", "elevation_change", "total_displacement",
        "num_transitions", "oscillation_score", "jerk_metric", "sudden_stop_flag", "lost_frames_ratio",
        "drop_metric", "drag_metric", "throw_metric", "step_metric", "rough_metric", "tilt_angle", "reserved"
    ]

    @classmethod
    def encode(
        cls,
        timeline: EntityTemporalTimeline,
        track_history: List[TrackedObject],
        behaviour: Optional[DetectedBehaviour] = None,
        zone_risk_multiplier: float = 1.0,
    ) -> BehaviourDNA:
        vec = [0.0] * 32

        if not track_history:
            return BehaviourDNA(vector_32d=vec, state_signature="EMPTY", feature_labels=cls.FEATURE_NAMES, magnitude=0.0)

        speeds = [t.speed_px_per_sec for t in track_history]
        vx_list = [abs(t.velocity_xy[0]) for t in track_history]
        vy_list = [abs(t.velocity_xy[1]) for t in track_history]

        mean_spd = float(np.mean(speeds)) if speeds else 0.0
        peak_spd = float(np.max(speeds)) if speeds else 0.0
        accel = (peak_spd - mean_spd) / max(0.1, float(len(track_history)) * 0.033)
        horiz_bias = float(np.mean(vx_list)) / max(0.01, mean_spd + 0.01)
        vert_bias = float(np.mean(vy_list)) / max(0.01, mean_spd + 0.01)

        # 0:5 Velocity kinematics
        vec[0] = min(1.0, mean_spd / 100.0)
        vec[1] = min(1.0, peak_spd / 200.0)
        vec[2] = min(1.0, accel / 500.0)
        vec[3] = min(1.0, horiz_bias)
        vec[4] = min(1.0, vert_bias)

        # 5:10 State durations
        total_transitions = len(timeline.state_history)
        seq_str = "->".join(timeline.state_sequence)
        states = timeline.state_sequence
        total_states = max(1, len(states))
        vec[5] = states.count(TemporalState.IDLE.value) / total_states
        vec[6] = states.count(TemporalState.HOLDING.value) / total_states
        vec[7] = states.count(TemporalState.MOVING.value) / total_states
        vec[8] = states.count(TemporalState.FALLING.value) / total_states
        vec[9] = states.count(TemporalState.IMPACT.value) / total_states

        # 15:20 Spatial context
        vec[15] = min(1.0, zone_risk_multiplier / 3.0)
        first_pos = track_history[0].centroid_xy
        last_pos = track_history[-1].centroid_xy
        disp = math.hypot(last_pos[0] - first_pos[0], last_pos[1] - first_pos[1])
        vec[18] = min(1.0, abs(last_pos[1] - first_pos[1]) / 500.0)
        vec[19] = min(1.0, disp / 800.0)

        # 20:25 Transition dynamics
        vec[20] = min(1.0, total_transitions / 10.0)
        vec[23] = 1.0 if (peak_spd > 20.0 and speeds[-1] < 2.0) else 0.0

        # 25:32 Anomaly fingerprints
        if behaviour:
            b_code = behaviour.behaviour_type.value
            vec[25] = 1.0 if "DROP" in b_code else 0.0
            vec[26] = 1.0 if "DRAG" in b_code else 0.0
            vec[27] = 1.0 if "THROW" in b_code else 0.0
            vec[28] = 1.0 if "STEP" in b_code else 0.0
            vec[29] = 1.0 if "ROUGH" in b_code else 0.0

        # Normalize 32d vector to unit length
        mag = math.sqrt(sum(v * v for v in vec))
        normalized_vec = [round(v / mag, 4) if mag > 0 else 0.0 for v in vec]

        return BehaviourDNA(
            vector_32d=normalized_vec,
            state_signature=seq_str or "IDLE",
            feature_labels=cls.FEATURE_NAMES,
            magnitude=round(mag, 4),
        )


class DNASimilarityEngine:
    """Calculates cosine similarity and distance between Behaviour DNA vectors."""

    @staticmethod
    def cosine_similarity(dna_a: List[float], dna_b: List[float]) -> float:
        if len(dna_a) != 32 or len(dna_b) != 32:
            return 0.0
        dot = sum(a * b for a, b in zip(dna_a, dna_b))
        mag_a = math.sqrt(sum(a * a for a in dna_a))
        mag_b = math.sqrt(sum(b * b for b in dna_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return round(max(-1.0, min(1.0, dot / (mag_a * mag_b))), 4)

    @staticmethod
    def euclidean_distance(dna_a: List[float], dna_b: List[float]) -> float:
        if len(dna_a) != 32 or len(dna_b) != 32:
            return 999.0
        return round(math.sqrt(sum((a - b) ** 2 for a, b in zip(dna_a, dna_b))), 4)
