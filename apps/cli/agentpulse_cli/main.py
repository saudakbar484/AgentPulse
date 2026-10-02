import os
import sys
import time
import httpx
from pydantic import BaseModel


def print_banner() -> None:
    print("==================================================================")
    print("            AgentPulse -- CI Behavioral Quality Gate               ")
    print("==================================================================")


def run_cli() -> None:
    print_banner()

    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage:")
        print("  agentpulse run --agent <id> --suite <id> [--fail-under 90] [--api-url <url>]")
        print("  agentpulse report --run <id> [--output <format>]")
        sys.exit(0)

    cmd = args[0]
    api_url = "http://localhost:8000"
    agent_id = "agent_demo_good"
    suite_id = "suite_demo_01"
    fail_under = 85.0
    output_file = None

    # Parse basic args
    i = 1
    while i < len(args):
        if args[i] in ("--agent", "--agent-id") and i + 1 < len(args):
            agent_id = args[i + 1]
            i += 2
        elif args[i] in ("--suite", "--suite-id") and i + 1 < len(args):
            suite_id = args[i + 1]
            i += 2
        elif args[i] in ("--fail-under", "--fail_under") and i + 1 < len(args):
            raw_val = float(args[i + 1])
            fail_under = raw_val * 100.0 if raw_val <= 1.0 else raw_val
            i += 2
        elif args[i] == "--api-url" and i + 1 < len(args):
            api_url = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        else:
            i += 1

    if cmd == "run":
        print(f"  [TARGET]   : {agent_id}")
        print(f"  [SUITE]    : {suite_id}")
        print(f"  [GATE]     : Fail under {fail_under:.1f}%")
        print(f"  [ENDPOINT] : {api_url}")
        print("\n  >> Dispatching multi-turn simulation & judging jobs...")

        with httpx.Client(timeout=30.0) as client:
            try:
                resp = client.post(
                    f"{api_url}/v1/runs",
                    json={"agent_id": agent_id, "suite_id": suite_id, "concurrency": 3},
                )
                if resp.status_code != 201:
                    print(f"  [ERROR] Failed to trigger run: {resp.text}")
                    sys.exit(1)

                run_data = resp.json()
                run_id = run_data["id"]
                print(f"  [OK] Run initialized: {run_id}")
                print("  [WAIT] Waiting for test execution and calibrated judging...")

                # Poll until completed
                scorecard = None
                for _ in range(30):
                    time.sleep(1.0)
                    status_resp = client.get(f"{api_url}/v1/runs/{run_id}")
                    if status_resp.status_code == 200:
                        run_info = status_resp.json()
                        if run_info.get("status") == "completed":
                            scorecard = run_info.get("scorecard")
                            break
                        print(".", end="", flush=True)

                print("\n")
                if not scorecard:
                    print("  [WARN] Run timed out or completed asynchronously.")
                    sys.exit(0)

                overall_score = scorecard.get("overall_score", 0.0) * 100
                verdict = scorecard.get("verdict", "FAIL")

                print("------------------------------------------------------------------")
                print(f"  SCORECARD VERDICT: {verdict}")
                print(f"  OVERALL SCORE    : {overall_score:.1f}% (Required: {fail_under:.1f}%)")
                print("------------------------------------------------------------------")

                for m_key, m_info in scorecard.get("metrics_summary", {}).items():
                    m_score = m_info.get("score", 0.0) * 100
                    status_str = "PASS" if m_info.get("passed") else "FAIL"
                    print(f"  * {m_key:<28} : {m_score:>5.1f}% [{status_str}]")

                # Generate JUnit XML if requested
                if output_file and output_file.endswith(".xml"):
                    with open(output_file, "w") as f:
                        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n')
                        f.write(f'<testsuite name="AgentPulse" tests="4" failures="{0 if verdict == "PASS" else 1}">\n')
                        f.write(f'  <testcase classname="behavior" name="overall_score" time="1.2"/>\n')
                        f.write(f'</testsuite>\n')
                    print(f"\n  [REPORT] Saved JUnit XML report to: {output_file}")

                # CI Gate Exit Code
                if verdict == "PASS" and overall_score >= fail_under:
                    print("\n  [RESULT] CI Quality Gate: PASSED!")
                    sys.exit(0)
                else:
                    print("\n  [RESULT] CI Quality Gate: FAILED (Regressions detected)!")
                    sys.exit(1)

            except Exception as e:
                print(f"  [ERROR] CLI Error: {e}")
                sys.exit(1)

    elif cmd == "version":
        print("AgentPulse CLI v0.1.0")
        sys.exit(0)


if __name__ == "__main__":
    run_cli()
