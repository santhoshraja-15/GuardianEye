# Deployment Guide
## W-SAFE — Docker Compose, Environment, GPU, Monitoring

## 1. Docker Compose Services

```yaml
# docker-compose.yml (illustrative — adapt paths/images to your repo)
version: "3.9"
services:
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://wsafe:wsafe@postgres:5432/wsafe
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - JWT_SECRET=${JWT_SECRET}
      - LLM_API_KEY=${LLM_API_KEY}
    depends_on: [postgres, redis, minio]

  ai-worker:
    build: ./ai
    environment:
      - DATABASE_URL=postgresql://wsafe:wsafe@postgres:5432/wsafe
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - INFERENCE_DEVICE=cuda   # or cpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on: [postgres, redis, minio]

  postgres:
    image: ankane/pgvector:latest
    environment:
      - POSTGRES_USER=wsafe
      - POSTGRES_PASSWORD=wsafe
      - POSTGRES_DB=wsafe
    volumes: ["pgdata:/var/lib/postgresql/data"]
    ports: ["5432:5432"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=wsafe
      - MINIO_ROOT_PASSWORD=wsafe123
    volumes: ["miniodata:/data"]
    ports: ["9000:9000", "9001:9001"]

  prometheus:
    image: prom/prometheus
    volumes: ["./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
    depends_on: [prometheus]

volumes:
  pgdata:
  miniodata:
```

## 2. Environment Variables

```
# backend/.env
DATABASE_URL=postgresql://wsafe:wsafe@postgres:5432/wsafe
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=wsafe
S3_SECRET_KEY=wsafe123
S3_BUCKET=wsafe-videos
JWT_SECRET=change-me
LLM_API_KEY=your-llm-key
LLM_MODEL=your-model-name
YOLO_WEIGHTS_PATH=/models/yolo_wsafe.pt
INFERENCE_DEVICE=cuda
DEFAULT_RISK_THRESHOLDS=25,50,75
ALERT_COOLDOWN_SECONDS=10
RETENTION_RAW_VIDEO_DAYS=14
RETENTION_EVIDENCE_DAYS=180
```

## 3. Local Development Startup

```bash
git clone <repo>
cd warehouse-ai
cp backend/.env.example backend/.env   # fill in secrets
docker compose up --build
# frontend: http://localhost:5173
# backend docs: http://localhost:8000/docs
# grafana: http://localhost:3000
# minio console: http://localhost:9001
```

Run migrations:
```bash
docker compose exec backend alembic upgrade head
```

Seed reference data (behaviours, sample zones/products):
```bash
docker compose exec backend python scripts/seed.py
```

## 4. GPU Setup

- Install NVIDIA drivers + `nvidia-container-toolkit` on the host.
- Confirm with `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi`.
- Set `INFERENCE_DEVICE=cuda` for the `ai-worker` service; the pipeline should
  gracefully fall back to `cpu` if no GPU is present (slower, but functional
  for development).

## 5. Monitoring Setup

- Prometheus scrapes `backend` and `ai-worker` metrics endpoints (expose
  `/metrics` via a FastAPI middleware / Celery exporter).
- Grafana dashboards: FPS, inference latency, queue length, camera health,
  API latency, DB/Redis health, storage usage, worker status.

## 6. Production Considerations (beyond hackathon prototype)

- Terminate TLS at a reverse proxy (e.g. Nginx/Traefik) in front of
  `frontend`/`backend`.
- Move object storage to real S3 (or equivalent) instead of MinIO.
- Externalize secrets to a secret manager instead of `.env` files.
- Consider Kubernetes only once multi-warehouse/multi-tenant scale is
  actually needed — not before (see `TECH_STACK.md` §4).
- Introduce Kafka only if the platform scales to many warehouses with heavy
  streaming (not required at prototype/single-warehouse scale).

## 7. Backup & Disaster Recovery (lightweight, for a longer-lived deployment)

- Nightly `pg_dump` of PostgreSQL, retained per the configured retention
  policy.
- MinIO/S3 versioning enabled on the evidence bucket.
- Document a runbook: what to do on camera-offline, worker-crash, and
  DB-connection-loss events, mapped to `SYSTEM_DESIGN.md` §12 Failure
  Handling.

## 8. Rollback Strategy

- Model rollback: model registry keeps prior `DEPLOYED`/`RETIRED` versions —
  redeploying is a config change (point `ai-worker` at the prior
  `model_version_id`), not a rebuild.
- App rollback: tag Docker images per release; `docker compose` down to a
  prior tagged image set if a deploy regresses golden-test metrics.
