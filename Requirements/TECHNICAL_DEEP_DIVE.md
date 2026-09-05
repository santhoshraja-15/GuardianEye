# Technical Deep Dive
## W-SAFE — AI/CV Pipeline Internals

This document goes one level deeper than `LAYER_ARCHITECTURE.md` into how each
AI/CV component is actually implemented.

---

## 1. Video Ingestion & Preprocessing

**Sources supported:** `FileSource (MP4/AVI/MOV)`, `RTSPSource`, `WebcamSource`,
`VMSSource` — all behind a common `VideoSource` interface so the pipeline is
never tightly coupled to one camera provider.

**Pipeline:**
```
Input → Decode → Validate → Resize → Frame Sampling → Timestamp Synchronization
→ Inference → Tracking → Behaviour Analysis
```

**Required implementation details:**
- FPS control (decouple source FPS from inference FPS — e.g. sample every 3rd
  frame of a 30fps source to get ~10fps inference)
- Frame buffering, resolution normalization
- Corrupt-frame handling (validate before inference; reject/skip damaged
  segments)
- Video codec handling, CPU fallback + GPU acceleration
- Processing progress / job status surfaced to the API

## 2. Object Detection

**Model:** YOLO-family detector (e.g. YOLOv8/YOLOv11), fine-tuned on the
warehouse object taxonomy.

**Classes (MVP):**
```
Person (operator/supervisor/pedestrian)
Material (carton/product/package/pallet)
Equipment (trolley/pallet truck/forklift/other handling equipment)
Environment (loading bay/vehicle/floor/storage area/restricted zone)
```

**Per-object output contract:**
```json
{"class": "carton", "confidence": 0.94, "bbox": [x1,y1,x2,y2],
 "timestamp": "...", "camera_id": "...", "track_id": "..."}
```

**Evaluation:** mAP, precision, recall, false positives/negatives on a held-out
validation set — do not proceed to behaviour work until detection is reasonably
reliable.

## 3. Multi-Object Tracking

**Model:** ByteTrack maintains persistent identities across frames.

```
Frame 102 → Box #17
Frame 103 → Box #17
...
Frame 151 → Box #17
```

**Per-track state:** position, velocity, acceleration, direction, trajectory,
time-in-scene, interaction history.

**Track recovery state machine:**
```
ACTIVE → LOST → REACQUIRED
```
The system must not create a new incident merely because tracking temporarily
failed (e.g. brief occlusion).

## 4. Spatial Intelligence (Scene Understanding)

Warehouse areas are represented as **polygons**:
```
Warehouse
 ├── Loading Bay A / B
 ├── Staging Zone
 ├── Storage Zone
 ├── Pedestrian Lane
 ├── Forklift Lane
 └── Restricted Zone
```
Virtual boundaries supported: tripwires, restricted areas, loading areas, safe
staging areas, equipment-only areas, pedestrian zones. The **same action**
(e.g. a drop) can carry a different risk level depending on which zone it
occurs in.

## 5. Human-Object Interaction Engine

Relationship types detected via geometric reasoning (bbox overlap/proximity +
joint motion):
```
person near product · person holding product · person moving product
product placed on pallet · product placed on floor
product moving with trolley · product approaching vehicle
product colliding with another object · forklift approaching pedestrian
product supported by pallet · product outside zone
```

Represented as an **interaction graph**:
```
             PERSON
             /    \
         holding   near
           /        \
       PRODUCT ---- PALLET
          |
        placed_on
          |
        PALLET
          |
       located_in
          |
      LOADING BAY
```
This enables reasoning beyond independent per-object detections (e.g. "this
carton is on this pallet, in this bay, currently held by this person").

## 6. Behaviour Taxonomy & Detection Logic

Full B01–B20 list is in `PRD.md` §7. Representative detection logic:

**B01 — Drop:** extract object height, vertical velocity, vertical acceleration,
person proximity, impact movement, post-impact state.
```
Picked up → Object moves → Rapid downward movement → Impact → Stationary → DROP=TRUE
```

**B02/B03 — Drag / Throw:**
- Drag: product stays near floor + horizontal movement + person movement + no
  lifting event observed.
- Throw: product near person → sudden high velocity → leaves person's
  interaction zone → free movement → impact/landing.

**B05/B06 — Incorrect / Unstable Stacking:** maintain relative size, relative
position, weight category, support area, and orientation across stacked
products; classify as `Stable / Improper / Unstable`.

**Modular detector interface** (each behaviour is a pluggable unit so improving
one never risks breaking another):
```
BehaviourDetector
    ├── DropDetector
    ├── DragDetector
    ├── ThrowDetector
    ├── ImpactDetector
    ├── StackingDetector
    ├── PlacementDetector
    ├── EquipmentDetector
    ├── PalletDetector
    └── LoadingSequenceDetector
```

## 7. Temporal Behaviour Intelligence

Instead of `Frame → Classification`, W-SAFE reasons over sequences:
```
Frames → Tracks → Motion Features → Interactions → Temporal State
→ Behaviour Sequence → Event
```

**v1 implementation — deterministic state machine** (interpretable, easy to
validate):
```
IDLE → APPROACHING → CONTACT → HOLDING → MOVING → RELEASED → FALLING
→ IMPACT → STATIONARY
```
Every transition is timestamped.

**v2 extension — Temporal Transformer** (after the rule engine works and enough
labelled sequences exist). Input per timestep:
```
[x, y, width, height, velocity, acceleration, direction, interaction, zone,
 object_type]
```
Output: `Behaviour, Probability, Temporal confidence`. The deterministic engine
remains available in parallel for explainability/fallback.

## 8. Behaviour DNA

Every incident receives an ordered temporal fingerprint, e.g.:
```
APPROACH → HOLD → MOVE → ACCELERATE → RELEASE → FALL → IMPACT → STOP
```
Stored as an ordered event sequence — enables incident comparison,
similar-event search, behaviour clustering, root-cause analysis, and predictive
modelling.

## 9. Product Intelligence

Risk cannot depend on behaviour alone. Each product category carries:
```
product_type, fragility, weight, dimensions, handling_requirement,
maximum_drop_height, stacking_limit, orientation_requirement,
equipment_requirement
```
A 50cm drop of a robust carton and a 50cm drop of fragile equipment must not
receive the same risk score.

## 10. Context & Risk Engine

The **same behaviour** carries different risk depending on product, zone,
equipment, process, time, frequency, and history:
```
DROP + FRAGILE PRODUCT + 1m HEIGHT   >   DROP + EMPTY CARTON + 10cm HEIGHT
```

**Conceptual scoring formula:**
```
Risk = Behaviour Severity × Product Sensitivity × Impact × Height × Location
       × Frequency × Context
```
Normalized: `0–25 LOW · 26–50 MEDIUM · 51–75 HIGH · 76–100 CRITICAL`
(configurable thresholds).

**Explainability example:**
```
Risk: HIGH — 78/100
Behaviour severity   +25
Drop height           +18
Product fragility     +15
Impact estimate       +10
Repeated behaviour     +5
Location factor        +5
Primary reason: Product was dropped from approximately 1.0 m during unloading.
Confidence: 0.89
```

**Three separate risk concepts** (never merged into one vague score):
1. Behaviour Risk — how unsafe is the action?
2. Damage Risk — how likely is product damage?
3. Safety Consequence — could this endanger people/equipment?

## 11. Damage Prediction

```
Observed Behaviour → Potential Damage → Human Inspection → Confirmed Damage
```
Output:
```
Potential Damage Probability: 82%
Likely damage mode: Packaging deformation
Confidence: 0.81
```
Damage categories: packaging deformation, breakage, abrasion, stack collapse,
orientation damage, unknown. Damage status field:
`NOT_OBSERVED / POTENTIAL_DAMAGE / CONFIRMED_BY_HUMAN / CONFIRMED_BY_EXTERNAL_SYSTEM`.

Recommended v1 model for tabular damage prediction: **XGBoost/LightGBM** over
`drop height, velocity, impact, product fragility, behaviour, surface, stack
configuration` — preferable to a deep network for this kind of structured,
low-dimensional input.

## 12. Predictive Risk Engine

Answers "what is likely to happen next?" using current behaviour, recent
history, location, frequency, process, and similar historical incidents:
```
Predicted event: Improper stacking
Probability: 74%
Prediction horizon: Next 30–60 seconds
Confidence: 0.71
```

## 13. Real-Time Alert Engine & De-duplication

```
Behaviour detected → Temporal confirmation → Context validation → Risk score
→ Alert decision
```
De-duplication pipeline:
```
Alert cooldown → Incident grouping → Temporal merging → Duplicate suppression
```
Alert payload: severity, timestamp, camera, location, behaviour, risk score,
explanation, evidence, track IDs.

## 14. Evidence Engine & Replay

Every significant incident auto-generates:
```
Snapshot · Video clip (pre/event/post) · Frame range · Object IDs · Trajectory
· Behaviour DNA · Risk score · Confidence · Zone · Timestamp · Model version
· Explanation · Checksum/hash
```
Replay overlays: original video, bounding boxes, track IDs, trajectories,
behaviour states, risk escalation, timeline markers (e.g.
`00:13 Pickup · 00:17 Movement · 00:20 Release · 00:21 Fall · 00:22 Impact
· 00:23 HIGH RISK`).

## 15. Root Cause, Recommendation, Counterfactual

**Root cause categories:** equipment, environment, process, congestion,
workflow, placement, handling, training, infrastructure, unknown. Always
distinguish `Observed` fact from `AI-inferred` (labelled, never presented as
proven).

**Recommendation example:**
```
Observed: Product dragged across floor.
Recommendation: Use trolley/pallet truck.
Reason: Dragging can increase packaging abrasion and uncontrolled movement.
Estimated risk reduction: 35–50% (Confidence: 0.74)
```

**Counterfactual example:**
```
Observed: Manual movement → drop → impact           (Risk 82)
Alternative: Trolley movement → controlled placement (Est. risk 31)
Potential reduction: 51 points
```
Assumptions are always shown alongside the comparison.

## 16. AI Assistant Architecture

```
User Question → Intent Detection → Query Planning → Structured DB Query
→ Incident Retrieval → Similar Event Search (pgvector) → Evidence Retrieval
→ LLM → Grounded Response
```
The LLM never performs the core risk calculation — the deterministic/ML risk
engine computes it; the LLM explains it, grounded strictly in retrieved
evidence, using tool/function calling for DB queries rather than free-form SQL
generation.

## 17. Confidence Handling

```
HIGH CONFIDENCE   → automatic event
MEDIUM CONFIDENCE → human review
LOW CONFIDENCE    → uncertain / no alert
```
Raw neural-network confidence is never treated as a calibrated probability
without validation against the golden test set.

## 18. Model Evaluation Metrics by Component

| Component | Metrics |
|---|---|
| Object detection | mAP, precision, recall |
| Tracking | ID consistency, ID switches, tracking accuracy |
| Behaviour | Precision, recall, F1, confusion matrix |
| Risk | False positives, false negatives, calibration |
| Prediction | MAE, RMSE, ROC-AUC, PR-AUC, Brier score (depending on model) |

## 19. False-Positive Management Pipeline

```
Detection → Confidence threshold → Temporal confirmation → Spatial validation
→ Context validation → Risk threshold → Duplicate suppression → Alert
```
This is deliberately **not**: `YOLO detects something → immediately alert`.
