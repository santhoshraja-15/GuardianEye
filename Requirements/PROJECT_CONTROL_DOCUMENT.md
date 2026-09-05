# Project Control Document
## W-SAFE — Team Roles, Sprints, Dependencies, Risk Register

## 1. Team Workload Split (4-member team)

| Member | Primary Responsibility |
|---|---|
| **Member A — AI/CV Lead** | Video processing, object detection, tracking, behaviour recognition, risk features, model optimization |
| **Member B — Backend/AI Platform** | Backend environment, database, risk engine, alert system, LLM assistant, API integration, advanced intelligence |
| **Member C — Frontend** | Frontend setup, entire UI, API integration prep, real-time alerts UI, full frontend integration, UX polish |
| **Member D — Data/DevOps/QA** | Dataset planning, Git/Docker/environment, video dataset & annotation, tracking evaluation, behaviour test videos, testing, deployment/demo |

### 5-member variant
`A: Detection/ML · B: Behaviour/Tracking · C: Backend/AI · D: Frontend ·
E: Data/Testing/DevOps`

## 2. Detailed Level Ownership

**Member A (AI/CV):** Level 0 behaviour definitions → Level 4 video processing
→ Level 5 detection → Level 6 tracking → Level 7 behaviour recognition →
Level 8 risk features → Level 11 model optimization.

**Member B (Backend/AI):** Level 1 backend environment → Level 3 database →
Level 8 risk engine → Level 9 alert system → Level 10 LLM assistant →
Level 11 API integration → Level 12 advanced intelligence.

**Member C (Frontend):** Level 1 frontend setup → Level 2 entire UI →
Level 3 API integration prep → Level 9 real-time alerts → Level 11 full
frontend integration → Level 12 UX optimization.

**Member D (Data/DevOps/QA):** Level 0 dataset planning → Level 1 Git/Docker/
environment → Level 4 video dataset → Level 5 annotation → Level 6 tracking
evaluation → Level 7 behaviour test videos → Level 11 testing →
Level 12 integration/deployment/demo.

## 3. Sprint Plan (parallel development)

```
Sprint 1: A → Dataset + detection research   B → Backend skeleton
          C → UI design                       D → Dataset + environment
Sprint 2: A → Object detection                B → Database/API
          C → Dashboard                        D → Video pipeline
Sprint 3: A → Tracking                          B → Incident API
          C → Live monitoring                    D → Behaviour datasets
Sprint 4: A → Behaviour detection                B → Risk engine
          C → Incident UI                         D → Testing
Sprint 5: A → Behaviour optimization              B → AI assistant
          C → Analytics                            D → Integration
Sprint 6: Everyone → Full integration
```

## 4. Dependency Matrix

| Feature | Depends On |
|---|---|
| Detection | Video pipeline |
| Tracking | Detection |
| Behaviour | Detection + Tracking |
| Risk | Behaviour |
| Incident | Risk |
| Alerts | Incident |
| Dashboard | Backend |
| Replay | Incident |
| AI Assistant | Event database |
| Analytics | Event database |
| Predictive AI | Historical events |
| Multi-camera | Tracking |

**Implication:** the AI assistant, analytics, and predictive-risk work must
never be scheduled before the event database (incidents/behaviour_events)
actually exists and is populated by real pipeline output.

## 5. Development Effort Distribution

```
AI/CV                    35%
Backend                  25%
Frontend                 20%
Data + Evaluation        10%
DevOps + Security        10%
```
(AI/CV gets the largest share because the challenge weights AI/video
integration and technical execution at 20% each of the judging criteria.)

## 6. Priority Tiers

```
Tier 1 (P0 / Mandatory core):
  Video ingestion, object detection, object tracking, spatial zones,
  human-object interaction, 10 behaviours, temporal reasoning,
  risk classification, alert system, evidence generation, incident replay,
  dashboard

Tier 2 (P1 / Major differentiators):
  Behaviour DNA, interaction graph, product-specific risk, damage probability,
  predictive risk, risk heatmaps, root-cause analysis, prevention
  recommendations, counterfactual analysis, AI assistant, similar incident
  search, digital twin

Tier 3 (P2 / Exceptional):
  Active learning, unknown behaviour detection, Tamil voice, voice alerts,
  Temporal Transformer, pallet stability estimation, forklift/pedestrian
  prediction, intervention simulator

Tier 4 (P3 / Production/research extensions):
  Cross-camera identity, edge deployment, GNN scene reasoning,
  self-supervised learning, full WMS/VMS integration, large-scale
  distributed inference
```

## 7. Milestones

| Milestone | Definition of Done |
|---|---|
| M1 — Vertical Slice 1 | One video → one carton detected → displayed |
| M2 — Vertical Slice 2 | + Tracking, trajectory displayed |
| M3 — Vertical Slice 3 | + Interaction engine, one Drop detected |
| M4 — Vertical Slice 4 | + Risk score, alert fired |
| M5 — Vertical Slice 5 | + Evidence clip, replay working |
| M6 — Vertical Slice 6 | + Root cause + recommendation shown |
| M7 — Vertical Slice 7 | + Incident DB fully populated, AI assistant answers |
| M8 — Vertical Slice 8 | + Human review, dataset versioning, learning loop stub |
| M9 — Full Integration | All P0 + P1 features wired end-to-end |
| M10 — Demo Ready | Golden test videos pass, slide deck + demo script ready |

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Detection accuracy too low on real footage | Medium | High | Use controlled pilot environment; fine-tune on own footage early |
| Behaviour classification overfits to few examples | Medium | Medium | Keep rule/state-machine baseline as fallback; don't over-invest in ML before rules work |
| Frontend/backend integration slips to the end | High | High | Enforce vertical-slice development; no "big bang" integration |
| LLM assistant hallucinates incidents | Medium | High | Enforce evidence-first rule; tool-calling only, never freeform SQL from the LLM |
| Team runs out of time before Tier 2 | High | Medium | Strict P0→P1→P2→P3 prioritization; Tier 1 must be bulletproof before any Tier 2 work starts |
| False positives erode trust in demo | Medium | High | False-positive pipeline (confidence→temporal→spatial→context→risk→dedup); golden test set regression |
| GPU unavailable on dev machines | Medium | Medium | CPU fallback path; cloud GPU for final training runs |
| Privacy/responsible-AI concerns raised by judges | Low | High | Bake in face-blurring option, RBAC, audit log, "AI-inferred vs observed" labelling from Level 0 |

## 9. Definition of Ready / Definition of Done

**Definition of Ready (per level):** dependencies satisfied per §4, sample data
available, acceptance criteria agreed.

**Definition of Done (per level):** feature works end-to-end on at least one
golden test video, covered by at least one automated test, merged to
`development` via PR, documented (docstring/README update if API changed).

## 10. Submission Checklist

- [ ] 5–6 slide presentation
- [ ] Prototype screenshots
- [ ] Live/recorded demo covering representative scenarios (all 10 MVP
      behaviours ideally)
- [ ] README + architecture docs (this documentation set)
- [ ] Golden test videos + results
- [ ] Responsible-AI statement included in the deck
