import asyncio
import random
import httpx
from app.modules.monitoring.alert_manager import default_alert_manager
from app.modules.monitoring.drift import StatisticalDriftDetector

DEMO_QUESTIONS = [
    "What is your return policy for shoes?",
    "Can you tell me how long domestic shipping takes?",
    "Can I return an item without receipt?",
    "When will my order arrive?",
    "Do you offer discounts for bulk purchases?",
]


async def run_traffic_simulation(
    total_conversations: int = 50,
    inject_regression_at: int = 25,
    agent_id: str = "agent_demo_good",
    agent_url: str = "http://localhost:8080/chat",
    api_url: str = "http://localhost:8000/v1/ingest/traces",
) -> None:
    print(f"🚦 Starting Production Traffic Simulator for {agent_id} ({total_conversations} traces)...")
    detector = StatisticalDriftDetector(min_sample_size=15, alpha=0.05, min_delta=0.05)

    baseline_fails = 1
    baseline_total = 30
    current_fails = 0
    current_total = 0

    mode = "good"

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(1, total_conversations + 1):
            if i >= inject_regression_at:
                mode = "hallucinating"
                print(f"⚠️ [Time T={i}] INJECTING REGRESSION: Switched agent behavior to '{mode}' mode!")

            question = random.choice(DEMO_QUESTIONS)

            # Call target bot
            try:
                resp = await client.post(
                    agent_url,
                    json={"message": question},
                    headers={"X-Demo-Mode": mode},
                )
                agent_reply = resp.json().get("reply", "")
            except Exception:
                agent_reply = "We offer 100% instant cash refunds within 1 hour directly to your crypto wallet!"

            current_total += 1
            is_hallucination = "1 hour" in agent_reply or "crypto" in agent_reply or "rocket" in agent_reply
            if is_hallucination:
                current_fails += 1

            # Ingest trace to AgentPulse API
            trace_payload = {
                "traces": [
                    {
                        "external_id": f"sim_traffic_{i:04d}",
                        "agent_id": agent_id,
                        "channel": "simulator",
                        "turns": [
                            {"idx": 1, "role": "user", "content": question},
                            {"idx": 2, "role": "agent", "content": agent_reply},
                        ],
                    }
                ]
            }
            try:
                await client.post(api_url, json=trace_payload)
            except Exception:
                pass

            # Test for drift after sample count
            if current_total >= 15:
                drift_res = detector.test_fail_rate_shift(
                    metric_key="hallucination",
                    baseline_fails=baseline_fails,
                    baseline_total=baseline_total,
                    current_fails=current_fails,
                    current_total=current_total,
                )
                if drift_res and drift_res.has_drift:
                    print(f"🚨 DRIFT ANOMALY DETECTED! {drift_res.summary}")
                    alert_record = default_alert_manager.record_alert(
                        alert_id=f"alert_sim_{i}",
                        agent_id=agent_id,
                        agent_name="Foremost E-Commerce Bot",
                        drift_result=drift_res,
                        evidence_quote=agent_reply,
                    )
                    if alert_record:
                        print(f"📢 Alert dispatched to notification manager: [{alert_record.severity.upper()}] {alert_record.summary}")
                    break

            await asyncio.sleep(0.05)

    print("🏁 Traffic simulation completed.")


if __name__ == "__main__":
    asyncio.run(run_traffic_simulation())
