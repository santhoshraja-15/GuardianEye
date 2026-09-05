# GUARDIAN EYE — ARCHITECTURE VALIDATION SPECIFICATION

**System:** GuardianEye Warehouse Intelligence Platform  
**Document:** Architecture Validation & Interface Contracts  
**Version:** 1.0.0  
**Status:** VALIDATED  

---

## 1. Five Intelligence Layers Overview

GuardianEye transforms raw unstructured video streams into actionable, auditable, explainable operational intelligence through 5 strictly separated, decoupled layers.

```
+-----------------------------------------------------------------------------------+
| LAYER 1: PERCEPTION & SPATIAL                                                     |
| Video Ingestion -> Frame Decoding -> YOLO Detection -> ByteTrack -> Zone Topology|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 2: BEHAVIOUR INTELLIGENCE                                                   |
| Interaction Engine -> Temporal State Machines -> Behaviour Rules -> Behaviour DNA |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 3: RISK & DAMAGE INTELLIGENCE                                               |
| Context Engine -> Deterministic Risk Engine -> Damage Prediction -> Alerts        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 4: PREVENTION INTELLIGENCE                                                  |
| Root Cause Attribution -> Preventive Recommendations -> Counterfactual Simulation|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 5: EVIDENCE, REPLAY & CONTINUOUS LEARNING                                   |
| Evidence Packaging -> Replay Studio -> Grounded AI Assistant -> Active Learning   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Interface Contracts (Dataflow Schema)

### 2.1 Layer 1: Perception to Tracking & Spatial

```python
# Video Frame -> Detector Output
class DetectionOutput:
    frame_id: int
    timestamp_sec: float
    class_id: int
    class_name: str  # person, carton, pallet, trolley, forklift, equipment
    confidence: float
    bbox_xyxy: list[float]  # [x1, y1, x2, y2] normalized or pixel coords

# Detector Output -> Tracker Output
class TrackedEntity:
    track_id: int
    class_name: str
    current_bbox: list[float]
    velocity_xy: tuple[float, float]  # pixels/sec or normalized units/sec
    speed: float
    direction_deg: float
    trajectory: list[dict]  # history of {frame_id, timestamp, centroid_xy, bbox}
    zone_ids: list[str]     # zones currently occupied by centroid/bbox
    state: str              # ACTIVE, LOST, REACQUIRED
```

### 2.2 Layer 2: Tracking & Spatial to Behaviour Intelligence

```python
class InteractionEvent:
    interaction_id: str
    source_track_id: int      # e.g., person track_id
    target_track_id: int      # e.g., carton track_id
    interaction_type: str     # APPROACHING, CONTACT, HOLDING, CARRYING, SEPARATED
    distance_px: float
    iou: float
    start_time: float
    end_time: float | None

class BehaviourEvent:
    event_id: str
    behaviour_code: str       # B01_DROP, B02_DRAG, B03_THROW, etc.
    behaviour_name: str
    confidence: float
    primary_track_id: int
    secondary_track_id: int | None
    zone_id: str
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    duration_sec: float
    state_sequence: list[str] # Temporal state transitions
    dna_vector: list[float]   # 32-dim normalized behavioural fingerprint
```

### 2.3 Layer 3: Behaviour to Risk & Damage Intelligence

```python
class RiskAssessment:
    assessment_id: str
    event_id: str
    risk_score: float         # 0.0 to 100.0 (Deterministic)
    risk_level: str           # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float         # 0.0 to 1.0
    factors: list[dict]       # [{"factor": "drop_height", "score": 25.0, "reason": "Height > 1.2m"}]
    explanation: str

class DamagePrediction:
    prediction_id: str
    event_id: str
    damage_probability: float # 0.0 to 1.0
    likely_damage_type: str   # PACKAGING_DEFORMATION, BREAKAGE, ABRASION, CRUSHING
    status: str               # NOT_OBSERVED, POTENTIAL_DAMAGE, CONFIRMED_BY_HUMAN
```

### 2.4 Layer 4: Incident to Prevention & Root Cause

```python
class RootCauseAnalysis:
    analysis_id: str
    incident_id: str
    primary_cause_category: str  # PROCESS, EQUIPMENT, CONGESTION, ERGONOMIC, INFRASTRUCTURE
    observed_factors: list[str]  # Directly observed in video
    inferred_factors: list[str]  # Inferred based on context and history
    confidence: float

class Recommendation:
    recommendation_id: str
    incident_id: str
    action_title: str
    description: str
    prevention_type: str         # TRAINING, EQUIPMENT_CHANGE, LAYOUT_MODIFICATION
    estimated_risk_reduction_pct: float  # e.g., 65.0% (Estimated, never guaranteed)
```

### 2.5 Layer 5: Evidence & Grounded Assistant

```python
class EvidencePackage:
    evidence_id: str
    incident_id: str
    snapshot_uri: str
    clip_uri: str
    pre_event_seconds: float
    post_event_seconds: float
    sha256_checksum: str
    metadata_json: dict
```

---

## 3. Core Behavioral Taxonomy Formulation

The 10 MVP Behaviours are mathematically formulated using spatial, temporal, and interaction rules:

1. **B01 (Product Drop):** `Interaction(Person, Carton) == HOLDING` at $t_1 \to$ `Interaction == SEPARATED` with $v_y > v_{drop\_threshold}$ at $t_2 \to$ `Impact(Carton, Floor/Pallet)` at $t_3$.
2. **B02 (Product Dragging):** `Centroid(Carton)` is inside `Floor Zone` AND $v_{horizontal} > v_{drag\_threshold}$ with `Contact(Person, Carton)` AND `Distance(Carton, Floor) \approx 0` for $t > 1.0s$.
3. **B03 (Product Throwing):** `Holding` $\to$ sudden velocity spike $v_{release} > v_{throw\_threshold}$ with parabolic trajectory $y(t) = y_0 + v_{0y}t - \frac{1}{2}gt^2$ and uncontrolled impact.
4. **B04 (Rough Handling):** Acceleration $|a| = |\frac{dv}{dt}| > a_{rough\_threshold}$ or abrupt direction change $\Delta \theta > 90^\circ$ within $\Delta t < 0.3s$ during carton contact.
5. **B05 (Improper Stacking):** Vertical stack where $Mass(Top) > Mass(Bottom)$ (via metadata) or `Aspect_Ratio(Carton)` violated (horizontal orientation of vertical-only carton).
6. **B06 (Unstable Stacking):** Stack tilt angle $\theta_{tilt} = \arctan\left(\frac{|\Delta x|}{\Delta y}\right) > 15^\circ$ or horizontal overhang ratio $\frac{w_{overhang}}{w_{base}} > 0.20$.
7. **B07 (Incorrect Placement):** Carton centroid $(x_c, y_c) \notin Polygon(StorageZone) \cup Polygon(LoadingBay)$ when `Stationary` for $t > 5.0s$.
8. **B08 (Handling Without Equipment):** Carton weight $m > 25kg$ handled by `Person` without `Trolley/Forklift` present within radius $R < 2.0m$.
9. **B09 (Incorrect Pallet Position):** Forklift fork alignment angle with pallet slot $\Delta \phi > 12^\circ$ or incomplete fork insertion depth $< 80\%$.
10. **B10 (Unsafe Loading Sequence):** Upper tier loaded before foundational tier secured in loading bay zone.

---

## 4. Responsible AI & Verification Commitments

1. **Deterministic Risk:** Core risk scoring is calculated via rule-based weighted formula and audited decision trees. LLMs are NEVER permitted to generate or override numerical risk scores.
2. **Epistemic Classification:** All outputs are strictly labelled as `OBSERVED`, `INFERRED`, `PREDICTED`, `ESTIMATED`, or `UNKNOWN`.
3. **Privacy by Design:** Focus on object interaction and process dynamics. Biometric facial recognition is prohibited by default.
4. **Human in the Loop:** Active learning and critical operational adjustments require human supervisor sign-off.
