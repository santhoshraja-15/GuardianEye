# Requirements & Prerequisites
## W-SAFE — Everything Needed Before You Start Building

## 1. Team Prerequisites

| Role | Skills Needed |
|---|---|
| AI/CV Lead | Python, PyTorch, OpenCV, object detection (YOLO), tracking (ByteTrack), basic geometry/motion math |
| Backend Engineer | Python, FastAPI, SQLAlchemy/Alembic, REST/WebSocket API design, Redis/Celery |
| Frontend Engineer | React, TypeScript, Tailwind, state management (Zustand), charting (Recharts) |
| Data/MLOps Engineer | Dataset annotation tooling, evaluation metrics, model registry concepts, Docker |
| (Shared) | Git/GitHub workflow, basic Docker, basic SQL |

## 2. Software Prerequisites

### Core tooling
- Git + GitHub account
- VS Code (or preferred IDE)
- Docker + Docker Compose
- Python 3.11+
- Node.js 18+ / npm or pnpm
- PostgreSQL 15+ (via Docker) with the `pgvector` extension
- Redis (via Docker)
- MinIO (via Docker) for local S3-compatible storage

### Python packages (backend + AI)
```
fastapi
uvicorn
pydantic
sqlalchemy
alembic
python-jose (JWT)
celery
redis
opencv-python
ffmpeg-python
torch / torchvision
ultralytics (YOLO)
numpy
pandas
psycopg2-binary
pgvector
boto3 (S3/MinIO client)
pytest
```
Always install with `pip install --break-system-packages` in constrained
environments (e.g. this sandbox); use a virtualenv for real development.

### Node packages (frontend)
```
react, react-dom
typescript
vite
tailwindcss
@tanstack/react-query
zustand
recharts
shadcn/ui (via CLI)
```

### AI/model prerequisites
- Pretrained YOLO weights (e.g. YOLOv8/YOLOv11 checkpoint) as a starting point for
  fine-tuning on warehouse object classes.
- ByteTrack reference implementation or an `ultralytics`-integrated tracker.
- An LLM API key (for the AI assistant) — any tool-calling-capable chat completion
  API.
- (Optional, Tier 3) Speech-to-text/text-to-speech service supporting Tamil +
  English.

## 3. Hardware Prerequisites

| Purpose | Minimum | Recommended |
|---|---|---|
| Development machine | 16 GB RAM, modern CPU | 32 GB RAM |
| Model inference | CPU-only (slow) works for dev | NVIDIA GPU (CUDA-capable, 8GB+ VRAM) |
| Video capture (pilot) | Any USB webcam / smartphone camera | Fixed CCTV-style camera + tripod |
| Controlled pilot props | Boxes, pallets/mini-pallets, a small trolley, tables to simulate racking, small toy vehicle | Same, plus multiple lighting conditions |

Development/testing without a GPU is possible (slower inference); production
demo benefits strongly from a CUDA GPU.

## 4. Data Prerequisites

- A small library of **recorded** warehouse-style videos (own footage from a
  controlled pilot environment is the safest option; otherwise properly licensed
  public/synthetic footage — never scrape copyrighted CCTV footage).
- A **golden test set** of 10–20 manually-labelled videos, one per behaviour
  scenario, used to regression-test every change (see `TESTING_STRATEGY.md`).
- Product metadata seed list: `product_type, fragility, weight, dimensions,
  handling_requirement, max_drop_height, stacking_limit, orientation_requirement,
  equipment_requirement`.
- Zone/polygon definitions for at least one pilot warehouse layout (loading bay,
  staging zone, storage zone, pedestrian lane, forklift lane, restricted zone).

## 5. Accounts / Access Prerequisites

- GitHub organization/repo access for the team.
- Cloud object storage account (S3 or equivalent) if deploying beyond local MinIO.
- LLM API provider account + key.
- (Optional) Cloud GPU provider account if local GPU is unavailable.
- Docker Hub (or equivalent registry) account for image publishing if deploying
  to a shared/cloud environment.

## 6. Conceptual Prerequisites (recommended reading before coding)

- Basic object detection concepts (bounding boxes, IoU, confidence, NMS).
- Basic multi-object tracking concepts (track ID assignment, occlusion handling).
- Basic finite state machine design.
- Basic risk-scoring / weighted-factor scoring concepts.
- Basic RAG (retrieval-augmented generation) concepts and tool-calling for LLMs.
- RBAC and audit-logging fundamentals.

## 7. Environment Variables Checklist (see `DEPLOYMENT_GUIDE.md` for full list)

```
DATABASE_URL=
REDIS_URL=
S3_ENDPOINT= / S3_ACCESS_KEY= / S3_SECRET_KEY= / S3_BUCKET=
JWT_SECRET=
LLM_API_KEY=
LLM_MODEL=
YOLO_WEIGHTS_PATH=
INFERENCE_DEVICE=cpu|cuda
DEFAULT_RISK_THRESHOLDS=
```

## 8. Definition of Ready (before Level 0 kicks off)

- [ ] Team roles assigned (see `PROJECT_CONTROL_DOCUMENT.md`)
- [ ] Repo created with branch strategy agreed
- [ ] Docker + Python + Node installed on every machine
- [ ] At least 3–5 sample warehouse videos available for early pipeline testing
- [ ] MVP object classes and 10-behaviour list frozen (see `PRD.md` §7)
- [ ] LLM API key provisioned
- [ ] Everyone has read `PRD.md`, `LAYER_ARCHITECTURE.md`, and `TECH_STACK.md`
