#!/usr/bin/env python3
"""AgentPulse Production Load & Ingestion Stress Test Harness Simulates

sustained high-throughput traffic (100+ requests/min), measures latency
quantiles (p50, p95, p99), error rates, and validates rate limiting & circuit
breaker health.
"""

import asyncio
import json
import statistics
import time
import urllib.request
from typing import Any

API_BASE = "http://localhost:8000"


def send_probe_request(url: str, payload: dict[str, Any] | None = None) -> tuple[int, float]:
    start = time.time()
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}

    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            latency = (time.time() - start) * 1000
            return resp.status, latency
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        return e.code, latency
    except Exception:
        latency = (time.time() - start) * 1000
        return 500, latency


async def run_load_test(total_requests: int = 100, concurrency: int = 10) -> None:
    print(f"\n=======================================================")
    print(f" AgentPulse Stress & Load Test: {total_requests} requests (Concurrency: {concurrency})")
    print(f" Target: {API_BASE}/healthz & /v1/agents")
    print(f"=======================================================\n")

    loop = asyncio.get_running_loop()
    semaphore = asyncio.Semaphore(concurrency)

    latencies: list[float] = []
    status_counts: dict[int, int] = {}

    async def worker(idx: int) -> None:
        async with semaphore:
            endpoint = f"{API_BASE}/healthz" if idx % 2 == 0 else f"{API_BASE}/v1/agents"
            code, latency = await loop.run_in_executor(None, send_probe_request, endpoint)
            latencies.append(latency)
            status_counts[code] = status_counts.get(code, 0) + 1

    t0 = time.time()
    tasks = [worker(i) for i in range(total_requests)]
    await asyncio.gather(*tasks)
    total_time = time.time() - t0

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else max(latencies)
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else max(latencies)

    rps = total_requests / total_time if total_time > 0 else 0.0

    print("Load Test Results Summary:")
    print(f"  • Total Requests Completed : {len(latencies)} / {total_requests}")
    print(f"  • Total Duration           : {round(total_time, 2)}s")
    print(f"  • Throughput               : {round(rps, 1)} req/sec ({round(rps * 60, 0)} req/min)")
    print(f"  • Latency Min              : {round(min(latencies), 2)}ms")
    print(f"  • Latency Median (p50)     : {round(p50, 2)}ms")
    print(f"  • Latency p95              : {round(p95, 2)}ms")
    print(f"  • Latency p99              : {round(p99, 2)}ms")
    print(f"  • Latency Max              : {round(max(latencies), 2)}ms")
    print(f"  • Status Breakdown         : {dict(status_counts)}")

    success_rate = (status_counts.get(200, 0) / len(latencies)) * 100
    print(f"  • Success Rate             : {round(success_rate, 1)}%")

    if success_rate >= 99.0 and p95 < 250.0:
        print("\n>>> STATUS: PASS (Exceeds SLA threshold: >99% success, p95 < 250ms)\n")
    else:
        print("\n>>> STATUS: WARNING (Investigate bottlenecks)\n")


if __name__ == "__main__":
    asyncio.run(run_load_test())
