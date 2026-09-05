# API Specification
## W-SAFE — REST + WebSocket Reference

Base URL: `/api`. Auth: `Bearer <JWT>` on every protected route. All responses
JSON. All list endpoints support pagination (`?limit=&offset=`) and relevant
filters.

## 1. Auth

```
POST /api/auth/login          { email, password } → { token, role }
POST /api/auth/refresh        → { token }
GET  /api/users                (Admin only)
POST /api/users                (Admin only) create user + role
```

## 2. Warehouses, Zones, Cameras

```
GET  /api/warehouses
POST /api/warehouses

GET  /api/zones?warehouse_id=
POST /api/zones                { warehouse_id, name, zone_type, polygon }
PUT  /api/zones/{id}
DELETE /api/zones/{id}

GET  /api/cameras?warehouse_id=
POST /api/cameras               { warehouse_id, zone_id, source_type, stream_url }
PUT  /api/cameras/{id}
GET  /api/cameras/{id}/health
```

## 3. Video & Processing

```
POST /api/videos/upload         multipart file → { video_id }
GET  /api/videos
GET  /api/videos/{id}

POST /api/videos/{id}/process   → { job_id }
GET  /api/jobs/{id}             → { status, progress, error_message }
```

## 4. Detection / Tracking / Behaviour (read/inspect)

```
GET /api/detection?video_id=
GET /api/tracks?video_id=
GET /api/tracks/{id}            → trajectory, velocity, acceleration, status
GET /api/behaviours              → taxonomy list (B01..B20)
GET /api/behaviours/events?video_id=&behaviour_id=&zone_id=&date_from=&date_to=
GET /api/interactions?video_id=
```

## 5. Risk / Damage / Predictions

```
GET /api/risk/{behaviour_event_id}
GET /api/damage/{behaviour_event_id}
GET /api/predictions?zone_id=
```

## 6. Incidents / Alerts / Evidence / Replay

```
GET  /api/incidents?status=&risk_level=&zone_id=&date_from=&date_to=
GET  /api/incidents/{id}          → full detail incl. risk, damage, evidence,
                                     root cause, recommendation, counterfactual
PATCH /api/incidents/{id}/status  { status, notes }

GET  /api/alerts?status=
PATCH /api/alerts/{id}/status     { status }

GET  /api/evidence/{incident_id}
GET  /api/replay/{incident_id}    → timeline + overlay data
```

## 7. Root Cause / Recommendations / Counterfactual

```
GET /api/root-cause/{incident_id}
GET /api/recommendations/{incident_id}
GET /api/counterfactual/{incident_id}
```

## 8. Analytics / Heatmap / Digital Twin

```
GET /api/analytics/overview        → today's KPI cards
GET /api/analytics/behaviours       → frequency breakdown
GET /api/analytics/locations         → risk/incidents by zone
GET /api/analytics/shifts             → shift comparison
GET /api/heatmap?type=incident_density|risk_intensity|damage_probability|behaviour_frequency
GET /api/digital-twin/state          → live entity positions for the 2D map
```

## 9. AI Assistant / Search

```
POST /api/assistant/query        { text, conversation_id?, lang: "en"|"ta" }
                                  → { answer, evidence_refs[], follow_up_suggestions[] }
POST /api/assistant/voice        multipart audio → same response shape + audio reply
GET  /api/search/similar-incidents?incident_id=
```

## 10. Human Review / Datasets / Models / Evaluation

```
GET   /api/reviews?status=pending
POST  /api/reviews                { behaviour_event_id, verdict, corrected_behaviour_id?, notes }

GET   /api/datasets
POST  /api/datasets/versions       { dataset_id, notes }

GET   /api/models
GET   /api/models/{id}/versions
POST  /api/models/{id}/versions/{version_id}/approve   (Admin/ML lead only)

GET   /api/evaluation/{model_version_id}
```

## 11. Config / Audit / System

```
GET  /api/config/thresholds
PUT  /api/config/thresholds        { risk_thresholds, alert_cooldown_seconds, retention_days }
GET  /api/config/products
POST /api/config/products
GET  /api/config/equipment

GET  /api/audit?entity_type=&entity_id=&date_from=&date_to=

GET  /api/system/health
GET  /api/system/metrics
```

## 12. WebSocket

```
WS /ws/events?token=<JWT>&warehouse_id=

Server → Client message types:
  NEW_INCIDENT        { incident_id, risk_level, behaviour, zone, timestamp }
  RISK_ESCALATED       { incident_id, old_level, new_level }
  ALERT_CREATED         { alert_id, incident_id, severity }
  CAMERA_OFFLINE          { camera_id }
  PROCESSING_COMPLETE      { job_id, video_id }
  REVIEW_REQUIRED           { behaviour_event_id }
```

## 13. Standard Error Shape

```json
{ "error": { "code": "STRING_CODE", "message": "Human readable message" } }
```

## 14. Response Example — `GET /api/incidents/{id}`

```json
{
  "incident_id": "INC-1042",
  "status": "UNDER_REVIEW",
  "behaviour": "PRODUCT_DROP",
  "zone": "Loading Bay 2",
  "camera_id": "CAM-04",
  "risk": {
    "score": 84,
    "level": "HIGH",
    "confidence": 0.91,
    "factors": {"behaviour_severity": 25, "drop_height": 18,
                "product_fragility": 15, "impact_estimate": 10,
                "repeated_behaviour": 5, "location_factor": 5}
  },
  "damage": {"probability": 0.82, "category": "packaging_deformation",
             "status": "POTENTIAL_DAMAGE", "confidence": 0.81},
  "evidence": {"clip_url": "...", "snapshot_url": "...",
               "trajectory": [...], "checksum": "..."},
  "root_cause": {"category": "process", "description": "Repeated event, same zone, peak time",
                 "is_ai_inferred": true, "confidence": 0.68},
  "recommendation": {"text": "Use trolley/pallet truck.",
                      "estimated_risk_reduction": [35, 50], "confidence": 0.74},
  "counterfactual": {"observed_risk": 82, "alternative_risk": 31,
                      "alternative_scenario": "Trolley movement → controlled placement"}
}
```
