# GUARDIAN EYE — MASTER PROJECT ROADMAP

**Project:** GuardianEye — Warehouse Intelligence Platform  
**Total Development Levels:** 50 (Part I) + 15 (Part II) + Final System Acceptance  
**Current Phase:** PART I (Backend, AI, Data & Infrastructure Foundation)  

---

## Part I: Backend, AI, Data & Infrastructure Roadmap

```
Level 00: Requirements Discovery & Architecture Validation [IN PROGRESS]
Level 01: Repository & Environment Configuration (Docker, Compose, Makefile, .gitignore)
Level 02: Backend Core Foundation (FastAPI, Lifespan, Logging, Config, Healthchecks)
Level 03: Database Engine, Relational Schemas & Migrations (SQLAlchemy 2.0, Alembic, PostgreSQL)
Level 04: Authentication & Server-Side RBAC (JWT, Hashing, Roles, Audit Logs)
Level 05: Object Storage Management (MinIO / S3 Integration, Checksums, File Validation)
Level 06: Video Ingestion & Metadata Pipeline (Upload, FFmpeg/OpenCV, Codec/FPS Extraction)
Level 07: Video Decoding & Frame Processing Engine (Decoupled Inference FPS, Queue Worker)
Level 08: Object Perception & YOLO Detection Engine (Ultralytics / ONNX / Torch, 9 Classes)
Level 09: Sample Video Dataset Lineage, Splits & Annotation Infrastructure
Level 10: Multi-Object Tracking Engine (ByteTrack, Kalman Filtering, Trajectory Logging)
Level 11: Spatial Geometry & Zone Intelligence Engine (Point-in-Polygon, Proximity, Distances)
Level 12: Human-Object-Equipment Interaction Engine (Contact, Holding, Carrying, Carrying States)
Level 13: Temporal State Machine & Sequence Reasoning Engine (Occlusion Recovery, State Shifts)
Level 14: Behaviour Intelligence Engine (B01-B10 Core Warehouse Scenario Detectors)
Level 15: Behaviour DNA Engine (Fingerprinting, Temporal Sequence Vectors)
Level 16: Context Engine (Enrichment via Zones, Shifts, Equipment & Product Fragility)
Level 17: Deterministic & Auditable Risk Engine (Weighted Scoring, LOW/MED/HIGH/CRITICAL)
Level 18: Damage Prediction Intelligence (Damage Probability, Packaging/Breakage Estimation)
Level 19: Predictive Risk & Trend Forecasting Engine (Shift Trends, Recurrence Forecasts)
Level 20: Real-Time Alert Engine (Deduplication, Spatial/Temporal Cooldown, Lifecycle)
Level 21: Incident Engine & Audit Trail (State Machine: DETECTED -> UNDER_REVIEW -> RESOLVED)
Level 22: Visual Evidence Package Generator (Frame Snapshots, Pre/Post Clips, SHA256 Checksums)
Level 23: Synchronized Incident Replay Backend (Timestamp-Aligned Overlay Data Stream)
Level 24: Root Cause Attribution Engine (Observed vs Inferred Classification)
Level 25: Corrective Prevention Recommendation Engine (Estimated Benefit Ranges)
Level 26: Counterfactual Simulation Engine (Observed vs Alternative Safe Delta)
Level 27: Operational Analytics & Aggregation Engine (Zone, Shift, Behaviour, Fragility Metrics)
Level 28: Risk & Incident Heatmap Engine (Spatial Grid Density, Zone Aggregations)
Level 29: 2D Digital Twin Backend (Warehouse Topology, Live Camera & Entity Positioning)
Level 30: Grounded AI Assistant Backend (Structured DB Queries, Function Tools, Guardrails)
Level 31: Semantic Similarity Search (pgvector Incident & Behaviour DNA Indexing)
Level 32: Human Review Queue & Feedback Collector (CORRECT, INCORRECT, AMBIGUOUS)
Level 33: Unknown & Emerging Behaviour Clustering Engine
Level 34: Active Learning Orchestrator (Curated Datasets, Training Queue)
Level 35: Dataset Versioning & Governance (Splits, Hashes, Leakage Checks)
Level 36: Model Registry & Artifact Management (Model Lifecycle & Evaluation Metrics)
Level 37: Automated Model Evaluation Benchmark Suite (mAP, F1, Confusion Matrices)
Level 38: Golden Scenario Verification Harness (10 Verified Warehouse Tests)
Level 39: Negative Control Verification Suite (False-Positive Elimination)
Level 40: WebSocket Real-Time Event Bus (/ws/events)
Level 41: Operational Report Generator (PDF, CSV, JSON Export Services)
Level 42: Backend Security Hardening & Input Sanitization
Level 43: Privacy by Design & Responsible AI Enforcements
Level 44: Failure Recovery, Error Handling & Graceful Degradation
Level 45: Prometheus Telemetry, Health Probes & Structured Logs
Level 46: API Contract Specification Freeze & Documentation (docs/06-api/)
Level 47: End-to-End Backend Integration Verification
Level 48: Backend Performance & Latency Benchmarks
Level 49: Security, Auth & Injection Penetration Tests
Level 50: Backend Final Audit & Part I Completion Handoff
```

---

## Part II: Frontend & Full System Integration Roadmap (Awaiting Employer Input)

```
Level 01: Application Shell, Routing, Vite/Tailwind/shadcn Setup
Level 02: Real Authentication & Session Management
Level 03: Executive Command Center & Operational Overview
Level 04: Video Management & Processing Dashboard
Level 05: Live Stream Monitoring & Real-time Bounding Box Overlays
Level 06: Incident Center & Advanced Multi-Filter Grid
Level 07: Incident Detail & Comprehensive Investigation Dossier
Level 08: Synchronized Incident Replay Studio (Video + Timeline + DNA + Tracks)
Level 09: Operational Analytics & Trend Visualizer (Recharts)
Level 10: Interactive Warehouse Risk Heatmap
Level 11: 2D Warehouse Digital Twin Visualizer
Level 12: Grounded AI Assistant Natural Language Interface
Level 13: Supervisor Human Review Queue & Annotation Interface
Level 14: Executive Report Generator & Export Center
Level 15: Warehouse, Zone, Camera & System Configuration Settings
Final E2E Integration & Full Acceptance Validation
```
