from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_release_version_and_metadata():
    # 1. Root metadata
    res_root = client.get("/")
    assert res_root.status_code == 200
    root_data = res_root.json()
    assert root_data["app"] == "AgentPulse"
    assert root_data["version"] == "1.0.0"

    # 2. Health probe
    res_health = client.get("/healthz")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    assert res_health.json()["app"] == "AgentPulse"


def test_production_release_artifacts_exist():
    workspace_root = Path(__file__).parents[3]

    changelog = workspace_root / "CHANGELOG.md"
    assert changelog.exists()
    assert "[1.0.0]" in changelog.read_text(encoding="utf-8")

    runbook = workspace_root / "docs" / "runbooks" / "operations-runbook.md"
    assert runbook.exists()
    assert "Incident Response Triage" in runbook.read_text(encoding="utf-8")

    privacy = workspace_root / "docs" / "legal" / "privacy-policy.md"
    assert privacy.exists()
    assert "Zero-Retention PII Scrubbing" in privacy.read_text(encoding="utf-8")

    terms = workspace_root / "docs" / "legal" / "terms-of-service.md"
    assert terms.exists()
    assert "designed to support compliance" in terms.read_text(encoding="utf-8")

    ci_workflow = workspace_root / ".github" / "workflows" / "agentpulse-ci.yml"
    assert ci_workflow.exists()
    assert "agentpulse run" in ci_workflow.read_text(encoding="utf-8")


def test_fresh_onboarding_lifecycle():
    # 1. Login
    res_login = client.post(
        "/v1/auth/login",
        json={"email": "admin@agentpulse.dev", "password": "AgentPulse2026!"},
    )
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register fresh agent
    res_agent = client.post(
        "/v1/agents",
        json={
            "name": "Phase 6 GA Release Bot",
            "adapter_type": "mock",
            "adapter_config": {"mode": "good", "latency_ms": 10.0},
            "version_label": "v1.0.0",
        },
        headers=headers,
    )
    assert res_agent.status_code == 201
    agent_id = res_agent.json()["id"]

    # 3. Generate suite
    res_suite = client.post(
        "/v1/suites/generate",
        json={"agent_id": agent_id, "name": "Release Gate Suite", "count": 2},
        headers=headers,
    )
    assert res_suite.status_code == 201
    suite_id = res_suite.json()["suite"]["id"]

    # 4. Trigger run
    res_run = client.post(
        "/v1/runs",
        json={"agent_id": agent_id, "suite_id": suite_id, "concurrency": 2},
        headers=headers,
    )
    assert res_run.status_code == 201
    run_id = res_run.json()["id"]

    # 5. Ingest trace with PII
    res_ingest = client.post(
        "/v1/ingest/traces",
        json={
            "traces": [
                {
                    "external_id": "phase6_trace_01",
                    "agent_id": agent_id,
                    "turns": [
                        {"idx": 1, "role": "user", "content": "My card is 4111 2222 3333 4444."},
                        {"idx": 2, "role": "agent", "content": "Thank you, payment confirmed."},
                    ],
                }
            ]
        },
        headers=headers,
    )
    assert res_ingest.status_code == 202
    assert res_ingest.json()["pii_redacted"] == 1

    # 6. Share report
    res_share = client.post(
        "/v1/reports/share",
        json={"run_id": run_id, "title": "v1.0.0 GA Sign-Off Audit"},
        headers=headers,
    )
    assert res_share.status_code == 200
    assert "reports/share/" in res_share.json()["share_url"]
