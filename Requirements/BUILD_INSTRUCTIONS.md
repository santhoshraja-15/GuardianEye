# Build Instructions
## W-SAFE — Level-by-Level Build Guide

**Golden rule:** build in vertical slices that each produce a working, demoable
increment. Never build frontend, backend, and AI in isolation and try to
integrate everything at the very end.

```
Video → Detection → Tracking → Interaction → Behaviour → Risk → Alert
→ Evidence → Replay → Root Cause → Recommendation → AI Assistant
→ Analytics → Human Review → Active Learning
```

## Level 0 — Requirements & Planning

- Freeze MVP object classes: `Person, Carton/Product, Pallet, Trolley, Vehicle`.
- Freeze the 10-behaviour MVP list (`PRD.md` §7, B01–B10).
- Confirm team roles (`PROJECT_CONTROL_DOCUMENT.md`).
- Decide risk thresholds (LOW/MEDIUM/HIGH/CRITICAL cut points — configurable).

## Level 1 — Project & Environment Setup

```bash
mkdir warehouse-ai && cd warehouse-ai
git init
mkdir -p frontend backend ai/{detection,tracking,behaviour,risk,preprocessing} \
  data/{raw,processed,annotations,test} models videos database docs docker scripts
```
Install: Git, VS Code, Python 3.11+, Node.js 18+, PostgreSQL, Docker,
PyTorch, OpenCV, Ultralytics/YOLO, FastAPI, React/TypeScript/Tailwind.

Branch strategy:
```
main
development
feature/frontend
feature/backend
feature/detection
feature/tracking
feature/behaviour
feature/assistant
feature/analytics
```
Merge feature → development → main after integration testing.

## Level 2 — UI/UX Foundation (build with mock data first)

Build these pages against mock data — don't wait for the AI models:
`Login · Main Dashboard · Live Monitoring · Incident Center · Incident Detail
· Analytics · AI Assistant`. See `SYSTEM_DESIGN.md` §8–9 for the page list and
screen sketches.

## Level 3 — Backend & Database

```bash
cd backend
pip install fastapi uvicorn pydantic sqlalchemy alembic python-jose \
  celery redis psycopg2-binary --break-system-packages
```
Apply the schema in `DATABASE_SCHEMA.md`. Implement auth, CRUD for
warehouses/zones/cameras, and stub endpoints per `API_SPECIFICATION.md`.

## Level 4 — Video Processing Pipeline (no AI yet)

Implement `VideoSource` adapters (File first), OpenCV frame extraction, FPS
decoupling (e.g. sample every 3rd frame of a 30fps source), video upload →
`processing_jobs` row → Celery queue.

```python
# ai/preprocessing/frame_sampler.py (sketch)
import cv2
def sample_frames(path, inference_fps=10):
    cap = cv2.VideoCapture(path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(src_fps / inference_fps))
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            yield idx, frame
        idx += 1
```

## Level 5 — Object Detection

Fine-tune/apply a YOLO model on the MVP object classes. Validate on a held-out
set (mAP/precision/recall) before moving on — do not proceed until detection is
reasonably reliable.

## Level 6 — Multi-Object Tracking

Integrate ByteTrack over YOLO detections. Store `track_id, frame, timestamp, x,
y, width, height, velocity, acceleration`. Visualize trajectories to sanity
check before building behaviour logic on top.

## Level 7 — Zone Engine

Let an admin draw polygons on the video/map (Loading Bay, Storage Zone,
Restricted Zone, Staging Zone, Pedestrian Lane). Store as `zones.polygon`.

## Level 8 — Interaction Engine

Implement geometric relationship rules:
```
Person bbox overlaps carton bbox        → CONTACT
Person + carton moving together          → HOLDING / MOVING
Carton near pallet                        → NEAR_PALLET
Carton transitions floor → elevated        → PICKUP
```

## Level 9 — Temporal Behaviour Engine

Start with state machines for: `Pickup, Drop, Drag, Throw, Placement,
Stacking`. Expand to the full 10-behaviour MVP set, then B11–B20 if time
allows (see `TECHNICAL_DEEP_DIVE.md` §6–7).

## Level 10 — Risk Engine

Implement deterministic scoring first (see `TECHNICAL_DEEP_DIVE.md` §10) via a
configuration table of `behaviour_severity, product_sensitivity, height_weight,
impact_weight, frequency_weight, location_weight`, editable from an admin
panel — never hard-coded in source.

## Level 11 — Alert Engine

```
Risk threshold → Temporal confirmation → Deduplication → Incident creation
→ WebSocket alert
```

## Level 12 — Evidence

Automatically extract pre-event / event / post-event clips + snapshot +
trajectory on incident creation (required for incident visualization/evidence
per the challenge brief).

## Level 13 — Replay

Build a video player overlay showing original video, bounding boxes, track
IDs, trajectory, behaviour state, and risk escalation timeline.

## Level 14 — Damage Prediction

Start with a structured model (XGBoost/LightGBM) over `drop height, velocity,
impact, product fragility, behaviour, surface, stack configuration` — this is
preferable to a deep network for tabular risk/damage prediction.

## Level 15 — Analytics

KPI cards, line/bar charts, heatmaps, risk/behaviour trends, zone analytics —
wired to real `incidents`/`behaviour_events` data.

## Level 16 — Root Cause

Start with explainable rule-based candidates (e.g. repeated event + same zone +
peak time + high congestion ⇒ "likely workflow/congestion contributor"),
explicitly labelled as **AI-inferred**, never presented as fact.

## Level 17 — AI Assistant

```
User query → intent → SQL (tool-called, not LLM-generated freeform)
→ vector retrieval (pgvector) → evidence → LLM → grounded answer
```
Implement the 5 baseline queries first (today's high-risk events; most common
behaviour; riskiest bay; "why HIGH risk?"; recommended action) before anything
more elaborate.

## Level 18 — Human Review

Build the review page: video + AI classification + confidence + risk +
evidence, reviewer marks `Correct / Incorrect / Changed / Uncertain`. Persist
every correction.

## Level 19 — Active Learning

```
Review Queue → Label Store → Dataset Version → Training Queue → Evaluation
→ Model Registry
```
No model auto-deploys purely from being retrained — always requires human
approval.

## Level 20 — Digital Twin

2D warehouse layout; connect real incidents to map coordinates.

## Level 21 — Voice (Tamil/English) — only after the text assistant is reliable

```
Tamil/English STT → Assistant → Tamil/English TTS
```

## Level 22 — Security

JWT, RBAC (server-enforced), audit logging, encryption in transit (TLS), access
control on evidence URLs, rate limiting.

## Level 23 — Testing

Backend: Pytest. Frontend: Vitest. E2E: Playwright. AI: dedicated evaluation
datasets. Integration: `Video → AI → Database → Alert → Frontend`.
See `TESTING_STRATEGY.md`.

## Level 24 — Deployment

```bash
docker compose up --build
```
Services: `frontend, backend, ai-worker, postgres, redis, minio, prometheus,
grafana`. GPU: `nvidia-docker`/CUDA runtime for the `ai-worker` service. See
`DEPLOYMENT_GUIDE.md`.

## Recommended Vertical-Slice Order (if you only remember one thing)

```
Slice 1  Video → Detection → Display
Slice 2  + Tracking → Display trajectory
Slice 3  + Interaction → Drop detection
Slice 4  + Risk → Alert
Slice 5  + Evidence → Replay
Slice 6  + Root cause → Recommendation
Slice 7  + Incident database → AI assistant
Slice 8  + Human review → Dataset → Learning
```
Milestone to aim for first: **get one video → detect one carton → track it →
recognize one drop → calculate risk → create incident → display it on the
dashboard.** Then expand 1 behaviour → 5 → 10 → AI assistant → analytics →
advanced innovation.

## Definition of "Finished" (MVP)

```
[ ] Upload video
[ ] Process video
[ ] Detect objects
[ ] Track objects
[ ] Understand behaviour
[ ] Detect 10 scenarios
[ ] Calculate risk
[ ] Generate incident
[ ] Extract evidence clip
[ ] Alert supervisor
[ ] Show incident dashboard
[ ] Explain incident
[ ] Recommend action
[ ] Generate analytics
[ ] Answer supervisor questions
```

## Priority Tiers If Time Runs Short

```
P0 (must-have):    Video upload, detection, tracking, 5 reliable behaviours,
                   risk scoring, incident generation, dashboard, replay
P1 (strong entry): 10 behaviours, real-time alerts, AI assistant, analytics,
                   recommendations
P2 (innovation):   Heatmaps, predictive risk, forklift/pedestrian conflict,
                   loading-sequence verification
P3 (future):       Digital twin, multi-camera, WMS integration, advanced
                   predictive models
```
