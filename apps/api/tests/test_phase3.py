import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.main import app
from app.modules.evaluation.calibration import compute_cohens_kappa

client = TestClient(app)


def test_cohens_kappa_math():
    # 1. High agreement (90% agreement with balanced margins)
    # tp=80, fp=5, tn=80, fn=5 (Total=170)
    high_kappa = compute_cohens_kappa(tp=80, fp=5, tn=80, fn=5)
    assert high_kappa >= 0.85

    # 2. Pure chance agreement (symmetric 50/50 distribution)
    # tp=25, fp=25, tn=25, fn=25 (Total=100)
    chance_kappa = compute_cohens_kappa(tp=25, fp=25, tn=25, fn=25)
    assert abs(chance_kappa) < 0.05

    # 3. Empty counts safe fallback
    zero_kappa = compute_cohens_kappa(tp=0, fp=0, tn=0, fn=0)
    assert zero_kappa == 0.0


def test_calibration_endpoint():
    response = client.get("/v1/metrics/calibration")
    assert response.status_code == 200
    data = response.json()

    assert data["judge_model"] == "qwen2.5:32b"
    assert data["overall_kappa"] >= 0.70
    assert "metrics" in data
    assert "safety_jailbreak" in data["metrics"]
    safety_cal = data["metrics"]["safety_jailbreak"]
    assert safety_cal["cohen_kappa"] >= 0.70
    assert safety_cal["accuracy"] >= 0.80
    assert "confusion_matrix" in safety_cal


def test_custom_metric_creation_and_rbac():
    # Create tokens for different roles
    viewer_token = create_access_token({"sub": "u_viewer", "email": "viewer@agentpulse.dev", "role": "viewer"})
    engineer_token = create_access_token({"sub": "u_eng", "email": "eng@agentpulse.dev", "role": "engineer"})

    payload = {
        "key": "custom_politeness",
        "name": "Customer Empathy & Politeness",
        "rubric": "Score 1.0 if agent expresses clear warmth and active listening without robotic boilerplate.",
        "threshold": 0.80,
        "is_blocking": False,
    }

    # 1. Viewer attempts to create -> 403 Forbidden
    res_viewer = client.post(
        "/v1/metrics/custom",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res_viewer.status_code == 403

    # 2. Engineer creates -> 201 Created
    res_eng = client.post(
        "/v1/metrics/custom",
        json=payload,
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert res_eng.status_code == 201
    created_metric = res_eng.json()
    assert created_metric["key"] == "custom_politeness"
    assert created_metric["is_custom"] is True


def test_review_queue_and_override_rbac():
    # 1. Inspect review queue
    res_queue = client.get("/v1/metrics/review-queue")
    assert res_queue.status_code == 200
    queue = res_queue.json()
    assert len(queue) >= 1
    eval_id = queue[0]["evaluation_id"]

    viewer_token = create_access_token({"sub": "u_viewer", "email": "viewer@agentpulse.dev", "role": "viewer"})
    admin_token = create_access_token({"sub": "u_admin", "email": "admin@agentpulse.dev", "role": "admin"})

    override_payload = {
        "new_verdict": "pass",
        "audit_reason": "Verified human manager authorized exception in Salesforce ticket #9201",
    }

    # 2. Viewer tries override -> 403 Forbidden
    res_forbidden = client.post(
        f"/v1/metrics/evaluations/{eval_id}/override",
        json=override_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res_forbidden.status_code == 403

    # 3. Admin performs override -> 200 OK
    res_override = client.post(
        f"/v1/metrics/evaluations/{eval_id}/override",
        json=override_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_override.status_code == 200
    data = res_override.json()
    assert data["success"] is True
    assert data["record"]["new_verdict"] == "pass"
    assert data["record"]["overridden_by"] == "admin@agentpulse.dev"


def test_run_comparison_engine():
    res = client.get("/v1/runs/compare/diff?run_a=run_demo_01&run_b=run_demo_02")
    assert res.status_code == 200
    data = res.json()

    assert "overall_delta" in data
    assert data["verdict_a"] == "PASS"
    assert data["verdict_b"] == "FAIL"
    assert len(data["metric_deltas"]) > 0

    degraded_metrics = [m for m in data["metric_deltas"] if m["status"] == "degraded"]
    assert len(degraded_metrics) >= 1
    assert data["regressed_scenario_count"] >= 1


def test_shareable_reports_and_html():
    # 1. Create share link
    share_res = client.post(
        "/v1/reports/share",
        json={"run_id": "run_demo_signoff", "title": "Release v2.4 Sign-Off Audit", "expires_in_days": 7},
    )
    assert share_res.status_code == 200
    share_data = share_res.json()
    token = share_data["share_token"]
    assert len(token) > 10
    assert "reports/share/" in share_data["share_url"]

    # 2. Fetch public report by token
    public_res = client.get(f"/v1/reports/public/{token}")
    assert public_res.status_code == 200
    report_data = public_res.json()
    assert report_data["title"] == "Release v2.4 Sign-Off Audit"
    assert "methodology" in report_data
    assert "κ = 0.78" in report_data["methodology"]["calibration_status"]

    # 3. Test HTML export
    html_res = client.get("/v1/reports/html/run_demo_signoff")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "AgentPulse Behavioral Sign-Off Report" in html_res.text
