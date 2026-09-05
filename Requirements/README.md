# W-SAFE
### AI-Powered Warehouse Behaviour, Risk, Damage Prevention & Operational Intelligence Platform

> From Video Surveillance to Proactive Warehouse Intelligence

---

## What is W-SAFE?

W-SAFE converts ordinary warehouse CCTV/recorded video into a real-time operational
intelligence system. It doesn't just detect objects — it understands **who** is
interacting with **what**, **what action** is happening, **how risky** it is, whether
**product damage** may result, **why** it happened, and **what to do** to prevent it
happening again.

```
Camera/Video → Perception → Tracking → Scene Understanding → Behaviour Understanding
→ Context Analysis → Risk Assessment → Damage Prediction → Alert → Human Intervention
→ Root Cause → Prevention → Learning
```

Built for the **"AI Video Intelligence for Warehouse Handling"** hackathon challenge
(submission deadline: 10 September 2026), covering the mandatory pipeline — video
ingestion, object detection/tracking, behaviour identification, risk classification,
incident visualization, AI-generated explanation/recommendation — plus 20 differentiator
behaviours, predictive risk, root-cause/counterfactual analysis, a bilingual (Tamil/
English) evidence-grounded AI assistant, and full MLOps/responsible-AI governance.

## Document Index

This repository/zip contains the complete documentation set needed to plan, build,
and ship W-SAFE:

| # | Document | Purpose |
|---|----------|---------|
| 1 | `README.md` | This file — project overview & doc index |
| 2 | `PRD.md` | Product Requirements Document — problem, users, scope, success metrics |
| 3 | `TECHNICAL_DEEP_DIVE.md` | Deep dive into the AI/CV pipeline: detection, tracking, behaviour, risk, damage prediction |
| 4 | `TECH_STACK.md` | Locked technology stack with rationale for every choice |
| 5 | `REQUIREMENTS_AND_PREREQUISITES.md` | Software, hardware, accounts, datasets, skills needed before starting |
| 6 | `FLOW_DOCUMENT.md` | End-to-end data flow, user flows, and event lifecycle diagrams |
| 7 | `SYSTEM_DESIGN.md` | Component design, database schema, API contracts, deployment topology |
| 8 | `LAYER_ARCHITECTURE.md` | The 5-layer intelligence architecture (Perception → Learning) |
| 9 | `BUILD_INSTRUCTIONS.md` | Step-by-step local setup and level-by-level build guide |
| 10 | `PROJECT_CONTROL_DOCUMENT.md` | Team roles, sprints, dependency matrix, priority tiers, risk register |
| 11 | `ANTIGRAVITY_BUILD_PROMPT.md` | Ready-to-paste master prompt(s) for building W-SAFE with an agentic AI IDE (Antigravity) |
| 12 | `API_SPECIFICATION.md` | Full REST + WebSocket API reference |
| 13 | `DATABASE_SCHEMA.md` | PostgreSQL schema (DDL) for every table |
| 14 | `TESTING_STRATEGY.md` | Unit/model/E2E testing approach + golden test dataset design |
| 15 | `DEPLOYMENT_GUIDE.md` | Docker Compose, environment variables, GPU setup, monitoring |

## Reading Order

- **New to the project?** Read `PRD.md` → `LAYER_ARCHITECTURE.md` → `TECH_STACK.md`.
- **About to start building?** Read `REQUIREMENTS_AND_PREREQUISITES.md` →
  `BUILD_INSTRUCTIONS.md` → `PROJECT_CONTROL_DOCUMENT.md`.
- **Using an AI coding agent (Antigravity, Claude Code, Cursor, etc.)?** Go straight to
  `ANTIGRAVITY_BUILD_PROMPT.md` and feed it the phase prompts in order.
- **Need architecture/API details while coding?** `SYSTEM_DESIGN.md`,
  `API_SPECIFICATION.md`, `DATABASE_SCHEMA.md`, `TECHNICAL_DEEP_DIVE.md`.

## One-Sentence Summary

> W-SAFE sees the warehouse, understands the behaviour, connects the entities,
> evaluates the context, estimates risk, predicts potential damage, alerts the right
> person, explains the evidence, recommends prevention, and learns from human feedback.

## Responsible AI Note

W-SAFE is a **process-improvement and damage-prevention** platform — not an employee
surveillance or automated-punishment system. No facial recognition by default, no
automatic penalties, AI-inferred causes are always labelled as inferred (not fact),
and every consequential decision routes through human review. See `PRD.md` §9 and
`LAYER_ARCHITECTURE.md` §Layer 5 for details.
