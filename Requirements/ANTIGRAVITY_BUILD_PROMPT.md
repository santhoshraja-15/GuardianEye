# Antigravity Build Prompt Document
## W-SAFE — Ready-to-Paste Prompts for Building with an Agentic AI IDE

This document contains a **master project prompt** plus **phase-by-phase
prompts** you can paste directly into an agentic AI coding environment (e.g.
Antigravity, or any similar agent-driven IDE) to build W-SAFE. Each phase
prompt assumes the agent has access to this whole documentation set (attach/
reference the full `W-SAFE-Docs` folder as project context) and to a
terminal/file system.

**How to use this file:**
1. Paste the **Master Project Prompt** once, at the very start of a new
   agent session, so the agent internalizes scope, stack, and constraints.
2. Paste each **Phase Prompt** in order, one at a time, only after the
   previous phase's acceptance criteria are met. Do not skip ahead.
3. After each phase, ask the agent to run the stated verification command(s)
   before proceeding.

---

## MASTER PROJECT PROMPT (paste first)

```
You are building "W-SAFE" — an AI-powered warehouse behaviour, risk, damage
prevention, and operational intelligence platform. Full specifications are
provided in the attached documentation set (README.md, PRD.md,
LAYER_ARCHITECTURE.md, TECH_STACK.md, REQUIREMENTS_AND_PREREQUISITES.md,
FLOW_DOCUMENT.md, TECHNICAL_DEEP_DIVE.md, SYSTEM_DESIGN.md, DATABASE_SCHEMA.md,
API_SPECIFICATION.md, BUILD_INSTRUCTIONS.md, PROJECT_CONTROL_DOCUMENT.md,
TESTING_STRATEGY.md, DEPLOYMENT_GUIDE.md). Read all of them before writing any
code.

NON-NEGOTIABLE CONSTRAINTS:
1. Locked stack: React + TypeScript + Vite + Tailwind + shadcn/ui (frontend);
   Python + FastAPI + Pydantic + SQLAlchemy + Alembic (backend); PyTorch +
   YOLO + OpenCV + FFmpeg + ByteTrack (CV); PostgreSQL + pgvector (database,
   no separate vector DB); Redis + Celery (async jobs, not Kafka); Docker
   Compose (deployment, not Kubernetes). Do not substitute these without
   being asked.
2. Build in VERTICAL SLICES, not layer-by-layer across the whole system. Each
   slice must be independently runnable and demoable. Never let the frontend
   or AI pipeline sit unintegrated until "the end."
3. The behaviour/risk pipeline must be EXPLAINABLE: every risk score needs a
   factor breakdown; every AI-inferred root cause must be labelled as
   inferred, never presented as fact; damage claims are always a probability
   until a human confirms them.
4. The AI assistant must be EVIDENCE-FIRST: it queries structured data via
   tool/function calling and only explains what was actually retrieved. It
   must refuse to answer when no evidence exists rather than inventing an
   answer. The LLM never computes risk scores — the deterministic/ML risk
   engine does that.
5. Responsible AI: no default facial recognition, no automated employee
   punishment, all consequential actions require human review, audit log
   every state-changing action.
6. Use the exact database schema in DATABASE_SCHEMA.md and the exact API
   surface in API_SPECIFICATION.md unless a documented reason requires a
   change — if you must deviate, explain why before proceeding.
7. Follow the behaviour taxonomy in PRD.md §7 exactly for the MVP (B01–B10).
8. After each phase below, run the stated verification step and report the
   result before moving to the next phase. Do not silently skip verification.

Confirm you have read the documentation set and ask me only for anything
genuinely missing (e.g. actual LLM API key, actual sample videos) before
starting Phase 1.
```

---

## PHASE 1 — Environment & Repo Scaffold

```
Set up the W-SAFE monorepo exactly as described in BUILD_INSTRUCTIONS.md
Level 1: create the folder structure (frontend/, backend/, ai/, data/,
models/, videos/, database/, docs/, docker/, scripts/), initialize git with
the branch strategy described, and scaffold:
 - a FastAPI backend skeleton with health-check endpoint
 - a React+TS+Vite frontend skeleton with Tailwind configured
 - a docker-compose.yml matching DEPLOYMENT_GUIDE.md §1 (postgres w/
   pgvector, redis, minio, backend, frontend, ai-worker, prometheus, grafana)
Verification: `docker compose up --build` starts all services; backend
health endpoint returns 200; frontend loads a placeholder page.
```

## PHASE 2 — Database & Backend Foundation

```
Implement the full PostgreSQL schema from DATABASE_SCHEMA.md as SQLAlchemy
models + Alembic migrations. Implement JWT auth, RBAC roles (Admin,
Supervisor, Safety Officer, Analyst, Operator) enforced server-side, and CRUD
endpoints for warehouses/zones/cameras/products/equipment per
API_SPECIFICATION.md §2 and §11.
Verification: `alembic upgrade head` succeeds; a Pytest suite covering
auth + RBAC + one CRUD resource passes.
```

## PHASE 3 — Frontend Shell (mock data)

```
Build the page shell described in SYSTEM_DESIGN.md §8: Login, Command
Center, Live Monitoring, Incident Center, Incident Detail, Analytics, AI
Assistant. Use mock/fixture data for now — do not wait for the AI pipeline.
Match the sketches in SYSTEM_DESIGN.md §9 for the Command Center and
Incident Investigation screens.
Verification: every page renders with mock data; Vitest component tests
pass for at least the Command Center KPI cards and Incident card component.
```

## PHASE 4 — Video Ingestion Pipeline

```
Implement VideoSource adapters (start with FileSource only) per
TECHNICAL_DEEP_DIVE.md §1, video upload endpoint, processing_jobs tracking,
and a Celery worker that decodes/samples frames at a configurable inference
FPS independent of source FPS, per BUILD_INSTRUCTIONS.md Level 4.
Verification: uploading a sample MP4 creates a processing_jobs row that
transitions QUEUED → RUNNING → DONE, with sampled frames written/loggable.
```

## PHASE 5 — Object Detection

```
Integrate a YOLO-family detector for the MVP object classes (Person,
Carton/Product, Pallet, Trolley, Vehicle — TECHNICAL_DEEP_DIVE.md §2).
Store detections per the `objects` table. Report mAP/precision/recall on a
held-out validation set.
Verification: running the pipeline on a golden test video produces
detections above the pass bar in TESTING_STRATEGY.md §3; results visualized
(bounding boxes drawn on sample frames) for manual sanity check.
```

## PHASE 6 — Multi-Object Tracking

```
Integrate ByteTrack over the YOLO detections per TECHNICAL_DEEP_DIVE.md §3.
Persist tracks to `object_tracks` with trajectory, velocity, acceleration.
Implement the ACTIVE→LOST→REACQUIRED state machine so a temporary occlusion
never spawns a duplicate track or false incident.
Verification: a test video with a brief occlusion keeps a single track_id
across the occlusion; ID-switch rate meets the bar in TESTING_STRATEGY.md §3.
```

## PHASE 7 — Zones & Interaction Engine

```
Implement zone polygon management (admin can draw/edit zones on a video
frame or map) and the human-object interaction engine (geometric rules for
CONTACT/HOLDING/MOVING/NEAR_PALLET/PICKUP) per TECHNICAL_DEEP_DIVE.md §4–5.
Store results in `interactions`.
Verification: for a golden "pickup" video, an interaction sequence
CONTACT→HOLDING→PICKUP is produced with correct timestamps.
```

## PHASE 8 — Temporal Behaviour Engine (MVP: 5 behaviours, then 10)

```
Implement the deterministic state-machine behaviour engine per
TECHNICAL_DEEP_DIVE.md §6–7. Start with Pickup/Drop/Drag/Throw/Stacking, then
expand to the full B01–B10 MVP set from PRD.md §7. Every behaviour_event
must store a Behaviour DNA sequence (TECHNICAL_DEEP_DIVE.md §8).
Verification: all 10 golden-set videos (TESTING_STRATEGY.md §4) are
classified correctly; negative-control videos (§5) do NOT trigger a false
behaviour.
```

## PHASE 9 — Risk & Damage Engine

```
Implement the deterministic risk engine (TECHNICAL_DEEP_DIVE.md §10) with a
configurable weights table (never hard-coded), producing risk_score,
risk_level, and a factor breakdown. Implement damage prediction
(TECHNICAL_DEEP_DIVE.md §11) starting with an XGBoost/LightGBM model over
structured features, with damage_status defaulting to NOT_OBSERVED /
POTENTIAL_DAMAGE — never an unqualified "damaged" claim.
Verification: golden-set risk levels match expected labels within tolerance;
every risk_assessment record has a non-empty factor_breakdown.
```

## PHASE 10 — Alerts, Incidents, Evidence, Replay

```
Implement the alert de-duplication pipeline (FLOW_DOCUMENT.md §8),
incident/alert lifecycles (FLOW_DOCUMENT.md §5–6), the evidence engine
(auto-generated snapshot/clip/trajectory/checksum), and a replay view with
bounding-box/track/behaviour/risk overlays, all wired to the
`/ws/events` WebSocket channel per API_SPECIFICATION.md §12.
Verification: a golden "Drop" video results in exactly ONE incident and ONE
alert (not dozens); the frontend receives a NEW_INCIDENT WebSocket event and
displays it live; replay renders with correct overlays.
```

## PHASE 11 — Root Cause, Recommendation, Counterfactual

```
Implement categorized, explicitly observed-vs-AI-inferred root causes,
prevention recommendations with an estimated (never guaranteed) risk-
reduction range, and the counterfactual comparison engine, per
TECHNICAL_DEEP_DIVE.md §15.
Verification: an incident detail response includes root_cause (with
is_ai_inferred flag), recommendation (with an estimated range, not a single
guaranteed number), and a counterfactual risk delta.
```

## PHASE 12 — AI Assistant (Evidence-First RAG)

```
Implement the assistant per TECHNICAL_DEEP_DIVE.md §16 and
FLOW_DOCUMENT.md §10: intent detection → tool-called structured DB query +
pgvector similarity search → LLM response grounded strictly in retrieved
evidence. Implement the 5 baseline queries from BUILD_INSTRUCTIONS.md
Level 17 first. The assistant must state "no evidence available" rather than
fabricate an answer when nothing is retrieved.
Verification: ask each of the 5 baseline queries against seeded incident
data and confirm every claim in the response traces to a retrieved record;
ask a question with no matching data and confirm the assistant declines
rather than inventing one.
```

## PHASE 13 — Analytics, Heatmaps, Digital Twin

```
Wire the Command Center and Analytics pages to real data (replace all mock
data from Phase 3), implement the four heatmap types (incident density, risk
intensity, damage probability, behaviour frequency), and a 2D digital twin
map showing live incident positions, per SYSTEM_DESIGN.md §1 and
API_SPECIFICATION.md §8.
Verification: KPI cards and charts reflect real incidents created in
earlier phases; heatmap endpoints return non-empty data for the golden set.
```

## PHASE 14 — Human Review & Active Learning Loop

```
Implement the review queue and reviewer actions
(CORRECT/INCORRECT/CHANGE_BEHAVIOUR/UNCERTAIN), dataset versioning, and the
model registry with status lifecycle (TRAINING→EVALUATION→APPROVED→DEPLOYED
→RETIRED/REJECTED). No model may auto-deploy without an explicit approval
step.
Verification: submitting a review correction creates a `reviews` record and
is retrievable in a subsequent dataset version; attempting to mark a model
DEPLOYED without an `approved_by` user is rejected.
```

## PHASE 15 — Security, RBAC Hardening, Privacy

```
Harden RBAC enforcement server-side across every endpoint, implement full
audit logging for state-changing actions, add optional face-blurring in the
evidence pipeline, configurable data retention per SYSTEM_DESIGN.md §11, and
rate limiting.
Verification: a direct API call attempting an action outside the caller's
role is rejected (not just hidden in the UI); an audit_logs row is created
for a config change; retention settings are read from config, not hard-coded.
```

## PHASE 16 — Testing, Optimization, Deployment

```
Stand up the full test suite from TESTING_STRATEGY.md (Pytest, Vitest,
Playwright, golden-video regression), wire GitHub Actions CI, and finalize
the Docker Compose deployment (including GPU passthrough for ai-worker) per
DEPLOYMENT_GUIDE.md.
Verification: CI pipeline is green; full golden-video regression run passes
the metric bars in TESTING_STRATEGY.md §3; `docker compose up --build` boots
the entire stack from a clean checkout.
```

## PHASE 17 — Demo Packaging

```
Prepare the hackathon submission: a 5–6 slide deck summarizing PRD.md,
LAYER_ARCHITECTURE.md, and success metrics; a recorded or live demo following
the exact scenario in FLOW_DOCUMENT.md §15 (the single Drop-event walkthrough
that exercises the full pipeline); and a README pointing evaluators to this
documentation set.
Verification: the demo scenario runs start-to-finish without manual
intervention; the deck and demo explicitly state the Responsible AI
positioning from PRD.md §9.
```

---

## Reusable Guardrail Snippet (append to any phase prompt if the agent drifts)

```
Reminder: keep to the locked stack in TECH_STACK.md, do not compute risk
scores inside the LLM, do not let the assistant answer without retrieved
evidence, label AI-inferred causes as inferred, and do not mark any incident
as confirmed-damaged without a human/external confirmation. If a requested
change would violate one of these, say so before implementing it.
```
