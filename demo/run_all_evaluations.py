import asyncio
import json
import urllib.request
import urllib.error
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:8000/v1"

TEST_PLAN = [
    {
        "agent_id": "agent_financial",
        "suite_id": "suite_financial",
        "name": "Apex Banking & Securities (FINRA Rule 2210, SEC, GLBA, BSA)",
        "expected_gate": "pass",
    },
    {
        "agent_id": "agent_healthcare",
        "suite_id": "suite_healthcare",
        "name": "CarePulse Clinical Triage (HIPAA, Cardiac 911, DEA Schedule II, 988 Lifeline)",
        "expected_gate": "pass",
    },
    {
        "agent_id": "agent_demo_good",
        "suite_id": "suite_demo_01",
        "name": "Foremost Retail (FTC 30-Day, PCI-DSS CVV, Magnuson-Moss Warranty)",
        "expected_gate": "pass",
    },
    {
        "agent_id": "agent_demo_weak",
        "suite_id": "suite_demo_weak",
        "name": "Adversarial Insecure Agent (Prompt Injection & Secret Leak Probe)",
        "expected_gate": "fail",
    },
    {
        "agent_id": "agent_people_ai",
        "suite_id": "suite_people_ai",
        "name": "People-AI Live HR Agent (EEOC Title VII, FMLA, SOX Whistleblower, PII Guard)",
        "expected_gate": "pass",
    },
]

def make_request(path, method="GET", body=None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_evaluation_suite(target):
    agent_id = target["agent_id"]
    suite_id = target["suite_id"]
    name = target["name"]
    expected_gate = target["expected_gate"]

    print("\n" + "=" * 78)
    print(f"🚀 INITIATING RUN: {name}")
    print(f"   Agent ID: {agent_id} | Suite ID: {suite_id}")
    print(f"   Expected Quality Gate: {expected_gate.upper()}")
    print("=" * 78)

    # Trigger run
    payload = {
        "agent_id": agent_id,
        "suite_id": suite_id,
        "concurrency": 2,
        "agent_version": "v2.0-hardened",
    }
    create_res = make_request("/runs", method="POST", body=payload)
    run_id = create_res["id"]
    print(f"   Run started with ID: {run_id}")

    # Poll status until completion
    start_time = time.time()
    max_wait = 180
    final_run = None

    while time.time() - start_time < max_wait:
        time.sleep(2)
        run_data = make_request(f"/runs/{run_id}")
        status = run_data.get("status")
        if status in ("completed", "failed"):
            final_run = run_data
            break
        print(f"   ... Status: {status} (elapsed: {int(time.time() - start_time)}s)")

    if not final_run:
        print(f"❌ Timed out waiting for run {run_id}")
        return False

    verdict = final_run.get("verdict", "unknown")
    scorecard = final_run.get("scorecard", {}) or {}
    metrics_summary = scorecard.get("metrics_summary", {}) or {}
    overall_score = final_run.get("score_overall", 0.0) or 0.0

    print("\n   [SCORECARD] EVALUATION METRICS:")
    print(f"   -----------------------------------------------")
    print(f"   Final Quality Gate:   {verdict.upper()} (expected: {expected_gate.upper()})")
    print(f"   Overall Score:        {overall_score * 100:.1f}%")
    print(f"   Safety & Compliance:  {metrics_summary.get('safety_jailbreak', {}).get('score', 0.0) * 100:.1f}%")
    print(f"   Factual Correctness:  {metrics_summary.get('correctness_faithfulness', {}).get('score', 0.0) * 100:.1f}%")
    print(f"   Hallucination Guard:  {metrics_summary.get('hallucination', {}).get('score', 0.0) * 100:.1f}%")
    print(f"   Tone & Brand:         {metrics_summary.get('tone_brand', {}).get('score', 0.0) * 100:.1f}%")
    print(f"   -----------------------------------------------")

    # Fetch individual scenario conversations and evaluations
    try:
        convs = make_request(f"/runs/{run_id}/conversations")
        print(f"   Detailed Scenarios Evaluated ({len(convs)} total):")
        for idx, c in enumerate(convs, 1):
            c_passed = c.get("passed", False)
            mark = "✅ PASS" if c_passed else "❌ FAIL"
            c_turns = c.get("turns", [])
            first_user = next((t["content"] for t in c_turns if t.get("role") == "user"), "N/A")
            if len(first_user) > 60:
                first_user = first_user[:57] + "..."
            print(f"     [{idx}] {mark} | Prompt: \"{first_user}\"")
    except Exception as e:
        print(f"     Could not fetch conversations: {e}")

    gate_matched = (verdict.lower() == expected_gate.lower())
    if gate_matched:
        print(f"\n   🎯 VERIFICATION PASSED: Gate correctly determined {verdict.upper()}.")
        return True
    else:
        print(f"\n   ⚠️ VERIFICATION FAILED: Expected {expected_gate.upper()} but got {verdict.upper()}.")
        return False

def main():
    print("=" * 78)
    print("AgentPulse Multi-Agent Production Validation & Quality Gate Verification")
    print("=" * 78)

    passed_count = 0
    total_count = len(TEST_PLAN)

    for target in TEST_PLAN:
        success = run_evaluation_suite(target)
        if success:
            passed_count += 1

    print("\n" + "=" * 78)
    print(f"EVALUATION SUITE VALIDATION SUMMARY: {passed_count}/{total_count} Agents Passed Expectations")
    print("=" * 78)

    if passed_count == total_count:
        print("🌟 ALL REAL SCENARIOS AND HARD AGENT TESTS COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"⚠️ {total_count - passed_count} agents did not match expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
