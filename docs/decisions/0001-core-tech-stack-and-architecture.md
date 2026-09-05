# GUARDIAN EYE — ARCHITECTURAL DECISION RECORD 001

**Title:** Selection of Core Technology Stack and Layered Architecture  
**Date:** 2026-09-05  
**Status:** ACCEPTED  

## Context
GuardianEye requires a real-time, explainable, and auditable computer vision platform to detect and mitigate unsafe warehouse behaviours and damage risks. The system must process high-throughput video streams, execute multi-object tracking, evaluate complex spatial-temporal interactions, compute deterministic risk scores, and provide grounded AI assistant interfaces.

## Decisions
1. **Backend Framework: FastAPI (Python 3.11+)**
   - Rationale: High performance asynchronous capabilities, native Pydantic v2 data validation, OpenAPI v3 generation, seamless integration with PyTorch/OpenCV/NumPy scientific computing ecosystem.
2. **Relational Database: PostgreSQL 16 + pgvector**
   - Rationale: ACID compliance for audit trails, rich relational integrity for warehouse topologies, and unified semantic vector storage without needing an external vector database.
3. **Computer Vision & Tracking: YOLOv8/v11 + ByteTrack**
   - Rationale: High-throughput real-time detection on CUDA/CPU, resilient multi-object tracking with low computational overhead and robust occlusion recovery.
4. **Risk Computation: Deterministic Rule-Engine with Explainability**
   - Rationale: Legal auditability and strict repeatability. Core risk calculation must never be delegated to an unconstrained LLM.
5. **AI Assistant: Grounded Retrieval via Tool-Calling & Structured Queries**
   - Rationale: Eliminates hallucinations by requiring all assistant answers to cite verified database records, evidence packages, and mathematical formulas.
