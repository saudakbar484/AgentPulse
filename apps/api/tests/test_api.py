import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_probes():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "AgentPulse"


def test_auth_login():
    response = client.post(
        "/v1/auth/login",
        json={"email": "admin@agentpulse.dev", "password": "AgentPulse2026!"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["user"]["email"] == "admin@agentpulse.dev"


def test_list_agents_and_test_connection():
    # 1. List agents
    agents_res = client.get("/v1/agents")
    assert agents_res.status_code == 200
    agents = agents_res.json()
    assert len(agents) >= 2

    # 2. Test connection with mock adapter
    conn_res = client.post(
        "/v1/agents/test-connection",
        json={
            "adapter_type": "mock",
            "adapter_config": {"mode": "good", "latency_ms": 10.0},
            "test_message": "Hello, when will my order ship?",
        },
    )
    assert conn_res.status_code == 200
    conn_data = conn_res.json()
    assert conn_data["success"] is True
    assert len(conn_data["reply"]) > 0


def test_suite_generation_and_run():
    # 1. Generate suite
    gen_res = client.post(
        "/v1/suites/generate",
        json={
            "agent_id": "agent_demo_good",
            "name": "Auto-Generated Test Suite",
            "count": 2,
        },
    )
    assert gen_res.status_code == 201
    suite_data = gen_res.json()
    suite_id = suite_data["suite"]["id"]
    assert len(suite_data["scenarios"]) == 2

    # 2. Trigger run
    run_res = client.post(
        "/v1/runs",
        json={
            "agent_id": "agent_demo_good",
            "suite_id": suite_id,
            "concurrency": 2,
        },
    )
    assert run_res.status_code == 201
    run_info = run_res.json()
    assert run_info["status"] in ("running", "completed")


def test_trace_ingest_with_pii_redaction():
    payload = {
        "traces": [
            {
                "external_id": "prod_conv_99",
                "agent_id": "agent_demo_good",
                "turns": [
                    {"idx": 1, "role": "user", "content": "My card is 4111 2222 3333 4444."},
                    {"idx": 2, "role": "agent", "content": "Thank you, your order is confirmed."},
                ],
            }
        ]
    }
    res = client.post("/v1/ingest/traces", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert data["ingested"] == 1
    assert data["pii_redacted"] == 1
