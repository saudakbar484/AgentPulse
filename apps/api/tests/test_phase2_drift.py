import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modules.monitoring.alert_manager import AlertManager
from app.modules.monitoring.drift import StatisticalDriftDetector

client = TestClient(app)


def test_two_proportion_z_test_detects_drift():
    detector = StatisticalDriftDetector(min_sample_size=30, alpha=0.01, min_delta=0.05)

    # Injected degradation: baseline 2/50 (4%) -> current 12/50 (24%)
    drift_res = detector.test_fail_rate_shift(
        metric_key="hallucination",
        baseline_fails=2,
        baseline_total=50,
        current_fails=12,
        current_total=50,
    )

    assert drift_res is not None
    assert drift_res.has_drift is True
    assert drift_res.p_value < 0.01
    assert drift_res.severity in ("warning", "critical")
    assert "rose from 4.0% to 24.0%" in drift_res.summary


def test_two_proportion_z_test_stable_stream_no_false_alarm():
    detector = StatisticalDriftDetector(min_sample_size=30, alpha=0.01, min_delta=0.05)

    # Stable stream with minor sample variance: baseline 2/50 (4%) -> current 2/50 (4%)
    drift_res = detector.test_fail_rate_shift(
        metric_key="hallucination",
        baseline_fails=2,
        baseline_total=50,
        current_fails=2,
        current_total=50,
    )

    assert drift_res is not None
    assert drift_res.has_drift is False
    assert drift_res.p_value >= 0.01


def test_alert_manager_cooldown_and_autoresolve():
    manager = AlertManager(cooldown_hours=6)
    detector = StatisticalDriftDetector(min_sample_size=30)

    drift_res = detector.test_fail_rate_shift("hallu", 1, 50, 10, 50)
    assert drift_res and drift_res.has_drift

    # 1. First alert should fire
    alert1 = manager.record_alert("al_01", "agent_1", "TestBot", drift_res, "bad quote")
    assert alert1 is not None

    # 2. Second alert immediately after should be blocked by cooldown
    alert2 = manager.record_alert("al_02", "agent_1", "TestBot", drift_res, "bad quote")
    assert alert2 is None

    # 3. Consecutive healthy windows should auto-resolve
    manager.record_healthy_window("agent_1", "hallu")
    manager.record_healthy_window("agent_1", "hallu")
    resolved_id = manager.record_healthy_window("agent_1", "hallu")
    assert resolved_id == "al_01"
    assert manager.active_alerts["al_01"]["status"] == "resolved"


def test_convert_trace_to_regression_scenario():
    # 1. Ingest a sample trace
    ingest_payload = {
        "traces": [
            {
                "external_id": "trace_for_regr_01",
                "agent_id": "agent_demo_good",
                "turns": [
                    {"idx": 1, "role": "user", "content": "How do I return a damaged gift card?"},
                    {"idx": 2, "role": "agent", "content": "Gift cards are non-refundable."},
                ],
            }
        ]
    }
    ingest_res = client.post("/v1/ingest/traces", json=ingest_payload)
    assert ingest_res.status_code == 202

    # 2. Convert trace to scenario
    convert_res = client.post(
        "/v1/traces/trace_for_regr_01/convert-to-scenario?suite_id=suite_demo_01"
    )
    assert convert_res.status_code == 200
    conv_data = convert_res.json()
    assert conv_data["success"] is True
    assert conv_data["scenario"]["opening_message"] == "How do I return a damaged gift card?"
    assert conv_data["scenario"]["origin"] == "trace"
