# AgentPulse — Production Operations Runbook

> **Target Audience:** Site Reliability Engineers (SRE), Platform Engineers, DevSecOps  
> **Classification:** Confidential / Internal Operations  
> **Version:** 1.0.0 (GA)

---

## 1. Incident Response Triage: Statistical Drift Alerts

When a Slack or PagerDuty alert is triggered by the **Statistical Drift Engine**:

### Alert Payload Anatomy:
```json
{
  "incident_id": "alert_drift_hallu_992",
  "agent_id": "agent_ecommerce",
  "metric_key": "hallucination",
  "severity": "WARNING",
  "z_score": 2.96,
  "p_value": 0.0031,
  "sample_failure_rate": 0.124,
  "baseline_failure_rate": 0.048,
  "sample_size": 150
}
```

### Action Checklist:
1. **Verify Statistical Significance**: Confirm $n \ge 30$ and $p < 0.01$. If $p \ge 0.01$, the alert will automatically stay suppressed by the 6-hour deduplication cooldown.
2. **Inspect Clustered Transcripts**:
   - Navigate to **Drift Monitor** in the AgentPulse Dashboard (`http://localhost:3000`).
   - Click on the active incident to inspect the verbatim quotes flagged by the LLM judge.
3. **Synthesize Regression Scenario**:
   - Click **"Convert Trace to CI Scenario"** on the incident card.
   - This automatically adds the offending interaction to `suite_regression_v1`.
4. **Trigger Canary Rollback**:
   - If the degradation is caused by a recent prompt or weights release, initiate the canary rollback (`./deploy/scripts/rollback.sh`).

---

## 2. Circuit Breaker Triage & Fast-Fail Recovery

AgentPulse isolates external HTTP dependencies using circuit breakers:
- `llm_gateway`: Trips after 5 consecutive failures / timeouts.
- `target_agent_adapter`: Trips after 4 consecutive failures.
- `slack_webhook`: Trips after 3 consecutive failures.

### Symptoms:
- API returns HTTP `503 Service Unavailable` with problem JSON `CIRCUIT_BREAKER_OPEN`.
- Prometheus metric `agentpulse_circuit_breaker_open{target="..."} == 1.0`.

### Recovery Procedure:
1. Check downstream health:
   ```bash
   curl -I http://localhost:8000/v1/system/resilience
   ```
2. Verify if the target model provider (Ollama / vLLM / LiteLLM) is responsive.
3. Once downstream service recovers, the breaker automatically enters `HALF-OPEN` after its recovery timeout (15–30s) and resets to `CLOSED` upon the first successful probe.

---

## 3. Database Backup & Disaster Recovery (PITR)

### 1. Nightly Automated Dump
```bash
docker exec -t agentpulse-postgres pg_dump -U agentpulse -Fc agentpulse > /backups/agentpulse_$(date +%F).dump
```

### 2. Point-in-Time Recovery Drill (Target: < 15 minutes)
1. Stop running API and worker containers:
   ```bash
   docker compose -f deploy/docker-compose.dev.yml stop api worker
   ```
2. Drop and recreate database:
   ```bash
   docker exec -i agentpulse-postgres psql -U agentpulse -c "DROP DATABASE IF EXISTS agentpulse;"
   docker exec -i agentpulse-postgres psql -U agentpulse -c "CREATE DATABASE agentpulse;"
   ```
3. Restore from backup archive:
   ```bash
   pg_restore -U agentpulse -d agentpulse -v /backups/agentpulse_latest.dump
   ```
4. Re-apply PostgreSQL Row-Level Security:
   ```bash
   docker exec -i agentpulse-postgres psql -U agentpulse -d agentpulse -f deploy/sql/rls_init.sql
   ```
5. Restart services and verify `/healthz` returns `{"status": "healthy"}`.

---

## 4. Canary Deployment & Rollback Strategy

1. **10% Canary Traffic Routing**:
   - Direct 10% of ingested customer traffic to candidate model $v_{1.1}$, while 90% stays on baseline $v_{1.0}$.
2. **Canary Observation Window**:
   - Run for 4 hours (minimum 200 conversations per arm).
3. **Automated Rollback Criteria**:
   - Any blocking metric ($\kappa$-calibrated safety or hallucination) drops by $\ge 3.0\%$ with $p < 0.01$.
   - Latency p95 increases by $> 50\%$.
4. **Full Rollout**:
   - If zero drift alerts fire during the 4-hour window, promote candidate $v_{1.1}$ to 100%.

---

## 5. Capacity Planning & Cost Calculator

| Workload Volume | Daily Traces | GPU Inference Sizing | Monthly Infrastructure Cost |
|---|:---:|---|:---:|
| **Startup / Pilot** | < 10,000 | 1x RTX 4090 (24GB) or Cloud A10G | ~$350 / mo |
| **Mid-Market** | 100,000 | 2x A10G (24GB) with vLLM AWQ | ~$850 / mo |
| **Enterprise High-Volume** | > 1,000,000 | 4x A100 (80GB) with Tensor Parallelism | ~$2,800 / mo |
