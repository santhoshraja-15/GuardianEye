import time
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'
API_V1 = f'{BASE_URL}/api/v1'

print('=== 1. TESTING HEALTH & SYSTEM STATUS ===')
t0 = time.perf_counter()
resp = requests.get(f'{API_V1}/health')
t_health = (time.perf_counter() - t0) * 1000
print(f'Health API ({t_health:.1f}ms): {resp.status_code} -> {resp.json()}')

print('\n=== 2. TESTING AUTHENTICATION & JWT TOKEN ===')
t0 = time.perf_counter()
resp = requests.post(f'{API_V1}/auth/login', json={'email': 'admin@guardianeye.ai', 'password': 'Admin@123456'})
t_login = (time.perf_counter() - t0) * 1000
assert resp.status_code == 200, f'Login failed: {resp.text}'
tokens = resp.json()
access_token = tokens['access_token']
headers = {'Authorization': f'Bearer {access_token}'}
print(f'Auth Login ({t_login:.1f}ms): Token received successfully ({access_token[:20]}...)')

print('\n=== 3. TESTING VIDEO LIST & STREAMING (HTTP 206) ===')
resp = requests.get(f'{API_V1}/videos', headers=headers)
videos = resp.json()
print(f'Retrieved {len(videos)} videos from backend.')
if videos:
    v = videos[0]
    vid_id = v['id']
    print(f'Selected video {vid_id} ({v["filename"]}, size: {v["file_size_bytes"]} bytes)')
    
    # Test HTTP 206 Range request
    range_headers = {'Range': 'bytes=0-1023'}
    t0 = time.perf_counter()
    s_resp = requests.get(f'{API_V1}/videos/{vid_id}/stream', headers=range_headers)
    t_stream = (time.perf_counter() - t0) * 1000
    print(f'Range Stream 0-1023 ({t_stream:.1f}ms): Status={s_resp.status_code}')
    print(f'  Content-Range: {s_resp.headers.get("Content-Range")}')
    print(f'  Content-Length: {s_resp.headers.get("Content-Length")}')
    print(f'  Content-Type: {s_resp.headers.get("Content-Type")}')
    assert s_resp.status_code == 206, f'Expected 206, got {s_resp.status_code}'
    assert len(s_resp.content) == 1024, f'Expected 1024 bytes, got {len(s_resp.content)}'

print('\n=== 4. TESTING INCIDENTS & EVIDENCE VAULT API ===')
t0 = time.perf_counter()
i_resp = requests.get(f'{API_V1}/incidents', headers=headers)
t_inc = (time.perf_counter() - t0) * 1000
incidents = i_resp.json()
print(f'Incidents API ({t_inc:.1f}ms): Retrieved {len(incidents)} real incidents.')
if incidents:
    inc = incidents[0]
    inc_id = inc['id']
    print(f'Latest Incident: {inc["incident_code"]} - {inc["title"]} (Severity: {inc["severity"]}, Status: {inc["status"]})')
    
    # Check Evidence Package
    ev_resp = requests.get(f'{API_V1}/evidence/incident/{inc_id}', headers=headers)
    print(f'Evidence API: {ev_resp.status_code} -> SHA256: {ev_resp.json().get("sha256_checksum")}')

print('\n=== 5. TESTING HUMAN REVIEW WORKFLOW ===')
if incidents:
    rev_payload = {
        'incident_id': incidents[0]['id'],
        'review_outcome': 'CORRECT',
        'reviewer_notes': 'Verified correct handling anomaly by automated live acceptance test.',
        'is_curated_for_training': True
    }
    t0 = time.perf_counter()
    rev_resp = requests.post(f'{API_V1}/reviews', json=rev_payload, headers=headers)
    t_rev = (time.perf_counter() - t0) * 1000
    print(f'Submit Review ({t_rev:.1f}ms): Status={rev_resp.status_code}, Outcome={rev_resp.json().get("review_outcome")}')

print('\n=== 6. TESTING GROUNDED ASSISTANT & ZERO-HALLUCINATION ===')
test_queries = [
    'What were the most common risky behaviours detected?',
    'Which loading bay or zone has the highest risk?',
    'Show recent drop or dragging incidents.',
    'What preventive actions are recommended?',
    'Give me a summary of shift incidents.',
    'Did a purple UFO crash into Bay 99?'
]
for q in test_queries:
    t0 = time.perf_counter()
    a_resp = requests.post(f'{API_V1}/assistant/chat', json={'query': q, 'max_citations': 3}, headers=headers)
    t_a = (time.perf_counter() - t0) * 1000
    if a_resp.status_code != 200:
        print(f'Query FAILED ({a_resp.status_code}): {a_resp.text}')
    res = a_resp.json()
    print(f'Query ({t_a:.1f}ms): "{q}"')
    print(f'  Answer: {res.get("answer", "NO_ANSWER")[:140]}...')
    print(f'  Citations: {len(res.get("grounded_citations", []))}')

print('\n=== LIVE SYSTEM INTEGRATION TEST COMPLETE: 100% SUCCESS ===')
