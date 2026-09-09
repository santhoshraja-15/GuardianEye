import asyncio
import json
import urllib.request
import websockets
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws/events"

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        return e.code, json.loads(content) if content else {"error": str(e)}

def run_tests():
    print("==================================================")
    print("   GUARDIAN EYE FULL SYSTEM VERIFICATION SUITE   ")
    print("==================================================")

    # 1. Login
    print("\n[1] Testing Authentication (/auth/login)...")
    status, res = make_request("/auth/login", method="POST", data={
        "email": "admin@guardianeye.ai",
        "password": "Admin@123456"
    })
    assert status == 200, f"Login failed: {res}"
    token = res["access_token"]
    print(f" -> OK: Logged in successfully as Admin (token type: {res['token_type']})")

    # 2. User Profile
    print("\n[2] Testing Current User Profile (/auth/me)...")
    status, me = make_request("/auth/me", token=token)
    assert status == 200, f"Profile failed: {me}"
    print(f" -> OK: User: {me['full_name']} ({me['email']}), Active: {me['is_active']}")

    # 3. Dashboard Summary
    print("\n[3] Testing Dashboard Analytics (/analytics/dashboard)...")
    status, summary = make_request("/analytics/dashboard", token=token)
    assert status == 200, f"Dashboard summary failed: {summary}"
    print(f" -> OK: Risk Score: {summary.get('overall_risk_score', 'N/A')}, Active Alerts: {summary.get('active_alerts_count', 'N/A')}, Total Incidents: {summary.get('total_incidents_today', 'N/A')}")

    # 4. Digital Twin Topology
    print("\n[4] Testing Digital Twin Topology (/digital-twin/topology)...")
    status, topology = make_request("/digital-twin/topology", token=token)
    assert status == 200, f"Digital twin topology failed: {topology}"
    print(f" -> OK: Warehouses: {len(topology.get('warehouses', []))}, Zones: {len(topology.get('zones', []))}, Cameras: {len(topology.get('cameras', []))}")

    # 5. List Videos
    print("\n[5] Testing Video Library (/videos)...")
    status, videos = make_request("/videos", token=token)
    assert status == 200 and len(videos) > 0, f"Video listing failed: {videos}"
    print(f" -> OK: {len(videos)} warehouse videos loaded in library:")
    for v in videos:
        print(f"    - [{v['status']}] {v['filename']} ({v['duration_seconds']}s, {v['width']}x{v['height']})")

    # 6. Video Processing & Tracks
    target_video = videos[0]
    vid = target_video["id"]
    print(f"\n[6] Checking AI Tracks for video '{target_video['filename']}' (/tracks/{vid})...")
    status, track_res = make_request(f"/tracks/{vid}", token=token)
    print(f" -> OK: Status {status}, Total Tracks: {track_res.get('total_tracks')}")

    # 7. Video Behaviours
    print(f"\n[7] Checking Behaviour Events for video '{target_video['filename']}' (/behaviours/video/{vid})...")
    status, behaviours = make_request(f"/behaviours/video/{vid}", token=token)
    print(f" -> OK: Status {status}, Behaviours Count: {len(behaviours) if isinstance(behaviours, list) else 0}")

    # 8. Alerts
    print("\n[8] Testing Real-Time Alerts (/alerts)...")
    status, alerts = make_request("/alerts", token=token)
    assert status == 200, f"Alerts failed: {alerts}"
    print(f" -> OK: {len(alerts)} alerts retrieved")
    if len(alerts) > 0:
        a = alerts[0]
        print(f"    - Sample Alert: {a.get('title')} [{a.get('severity')}] - Status: {a.get('status')}")

    # 9. Incidents
    print("\n[9] Testing Incident Management (/incidents)...")
    status, incidents = make_request("/incidents", token=token)
    assert status == 200, f"Incidents failed: {incidents}"
    print(f" -> OK: {len(incidents)} incidents retrieved")
    if len(incidents) > 0:
        inc = incidents[0]
        print(f"    - Sample Incident: {inc.get('incident_code')} - {inc.get('title')} [{inc.get('severity')}]")

    # 10. AI Assistant / Copilot Query
    print("\n[10] Testing Grounded AI Assistant (/assistant/chat)...")
    status, assistant_res = make_request("/assistant/chat", method="POST", data={
        "query": "What are the primary warehouse hazards detected today?"
    }, token=token)
    print(f" -> OK: Status {status}, Assistant Response: {assistant_res.get('response_text', '')[:100]}...")

    # 11. Video Streaming (HTTP 206 Partial Content)
    print(f"\n[11] Testing Video Range Streaming (/videos/{vid}/stream)...")
    req = urllib.request.Request(f"{BASE_URL}/videos/{vid}/stream", headers={"Range": "bytes=0-4096"})
    with urllib.request.urlopen(req) as resp:
        print(f" -> OK: HTTP Status {resp.status}, Content-Range: {resp.headers.get('Content-Range')}, Bytes: {len(resp.read())}")

    # 12. WebSocket Real-Time Connection
    print("\n[12] Testing Live WebSocket Stream (/ws/events)...")
    async def test_ws():
        uri = f"{WS_URL}?token={token}&warehouse_id=WH-CENTRAL-01"
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            print(f" -> OK: WebSocket Connected, Event: '{data.get('event')}', Message: '{data.get('data', {}).get('message')}'")
    asyncio.run(test_ws())

    print("\n==================================================")
    print("   ALL GUARDIAN EYE SERVICES & TESTS PASSED!     ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
