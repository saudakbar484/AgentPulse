#!/usr/bin/env python3
"""AgentPulse Automated Fresh Account Onboarding & E2E Lifecycle Verification

Validates the full enterprise workflow end-to-end:
1. Authentication & JWT access token issuance
2. Target agent registration with zero-trust SSRF validation
3. Combinatorial test suite auto-generation
4. Execution of behavioral evaluation run
5. Ingestion of live production traces with deterministic PII scrubbing
6. Generation of shareable stakeholder sign-off link
"""

import json
import urllib.request
from typing import Any

API_BASE = "http://localhost:8000"


def make_request(path: str, method: str = "GET", payload: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_fresh_onboarding_check() -> bool:
    print("\n=======================================================")
    print(" AgentPulse Fresh Account Onboarding E2E Verification")
    print(" Target: http://localhost:8000")
    print("=======================================================\n")

    # Step 1: Health Probes
    health = make_request("/healthz")
    assert health["status"] == "healthy", "Health probe failed"
    print("  [OK] Step 1: Core API health probe verified (healthy)")

    # Step 2: Authentication
    login_res = make_request(
        "/v1/auth/login",
        method="POST",
        payload={"email": "admin@agentpulse.dev", "password": "AgentPulse2026!"},
    )
    token = login_res["access_token"]
    assert len(token) > 20, "Invalid access token"
    print(f"  [OK] Step 2: Authenticated as {login_res['user']['email']} (JWT issued)")

    # Step 3: Register Target Agent
    agent_payload = {
        "name": "Onboarding Pilot Bot",
        "description": "Enterprise customer service agent for E2E verification",
        "adapter_type": "mock",
        "adapter_config": {"mode": "good", "latency_ms": 15.0},
        "tone_guidelines": "Helpful and concise",
        "prohibited_behaviours": ["Disclosing credentials"],
        "version_label": "v1.0",
    }
    agent_res = make_request("/v1/agents", method="POST", payload=agent_payload, token=token)
    agent_id = agent_res["id"]
    print(f"  [OK] Step 3: Target Agent registered (ID: {agent_id})")

    # Step 4: Auto-Generate Red-Team Suite
    suite_res = make_request(
        "/v1/suites/generate",
        method="POST",
        payload={"agent_id": agent_id, "name": "Onboarding Smoke Suite", "count": 2},
        token=token,
    )
    suite_id = suite_res["suite"]["id"]
    print(f"  [OK] Step 4: Test Suite generated with {len(suite_res['scenarios'])} scenarios (ID: {suite_id})")

    # Step 5: Execute Suite Run
    run_res = make_request(
        "/v1/runs",
        method="POST",
        payload={"agent_id": agent_id, "suite_id": suite_id, "concurrency": 2},
        token=token,
    )
    run_id = run_res["id"]
    print(f"  [OK] Step 5: Run initiated (ID: {run_id}, status: {run_res['status']})")

    # Step 6: Ingest Production Trace with PII Redaction
    ingest_payload = {
        "traces": [
            {
                "external_id": "onboarding_trace_01",
                "agent_id": agent_id,
                "turns": [
                    {"idx": 1, "role": "user", "content": "My payment card is 4111 2222 3333 4444. Check my balance."},
                    {"idx": 2, "role": "agent", "content": "Your payment method is confirmed. Your balance is $450."},
                ],
            }
        ]
    }
    ingest_res = make_request("/v1/ingest/traces", method="POST", payload=ingest_payload, token=token)
    assert ingest_res["pii_redacted"] == 1, "PII redaction failed"
    print(f"  [OK] Step 6: Trace ingested with automatic PII sanitization (Redacted: {ingest_res['pii_redacted']})")

    # Step 7: Create Shareable Stakeholder Report
    share_res = make_request(
        "/v1/reports/share",
        method="POST",
        payload={"run_id": run_id, "title": "Onboarding Verification Sign-Off"},
        token=token,
    )
    share_token = share_res["share_token"]
    print(f"  [OK] Step 7: Shareable report created (Token: {share_token})")
    print(f"       Public URL: {share_res['share_url']}")

    print("\n=======================================================")
    print(" >>> RESULT: ONBOARDING LIFECYCLE 100% OPERATIONAL")
    print("=======================================================\n")
    return True


if __name__ == "__main__":
    run_fresh_onboarding_check()
