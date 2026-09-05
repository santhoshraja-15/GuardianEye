# Flow Document
## W-SAFE — End-to-End Data Flow, Event Lifecycle, and User Flows

## 1. Master Intelligence Pipeline

```
Camera / Video → Perception → Tracking → Scene Understanding → Behaviour Understanding
→ Context Analysis → Risk Assessment → Damage Prediction → Alert → Human Intervention
→ Root Cause → Prevention → Learning
```

## 2. Complete Data Flow (technical)

```
VIDEO
  ↓
VIDEO_SOURCE (File / RTSP / VMS / Webcam)
  ↓
FRAME (decode, resize, sample @ inference FPS, timestamp)
  ↓
DETECTION (YOLO: class, confidence, bbox)
  ↓
TRACK (ByteTrack: persistent track_id, position, velocity, acceleration)
  ↓
MOTION_FEATURE (direction, trajectory, time-in-scene)
  ↓
INTERACTION (person↔product↔equipment↔zone geometric relationships)
  ↓
BEHAVIOUR_EVENT (state machine → behaviour type + Behaviour DNA sequence)
  ↓
CONTEXT (product profile, zone, equipment, history, process)
  ↓
RISK_ASSESSMENT (score, level, explainable factor breakdown, confidence)
  ↓
DAMAGE_PREDICTION (probability, damage category, confidence)
  ↓
INCIDENT (created once risk/damage crosses threshold, deduplicated)
  ↓
ALERT (WebSocket push, lifecycle-tracked)
  ↓
EVIDENCE (snapshot + clip + trajectory + timeline + checksum)
  ↓
REVIEW (human confirms/corrects, optional)
  ↓
ROOT_CAUSE (categorized, observed vs AI-inferred)
  ↓
RECOMMENDATION (+ counterfactual comparison)
  ↓
INTERVENTION (supervisor acknowledges → investigates → acts)
  ↓
OUTCOME (incident resolved)
  ↓
LEARNING (correction feeds dataset → retraining → evaluation → registry → deploy)
```

## 3. Phase-by-Phase Processing Flow

```
Phase 1  Video Input        Camera/MP4/RTSP → VideoSource Adapter
Phase 2  Preprocessing      Decode → Resize → Frame sampling → Timestamp sync
Phase 3  Object Detection   YOLO → Person/Product/Pallet/Equipment/Vehicle
Phase 4  Tracking           ByteTrack → Track IDs → Trajectory → Velocity → Acceleration
Phase 5  Scene Understanding Determine zone/loading area/staging/equipment lane/restricted area
Phase 6  Interaction Detect  person↔product, product↔pallet, product↔trolley,
                             forklift↔pedestrian, product↔vehicle
Phase 7  Temporal Reasoning  Build event sequence (Approach→Pickup→Move→Release→Fall→Impact)
Phase 8  Behaviour Classify  DROP / DRAG / THROW / ROUGH_HANDLING / ...
Phase 9  Context Enrichment  Add product/zone/equipment/history/process/environment
Phase 10 Risk Calculation    Score + level + explanation + confidence
Phase 11 Damage Prediction   Probability + damage type + confidence
Phase 12 Alert                Create Incident → Create Alert → WebSocket → Dashboard
Phase 13 Evidence             Save snapshot/clip/trajectory/timeline/track IDs/explanation
Phase 14 Intervention         Supervisor: Acknowledge → Investigate → Review → Act
Phase 15 Root Cause            Analyze location/process/frequency/environment/equipment/workflow
Phase 16 Prevention            Recommendation → Estimated impact → Counterfactual
Phase 17 Learning               Human review → Correct label → Dataset → Training → Evaluation
                                 → Approval → Registry
```

## 4. Behaviour Sequence Example (Drop event)

```
APPROACH → CONTACT → PICKUP → CONTROLLED MOVEMENT → ACCELERATION → RELEASE
→ FALL → IMPACT → STATIONARY → POTENTIAL DAMAGE
```

Track recovery sub-flow (prevents false incidents from tracking glitches):
```
ACTIVE → LOST → REACQUIRED   (no new incident created solely from this transition)
```

## 5. Alert Lifecycle

```
OPEN → ACKNOWLEDGED → INVESTIGATING → RESOLVED
                 (or)
OPEN → REJECTED / DISMISSED
```

## 6. Incident Lifecycle

```
DETECTED → ALERTED → ACKNOWLEDGED → UNDER REVIEW → CONFIRMED/REJECTED
→ ACTION TAKEN → RESOLVED
```

## 7. Damage Status Lifecycle

```
NOT_OBSERVED → POTENTIAL_DAMAGE → CONFIRMED_BY_HUMAN / CONFIRMED_BY_EXTERNAL_SYSTEM
```

## 8. Alert De-duplication Flow

```
Detection → Confidence threshold → Temporal confirmation → Spatial validation
→ Context validation → Risk threshold → Duplicate suppression (cooldown +
incident grouping + temporal merging) → Alert
```
Example: "same box falling for 2 seconds" → ONE incident → ONE alert (never 30).

## 9. Active Learning Flow

```
Video → AI → Uncertain Event → Human Review → Corrected Label → Curated Dataset
→ Training Queue → Model Training → Evaluation → Human Approval → Model Registry
→ Deployment
```

## 10. AI Assistant Flow (Evidence-First)

```
User Question
   ↓
Intent Detection
   ↓
Query Planning
   ↓
Structured Database Query  ──┐
   ↓                          ├─→ Evidence Retrieval
Similar Event Search (pgvector) ┘
   ↓
LLM (explains only what was retrieved)
   ↓
Grounded Response
```
Evidence-first rule:
```
Evidence exists? ── YES ──→ Answer with evidence
        │
        NO
        ↓
State that evidence is unavailable
```
The assistant must never invent incidents, times, risk levels, damage, root
causes, or locations.

## 11. Multilingual Voice Flow (Tier 3)

```
Voice → Speech-to-Text → Intent → Evidence Query → LLM → Response → Text-to-Speech
```
Supports English and Tamil. Voice is an extension layered on top of the reliable
text assistant — not a Phase 1 dependency.

## 12. User Flow — Supervisor Investigating an Incident

```
1. Dashboard shows a live HIGH-RISK alert badge
2. Supervisor clicks into Incident Center
3. Filters/finds the incident card
4. Opens Incident Detail → watches replay with overlays
5. Reads risk breakdown ("why HIGH?") and damage probability
6. Reviews recommended action + counterfactual comparison
7. Checks similar past incidents (assistant / similar-incident search)
8. Acknowledges → Investigates → takes action → marks Resolved
9. (Optional) Submits a human-review correction if AI got it wrong
```

## 13. User Flow — Supervisor Using the AI Assistant

```
1. Opens AI Assistant panel
2. Types/speaks: "Which loading bay had the highest number of risky events today?"
3. Assistant resolves intent → structured DB query → retrieves evidence
4. Responds with a grounded, evidence-linked answer (never fabricated)
5. Supervisor can click through to the underlying incidents
6. Follow-up question maintains conversation context
```

## 14. User Flow — Admin Configuring the System

```
1. Logs in as Admin
2. Draws/edits zone polygons on the warehouse map
3. Configures product profiles (fragility, weight, drop-height limits)
4. Sets risk thresholds and alert cooldowns
5. Manages cameras (add/remove/health status)
6. Manages RBAC roles/permissions
7. Reviews audit log for prior configuration changes
```

## 15. Demonstration Scenario (recommended for the hackathon demo)

```
VIDEO START → Person approaches carton → Carton detected → Track ID assigned
→ Person picks carton → Carton moves → Sudden acceleration → Carton released
→ Carton falls → Impact detected → Carton becomes stationary
→ BEHAVIOUR = DROP → RISK = HIGH → DAMAGE PROBABILITY = 82% → ALERT GENERATED
→ Supervisor notified → Evidence clip created → Supervisor opens replay
→ AI explains risk factors → Similar incidents shown → Root cause identified
→ Recommendation generated → Counterfactual scenario shown → Supervisor takes
intervention → Event marked resolved → Human review → Learning dataset updated
```
This single flow demonstrates nearly the entire architecture end-to-end and is
the recommended anchor for the hackathon demo video/live walkthrough.
