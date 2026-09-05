# Database Schema Document
## W-SAFE — PostgreSQL Schema (+ pgvector)

Central relational database. All tables live in PostgreSQL; embeddings use the
`pgvector` extension so no separate vector database is required.

## 1. Table Groups

```
users, roles
warehouses, zones, cameras, video_sources, videos, processing_jobs
objects, object_tracks, interactions
behaviours, behaviour_events, behaviour_sequences
products, equipment
risk_assessments, damage_predictions, predictions
incidents, alerts, incident_actions
evidence, root_causes, recommendations, counterfactuals
reviews, datasets, dataset_versions
models, model_versions, model_evaluations
audit_logs, system_events, notifications
```

## 2. Entity Relationship (simplified)

```
Camera
  │
  └── Video Session
          │
          ├── Objects ── Object Tracks
          │
          └── Behaviour Events
                    │
                    └── Incident
                           │
                           ├── Alert
                           ├── Evidence
                           ├── Root Cause
                           └── Recommendation ── Counterfactual
```

## 3. Illustrative DDL (core tables — extend per `SYSTEM_DESIGN.md`)

```sql
CREATE EXTENSION IF NOT EXISTS pgvector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN','SUPERVISOR','SAFETY_OFFICER','ANALYST','OPERATOR')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL
);

CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL, -- loading_bay, staging, storage, pedestrian_lane, forklift_lane, restricted
    polygon JSONB NOT NULL   -- list of [x,y] points
);

CREATE TABLE cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    zone_id UUID REFERENCES zones(id),
    source_type TEXT NOT NULL, -- file, rtsp, vms, webcam
    stream_url TEXT,
    status TEXT DEFAULT 'OFFLINE',
    fps INT,
    resolution TEXT,
    last_seen TIMESTAMPTZ
);

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id),
    storage_url TEXT NOT NULL,
    duration_seconds NUMERIC,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    status TEXT DEFAULT 'QUEUED', -- QUEUED, RUNNING, DONE, FAILED
    progress NUMERIC DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_type TEXT NOT NULL,
    fragility TEXT NOT NULL,      -- low/medium/high
    weight_kg NUMERIC,
    dimensions TEXT,
    handling_requirement TEXT,
    max_drop_height_cm NUMERIC,
    stacking_limit INT,
    orientation_requirement TEXT,
    equipment_requirement TEXT
);

CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_type TEXT NOT NULL -- trolley, pallet_truck, forklift, other
);

CREATE TABLE objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    class TEXT NOT NULL,
    confidence NUMERIC,
    bbox JSONB,
    frame_number INT,
    timestamp NUMERIC
);

CREATE TABLE object_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    track_id TEXT NOT NULL,
    object_class TEXT NOT NULL,
    trajectory JSONB, -- ordered list of {frame, x, y, w, h, velocity, acceleration}
    first_seen NUMERIC,
    last_seen NUMERIC,
    status TEXT DEFAULT 'ACTIVE' -- ACTIVE, LOST, REACQUIRED
);

CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    subject_track_id UUID REFERENCES object_tracks(id),
    object_track_id UUID REFERENCES object_tracks(id),
    relation TEXT NOT NULL, -- holding, near, placed_on, colliding, etc.
    start_ts NUMERIC,
    end_ts NUMERIC
);

CREATE TABLE behaviours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,   -- B01, B02, ...
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE behaviour_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    behaviour_id UUID REFERENCES behaviours(id),
    primary_track_id UUID REFERENCES object_tracks(id),
    confidence NUMERIC,
    start_ts NUMERIC,
    end_ts NUMERIC,
    zone_id UUID REFERENCES zones(id),
    classification TEXT DEFAULT 'KNOWN' -- KNOWN, UNKNOWN, AMBIGUOUS
);

CREATE TABLE behaviour_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    behaviour_event_id UUID REFERENCES behaviour_events(id),
    sequence JSONB NOT NULL, -- ["APPROACH","HOLD","MOVE","ACCELERATE","RELEASE","FALL","IMPACT","STOP"]
    embedding VECTOR(768)     -- pgvector column for similarity search
);

CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    behaviour_event_id UUID REFERENCES behaviour_events(id),
    behaviour_risk NUMERIC,
    damage_risk NUMERIC,
    safety_consequence NUMERIC,
    risk_score NUMERIC,
    risk_level TEXT, -- LOW, MEDIUM, HIGH, CRITICAL
    factor_breakdown JSONB,
    confidence NUMERIC
);

CREATE TABLE damage_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    behaviour_event_id UUID REFERENCES behaviour_events(id),
    damage_probability NUMERIC,
    damage_category TEXT,
    damage_status TEXT DEFAULT 'NOT_OBSERVED', -- NOT_OBSERVED, POTENTIAL_DAMAGE, CONFIRMED_BY_HUMAN, CONFIRMED_BY_EXTERNAL_SYSTEM
    confidence NUMERIC
);

CREATE TABLE predictions ( -- predictive risk engine outputs
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES zones(id),
    predicted_behaviour_id UUID REFERENCES behaviours(id),
    probability NUMERIC,
    horizon_seconds INT,
    confidence NUMERIC,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    behaviour_event_id UUID REFERENCES behaviour_events(id),
    risk_assessment_id UUID REFERENCES risk_assessments(id),
    damage_prediction_id UUID REFERENCES damage_predictions(id),
    status TEXT DEFAULT 'DETECTED', -- DETECTED, ALERTED, ACKNOWLEDGED, UNDER_REVIEW, CONFIRMED, REJECTED, ACTION_TAKEN, RESOLVED
    zone_id UUID REFERENCES zones(id),
    camera_id UUID REFERENCES cameras(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    severity TEXT,
    status TEXT DEFAULT 'OPEN', -- OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, REJECTED, DISMISSED
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE incident_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    user_id UUID REFERENCES users(id),
    action TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    snapshot_url TEXT,
    clip_url TEXT,
    start_frame INT,
    end_frame INT,
    trajectory JSONB,
    model_version TEXT,
    checksum TEXT
);

CREATE TABLE root_causes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    category TEXT, -- equipment, environment, process, congestion, workflow, placement, handling, training, infrastructure, unknown
    description TEXT,
    is_ai_inferred BOOLEAN DEFAULT TRUE,
    confidence NUMERIC
);

CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    recommendation_text TEXT,
    reason TEXT,
    estimated_risk_reduction_min NUMERIC,
    estimated_risk_reduction_max NUMERIC,
    confidence NUMERIC,
    embedding VECTOR(768)
);

CREATE TABLE counterfactuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    observed_scenario TEXT,
    alternative_scenario TEXT,
    observed_risk NUMERIC,
    alternative_risk NUMERIC,
    assumptions JSONB
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    behaviour_event_id UUID REFERENCES behaviour_events(id),
    reviewer_id UUID REFERENCES users(id),
    verdict TEXT, -- CORRECT, INCORRECT, CHANGE_BEHAVIOUR, UNCERTAIN
    corrected_behaviour_id UUID REFERENCES behaviours(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    description TEXT
);

CREATE TABLE dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    version TEXT,
    record_count INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type TEXT -- detection, tracking, behaviour, risk, damage
);

CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES models(id),
    version TEXT,
    dataset_version_id UUID REFERENCES dataset_versions(id),
    training_date TIMESTAMPTZ,
    metrics JSONB,
    parameters JSONB,
    status TEXT DEFAULT 'TRAINING', -- TRAINING, EVALUATION, APPROVED, DEPLOYED, RETIRED, REJECTED
    approved_by UUID REFERENCES users(id),
    deployment_date TIMESTAMPTZ
);

CREATE TABLE model_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id UUID REFERENCES model_versions(id),
    metric_name TEXT,
    metric_value NUMERIC
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action TEXT,
    entity_type TEXT,
    entity_id UUID,
    previous_value JSONB,
    new_value JSONB,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    message TEXT,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 4. Indexing Notes

- Index `incidents(status)`, `incidents(created_at)`, `incidents(zone_id)` for
  dashboard queries.
- Index `behaviour_events(video_id)`, `behaviour_events(behaviour_id)`.
- Use an IVFFLAT or HNSW pgvector index on `behaviour_sequences.embedding` and
  `recommendations.embedding` once row counts justify it.
- Partition `objects`/`object_tracks` by video/date if raw-frame volume grows
  large.

## 5. Retention Policy Mapping

| Data class | Suggested retention |
|---|---|
| Raw video (`videos`) | Short, configurable (e.g. 7–30 days) |
| Incident evidence (`evidence`) | Longer (e.g. 90–365 days) per policy |
| Aggregated analytics | Long-term / indefinite |

Exact durations must be configurable per organizational policy, not hard-coded.
