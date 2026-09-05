# Tech Stack Document
## W-SAFE — Locked Technology Stack & Rationale

**Guiding principle:** the CV / temporal-intelligence pipeline is the product core;
the website, database, and LLM are built **around** it — not the other way around.

---

## 1. Master Stack Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│ React + TypeScript + Vite + Tailwind + shadcn/ui         │
│ Recharts + TanStack Query + Zustand                      │
└──────────────────────┬──────────────────────────────────┘
                        │ REST / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                    BACKEND                                │
│ Python + FastAPI + Pydantic + SQLAlchemy                 │
│ Celery/Redis for heavy asynchronous jobs                 │
└──────────────────────┬──────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌───────────────┐
│ CV ENGINE    │ │ EVENT ENGINE │ │ AI ASSISTANT  │
│ PyTorch/YOLO │ │ Rules + ML   │ │ LLM + RAG     │
│ OpenCV       │ │ Risk Engine  │ │ pgvector      │
│ ByteTrack    │ │ Temporal     │ │ Tool calling  │
└──────┬───────┘ └──────┬───────┘ └───────┬───────┘
       └────────────────┼────────────────┘
                         ▼
               ┌─────────────────────┐
               │ PostgreSQL + pgvector│
               └──────────┬──────────┘
                          ▼
                ┌────────────────────┐
                │ Object Storage      │
                │ S3 / MinIO           │
                └────────────────────┘
```

## 2. Layer-by-Layer Stack Table

| Level | Recommended | Why |
|---|---|---|
| Dev tooling | Git + GitHub + VS Code | Best collaboration |
| Frontend | React + TypeScript + Vite | Fast, scalable, best ecosystem for a real-time dashboard |
| UI | Tailwind CSS + shadcn/ui | Rapid, polished, customizable UI |
| State | Zustand | Lightweight, minimal boilerplate |
| Server data | TanStack Query | Caching/refetch/loading/error handling |
| Charts | Recharts | Native React integration |
| Backend | Python + FastAPI | Best fit for direct AI/CV integration |
| Validation | Pydantic | Strong typed API schemas |
| ORM | SQLAlchemy + Alembic | Mature Python DB layer + migrations |
| Database | PostgreSQL | Reliable, relational, analytical queries |
| Vector search | pgvector (inside Postgres) | Avoids a second database |
| Video I/O | OpenCV + FFmpeg | Industry-standard decode/processing/transcode |
| Detection | YOLO-family | Real-time throughput, easy custom training |
| Deep learning | PyTorch | Dominant ecosystem, flexible for detection/temporal models |
| Tracking | ByteTrack | Fast, robust in crowded scenes, integrates easily with YOLO |
| Behaviour | Hybrid: rules + state machine + optional temporal model | Explainable, works with small datasets |
| Queue | Redis + Celery | Async video processing without blocking API |
| Real-time | WebSockets | Push alerts/events instead of polling |
| LLM/Assistant | LLM API + RAG | Grounded natural-language reasoning |
| Object storage | S3 (prod) / MinIO (local) | Video/clip storage outside the relational DB |
| Deployment | Docker + Docker Compose | Reproducibility across a many-dependency stack |
| GPU | NVIDIA CUDA | Fast inference |
| Monitoring | Prometheus + Grafana | Production observability |
| Testing | Pytest + Vitest + Playwright | Backend, frontend, E2E coverage |
| CI/CD | GitHub Actions | Lint → test → build → deploy pipeline |

## 3. Key Decisions & Rationale

### 3.1 React + Vite over Next.js
W-SAFE is an interactive **operational dashboard** (live video, bounding boxes,
incident timeline, real-time alerts, AI chat, analytics) — not an SEO/content
website. React + Vite gives faster iteration, a simpler mental model, and
frictionless WebSocket integration, with FastAPI staying cleanly separated as the
API layer.

### 3.2 Python + FastAPI over Node.js backend
The AI engine (PyTorch, OpenCV, YOLO, tracking, LLM calls) is Python-native.
Using FastAPI keeps everything — API, orchestration, and AI — in one ecosystem
instead of introducing a Node↔Python service boundary. FastAPI adds async
support, WebSockets, automatic OpenAPI docs, and Pydantic validation.

### 3.3 PostgreSQL over MongoDB
Warehouse intelligence queries are inherently relational/analytical ("which bay
had the most high-risk events?", "behaviour trend by shift?", "incidents this
week by zone?"). PostgreSQL's joins and aggregation are a much better fit than a
document store.

### 3.4 pgvector over a dedicated vector database
The assistant's retrieval needs (incident embeddings, similar-incident search,
recommendation embeddings) don't yet justify Pinecone/Weaviate/Chroma/Milvus.
`PostgreSQL + pgvector` keeps one database for both structured and semantic
queries, avoiding a second system to operate and keep in sync.

### 3.5 YOLO over Faster R-CNN
The system needs real-time inference at warehouse frame rates; YOLO trades a
small amount of peak accuracy for far better throughput/latency, which matters
more than benchmark accuracy for this use case.

### 3.6 ByteTrack over DeepSORT (v1)
ByteTrack is fast, simple to integrate with YOLO, and effective in crowded
scenes. DeepSORT's appearance-embedding re-identification is valuable but adds
complexity not needed for the first version; it (or full Re-ID) is a Tier-4
extension for multi-camera tracking.

### 3.7 Hybrid behaviour engine over one giant trained model
A single end-to-end "warehouse behaviour" model would need far more labelled
video than is available for a hackathon-scale project. Instead, W-SAFE composes:
`YOLO + ByteTrack + motion features + spatial rules + temporal state machines
(+ optional Temporal Transformer later)`. This is more explainable, testable,
and debuggable, and matches the challenge's explicit call for detection +
tracking + action recognition + temporal reasoning + risk classification working
together.

### 3.8 Deterministic rules for risk scoring (not the LLM)
Risk must be reproducible and auditable. A rules/ML risk engine computes the
score; the LLM's job is to **explain** the score in natural language, never to
compute it.

### 3.9 Redis + Celery over Kafka (v1)
Kafka is built for very large, partitioned, multi-consumer event-streaming
systems. A hackathon-scale (or even single-warehouse production) workload is
well served by Redis + Celery, which is dramatically simpler to operate. Kafka
remains a valid future upgrade if the platform scales to many warehouses with
heavy streaming.

### 3.10 LLM sees structured events, never raw video
`Video → CV → Structured Events → LLM`, not `Video → LLM`. This is cheaper,
deterministic, explainable, testable, and auditable — and satisfies the
evidence-first requirement for the assistant.

## 4. Explicitly Rejected Technologies (and why)

| Rejected | Reason |
|---|---|
| MongoDB | Warehouse analytics are relational; Postgres joins/aggregations are a better fit |
| Firebase | Would fragment the AI-heavy Python architecture |
| Node.js backend | Core intelligence is Python; avoids a service boundary |
| Next.js | No SEO requirement; React+Vite is simpler for a dashboard |
| Kubernetes | Overkill for the prototype scale |
| Kafka (v1) | Overkill; Redis+Celery is sufficient at this scale |
| Standalone vector DB | pgvector inside Postgres is sufficient |
| Many microservices (v1) | Unnecessary operational overhead for the prototype |
| LLM-based video detection | Use dedicated CV models — cheaper, faster, more reliable |
| LLM-based risk scoring | Must stay deterministic/auditable |
| Training everything from scratch | Use transfer learning / pretrained detectors |

## 5. Intelligence-Layer → Technology Map

| Intelligence | Technology | Purpose |
|---|---|---|
| Video | FFmpeg | Decode / clip / transcode |
| Frames | OpenCV | Frame processing |
| Detection | YOLO | Find objects |
| Tracking | ByteTrack | Persistent IDs |
| Motion | OpenCV / NumPy | Velocity / displacement |
| Interaction | Geometry (bbox overlap/proximity) | Person–object relationships |
| Behaviour | Rules + temporal state machine | Understand actions |
| Risk | Python rules (+ML later) | Score events |
| Incident | FastAPI service | Create event |
| Alert | WebSocket | Real-time notification |
| Storage | S3 / MinIO | Video clips |
| Database | PostgreSQL | Structured events |
| Retrieval | pgvector | Semantic/similar-incident search |
| Explanation | LLM | Natural-language reasoning |
| Dashboard | React | Visualization |
| Analytics | PostgreSQL + Recharts | Trends |
| Queue | Redis / Celery | Async processing |
| Deployment | Docker | Reproducibility |

## 6. Effort Allocation

```
AI/CV                    35%
Backend                  25%
Frontend                 20%
Data + Evaluation        10%
DevOps + Security        10%
```
AI/CV gets the largest share because AI + video intelligence is a primary judging
dimension of the challenge.
