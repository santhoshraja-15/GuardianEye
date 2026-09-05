# System Design Document
## W-SAFE — Component Design, Deployment Topology

## 1. High-Level Architecture

```
                     ┌─────────────────────────────┐
                     │       VIDEO SOURCES          │
                     │ CCTV / RTSP / VMS / MP4      │
                     │ Webcam / Smartphone          │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │    VIDEO SOURCE ADAPTER      │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │     VIDEO PROCESSING         │
                     │ FFmpeg + OpenCV              │
                     └──────────────┬──────────────┘
                                    ▼
              ┌──────────────────────────────────────────┐
              │              AI PERCEPTION                │
              │ YOLO Detector + Classification Models     │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │          MULTI-OBJECT TRACKING            │
              │ ByteTrack + Track IDs + Motion Features   │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │        SCENE UNDERSTANDING ENGINE          │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │      HUMAN-OBJECT INTERACTION ENGINE       │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │       TEMPORAL BEHAVIOUR ENGINE             │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │          INTERACTION GRAPH                  │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │             CONTEXT ENGINE                  │
              └────────────────────┬─────────────────────┘
                                   ▼
              ┌──────────────────────────────────────────┐
              │            RISK ENGINE                      │
              └────────────────────┬─────────────────────┘
                  ┌────────────────┼─────────────────┐
                  ▼                ▼                 ▼
          ┌──────────────┐ ┌───────────────┐ ┌──────────────┐
          │ DAMAGE       │ │ ALERT &       │ │ PREDICTIVE   │
          │ PREDICTION   │ │ INCIDENT      │ │ RISK ENGINE  │
          └──────┬───────┘ └──────┬────────┘ └──────┬───────┘
                 └────────────────┼─────────────────┘
                                  ▼
                    ┌──────────────────────────┐
                    │     EVIDENCE ENGINE       │
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ ROOT CAUSE + PREVENTION   │
                    │ + Counterfactual Analysis │
                    └────────────┬─────────────┘
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
       │ SUPERVISOR  │    │ AI          │    │ ANALYTICS /  │
       │ DASHBOARD   │    │ ASSISTANT   │    │ DIGITAL TWIN │
       └─────────────┘    └─────────────┘    └──────────────┘
              └──────────────────┼──────────────────┘
                                 ▼
                     ┌──────────────────────────┐
                     │     HUMAN REVIEW          │
                     └────────────┬─────────────┘
                                  ▼
                     ┌──────────────────────────┐
                     │     ACTIVE LEARNING       │
                     │ Dataset → Training →      │
                     │ Evaluation → Registry     │
                     └──────────────────────────┘
```

## 2. Deployment Topology

```
                    INTERNET / LAN
                          │
                  ┌───────▼─────────┐
                  │ Reverse Proxy    │
                  └───────┬─────────┘
              ┌───────────┴───────────┐
              ▼                       ▼
        React Frontend            FastAPI
                                      │
                  ┌───────────────────┼───────────────┐
                  ▼                   ▼               ▼
               Redis             PostgreSQL          MinIO
                  │                   │                │
                  ▼                   │                │
             Celery Worker            │                │
                  │                   │                │
                  ▼                   │                │
          AI/CV Pipeline ─────────────┴────────────────┘
                  │
                  ▼
            Model Registry
                  │
                  ▼
          Human Review / Learning

Monitoring: Prometheus → Grafana
```

## 3. Services / Containers

| Service | Responsibility |
|---|---|
| `frontend` | React SPA served via Vite build / static server |
| `backend` | FastAPI app — auth, REST APIs, WebSocket server |
| `ai-worker` | Celery worker running the CV pipeline (detection→tracking→behaviour→risk→damage) |
| `postgres` | Primary relational DB + pgvector extension |
| `redis` | Job queue + cache + WebSocket pub/sub + alert cooldowns |
| `minio` | S3-compatible object storage (videos, clips, snapshots, model artifacts) |
| `prometheus` | Metrics collection |
| `grafana` | Metrics dashboards |

## 4. Backend Module Layout

```
backend/app/
 ├── api/            # route handlers grouped by resource (see API_SPECIFICATION.md)
 ├── models/         # SQLAlchemy ORM models
 ├── schemas/        # Pydantic request/response schemas
 ├── services/       # business logic (risk calc orchestration, alert dedup, etc.)
 ├── database/       # session/engine setup, migrations (Alembic)
 ├── websocket/       # connection manager + event broadcast
 └── main.py         # app factory, router registration, startup/shutdown hooks
```

## 5. AI Pipeline Module Layout

```
ai/
 ├── detection/      # YOLO wrapper, class map, confidence/NMS config
 ├── tracking/       # ByteTrack wrapper, track state machine (ACTIVE/LOST/REACQUIRED)
 ├── behaviour/       # per-behaviour detectors (Drop/Drag/Throw/Stacking/etc.)
 ├── risk/            # deterministic risk scoring + (later) ML risk model
 ├── preprocessing/    # video decode, frame sampling, resize, timestamp sync
 └── inference/         # pipeline orchestrator tying detection→tracking→behaviour→risk
```

## 6. Real-Time Communication Design

WebSocket channel `/ws/events` broadcasts:
```
NEW_INCIDENT
RISK_ESCALATED
ALERT_CREATED
CAMERA_OFFLINE
PROCESSING_COMPLETE
REVIEW_REQUIRED
```
Connection manager keyed by warehouse/camera subscription so clients only
receive events relevant to what they're viewing.

## 7. Background Processing Design

```
FastAPI → Redis (queue) → Celery Worker → AI Pipeline
```
Flow: `Upload → Job Created → Queue → Worker → Video Processing → AI Inference
→ Event Processing → Database → WebSocket`. Video processing must never block
an API request/response cycle.

## 8. Frontend Application Structure

```
Dashboard
 ├── Command Center
 ├── Live Monitoring
 ├── Incident Center
 ├── Incident Replay
 ├── Risk Heatmap
 ├── Behaviour Analytics
 ├── Damage Intelligence
 ├── Digital Twin
 ├── Root Cause
 ├── Recommendations
 ├── AI Assistant
 ├── Human Review
 ├── Dataset Manager
 ├── Model Registry
 ├── Reports
 └── Administration
```

## 9. Key Screen Sketches

**Command Center (home):**
```
Today's Risk
────────────────────────
Critical       3
High          17
Medium        42
Low           81
Potential Damage: 12
Most Risky Zone: Loading Bay 2
Most Frequent Behaviour: Improper Stacking
[ Live incidents feed below ]
```

**Incident Investigation Screen:**
```
VIDEO REPLAY
Risk: HIGH   Behaviour: Product Drop   Confidence: 89%
TIMELINE: Pickup → Move → Release → Fall → Impact
WHY? Drop height 1.0m · Product: Fragile · Impact: High
     Zone: Loading Bay 2 · Frequency: Repeated
POTENTIAL DAMAGE: 82%
RECOMMENDATION: Inspect product and review unloading procedure.
```

## 10. Security Architecture

- JWT authentication, password hashing, RBAC enforced **server-side** (never
  only hidden in the frontend).
- Input validation via Pydantic on every endpoint.
- Rate limiting on public-facing endpoints.
- TLS termination at the reverse proxy.
- Access-controlled evidence URLs (signed/expiring links to S3/MinIO objects).
- Full audit logging of state-changing actions.
- Secrets managed via environment variables / secret manager, never committed.

## 11. Privacy Architecture

- No facial recognition by default; optional face-blurring pipeline stage.
- Role-based video access (only authorized roles can view raw footage).
- Configurable data retention per data class (raw video short, incident evidence
  longer, aggregated analytics long-term).
- Data minimization — store only what's needed for the operational/analytical
  purpose.
- Human review required before any consequential action is taken.

## 12. Failure Handling Design

| Failure | Handling |
|---|---|
| Camera disconnected | Mark offline → notify supervisor → retry connection |
| Inference failure | Retry → log error → fail safely (no silent incident loss) |
| Corrupt video | Validate on ingest → reject or skip damaged segment |
| Low confidence | No automatic high-risk alert → route to human review |

## 13. Monitoring

Track: CPU, GPU, RAM, FPS, inference latency, queue length, camera health, API
latency, DB health, Redis health, storage usage, worker status — via
Prometheus, visualized in Grafana.

## 14. Multi-Camera Note

v1 treats each camera independently (no cross-camera identity/re-ID). This is a
deliberate scope decision to keep the prototype tractable; cross-camera
tracking is a Tier 4 future extension.

## 15. Edge/Server Split (future extension)

```
EDGE: video decoding, object detection, tracking, basic behaviour extraction
SERVER: risk, analytics, database, RAG, AI assistant
```
For the hackathon prototype, a single GPU workstation/server deployment is
sufficient; the edge/server split reduces bandwidth for a later production
rollout.
