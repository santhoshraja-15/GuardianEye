# GUARDIAN EYE

### AI-Powered Warehouse Behaviour, Risk, Damage Prevention & Operational Intelligence Platform

[![CI Pipeline](https://github.com/santhoshraja-15/GuardianEye/actions/workflows/ci.yml/badge.svg)](https://github.com/santhoshraja-15/GuardianEye/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3.0-EE4C2C?logo=pytorch)](https://pytorch.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?logo=postgresql)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Executive Overview

**GuardianEye** is a real-time, closed-loop computer vision and behavioural intelligence platform engineered to transform warehouse video streams into proactive risk mitigation, automated evidence capture, root-cause attribution, and preventive operational insights.

Unlike legacy CCTV surveillance systems that only record historical incidents or basic bounding-box detectors, GuardianEye implements an 8-stage transformation paradigm:

```
SEE -> TRACK -> UNDERSTAND -> ASSESS -> PREDICT -> EXPLAIN -> PREVENT -> LEARN
```

```
VIDEO
  |
  v
VIDEO PROCESSING (Decoupled FPS decoding, corrupt frame recovery)
  |
  v
OBJECT DETECTION (YOLO: Person, Carton, Pallet, Trolley, Forklift, Equipment)
  |
  v
OBJECT TRACKING (ByteTrack: Persistent IDs, velocity, trajectories)
  |
  v
SPATIAL & INTERACTION UNDERSTANDING (Zones, Proximity, Holding, Contact states)
  |
  v
TEMPORAL REASONING (Multi-frame state machines, occlusion recovery)
  |
  v
BEHAVIOUR INTELLIGENCE (B01-B10 Core Scenarios & Behaviour DNA)
  |
  v
CONTEXT & DETERMINISTIC RISK ENGINE (Low / Medium / High / Critical with factor breakdown)
  |
  v
DAMAGE PREDICTION (Packaging deformation, breakage, abrasion probability)
  |
  v
ALERT & INCIDENT MANAGEMENT (Deduplication, state lifecycle, WebSocket push)
  |
  v
EVIDENCE & REPLAY STUDIO (Frame snapshots, pre/post clips, SHA256 integrity)
  |
  v
ROOT CAUSE & PREVENTION ENGINE (Process, equipment, layout, counterfactuals)
  |
  v
GROUNDED AI ASSISTANT & ACTIVE LEARNING (Database tools, pgvector similarity, review queue)
```

---

## 2. Core Behaviour Taxonomy (MVP B01–B10)

| ID | Behaviour Name | Detection Method | Typical Warehouse Risk |
|---|---|---|---|
| **B01** | Product Drop | Rapid downward vertical velocity ($v_y > v_{drop}$) + impact | High / Critical packaging or internal product breakage |
| **B02** | Dragging | Horizontal displacement on floor without mechanical equipment | High abrasion / package tearing |
| **B03** | Throwing | Release at high velocity with ballistic parabolic trajectory | Severe impact / catastrophic content destruction |
| **B04** | Rough Handling | High instantaneous acceleration ($|a| > a_{thresh}$) or sharp angle reversals | Concealed shock damage / calibration loss |
| **B05** | Improper Stacking | Heavy item placed on lighter item, or orientation axis violation | Lower carton crushing / structural stack failure |
| **B06** | Unstable Stacking | Stack tilt angle $\theta > 15^\circ$ or horizontal overhang ratio $> 20\%$ | Progressive stack collapse / worker hazard |
| **B07** | Incorrect Placement | Storage outside designated safe polygon zones | Traffic obstruction / fire exit hazard |
| **B08** | Handling Without Equipment | Manual lifting of heavy parcels ($m > 25\text{kg}$) without mechanical aid | Worker ergonomic injury & dropped load risk |
| **B09** | Incorrect Pallet Position | Misaligned fork engagement ($\Delta\phi > 12^\circ$) or insufficient depth | Pallet puncture / tipping load |
| **B10** | Unsafe Loading Sequence | Upper tier staging before foundational base is secured in loading bay | In-transit shifting / vehicle unbalance |

---

## 3. Technology Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16 + pgvector, Redis, Celery, JWT.
- **AI & Vision:** PyTorch, Ultralytics YOLOv8/v11, OpenCV, FFmpeg, ByteTrack, NumPy, Pandas, scikit-learn.
- **Frontend (Part II):** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, Recharts, WebSockets.
- **Storage & Telemetry:** MinIO (S3 compatible), Docker Compose, Prometheus, Grafana.
- **Testing:** Pytest, pytest-asyncio, HTTPX, Golden Scenario Benchmarks, Negative Control Harness.

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python 3.11 or higher
- Docker & Docker Compose
- FFmpeg installed on system PATH (optional for local standalone, included in Docker)

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/santhoshraja-15/GuardianEye.git
cd GuardianEye

# Copy environment template
cp .env.example .env

# Start infrastructure services (PostgreSQL, Redis, MinIO)
docker compose up -d postgres redis minio

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Running Backend & Processing Worker
```bash
# Start FastAPI API server (http://localhost:8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery Worker for asynchronous video processing
celery -A backend.workers.celery_app worker --loglevel=info
```

### Running Automated Test Suite
```bash
# Run complete test suite with coverage
pytest tests/ -v --cov=backend --cov=ai
```

---

## 5. Project Structure

```
GuardianEye/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── docs/                      # Comprehensive technical & architectural documentation
│   ├── 01-requirements/       # PRD & Functional Requirements
│   ├── 02-system-design/      # System architecture & dataflow
│   ├── 03-ai-methodology/     # Mathematical & CV algorithmic deep dive
│   ├── 04-behaviour-taxonomy/ # B01-B20 Behaviour specifications
│   ├── 05-database/           # PostgreSQL relational schema & pgvector
│   ├── 06-api/                # REST & WebSocket endpoint contracts
│   ├── 07-ai-assistant/       # Grounded Q&A assistant specifications
│   ├── 08-data/               # Video metadata & dataset governance
│   ├── 09-testing/            # Testing strategy, golden & negative test plans
│   ├── 10-security-privacy/   # Security controls & responsible AI policies
│   ├── 11-deployment/         # Docker Compose & production deployment
│   ├── 12-project-management/ # Roadmap & project control
│   ├── build-audits/          # Mandatory Level-by-Level Audit Reports
│   └── decisions/             # Architecture Decision Records (ADRs)
│
├── backend/                   # FastAPI Backend Application
│   ├── app/
│   │   ├── api/v1/            # API Route controllers & WebSockets
│   │   ├── core/              # Configuration, security, logging, monitoring
│   │   ├── models/            # SQLAlchemy 2.0 ORM Entities
│   │   ├── schemas/           # Pydantic v2 validation models
│   │   ├── services/          # Business logic & domain services
│   │   └── workers/           # Background tasks & Celery queues
│   ├── migrations/            # Alembic database migrations
│   ├── tests/                 # Backend unit & integration tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── ai/                        # 5-Layer AI & Computer Vision Intelligence
│   ├── preprocessing/         # Video loading, decoding, frame extraction
│   ├── perception/            # YOLO detection models & privacy blur filters
│   ├── tracking/              # ByteTrack multi-object tracking & Kalman filters
│   ├── spatial/               # Polygon zone geometry & distance calculation
│   ├── interaction/           # Human-Object interaction state graphs
│   ├── temporal/              # Temporal state machines & sequence models
│   ├── behaviour/             # B01-B10 Behaviour detection engines & DNA
│   ├── context/               # Context enrichment engine
│   ├── risk/                  # Deterministic & auditable risk scoring
│   ├── damage/                # Damage probability & category prediction
│   ├── prediction/            # Predictive risk forecasting
│   ├── prevention/            # Root cause, recommendations & counterfactuals
│   ├── evidence/              # Evidence packaging & replay data streams
│   ├── assistant/             # Grounded LLM agent & pgvector embeddings
│   ├── learning/              # Active learning & human review pipelines
│   └── evaluation/            # Golden scenario & negative control harnesses
│
├── data/                      # Dataset versioning & metadata manifests
├── models/                    # Model registry & weights
├── videos/                    # Input, golden, negative control test videos
├── storage/                   # Local evidence & snapshot storage directory
└── tests/                     # System-wide test suite
```

---

## 6. Responsible AI & Governance

GuardianEye is committed to ethical AI principles:
- **Operational Behaviour Focus:** Focuses exclusively on package safety, ergonomic handling, and operational workflow risk.
- **No Biometric Identification:** No facial recognition or individual worker surveillance by default.
- **Deterministic Risk Auditing:** Risk scores are calculated using transparent, auditable mathematical formulas—never ungrounded generative LLM guesses.
- **Human in the Loop:** All critical operational interventions and active learning dataset promotions require supervisor sign-off.

---

## 7. License

Distributed under the MIT License. See `LICENSE` for more information.
