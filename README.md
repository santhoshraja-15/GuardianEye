# 🛡️ GuardianEye

### AI-Powered Warehouse Behaviour, Risk, Damage Prevention & Operational Intelligence Platform

[![CI Pipeline](https://github.com/santhoshraja-15/GuardianEye/actions/workflows/ci.yml/badge.svg)](https://github.com/santhoshraja-15/GuardianEye/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GuardianEye turns ordinary warehouse CCTV video into a real-time, closed-loop **behaviour, risk, and damage-prevention command center**. It watches the same footage a warehouse already records, but instead of just archiving it, it tracks every person and object, understands *what they're doing*, scores the operational risk of that action, predicts the likely physical damage, packages tamper-evident evidence, and explains the root cause — so a supervisor can act before the loss happens, not after.

Unlike legacy CCTV surveillance that only stores footage or flags generic motion, GuardianEye runs an 8-stage transformation pipeline end to end:

```
SEE → TRACK → UNDERSTAND → ASSESS → PREDICT → EXPLAIN → PREVENT → LEARN
```

> **Note on access control:** the platform currently runs in **open-access mode** — `get_current_user` resolves a bearer token when one is supplied, and otherwise transparently falls back to the default system operator, so every route is reachable without a login screen. JWT auth, password hashing, and role-checking scaffolding remain in place in `backend/app/api/deps.py` and `backend/app/api/v1/auth.py` for whenever RBAC is turned back on.

---

## 📋 Table of Contents

- [Core Capabilities](#-core-capabilities)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Behaviour Taxonomy (B01–B20)](#-behaviour-taxonomy-b01b20)
- [Deterministic Risk & Damage Engine](#-deterministic-risk--damage-engine)
- [Spatial Intelligence, Digital Twin & Calibration](#-spatial-intelligence-digital-twin--calibration)
- [Evidence, Replay & Prevention](#-evidence-replay--prevention)
- [Grounded AI Assistant](#-grounded-ai-assistant)
- [Frontend Command Center](#-frontend-command-center)
- [Installation](#️-installation)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Responsible AI & Governance](#-responsible-ai--governance)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🚀 Core Capabilities

| Feature | Description |
|---|---|
| 🎯 **Behaviour Detection (B01–B20)** | 20 deterministic behaviour detectors — drops, throws, unsafe stacking, aisle obstruction, unsafe lifting posture, and more — driven by tracked velocity, acceleration, geometry, and zone context, not black-box guesses |
| 🧮 **Deterministic Risk Engine** | Auditable 0–100 risk score computed from an explicit formula (base severity × behaviour weight × height/speed factors × fragility, zone, and fatigue multipliers) — every score is explainable, never an opaque model output |
| 💥 **Damage Prediction** | Estimates damage probability and damage type (crush, impact, abrasion, breakage) from kinetic energy, drop height, packaging fragility, and floor conditions |
| 🧭 **Spatial Intelligence & Camera Calibration** | Operators click point correspondences between video pixels and real warehouse meters; GuardianEye solves the homography once and reuses it to place every detection in true world coordinates |
| 🗺️ **Digital Twin** | Live 2D warehouse topology — zones, camera viewpoints, and current risk heatmap — reconstructed from calibrated spatial data |
| 📈 **Temporal Analytics** | Shift-over-shift and period-over-period comparisons ("today vs. yesterday", "is risk increasing?") computed from real aggregates over resolved time windows |
| 🧬 **Behaviour DNA** | Per-track feature-vector fingerprinting for similarity search and pattern comparison across incidents |
| 🧾 **Evidence & Replay Studio** | Frame snapshots, pre/post-event clips, and SHA-256 integrity hashing so every incident ships with a tamper-evident evidence package |
| 🛠️ **Root-Cause & Prevention Engine** | Attributes incidents to process, equipment, or layout causes and generates counterfactual, actionable SOP recommendations |
| 🤖 **Grounded AI Copilot** | Answers operational questions from real database aggregates only — zero-hallucination by design, with an optional LLM layer that may rephrase but never originate a fact |
| 🧑‍⚖️ **Human Review & Active Learning** | Supervisor-in-the-loop review queue that can promote reviewed clips into the training/evaluation dataset |
| 🖥️ **11-Page Command Center UI** | Overview, Live Streams, Video Intelligence, Incident Board, Evidence Vault, Prevention Studio, Digital Twin, Camera Calibration, Behaviour DNA, Analytics, and Human Review — all real-time, WebSocket-backed |

---

## 🧠 Technology Stack

### Backend
```
FastAPI              → Async Python web framework (REST + WebSocket)
Pydantic v2           → Request/response validation & settings
SQLAlchemy 2.0        → ORM (typed, Mapped[] declarative models)
Alembic               → Database migrations
PostgreSQL 16         → Primary relational store
pgvector              → Vector similarity search (Behaviour DNA, assistant grounding)
Redis + Celery        → Async task queue for video processing workers
python-jose / passlib → JWT + password hashing (RBAC scaffolding)
MinIO                 → S3-compatible object storage for evidence media
Prometheus            → Metrics & monitoring hooks
```

### AI & Computer Vision
```
PyTorch               → Deep learning runtime
Ultralytics YOLOv8/v11 → Object detection (person, carton, pallet, trolley, forklift)
ByteTrack              → Multi-object tracking with persistent IDs & Kalman filtering
OpenCV + FFmpeg        → Video decoding, frame extraction, corrupt-frame recovery
NumPy / SciPy / pandas → Numerical & statistical processing
scikit-learn           → Feature engineering & similarity utilities
```

### Frontend
```
React 19 + TypeScript  → Component-based, type-safe UI
Vite 8                 → Dev server & build tooling
Tailwind CSS 4          → Utility-first styling
Zustand                 → Client state (sidebar, connection, warehouse selection)
TanStack Query          → Server-state caching & data fetching
React Router 7          → Client-side routing
Recharts                → Risk trend, distribution & heatmap charts
Framer Motion            → Page transitions & micro-interactions
React Hook Form + Zod    → Form state & schema validation
Axios                    → HTTP client
```

### Testing & Quality
```
Pytest + pytest-asyncio + pytest-cov  → Backend unit/integration tests + coverage
ruff                                  → Python linting
Vitest + Testing Library              → Frontend unit tests
Playwright + axe-core                 → Frontend E2E and accessibility tests
oxlint                                → Frontend linting
GitHub Actions                        → CI pipeline
```

### Infrastructure
```
Docker Compose  → postgres, redis, minio, backend, worker services
Makefile        → install / up / down / test / lint / migrate shortcuts
```

---

## 📐 System Architecture

### Pipeline Overview

```
VIDEO
  │
  ▼
VIDEO PROCESSING          Decoupled FPS decoding, corrupt frame recovery
  │
  ▼
OBJECT DETECTION          YOLO: Person, Carton, Pallet, Trolley, Forklift, Equipment
  │
  ▼
OBJECT TRACKING           ByteTrack: persistent IDs, velocity, trajectories
  │
  ▼
SPATIAL & INTERACTION     Zones, proximity, holding/contact states, calibrated
UNDERSTANDING             world coordinates via solved camera homography
  │
  ▼
TEMPORAL REASONING        Multi-frame state machines, occlusion recovery
  │
  ▼
BEHAVIOUR INTELLIGENCE    B01–B20 detectors & Behaviour DNA fingerprinting
  │
  ▼
CONTEXT & DETERMINISTIC   Low / Medium / High / Critical, full factor
RISK ENGINE               breakdown, fully auditable formula
  │
  ▼
DAMAGE PREDICTION         Packaging deformation, breakage, abrasion probability
  │
  ▼
ALERT & INCIDENT          Deduplication, lifecycle state machine, WebSocket
MANAGEMENT                push to the live dashboard
  │
  ▼
EVIDENCE & REPLAY STUDIO  Frame snapshots, pre/post clips, SHA-256 integrity
  │
  ▼
ROOT CAUSE & PREVENTION   Process / equipment / layout attribution +
ENGINE                    counterfactual recommendations
  │
  ▼
GROUNDED AI ASSISTANT &   Database-grounded Q&A, pgvector similarity,
ACTIVE LEARNING           human review queue feeding the training set
```

### Service Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                            │
│   Dashboard · Live Streams · Incident Board · Evidence Vault ·   │
│   Prevention Studio · Digital Twin · Calibration · DNA Explorer  │
│   · Analytics · Human Review           (WebSocket + REST)        │
└───────────────────────────────┬──────────────────────────────────┘
                                 │ HTTP/REST + WS
┌───────────────────────────────▼──────────────────────────────────┐
│                        FASTAPI BACKEND                            │
│  /videos /tracks /zones /cameras /events /interactions            │
│  /behaviours /risks /alerts /incidents /evidence /replay          │
│  /analytics /digital-twin /assistant /reviews /learning           │
│  /prevention /ws (realtime)                                       │
│                                                                     │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────────┐    │
│  │  API Routers   │─►│ Service Layer  │─►│  SQLAlchemy Models │    │
│  └───────────────┘  └───────┬────────┘  └───────────────────┘    │
└──────────────────────────────┼─────────────────────────────────────┘
                                │
                  ┌─────────────┼──────────────┬───────────────┐
                  ▼             ▼              ▼               ▼
          ┌───────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐
          │  ai/ 5-   │ │ PostgreSQL  │ │ Redis +     │ │  MinIO    │
          │  layer CV │ │ + pgvector  │ │ Celery      │ │ (evidence │
          │  pipeline │ │             │ │ worker      │ │  storage) │
          └───────────┘ └─────────────┘ └─────────────┘ └───────────┘
```

---

## 🎯 Behaviour Taxonomy (B01–B20)

Every behaviour detector lives in `ai/behaviour/behaviour_engine.py`, is typed in `ai/behaviour/behaviour_schemas.py`, and carries an explicit risk weight in `ai/risk/risk_taxonomy.py` — no behaviour silently inherits an undocumented default weight.

| ID | Behaviour | Typical Trigger | Operational Risk |
|---|---|---|---|
| **B01** | Product Drop | Rapid downward velocity + impact | Packaging / internal product breakage |
| **B02** | Dragging | Horizontal floor displacement without equipment | Abrasion / package tearing |
| **B03** | Throwing | High-velocity release, ballistic trajectory | Severe impact / content destruction |
| **B04** | Rough Handling | High instantaneous acceleration while held | Concealed shock damage |
| **B05** | Improper Stacking | Heavy-on-light or axis-violation placement | Lower carton crushing |
| **B06** | Unstable Stack | Excess tilt angle or overhang ratio | Progressive stack collapse |
| **B07** | Incorrect Placement | Storage outside designated safe zone polygon | Traffic / fire-exit obstruction |
| **B08** | Equipment Misuse | Manual lifting of heavy loads without mechanical aid | Ergonomic injury / dropped load |
| **B09** | Pallet Misalignment | Misaligned fork engagement or insufficient depth | Pallet puncture / tipping |
| **B10** | Loading Sequence Violation | Upper tier staged before base is secured | In-transit shifting / imbalance |
| **B11** | Stepping on Carton | Person weight-bearing on a package | Crush damage / fall hazard |
| **B12** | Kicking Product | Foot-applied impulse to a package | Impact damage |
| **B13** | Rolling Carton | Carton rolled instead of carried/lifted | Compression damage, seal failure |
| **B14** | Crushing Under Load | Excess load weight on a lower item | Structural product failure |
| **B15** | Wet Floor Dragging | Dragging detected on a flagged wet-floor zone | Elevated abrasion + slip hazard |
| **B16** | Aisle Obstruction | Object left blocking a designated aisle/exit | Safety & traffic-flow hazard |
| **B17** | Overloading Pallet | Pallet load exceeds safe weight/height profile | Pallet failure / tipping |
| **B18** | Unsecured Transit | Load moved without securing/strapping | In-transit shifting or fall |
| **B19** | Improper Lifting Posture | Ergonomically unsafe manual lift detected | Worker musculoskeletal injury |
| **B20** | Collision Risk | Converging trajectories between tracked entities | Equipment/personnel collision |

---

## 🧮 Deterministic Risk & Damage Engine

GuardianEye deliberately avoids opaque, ungrounded model scores for risk. `ai/risk/risk_engine.py` computes every incident's risk using an explicit, auditable formula:

```
Score = Clamp(
  (BaseSeverity × BehaviourWeight
     + (Height / MaxSafeHeight) × HeightWeight
     + (Speed / SpeedLimit) × SpeedWeight)
  × FragilityMultiplier
  × ZoneMultiplier
  × FatigueMultiplier
)
```

- **BaseSeverity** — LOW (20) / MEDIUM (45) / HIGH (70) / CRITICAL (90), from the detector's severity classification.
- **BehaviourWeight** — a per-behaviour-type weight sourced from the centralized `RISK_TAXONOMY` (all 20 behaviour types, explicit, documented — see [`ai/risk/risk_taxonomy.py`](ai/risk/risk_taxonomy.py)).
- **Fragility / Zone / Fatigue multipliers** — contextual factors pulled from the product catalogue, zone risk profile, and shift/fatigue context (`ai/context/context_enricher.py`).

Every factor that contributed to the final score is returned as a `RiskFormulaBreakdown` — the UI's Incident Board and Analytics pages render this breakdown directly, so an investigator can see *why* a score is what it is, not just the number.

`ai/damage/damage_predictor.py` runs alongside the risk engine to estimate **damage probability** and **damage type** (impact, crush, abrasion, breakage, or no observed damage) from kinetic-energy approximations (drop height, floor friction on drags, load pressure on stacks) combined with the product's fragility rating and unit value — feeding the "Potential Damage Exposure" figure on the Overview dashboard.

---

## 🧭 Spatial Intelligence, Digital Twin & Calibration

- **Camera calibration** (`/calibration` page, `backend/app/models/calibration.py`): an operator clicks matching point pairs between the video frame and a real-world warehouse floor plan (pixels ↔ meters). GuardianEye solves the homography once (`ai/spatial/coordinate_transform.py`) and persists it, so every subsequent detection from that camera is converted into true world coordinates without re-deriving the transform on each request.
- **Zone geometry** (`ai/spatial/zone_geometry.py`): polygon-based safe zones, restricted zones, and aisle definitions that behaviour detectors (B07 incorrect placement, B16 aisle obstruction) test detections against.
- **Digital Twin** (`/digital-twin` page, `GET /api/v1/digital-twin/topology`): renders the warehouse's live 2D topology — zones, camera viewpoints, and the current risk heatmap — reconstructed entirely from calibrated spatial data and recent events.
- **Temporal analytics**: the `temporal_analytics_service` aggregates events over resolved time windows so the dashboard and assistant can answer shift-over-shift and period-over-period questions ("is risk increasing?", "today vs. yesterday") from real numbers, not estimates.

---

## 🧾 Evidence, Replay & Prevention

**Evidence Vault** (`ai/evidence/evidence_generator.py`, `/evidence` page)
- Captures frame snapshots and pre/post-event clips around every incident.
- Computes a **SHA-256 integrity hash** for each evidence artifact at generation time, so any later modification is detectable.
- Serves evidence per-incident via `GET /api/v1/evidence/incident/{incident_id}`.

**Replay Studio** (`/api/v1/replay/{incident_id}`)
- Reconstructs a frame-by-frame replay stream around the incident window for investigator review.

**Prevention Engine** (`ai/prevention/prevention_engine.py`, `/prevention` page)
- Attributes each incident to a likely root cause category — process, equipment, or layout.
- Generates counterfactual recommendations ("if the pallet had been staged 0.4m further from the aisle, this would not have triggered B16") and maps them to actionable SOP rules operators can track and mark resolved.

---

## 🤖 Grounded AI Assistant

The Copilot (`backend/app/services/assistant_service.py`, `/api/v1/assistant/chat` & `/query`) is built specifically to avoid hallucination:

```
Question → Intent → Time Range(s) → Event Query → Aggregation → Insight → Response
```

- Comparative/temporal questions ("compare today vs. yesterday", "what changed this shift?", "is risk increasing?") are resolved through a dedicated intent layer backed by the same reusable temporal-analytics period aggregation the Analytics page uses — not ad-hoc keyword branches.
- **Every number in a response is a real aggregate for the resolved time window.** If a window has no data, the assistant says so rather than guessing.
- An optional LLM provider (`llm_provider.py`) may rephrase already-computed facts into more natural prose — it is never allowed to originate a fact. With no provider configured (the default), the assistant runs entirely off deterministic templates and real database queries: zero outbound network calls, zero hallucination surface.

---

## 🖥️ Frontend Command Center

An 11-page single-page app (`frontend/src/routes/index.tsx`), all served from one fixed shell (sidebar + header stay put; only content panels scroll):

| Route | Page | Purpose |
|---|---|---|
| `/` | Overview | Command-center KPIs, risk intelligence, open incident queue, live timeline |
| `/live` | Live Streams | Multi-camera live view, in-frame objects, active tracks, alerts |
| `/analysis` | Video Intelligence | Ingested CCTV stream library and per-video analysis |
| `/incidents` | Incident Board | Filterable, paginated incident table with lifecycle status |
| `/evidence` | Evidence Vault | Per-incident evidence artifacts with integrity hashes |
| `/prevention` | Prevention Studio | Root-cause recommendations and behaviour rule management |
| `/digital-twin` | Digital Twin | Live 2D warehouse topology, zones, and risk heatmap |
| `/calibration` | Camera Calibration | Point-correspondence calibration workflow per camera |
| `/dna` | Behaviour DNA | 32-dimensional feature-vector fingerprint explorer |
| `/analytics` | Analytics | Risk trend, hotspot drill-down, and incident correlation |
| `/human-review` | Human Review | Supervisor review queue feeding active learning |

The `/welcome` route serves a standalone marketing landing page outside the authenticated app shell.

---

## ⚙️ Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- FFmpeg on system PATH (optional locally — bundled in the Docker image)

### 1. Clone & configure
```bash
git clone https://github.com/santhoshraja-15/GuardianEye.git
cd GuardianEye
cp .env.example .env
```

### 2. Start infrastructure services
```bash
docker compose up -d postgres redis minio
```

### 3. Backend
```bash
pip install -r backend/requirements.txt

# Run the API server (http://localhost:8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Run the async video-processing worker (separate terminal)
celery -A backend.workers.celery_app worker --loglevel=info
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev   # http://localhost:3000 (or next free port)
```

### Makefile shortcuts
```bash
make install   # install backend + frontend dependencies
make up        # docker compose up (postgres, redis, minio, backend, worker)
make down      # stop the stack
make migrate   # run Alembic migrations
make test      # run the full test suite
make lint      # ruff (backend) + oxlint (frontend)
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

All routes are mounted from `backend/app/api/v1/router.py`. Full interactive documentation — every request/response schema, live "try it out" testing — is available at **`http://localhost:8000/docs`** (Swagger UI) once the backend is running.

| Prefix | Tag | Covers |
|---|---|---|
| `/auth` | Authentication | Login, token issue/refresh (RBAC scaffolding; open-access by default) |
| `/users` | Users | Operator/user records |
| `/storage` | Storage | Signed upload/download against MinIO |
| `/videos` | Videos | CCTV stream ingestion & metadata |
| `/tracks` | Tracking | ByteTrack object tracks per video |
| `/zones` | Zones | Warehouse zone polygon geometry |
| `/cameras` | Cameras | Camera registry & viewpoints |
| `/events` | Spatial Events | Proximity/contact/interaction events |
| `/interactions` | Interactions | Human-object interaction states |
| `/behaviours` | Behaviours | `GET /behaviours/video/{video_id}` — detected behaviours for a video |
| `/risks` | Risks | `GET /risks/event/{behaviour_event_id}` — full risk formula breakdown |
| `/alerts` | Alerts | `GET /alerts`, `POST /alerts/acknowledge` |
| `/incidents` | Incidents | `GET /incidents`, `GET /incidents/{id}`, `POST /incidents`, `POST /incidents/status` |
| `/evidence` | Evidence | `GET /evidence/incident/{incident_id}` — evidence package + integrity hashes |
| `/replay` | Replay | `GET /replay/{incident_id}` — frame-by-frame incident replay stream |
| `/analytics` | Analytics | `GET /analytics/dashboard` — KPI, trend & hotspot aggregates |
| `/digital-twin` | Digital Twin | `GET /digital-twin/topology` — live spatial topology |
| `/assistant` | Assistant Copilot | `POST /assistant/chat`, `POST /assistant/query` — grounded Q&A |
| `/reviews` | Human Review | Review queue for supervisor sign-off |
| `/learning` | Learning & Models | Active-learning dataset promotion |
| `/prevention` | Prevention & SOPs | Root-cause recommendations & SOP rules |
| `/ws` | Realtime | WebSocket channel pushing live alerts/incidents to the dashboard |

---

## 📂 Project Structure

```
GuardianEye/
├── README.md
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env.example
│
├── backend/                   # FastAPI application
│   └── app/
│       ├── api/v1/            # Route controllers & WebSocket endpoint
│       ├── core/              # Config, security, logging, error handling
│       ├── database/          # Session management, additive schema sync
│       ├── models/            # SQLAlchemy 2.0 ORM entities
│       ├── schemas/           # Pydantic v2 request/response models
│       ├── services/          # Business logic (assistant, digital twin, temporal analytics, ...)
│       └── workers/           # Celery task definitions
│
├── ai/                        # Computer vision & behaviour intelligence pipeline
│   ├── preprocessing/         # Video loading, decoding, frame extraction
│   ├── perception/            # YOLO detection models
│   ├── tracking/               # ByteTrack multi-object tracking
│   ├── spatial/                # Zone geometry & camera coordinate transforms
│   ├── interaction/            # Human-object interaction state graphs
│   ├── temporal/                # Temporal state machines & sequence models
│   ├── behaviour/               # B01–B20 behaviour engine, schemas & DNA
│   ├── context/                 # Context enrichment (product, zone, fatigue)
│   ├── risk/                    # Deterministic risk engine & taxonomy
│   ├── damage/                  # Damage probability & type prediction
│   ├── prevention/              # Root-cause & prevention/SOP engine
│   ├── evidence/                # Evidence packaging & SHA-256 integrity
│   └── learning/                # Active learning dataset management
│
├── frontend/                  # React + TypeScript command-center UI
│   └── src/
│       ├── app/                # App shell (landing vs. authenticated layout)
│       ├── components/         # Layout, copilot, common UI components
│       ├── config/              # Page backgrounds & app config
│       ├── hooks/                # React Query hooks per domain
│       ├── layouts/              # AppLayout (sidebar + header shell)
│       ├── pages/                 # 11 command-center pages + landing page
│       ├── routes/                # Route table
│       ├── stores/                # Zustand stores (app/session state)
│       └── services/               # API client layer
│
├── docs/                      # Requirements, architecture, ADRs, build audits
├── data/                      # Dataset versioning & metadata manifests
├── models/                    # Model registry & weights
├── Sample videos/             # Golden & negative-control test videos
├── storage/                   # Local evidence & snapshot storage
└── tests/                     # System-wide test suite
```

---

## 🧪 Testing

```bash
# Full backend test suite with coverage
pytest tests/ -v --cov=backend --cov=ai

# Frontend unit tests
cd frontend && npm run test

# Frontend E2E + accessibility (Playwright + axe-core)
cd frontend && npm run test:e2e

# Linting
ruff check .            # backend
cd frontend && npm run lint   # frontend (oxlint)
```

CI runs the pipeline defined in `.github/workflows/ci.yml` on every push.

---

## 🛡️ Responsible AI & Governance

- **Operational behaviour focus** — GuardianEye analyzes package handling, stacking, and workflow safety, not individual worker identity.
- **No biometric identification** — no facial recognition or individual worker surveillance by default.
- **Deterministic, auditable risk scoring** — every risk score is a transparent formula with a returned factor breakdown, never an opaque generative-model guess.
- **Zero-hallucination assistant** — the Copilot answers strictly from real database aggregates; an optional LLM layer may rephrase, never originate, a fact.
- **Human in the loop** — incident dispositioning and active-learning dataset promotion require supervisor review via the Human Review queue.

---

## 🗺️ Roadmap

### Phase 1 — Current ✅
- [x] YOLO detection + ByteTrack multi-object tracking
- [x] B01–B20 behaviour detection engine
- [x] Deterministic risk & damage prediction engines
- [x] Camera calibration, spatial intelligence & digital twin
- [x] Evidence vault with SHA-256 integrity & replay studio
- [x] Root-cause & prevention/SOP engine
- [x] Grounded AI copilot with temporal analytics
- [x] Human review & active learning queue
- [x] 11-page real-time command-center UI

### Phase 2 — Planned
- [ ] Re-enable RBAC / multi-tenant authentication for production deployment
- [ ] Multi-warehouse fleet view & cross-site analytics
- [ ] Mobile-responsive supervisor app
- [ ] Model registry versioning & automated retraining from the active-learning queue
- [ ] Expanded behaviour taxonomy beyond B20

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
