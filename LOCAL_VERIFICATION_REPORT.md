# GuardianEye Local Execution & Verification Report

## 1. System Overview & Running Services

GuardianEye is running locally with all backend API routes, AI detection & tracking pipelines, SQLite relational database, WebSocket real-time events, and Vite React frontend active.

| Service | Localhost URL | Port | Status |
|---|---|---|---|
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | 3000 | **ONLINE (HTTP 200)** |
| **Backend FastAPI API** | [http://localhost:8000](http://localhost:8000) | 8000 | **ONLINE (HTTP 200)** |
| **API Documentation (Swagger UI)** | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | 8000 | **ONLINE** |
| **Realtime WebSocket Stream** | `ws://localhost:3000/api/v1/ws/events` / `ws://localhost:8000/api/v1/ws/events` | 3000 / 8000 | **CONNECTED (`connection_ok`)** |
| **Database** | SQLite embedded at `./data/guardian_eye.db` | - | **INITIALIZED & SEEDED** |
| **Storage Engine** | Local File Storage at `./storage` | - | **ACTIVE (Videos, Snapshots, Clips)** |

---

## 2. Test Credentials

| Role | Email | Password | Permissions |
|---|---|---|---|
| **System Administrator** | `admin@guardianeye.ai` | `Admin@123456` | Full system access |
| **Warehouse Supervisor** | `supervisor@guardianeye.ai` | `Supervisor@123456` | Read, Write, Review, Acknowledge |
| **Safety Compliance Officer** | `safety@guardianeye.ai` | `Safety@123456` | Read, Review, Report, Export |
| **Terminal Operator** | `operator@guardianeye.ai` | `Operator@123456` | Read, Acknowledge |

---

## 3. Startup Commands

### Prerequisites
- Python 3.12+ (Virtual environment in `.venv`)
- Node.js 18+ & npm

### Backend API Server
```powershell
# From project root
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Development Server
```powershell
# From frontend directory
cd frontend
npm run dev
```

### Database Seeding & Video Cataloging (One-time or Reset)
```powershell
.venv\Scripts\python.exe -m backend.app.database.seed
```

---

## 4. End-to-End Verification Results

### Automated Test Suites
- **Backend Pytest Suite:** `55 passed` in 10.97s (Unit tests, CV algorithms, Kalman filter, ByteTrack, Behaviour FSMs, Risk calculations, RBAC, WebSockets).
- **Frontend Vitest Suite:** `42 passed` in 8.04s across 9 test files (App shell, Auth flow, Dashboard command center, Digital twin, Incidents, Evidence, Realtime manager).
- **Live Verification Script:** `12/12 test stages passed`:
  1. Authentication (`/auth/login` -> JWT Token)
  2. Profile Retrieval (`/auth/me`)
  3. Analytics Dashboard (`/analytics/dashboard`)
  4. Digital Twin Topology (`/digital-twin/topology`)
  5. Video Library Catalog (7 warehouse videos)
  6. AI Detection & Tracking (`/tracks/{video_id}` -> 17 entity tracks)
  7. Behaviour Intelligence (`/behaviours/video/{video_id}`)
  8. Real-time Alert Management (`/alerts`)
  9. Incident Management (`/incidents`)
  10. Grounded AI Assistant Copilot (`/assistant/chat`)
  11. HTTP 206 Partial Content Video Streaming (`/videos/{video_id}/stream`)
  12. WebSocket Real-time Event Connection (`/ws/events`)

---

## 5. Issues Identified & Fixed

1. **Digital Twin Topology Model Attribute Mismatch:**
   - **Issue:** `digital_twin_service.py` referenced `.zone_code`, `.zone_name`, `.risk_multiplier`, and `.camera_name` instead of `.code`, `.name`, `.risk_weight`, and `.name`.
   - **Fix:** Corrected property access to match SQLAlchemy `Zone` and `Camera` models in `backend/app/services/digital_twin_service.py`.
2. **Local SQLite & Local Storage Configuration:**
   - **Configuration:** Created `.env` tailored for local execution with SQLite (`./data/guardian_eye.db`), local storage (`./storage`), and YOLO CPU inference.
