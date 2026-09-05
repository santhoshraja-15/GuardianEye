# Layer Architecture Document
## W-SAFE — The Five Intelligence Layers

W-SAFE's design philosophy is organized into five progressive intelligence layers.
Each layer answers a distinct question and produces structured output consumed by
the next layer. This separation keeps the system explainable, debuggable, and
independently testable.

```
Layer 1  PERCEPTION            "What is present?"
Layer 2  BEHAVIOUR INTELLIGENCE "What is happening?"
Layer 3  RISK & DAMAGE INTELLIGENCE "How dangerous is it?"
Layer 4  PREVENTION INTELLIGENCE "Why did it happen, how to prevent it?"
Layer 5  EVIDENCE & LEARNING   "Can it be explained, reviewed, improved?"
```

---

## Layer 1 — Perception
**Question:** What is present?

Detects, per frame:
`Person · Product/Carton · Pallet · Trolley · Forklift · Vehicle · Handling
Equipment · Loading Bay · Floor · Stack`

**Technology:** YOLO-family detector + ByteTrack for persistent identity across
frames. Every detection carries `class, confidence, bbox, timestamp, camera_id,
track_id`.

**Output contract:** stream of `Detection` and `Track` objects.

---

## Layer 2 — Behaviour Intelligence
**Question:** What is happening?

Moves beyond "carton detected" to a temporal sequence:
`Person → approaches carton → picks carton → moves carton → accelerates →
releases carton → carton falls → impact occurs`.

**Sub-components:**
- **Scene Understanding Engine** — zones, pallets, equipment, geometry
- **Human-Object Interaction Engine** — holding / moving / near / contact
- **Temporal Behaviour Engine** — state machines (production v1) + optional
  Temporal Transformer (v2 research extension)
- **Interaction Graph** — Person ↔ Product ↔ Equipment ↔ Zone relationships
- **Behaviour DNA** — every incident stored as an ordered event-sequence
  fingerprint (`APPROACH → HOLD → MOVE → ACCELERATE → RELEASE → FALL → IMPACT →
  STOP`), enabling incident comparison, similar-event search, clustering, and
  root-cause analysis.

**Output contract:** `BehaviourEvent` with behaviour type + confidence +
Behaviour DNA sequence.

---

## Layer 3 — Risk & Damage Intelligence
**Question:** How dangerous is it?

Evaluates: behaviour type, product type, fragility, weight, drop height, velocity,
approximate impact, duration, stacking configuration, location, frequency,
historical patterns, equipment usage, environmental context.

**Three separate risk concepts (never combined into one vague metric):**
1. **Behaviour Risk** — how unsafe is the observed action?
2. **Damage Risk** — how likely is product damage?
3. **Safety Consequence** — could this endanger people/equipment?

**Risk Engine (deterministic v1, ML-augmented later):**
```
Risk Score = Behaviour Severity + Product Sensitivity + Impact + Height
             + Location + Frequency + Context
```
Normalized to `0–25 LOW · 26–50 MEDIUM · 51–75 HIGH · 76–100 CRITICAL`
(thresholds configurable, never hard-coded).

**Damage Prediction:** outputs a probability + likely damage category
(deformation, breakage, abrasion, stack collapse, orientation damage, unknown) —
never an unqualified "damaged" claim. Damage status:
`NOT_OBSERVED → POTENTIAL_DAMAGE → CONFIRMED_BY_HUMAN / CONFIRMED_BY_EXTERNAL_SYSTEM`.

**Predictive Risk Engine:** answers "what is likely to happen next?" using recent
behaviour history, location, frequency, process, and similar historical incidents.

**Output contract:** `RiskAssessment` + `DamagePrediction` + `Prediction`, each
with an explainable factor breakdown and confidence score.

---

## Layer 4 — Prevention Intelligence
**Question:** Why did it happen, and how can it be prevented?

Identifies likely root causes (categorized: equipment / environment / process /
congestion / workflow / placement / handling / training / infrastructure /
unknown), clearly separating:
- **Observed** — "Product was placed outside the designated staging zone."
- **AI-inferred** — "Congestion near the loading bay *may have* contributed."
  (never presented as proven fact)

**Prevention Recommendation Engine** — ties a recommendation to the detected
behaviour with an *estimated* (not guaranteed) risk-reduction range and
confidence.

**Counterfactual Safety Engine** — compares the observed scenario against an
alternative safe scenario and the resulting risk delta, with assumptions shown.

**Intervention Simulator** — lets supervisors compare current vs. proposed
workflow (add trolley, change staging area, change loading sequence, reduce
congestion, add equipment, modify stacking configuration) and see the estimated
risk change.

**Output contract:** `RootCause` + `Recommendation` + `Counterfactual`.

---

## Layer 5 — Evidence & Learning
**Question:** Can the decision be explained, reviewed, and improved?

Every significant AI decision carries: video evidence, timestamp, object IDs,
behaviour sequence, risk factors, model version, confidence, human-review state,
audit trail.

**Sub-components:**
- **Evidence Engine** — snapshot + clip + frame range + trajectory + Behaviour
  DNA + risk score + explanation, with a checksum for integrity.
- **Automatic Incident Replay** — original video + boxes + track IDs +
  trajectories + behaviour states + risk escalation timeline.
- **Human Review System** — reviewer sees video/classification/confidence/risk/
  evidence and marks `CORRECT / INCORRECT / CHANGE BEHAVIOUR / UNCERTAIN`.
- **Confidence-Aware AI** — `HIGH confidence → automatic event`,
  `MEDIUM → human review`, `LOW → uncertain/no alert`. Raw NN confidence is never
  treated as a calibrated probability without validation.
- **Unknown Behaviour Detection** — `KNOWN / UNKNOWN / AMBIGUOUS` instead of
  forcing every event into an existing category; repeated unknowns get reviewed
  and can be added to the taxonomy.
- **Active Learning Loop:**
  ```
  Video → AI → Uncertain Event → Human Review → Corrected Label
  → Curated Dataset → Training Queue → Model Training → Evaluation
  → Human Approval → Model Registry → Deployment
  ```
  No model auto-deploys purely because it was retrained.
- **Dataset Manager** — raw videos, annotated frames, behaviour clips, reviewed
  incidents, train/val/test splits, versioned.
- **Model Registry** — every model has `model_id, version, dataset_version,
  training_date, metrics, parameters, status (TRAINING/EVALUATION/APPROVED/
  DEPLOYED/RETIRED/REJECTED), approved_by, deployment_date`.

**Output contract:** `Evidence`, `Review`, `DatasetVersion`, `ModelVersion`.

---

## Responsible AI Flow (cross-cutting)

```
AI OBSERVATION → AI INTERPRETATION → AI RISK ESTIMATE → HUMAN REVIEW → HUMAN DECISION
```
**Not:** `AI → Punishment`.

Behaviour fingerprinting operates at the **process/zone/activity/incident** level
— the system answers "what happened?", not "who is a bad worker?"

## Layer Interaction Diagram

```
 Camera/Video
      │
      ▼
 ┌─────────────┐
 │  LAYER 1    │  Perception (Detect + Track)
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │  LAYER 2    │  Behaviour Intelligence (Interaction + Temporal + DNA)
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │  LAYER 3    │  Risk & Damage Intelligence (Score + Predict)
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │  LAYER 4    │  Prevention Intelligence (Root Cause + Recommend + Counterfactual)
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │  LAYER 5    │  Evidence & Learning (Replay + Review + Active Learning)
 └─────────────┘
        │
        ▼
 Supervisor Dashboard / AI Assistant / Analytics / Digital Twin
```
