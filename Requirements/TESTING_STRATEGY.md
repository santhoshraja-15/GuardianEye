# Testing Strategy
## W-SAFE — Unit, Model, E2E, and Golden Dataset Testing

## 1. Testing Pyramid

```
Unit Tests        → risk calculation, database, API, behaviour rules (Pytest)
Model Tests        → detection accuracy, tracking stability, behaviour accuracy,
                      false positives/negatives
End-to-End Tests     → Video → Detection → Tracking → Behaviour → Risk → Incident
                      → Dashboard → AI Assistant (Playwright + integration harness)
Frontend Unit Tests   → components/utilities (Vitest)
```

## 2. Unit Tests (Pytest)

Cover:
- Risk-score formula correctness (given fixed inputs, expected score/level)
- Alert de-duplication logic (cooldown windows, incident grouping)
- Database models/migrations
- RBAC permission checks
- Behaviour rule edge cases (e.g. drop vs. gentle placement)

## 3. Model Evaluation Tests

| Component | Metrics | Pass Bar (suggested starting point) |
|---|---|---|
| Object detection | mAP, precision, recall | mAP@0.5 ≥ 0.7 on validation set |
| Tracking | ID consistency, ID switches | < 1 ID switch per 100 frames of continuous track |
| Behaviour classification | Precision, recall, F1, confusion matrix | F1 ≥ 0.75 per MVP behaviour |
| Risk scoring | False positive rate, false negative rate, calibration | FP rate < 10% on golden set |
| Damage/predictive models | MAE/RMSE/ROC-AUC/PR-AUC/Brier (as applicable) | Track trend over iterations, not just a single number |

Do not report only "our model achieved 95% accuracy" — report all four
evaluation dimensions from `PRD.md` §10 (AI, Operational, Business, Human).

## 4. Golden Test Dataset

Create **10–20 manually-verified videos**, one per key scenario, and re-run
them after every meaningful pipeline change:

```
video_01.mp4  NORMAL
video_02.mp4  DROP
video_03.mp4  DRAG
video_04.mp4  THROW
video_05.mp4  ROUGH_HANDLING
video_06.mp4  INCORRECT_STACKING
video_07.mp4  UNSTABLE_STACKING
video_08.mp4  INCORRECT_PLACEMENT
video_09.mp4  IMPROPER_EQUIPMENT_USAGE
video_10.mp4  UNSAFE_LOADING_SEQUENCE
```
Recommended controlled-pilot scenarios to physically stage and film (boxes,
pallets, trolleys, tables, small vehicles, human participants):
```
Scenario 1  Normal pickup
Scenario 2  Drop
Scenario 3  Drag
Scenario 4  Throw
Scenario 5  Rough handling
Scenario 6  Incorrect stacking
Scenario 7  Unstable stacking
Scenario 8  Wrong placement
Scenario 9  No-equipment handling
Scenario 10 Unsafe loading sequence
```

## 5. False-Positive / Negative-Control Testing

Explicitly test scenarios that must **not** trigger an incident:
```
Product gently placed        → must NOT become DROP
Person walking beside carton  → must NOT become DRAGGING
Brief occlusion (ACTIVE→LOST→REACQUIRED) → must NOT create a new incident
```

## 6. End-to-End Test Flow

```
Upload golden video → Trigger processing job → Poll job status → Assert:
  - detections present for expected classes
  - track IDs persist across expected frame range
  - expected behaviour_event created with correct behaviour code
  - risk_assessment level matches expected label
  - incident created (or correctly NOT created, for negative-control videos)
  - evidence clip/snapshot generated
  - WebSocket NEW_INCIDENT event received by a test client
  - AI assistant answers a canned question correctly, grounded in this incident
```

## 7. Frontend Testing

- **Vitest** — component rendering, state (Zustand) logic, chart data
  transforms.
- **Playwright** — full user flows: login → dashboard loads → open incident →
  replay renders → assistant returns an answer → RBAC-gated pages correctly
  block unauthorized roles.

## 8. Responsible-AI Test Checklist

- [ ] AI-inferred root causes are visually/textually distinguished from
      observed facts in every UI surface
- [ ] Damage claims never appear without a probability + "potential" framing
      unless `CONFIRMED_BY_HUMAN`/`CONFIRMED_BY_EXTERNAL_SYSTEM`
- [ ] Assistant refuses to answer with fabricated details when no evidence
      exists ("I don't have evidence for that")
- [ ] RBAC enforced server-side (attempt a direct API call as a
      lower-privilege role and confirm rejection, not just UI hiding)
- [ ] Audit log entry created for every configuration change

## 9. CI Pipeline (GitHub Actions, lightweight)

```
git push → Lint → Unit tests (Pytest + Vitest) → Build (frontend + backend)
→ Docker build → Integration tests (golden video subset) → (Deploy, optional)
```

## 10. Regression Discipline

Any change to detection, tracking, behaviour rules, or risk weights must be
re-validated against the full golden dataset before merging to
`development`. Track metric history over time (a simple CSV/DB log of
mAP/F1/FP-rate per commit is sufficient for a hackathon timeline).
