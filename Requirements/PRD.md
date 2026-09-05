# Product Requirements Document (PRD)
## W-SAFE — AI-Powered Warehouse Behaviour, Risk, Damage Prevention & Operational Intelligence Platform

Version 1.0

---

## 1. Purpose

Define what W-SAFE must do, for whom, why, and how success will be measured, so that
engineering, design, and evaluation stay aligned to a single source of truth.

## 2. Problem Statement

Warehouses perform thousands of product movements daily (loading, unloading, transfer,
stacking, pallet handling, trolley/forklift movement, staging, storage). Conventional
CCTV **records** these activities but leaves interpretation entirely to human
supervisors, so damage-causing behaviours (dropping, dragging, rough handling,
incorrect/unstable stacking, incorrect placement, handling without required equipment,
incorrect pallet positioning, pushing/throwing, unsafe loading/unloading sequences) are
usually discovered only **after** damage has occurred.

**Core question:** How can warehouse video be transformed into real-time behavioural
intelligence that identifies actions capable of causing product damage, evaluates
their risk, explains why they are risky, and enables intervention **before** damage
occurs?

## 3. Goals / Objectives

### 3.1 Primary Objectives
1. Automatically detect warehouse entities (people, products, pallets, equipment, vehicles).
2. Track objects continuously across frames.
3. Understand human–object–equipment interactions.
4. Identify at least 10 predefined risky behaviours (see §7).
5. Reason over action **sequences**, not isolated frames.
6. Assign explainable risk levels (Low/Medium/High/Critical).
7. Estimate potential product-damage probability.
8. Generate real-time, de-duplicated alerts.
9. Preserve visual evidence for every significant incident.
10. Let supervisors investigate, replay, and explain incidents.
11. Identify recurring risk patterns and probable root causes.
12. Recommend preventive actions with estimated impact.
13. Predict emerging risk before the next incident.
14. Provide natural-language (English + Tamil) access to warehouse intelligence.
15. Continuously improve via human review and active learning.

### 3.2 Non-Goals (v1)
- Employee scoring, ranking, or automated punitive action.
- Full 3D digital twin (2D is sufficient for v1).
- Full WMS/ERP replacement — only integration interfaces are exposed.
- Cross-camera re-identification (future extension).
- Real facial recognition / biometric identification.

## 4. Target Users / Personas

| Persona | Needs |
|---|---|
| **Warehouse Supervisor** | Real-time alerts, incident replay, "why was this risky?", recommended actions |
| **Safety Officer** | Risk trends, root-cause analysis, review queue, compliance evidence |
| **Operations/Logistics Manager** | Analytics by zone/shift/process, damage-prevention ROI, heatmaps |
| **Warehouse Operator** | Non-punitive feedback on process, training opportunities |
| **System Admin** | Camera/zone/product/threshold configuration, RBAC, retention policy |
| **Data/ML Engineer** | Review queue, dataset versioning, model registry, evaluation metrics |

## 5. Scope (MVP vs Full)

### 5.1 MVP (Tier 1 — mandatory for demo)
Video ingestion → object detection → object tracking → spatial zones →
human-object interaction → **10 behaviours** → temporal reasoning → risk
classification → alert system → evidence generation → incident replay → dashboard.

### 5.2 Tier 2 — Major Differentiators
Behaviour DNA (temporal fingerprint), interaction graph, product-specific risk,
damage probability, predictive risk, risk heatmaps, root-cause analysis, prevention
recommendations, counterfactual analysis, AI assistant, similar-incident search,
2D digital twin.

### 5.3 Tier 3 — Exceptional / Stretch
Active learning loop, unknown-behaviour detection, Tamil voice interaction, voice
alerts, Temporal Transformer model, pallet stability estimation, forklift/pedestrian
conflict prediction, intervention simulator.

### 5.4 Tier 4 — Future / Research
Cross-camera identity, edge deployment, GNN-based scene reasoning, self-supervised
learning, full WMS/VMS integration, large-scale distributed inference.

## 6. Functional Requirements

### 6.1 Video Ingestion
- Accept MP4/AVI/MOV upload, RTSP live streams, webcam, and VMS adapters.
- Frame sampling with configurable inference FPS independent of source FPS.
- Corrupt-frame handling, camera health/offline detection.

### 6.2 Perception & Tracking
- Detect: person, carton/product, pallet, trolley, forklift, vehicle, equipment,
  loading bay, floor, stack.
- Multi-object tracking with persistent track IDs; track-loss recovery (no false
  incident on temporary occlusion).

### 6.3 Behaviour Identification
- Minimum 10 predefined behaviours (B01–B10, §7), expandable to 20 (B11–B20).
- Represent behaviour as an ordered temporal state sequence ("Behaviour DNA").
- Support an `UNKNOWN` / `AMBIGUOUS` classification rather than forcing a wrong label.

### 6.4 Risk Classification
- Context-aware score combining behaviour severity, product fragility, impact,
  height, location, frequency, and history.
- Four levels: LOW (0–25) / MEDIUM (26–50) / HIGH (51–75) / CRITICAL (76–100),
  thresholds configurable.
- Every score must be explainable with a factor breakdown.

### 6.5 Damage Prediction
- Separate **behaviour risk**, **damage risk**, and **safety consequence**.
- Output a damage probability + likely damage category, never an unqualified
  "product is damaged" claim without human confirmation.
- Damage status lifecycle: `NOT_OBSERVED → POTENTIAL_DAMAGE → CONFIRMED_BY_HUMAN /
  CONFIRMED_BY_EXTERNAL_SYSTEM`.

### 6.6 Alerts & Incidents
- Real-time WebSocket alerts on threshold breach with de-duplication/cooldown.
- Alert lifecycle: `OPEN → ACKNOWLEDGED → INVESTIGATING → RESOLVED` (or
  `REJECTED/DISMISSED`).
- Incident lifecycle: `DETECTED → ALERTED → ACKNOWLEDGED → UNDER REVIEW →
  CONFIRMED/REJECTED → ACTION TAKEN → RESOLVED`.

### 6.7 Evidence & Replay
- Auto-generate snapshot + pre/post clip + trajectory + timeline for every
  significant incident, with checksum for integrity.
- Replay view overlays boxes, track IDs, trajectories, behaviour states, and risk
  escalation markers.

### 6.8 Root Cause & Prevention
- Categorized root causes (equipment, environment, process, congestion, workflow,
  placement, handling, training, infrastructure, unknown).
- Explicitly label AI-inferred causes as inferred, not confirmed fact.
- Prevention recommendations tied to the observed behaviour, with an **estimated**
  (not guaranteed) risk-reduction range.
- Counterfactual engine: compare observed-scenario risk vs. alternative-safe-scenario
  risk.

### 6.9 Analytics & Digital Twin
- KPI dashboard, risk/behaviour/damage/frequency heatmaps.
- 2D warehouse map with live incident overlay.
- Reports: daily/shift/weekly/incident/zone/behaviour, exportable as PDF/CSV/JSON.

### 6.10 AI Assistant
- Evidence-grounded natural-language Q&A over incidents (English + Tamil, text +
  voice).
- Must never invent incidents, times, risk levels, damage, root causes, or locations
  — if no evidence exists, it must say so.
- Uses structured DB queries + vector similarity retrieval, not LLM-computed risk.

### 6.11 Human Review & Learning
- Review queue for uncertain/important events; reviewer actions:
  `CORRECT / INCORRECT / CHANGE BEHAVIOUR / UNCERTAIN`.
- Active learning loop: review → dataset versioning → training → evaluation → human
  approval → model registry → deployment. No model auto-deploys.

### 6.12 Governance & Configuration
- RBAC (Admin, Supervisor, Safety Officer, Analyst, Operator), enforced server-side.
- Configurable zones, products, equipment, thresholds, cooldowns, retention,
  language, notifications — no code changes required.
- Full audit log of all state changes with before/after values and reason.

## 7. Behaviour Taxonomy (MVP set, B01–B10)

| ID | Behaviour | Trigger Signal |
|---|---|---|
| B01 | Product Drop | Controlled movement → rapid descent → impact |
| B02 | Dragging | Floor-level horizontal movement without equipment |
| B03 | Throwing | Sudden high velocity release, uncontrolled landing |
| B04 | Rough Handling | High acceleration / sudden direction change / impact |
| B05 | Incorrect Stacking | Violates configured stacking rules |
| B06 | Unstable Stacking | Excess tilt / insufficient support geometry |
| B07 | Incorrect Placement | Product placed outside designated zone |
| B08 | Improper Equipment Usage | Manual handling when equipment is required |
| B09 | Incorrect Pallet Positioning | Pallet/product support relationship violated |
| B10 | Unsafe Loading/Unloading Sequence | Actions occur out of safe order |

Extended set B11–B20: Pushing, Rolling, Product Overhang, Unsupported Product,
Unsafe Orientation, Standing/Stepping on Product, Forklift/Pedestrian Conflict,
Unsafe Staging, Pallet Overloading, Unknown Behaviour.

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Latency | Near real-time alerting (seconds, not minutes) for HIGH/CRITICAL events |
| Explainability | Every AI decision must show a human-readable factor breakdown |
| Reliability | No new incident created purely from a tracking glitch (ACTIVE→LOST→REACQUIRED handling) |
| Privacy | No default facial recognition; face blurring option; role-based video access |
| Auditability | Every state change logged with actor, timestamp, reason |
| Extensibility | New behaviours, zones, products addable via configuration, not redeploy |
| Scalability | Architecture must not block scaling to multi-camera, multi-warehouse later |
| Availability | Camera disconnect handled gracefully (offline flag, retry, notify) |

## 9. Responsible AI Requirements

- The system evaluates **operational behaviours and process risk**, not employee
  worth or performance.
- Does **not**: automatically punish employees, perform facial recognition by
  default, assign permanent worker labels, claim confirmed damage without evidence,
  present inferred causes as fact.
- Does: detect events, explain risk, request human review, identify process-level
  patterns, recommend prevention.
- Behaviour fingerprinting operates at process/zone/activity/incident level, not
  individual-worker level.

## 10. Success Metrics

### AI/Model
- Detection mAP, precision, recall; behaviour F1/precision/recall; false-positive
  rate; inference latency.

### Operational
- High-risk events per shift, repeat-behaviour frequency, response time, risk by
  zone/loading bay.

### Business
- Potential-damage events identified, estimated risk reduction, repeat-risk
  reduction, rework/damage indicators.

### Human
- Supervisor usability score, operator acceptance, training opportunities surfaced,
  qualitative feedback.

## 11. Constraints & Assumptions

- Hackathon submission deadline: **10 September 2026** — 5–6 slide deck + prototype
  demo covering representative scenarios required.
- Development/testing may use a controlled miniature warehouse (boxes, pallets,
  trolleys, tables, small vehicles, human participants) or public/synthetic footage.
- GPU workstation/server deployment is acceptable for the prototype; edge deployment
  is a future extension.
- AI/CV work should receive the largest effort share (~35%) since it is a primary
  judging dimension (challenge weights AI/video integration and technical execution
  at 20% each).

## 12. Deliverables

Working web application; trained/fine-tuned detection + behaviour pipeline;
annotated behaviour dataset; complete backend API; operational event database;
real-time dashboard; evidence-grounded AI assistant; incident/operational reports;
model + operational + business evaluation; full documentation set (this repository).
