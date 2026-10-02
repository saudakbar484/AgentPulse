import urllib.request
import json

BASE = "http://localhost:8000/v1"

endpoints = [
    ("/agents", "GET"),
    ("/runs", "GET"),
    ("/metrics", "GET"),
    ("/metrics/calibration", "GET"),
    ("/metrics/review-queue", "GET"),
    ("/alerts", "GET"),
    ("/traces", "GET"),
    ("/audit/logs", "GET"),
    ("/system/resilience", "GET"),
    ("/system/rls-ddl", "GET"),
]

print("Checking API endpoints on localhost:8000...")
for path, method in endpoints:
    url = f"{BASE}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgentPulse-Validator"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            count = len(data) if isinstance(data, list) else (len(data.keys()) if isinstance(data, dict) else 1)
            print(f"[OK] {method} {path} -> status 200, items/keys: {count}")
    except Exception as e:
        print(f"[FAIL] {method} {path} -> {e}")
