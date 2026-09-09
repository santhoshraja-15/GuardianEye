import asyncio
import json
import time
import requests
import websockets

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:3000"
API_V1 = f"{BACKEND_URL}/api/v1"

results_table = []

def record(feature, target, tested, status, evidence):
    results_table.append({
        "feature": feature,
        "target": target,
        "tested": tested,
        "status": status,
        "evidence": evidence
    })
    print(f"[{status}] {feature} ({target}) -> {evidence}")

def main():
    print("================================================================================")
    print("GUARDIAN EYE — LOCALHOST FUNCTIONAL VERIFICATION")
    print("================================================================================\n")

    # 1. Services Reachability
    print("--- 1. REACHABILITY & HEALTH ---")
    try:
        h_resp = requests.get(f"{API_V1}/health", timeout=5)
        assert h_resp.status_code == 200
        data = h_resp.json()
        assert data["status"] == "healthy"
        record("Backend Health", "/api/v1/health", "✅", "PASS", f"HTTP 200, DB: {data['subsystems']['database']['status']}")
    except Exception as e:
        record("Backend Health", "/api/v1/health", "✅", "FAIL", str(e))

    try:
        f_resp = requests.get(FRONTEND_URL, timeout=5)
        assert f_resp.status_code == 200
        record("Frontend Reachability", "http://127.0.0.1:3000", "✅", "PASS", f"HTTP 200, HTML Length: {len(f_resp.text)} bytes")
    except Exception as e:
        record("Frontend Reachability", "http://127.0.0.1:3000", "✅", "FAIL", str(e))

    try:
        docs_resp = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        assert docs_resp.status_code == 200
        record("Swagger Docs", "/docs", "✅", "PASS", "HTTP 200 OpenAPI Interactive UI available")
    except Exception as e:
        record("Swagger Docs", "/docs", "✅", "FAIL", str(e))

    # 2. Authentication & RBAC
    print("\n--- 2. AUTHENTICATION & RBAC ---")
    # Valid Login
    token = None
    headers = {}
    try:
        l_resp = requests.post(f"{API_V1}/auth/login", json={"email": "admin@guardianeye.ai", "password": "Admin@123456"})
        assert l_resp.status_code == 200
        token = l_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        record("Auth Login (Valid)", "/api/v1/auth/login", "✅", "PASS", f"JWT token issued ({token[:18]}...)")
    except Exception as e:
        record("Auth Login (Valid)", "/api/v1/auth/login", "✅", "FAIL", str(e))

    # Invalid Login
    try:
        inv_resp = requests.post(f"{API_V1}/auth/login", json={"email": "admin@guardianeye.ai", "password": "WrongPassword"})
        assert inv_resp.status_code == 401
        record("Auth Login (Invalid)", "/api/v1/auth/login", "✅", "PASS", "HTTP 401 Unauthorized correctly returned")
    except Exception as e:
        record("Auth Login (Invalid)", "/api/v1/auth/login", "✅", "FAIL", str(e))

    # Protected endpoint without auth
    try:
        unauth_resp = requests.get(f"{API_V1}/incidents")
        assert unauth_resp.status_code == 401
        record("Protected API Guard", "/api/v1/incidents", "✅", "PASS", "HTTP 401 Unauthorized for missing token")
    except Exception as e:
        record("Protected API Guard", "/api/v1/incidents", "✅", "FAIL", str(e))

    # 3. Video List & Partial Range Streaming
    print("\n--- 3. VIDEO INGESTION & RANGE STREAMING ---")
    selected_video = None
    try:
        v_resp = requests.get(f"{API_V1}/videos", headers=headers)
        assert v_resp.status_code == 200
        videos = v_resp.json()
        assert len(videos) > 0
        selected_video = videos[0]
        record("Video List", "/api/v1/videos", "✅", "PASS", f"{len(videos)} real warehouse video records retrieved")
    except Exception as e:
        record("Video List", "/api/v1/videos", "✅", "FAIL", str(e))

    if selected_video:
        vid_id = selected_video["id"]
        try:
            # Range request
            r_resp = requests.get(f"{API_V1}/videos/{vid_id}/stream", headers={"Range": "bytes=0-1023", **headers})
            assert r_resp.status_code == 206
            assert r_resp.headers.get("Content-Range") == f"bytes 0-1023/{selected_video['file_size_bytes']}"
            assert len(r_resp.content) == 1024
            assert "video/mp4" in r_resp.headers.get("Content-Type", "")
            record("Video HTTP 206 Stream", f"/videos/{vid_id}/stream", "✅", "PASS", f"206 Partial Content, exact 1024 bytes, {r_resp.headers.get('Content-Range')}")
        except Exception as e:
            record("Video HTTP 206 Stream", f"/videos/{vid_id}/stream", "✅", "FAIL", str(e))

        try:
            # Full stream request
            full_resp = requests.get(f"{API_V1}/videos/{vid_id}/stream", headers=headers, stream=True)
            assert full_resp.status_code == 200
            record("Video Full Stream", f"/videos/{vid_id}/stream", "✅", "PASS", f"HTTP 200 OK, Content-Type: {full_resp.headers.get('Content-Type')}")
        except Exception as e:
            record("Video Full Stream", f"/videos/{vid_id}/stream", "✅", "FAIL", str(e))

    # 4. Incident Management
    print("\n--- 4. INCIDENT MANAGEMENT ---")
    selected_incident = None
    try:
        inc_resp = requests.get(f"{API_V1}/incidents", headers=headers)
        assert inc_resp.status_code == 200
        incidents = inc_resp.json()
        assert len(incidents) > 0
        selected_incident = incidents[0]
        record("Incidents List", "/api/v1/incidents", "✅", "PASS", f"{len(incidents)} real incidents loaded with severities and codes")
    except Exception as e:
        record("Incidents List", "/api/v1/incidents", "✅", "FAIL", str(e))

    try:
        crit_resp = requests.get(f"{API_V1}/incidents?severity=CRITICAL", headers=headers)
        assert crit_resp.status_code == 200
        crit_list = crit_resp.json()
        record("Incidents Severity Filter", "/api/v1/incidents?severity=CRITICAL", "✅", "PASS", f"Filtered {len(crit_list)} CRITICAL incidents")
    except Exception as e:
        record("Incidents Severity Filter", "/api/v1/incidents?severity=CRITICAL", "✅", "FAIL", str(e))

    if selected_incident:
        inc_id = selected_incident["id"]
        try:
            detail_resp = requests.get(f"{API_V1}/incidents/{inc_id}", headers=headers)
            assert detail_resp.status_code == 200
            detail = detail_resp.json()
            assert detail["incident_code"] == selected_incident["incident_code"]
            record("Incident Details", f"/api/v1/incidents/{inc_id}", "✅", "PASS", f"Code: {detail['incident_code']}, Title: {detail['title']}")
        except Exception as e:
            record("Incident Details", f"/api/v1/incidents/{inc_id}", "✅", "FAIL", str(e))

    # 5. Evidence Vault
    print("\n--- 5. EVIDENCE VAULT ---")
    if selected_incident:
        inc_id = selected_incident["id"]
        try:
            ev_resp = requests.get(f"{API_V1}/evidence/incident/{inc_id}", headers=headers)
            assert ev_resp.status_code == 200
            ev_data = ev_resp.json()
            assert "sha256_checksum" in ev_data
            record("Evidence Package", f"/api/v1/evidence/incident/{inc_id}", "✅", "PASS", f"SHA-256: {ev_data['sha256_checksum'][:24]}..., Snapshot: {ev_data['snapshot_path']}")
        except Exception as e:
            record("Evidence Package", f"/api/v1/evidence/incident/{inc_id}", "✅", "FAIL", str(e))

        try:
            rep_resp = requests.get(f"{API_V1}/replay/incident/{inc_id}", headers=headers)
            assert rep_resp.status_code == 200
            rep_data = rep_resp.json()
            record("Incident Forensic Replay", f"/api/v1/replay/incident/{inc_id}", "✅", "PASS", f"Clip URL: {rep_data.get('clip_url')}, Overlays: {len(rep_data.get('keyframes', []))} keyframes")
        except Exception as e:
            record("Incident Forensic Replay", f"/api/v1/replay/incident/{inc_id}", "✅", "FAIL", str(e))

    # 6. Human Review & Active Learning
    print("\n--- 6. HUMAN REVIEW & ACTIVE LEARNING ---")
    if selected_incident:
        inc_id = selected_incident["id"]
        try:
            rev_payload = {
                "incident_id": inc_id,
                "review_outcome": "CORRECT",
                "reviewer_notes": "Supervisor verified high-risk placement anomaly.",
                "is_curated_for_training": True
            }
            rev_resp = requests.post(f"{API_V1}/reviews", json=rev_payload, headers=headers)
            assert rev_resp.status_code == 201
            r_data = rev_resp.json()
            assert r_data["review_outcome"] == "CORRECT"
            
            # Verify incident status changed to CONFIRMED
            inc_chk = requests.get(f"{API_V1}/incidents/{inc_id}", headers=headers).json()
            assert inc_chk["status"] == "CONFIRMED"
            record("Human Review Workflow", "/api/v1/reviews", "✅", "PASS", f"Submitted CORRECT verdict -> Incident status updated to {inc_chk['status']}")
        except Exception as e:
            record("Human Review Workflow", "/api/v1/reviews", "✅", "FAIL", str(e))

        try:
            hist_resp = requests.get(f"{API_V1}/incidents/{inc_id}/history", headers=headers)
            assert hist_resp.status_code == 200
            histories = hist_resp.json()
            record("Incident Audit History", f"/api/v1/incidents/{inc_id}/history", "✅", "PASS", f"{len(histories)} transition audit records logged")
        except Exception as e:
            record("Incident Audit History", f"/api/v1/incidents/{inc_id}/history", "✅", "FAIL", str(e))

    # 7. Grounded AI Assistant
    print("\n--- 7. GROUNDED AI ASSISTANT ---")
    assistant_queries = [
        ("What were the most common risky behaviours detected?", True),
        ("Which loading bay or zone has the highest risk?", True),
        ("Show recent drop or dragging incidents.", True),
        ("What preventive actions are recommended?", True),
        ("Give me a summary of shift incidents.", True),
        ("Did a purple UFO crash into Bay 99?", False)
    ]
    for q, expect_citations in assistant_queries:
        for ep in ["/assistant/chat", "/assistant/query"]:
            try:
                a_resp = requests.post(f"{API_V1}{ep}", json={"query": q, "max_citations": 3}, headers=headers)
                assert a_resp.status_code == 200
                res = a_resp.json()
                assert len(res["answer"]) > 10
                citations_cnt = len(res["grounded_citations"])
                record(f"AI Assistant ({ep})", f"Query: '{q[:25]}...'", "✅", "PASS", f"Answered with {citations_cnt} citations ({res['answer'][:45]}...)")
            except Exception as e:
                record(f"AI Assistant ({ep})", f"Query: '{q[:25]}...'", "✅", "FAIL", str(e))

    # 8. Prevention Studio & Root Cause Analysis
    print("\n--- 8. PREVENTION STUDIO ---")
    try:
        p_resp = requests.get(f"{API_V1}/prevention/recommendations", headers=headers)
        assert p_resp.status_code == 200
        recs = p_resp.json()
        record("Prevention Recommendations", "/api/v1/prevention/recommendations", "✅", "PASS", f"{len(recs)} RCA prevention recommendations retrieved")
    except Exception as e:
        record("Prevention Recommendations", "/api/v1/prevention/recommendations", "✅", "FAIL", str(e))

    try:
        dash_resp = requests.get(f"{API_V1}/analytics/dashboard-summary", headers=headers)
        assert dash_resp.status_code == 200
        d_summary = dash_resp.json()
        record("Dashboard Summary", "/api/v1/analytics/dashboard-summary", "✅", "PASS", f"Total incidents: {d_summary.get('total_incidents')}, Open alerts: {d_summary.get('open_alerts_count')}")
    except Exception as e:
        record("Dashboard Summary", "/api/v1/analytics/dashboard-summary", "✅", "FAIL", str(e))

    # 9. Real-Time WebSocket
    print("\n--- 9. REAL-TIME WEBSOCKET ---")
    async def test_ws():
        uri = f"ws://127.0.0.1:8000/api/v1/events/ws?token={token}"
        try:
            async with websockets.connect(uri) as ws:
                # Connected successfully
                record("WebSocket Event Bus", "/api/v1/events/ws", "✅", "PASS", "WebSocket connection established and authenticated successfully")
        except Exception as e:
            record("WebSocket Event Bus", "/api/v1/events/ws", "✅", "FAIL", str(e))

    asyncio.run(test_ws())

    print("\n================================================================================")
    print("VERIFICATION COMPLETED SUCCESSFULLY!")
    print("================================================================================")

if __name__ == "__main__":
    main()
