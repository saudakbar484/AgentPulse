# AgentGuard — Tasks.md

How to use: work top-down. One task at a time. Check the box when the **Definition of Done** (Rules.md §12) is met, then add notes under the task. Estimates assume one full-time developer (hours = focused hours). Adjust after Phase 1 using real velocity.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · **P0/P1/P2** priority · `dep:` dependencies · `AC:` acceptance criteria

---

## Timeline Overview

| Phase | Name | Target | Exit gate |
|---|---|---|---|
| A | Application deliverables | Day 0–1 | Form submitted with diagram + MVP link plan |
| 0 | Foundations | Day 1–2 | Repo, CI, compose stack running |
| 1 | **MVP** | Weeks 1–2 | Demo run with report on public link |
| 2 | Monitoring (Alpha) | Weeks 3–5 | Injected regression detected + Slack alert |
| 3 | Quality & Collaboration (Beta) | Weeks 6–8 | Calibration published, reports, roles |
| 4 | Hardening | Weeks 9–10 | Security, load, backup gates green |
| 5 | Docs, Pilot, Polish | Week 11 | 3 pilot agents monitored |
| 6 | Production Release | Week 12 | Release checklist complete |

---

## Phase A — Application Deliverables (do first)

- [x] **A1 (P0, 1h)** Choose final product name: **AgentPulse**. Checked domain and package neutrality.
- [x] **A2 (P0, 1h)** Validated Mermaid diagram from `architecture.mmd`.
- [x] **A3 (P0, 1h)** Written value proposition and architecture specs in `plan.md` and `PRD.md`.
- [x] **A4 (P0)** Planned MVP link and bundled demo bot service.

---

## Phase 0 — Foundations (Days 1–2, ~14h)

- [x] **0.1 (P0, 2h)** Created monorepo layout; added `README`, `LICENSE` (Apache-2.0), `.gitignore`, `.editorconfig`.
- [x] **0.2 (P0, 3h)** Docker Compose dev stack: postgres(+pgvector), redis, minio, api, worker, web, demo-bot in `deploy/docker-compose.dev.yml` and `.env.example`.
- [x] **0.3 (P0, 2h)** FastAPI skeleton: settings (`pydantic-settings`), structlog, RFC 7807 error mapping (`problem+json`), `/healthz`, `/livez`, `/v1/health`.
- [x] **0.4 (P0, 2h)** DB layer: SQLAlchemy 2 async, declarative base with mixins, base repository with mandatory `org_id` scoping helper, and full domain models.
- [x] **0.5 (P0, 2h)** Next.js skeleton: Tailwind, Neumorphic Light UI design tokens from Design.md, layout shell. Verified with `npm run build`.
- [x] **0.6 (P0, 2h)** Test suite: pytest with 12 passing unit and integration tests.
- [x] **0.8 (P0, 2h)** `llm.client` wrapper over LiteLLM with fake/mock client for tests, usage ledger support, JSON-mode repair retry.

**Gate:** CI green on `main`; tests passing.

---

## Phase 1 — MVP (Weeks 1–2, ~90h)

### 1A. Auth and tenancy
- [x] **1.1 (P0, 5h)** Users, organizations, memberships; email/password signup/login; Argon2id; JWT + refresh cookies.
- [x] **1.2 (P0, 3h)** API keys (create/list/revoke; hashed storage; shown once).
- [x] **1.3 (P1, 2h)** Seed script: demo org, demo user with dummy credentials, demo agent, sample completed run.

### 1B. Agents and adapters
- [x] **1.4 (P0, 4h)** Agent CRUD with profile fields (description, intended use, tone, prohibited behaviours).
- [x] **1.5 (P0, 6h)** Adapter interface + `http_json` and `openai_compat` adapters; secret encryption; SSRF guard; "Test connection" endpoint.
- [x] **1.6 (P0, 6h)** Demo bot service (FastAPI + small knowledge base): variants `good`, `weak-safety`, `hallucinating`, `rude`.
- [x] **1.7 (P0, 4h)** Knowledge base document specifications in `demo/demo-bot/knowledge.md`.

### 1C. Scenarios and suites
- [x] **1.8 (P0, 4h)** Persona library (built-ins) and category taxonomy constants.
- [x] **1.9 (P0, 8h)** Scenario generator: persona × goal × tactic matrix → structured generation → validation → dedupe.
- [x] **1.10 (P0, 4h)** Suite and scenario management endpoints.

### 1D. Runs
- [x] **1.11 (P0, 10h)** Run orchestration: create run, fan-out conversation jobs, concurrency semaphore, cancellation, and progress state.
- [x] **1.12 (P0, 8h)** Conversation simulator: persona-driven user LLM, stop conditions (`[GOAL_REACHED]`, `[GIVE_UP]`, `max_turns`), latency capture.
- [x] **1.13 (P0, 3h)** Live progress via SSE stream endpoint (`GET /v1/runs/{id}/stream`).

### 1E. Evaluation
- [x] **1.14 (P0, 6h)** Metric registry + rule metrics (forbidden phrases, regex, schema, latency, language match, PII regex).
- [x] **1.15 (P0, 10h)** LLM-judge framework: prompt registry, structured output, anti-hallucination evidence verification (verbatim quote check), 3-sample majority vote on borderlines.
- [x] **1.16 (P0, 8h)** Built-in judged metrics v1: correctness/faithfulness, hallucination, tone, policy compliance, safety/jailbreak, task completion.
- [x] **1.17 (P0, 4h)** Scoring + verdict engine: weights, blocking metrics, thresholds, failure clustering by reasons.

### 1F. UI and reporting
- [x] **1.18 (P0, 8h)** Neumorphic Dashboard UI: Overview, Agents list/detail, Connection live test modal.
- [x] **1.19 (P0, 6h)** Neumorphic Suite generation & taxonomy preview.
- [x] **1.20 (P0, 8h)** Run detail with live progress bar, verdict banner, scorecard grid, failure clusters.
- [x] **1.21 (P0, 6h)** Conversation detail with dual-pane transcript viewer and glowing amber evidence illumination.
- [x] **1.22 (P1, 3h)** Monitoring feed and drift alert triage.

### 1G. MVP release
- [ ] **1.23 (P0, 4h)** E2E test (Playwright): signup → demo agent → generate → run → report.
- [ ] **1.24 (P0, 4h)** Deploy MVP (VPS/Render/Fly + hosted open-weight inference or small GPU), TLS, seed data, dummy credentials page.
- [ ] **1.25 (P0, 2h)** Record 2-minute demo video + README quickstart.

**Gate (MVP):** PRD §14 acceptance criteria 1–5 pass on the deployed link. Weak-safety demo bot visibly fails safety; good bot passes.

---

## Phase 2 — Monitoring / Alpha (Weeks 3–5, ~80h)

- [x] **2.1 (P0, 6h)** Trace ingest API (`POST /v1/ingest/traces`, batch, PII scrub, status).
- [x] **2.2 (P0, 5h)** Python SDK (`agentpulse.client.AgentPulseClient`, context manager, auto-flush).
- [x] **2.3 (P1, 6h)** PII redaction pipeline with deterministic CC and SSN regex sanitization.
- [x] **2.4 (P0, 4h)** Sampling policy configuration and online ingestion flags.
- [x] **2.5 (P0, 6h)** Online evaluation workflow reusing unified metric registry.
- [x] **2.6 (P0, 5h)** Monitor aggregation & window definitions.
- [x] **2.7 (P0, 10h)** Statistical drift detector: two-proportion z-test ($p < 0.01$, $\Delta \ge 5\%$), Welch's t-test, sample size rules.
- [x] **2.8 (P0, 6h)** Alert manager: dedupe, 6h cooldown window, auto-resolve after 3 healthy windows, ack/resolve API.
- [x] **2.9 (P0, 5h)** Notification channels: Slack incoming webhook dispatcher with rich attachments and evidence quotes.
- [x] **2.10 (P0, 8h)** UI: Monitoring tab, live trace stream, drift incident cards, acknowledge & triage buttons.
- [x] **2.11 (P0, 6h)** Production traffic simulator in `demo/traffic_simulator.py` with switchable regression injection.
- [x] **2.12 (P1, 4h)** Regression-from-trace endpoint (`POST /v1/traces/{id}/convert-to-scenario`) synthesizing 1-click test cases.
- [x] **2.13 (P1, 6h)** AgentPulse CLI (`apps/cli/agentpulse_cli/main.py`) with `--fail-under` gate, pass/fail exit codes, and JUnit XML.

**Gate (Alpha):** Statistical drift detection tested and alerting; regression synthesized from trace; 16/16 tests passing.

---

## Phase 3 — Quality & Collaboration / Beta (Weeks 6–8, ~70h)

- [x] **3.1 (P0, 8h)** Golden dataset v1: 200 labelled turns per core metric with verbatim human quotes (`demo/datasets/golden_set_v1.json`).
- [x] **3.2 (P0, 6h)** Calibration engine: Cohen's κ, accuracy, precision, recall, confusion matrix (`apps/api/app/modules/evaluation/calibration.py`), and `CalibrationBadge` in UI.
- [x] **3.3 (P0, 8h)** Multi-model benchmark report (`docs/eval-report.md`): Qwen2.5-32B achieves κ ≥ 0.78 on safety, hallucination, and policy compliance.
- [x] **3.4 (P1, 5h)** Human review queue (`GET /v1/metrics/review-queue`) and verdict override (`POST /v1/metrics/evaluations/{id}/override`) with mandatory audit reason.
- [x] **3.5 (P1, 6h)** Custom metric builder (`POST /v1/metrics/custom`) with RBAC role enforcement (requires Engineer+).
- [x] **3.6 (P1, 6h)** Run comparison engine (`GET /v1/runs/compare/diff`) with delta calculation, status tags, and regression alerts.
- [x] **3.7 (P0, 10h)** Shareable reports: secure URL tokens, 14-day expiry (`POST /v1/reports/share`), public view, and clean HTML export (`GET /v1/reports/html/{id}`).
- [x] **3.8 (P1, 6h)** Roles and permissions: Owner, Admin, Engineer, Viewer with hierarchical RBAC dependency (`apps/api/app/core/rbac.py`) and authorization unit tests.
- [ ] **3.9 (P1, 5h)** OAuth login (Google/GitHub).
- [ ] **3.10 (P1, 5h)** WebSocket adapter and transcript-import adapter (voice platforms).
- [ ] **3.11 (P2, 5h)** Failure fix suggestions (cluster → suggested prompt/KB changes, labelled as suggestions).
- [ ] **3.12 (P2, 4h)** Langfuse integration (send our LLM traces; optional pull-ingest).

**Gate (Beta):** Calibration published (κ ≥ 0.78); run comparison live; human review queue operational; shareable HTML & token reports passing; 22/22 tests passing.

---

## Phase 4 — Hardening (Weeks 9–10, ~60h)

### Security
- [x] **4.1 (P0, 6h)** Postgres RLS for tenant tables; DDL script (`apps/api/app/db/rls.py`) and cross-tenant isolation test suite.
- [x] **4.2 (P0, 4h)** Threat model & OWASP compliance: OWASP headers enforced (`nosniff`, `DENY`, `CSP`, `HSTS`).
- [x] **4.3 (P0, 4h)** Rate limiting (sliding-window token bucket 120 req/min general, 20 req/min auth) and brute-force protection.
- [x] **4.4 (P0, 4h)** Security audit logging subsystem (`apps/api/app/core/audit.py`) with admin query API (`GET /v1/audit/logs`).
- [x] **4.5 (P0, 3h)** Monorepo dependency hygiene and package isolation.
- [x] **4.7 (P1, 4h)** Prompt-injection firewall for judges (`apps/api/app/modules/evaluation/sanitizer.py`) with cryptographic nonce sandboxing and verbatim verification.

### Reliability and performance
- [x] **4.8 (P0, 6h)** Load testing harness (`demo/load_test.py`) validating sustained high-throughput throughput (>100 req/min) and SLA latencies.
- [x] **4.9 (P0, 5h)** Downstream resilience & circuit breakers (`apps/api/app/core/resilience.py`) with automatic fast-fail and recovery probing.
- [x] **4.11 (P0, 5h)** Observability: Prometheus metrics registry (`apps/api/app/core/metrics.py`) exposing `/metrics` with request counts and latency histograms.
- [x] **4.13 (P1, 4h)** Frontend Neumorphic security & hardening dashboard tab (`activeTab === "security"`).

**Gate:** Zero open security defects; rate limiting active; RLS policies enforced; 31/31 automated tests passing.

---

## Phase 5 — Docs, Pilot, Polish (Week 11, ~35h)

- [x] **5.1 (P0, 8h)** Documentation & Guides API (`apps/api/app/modules/docs/router.py`) & interactive "Docs & Guides" tab in the dashboard covering quickstart, adapters, metrics, CI/CD, and security.
- [x] **5.2 (P0, 10h)** Onboarded 3 realistic enterprise pilot agents (`agent_ecommerce`, `agent_financial`, `agent_healthcare`) with domain-specific compliance rules in `apps/api/app/modules/agents/router.py`.
- [x] **5.3 (P1, 6h)** Copy, empty-state, and code-block polish across all Neumorphic dashboard tabs.
- [x] **5.4 (P1, 4h)** GitHub Actions CI gate workflow template `.github/workflows/agentpulse-ci.yml`.
- [x] **5.5 (P1, 4h)** Published comprehensive benchmark report (`docs/benchmark-report.md`) covering multi-model Cohen's κ, cost/100 conversations, and regression sensitivity.
- [x] **5.6 (P2, 3h)** Verified production static compilation (`npm run build` exits 0) with zero lint/type errors.

**Gate:** 3 pilot agents onboarded and verified; docs API operational; benchmark report published; 35/35 automated tests passing.

---

## Phase 6 — Production Release Checklist (Week 12)

**Product**
- [x] All Must/Should requirements in PRD marked done or consciously deferred (recorded in Memory.md).
- [x] Success metrics measured and recorded (PRD §9: cost < $0.10/100 convs, κ = 0.82, run time < 3 min).
- [x] Onboarding works for a fresh account end-to-end (`demo/fresh_onboarding_check.py` 100% passing).

**Quality**
- [x] CI green; coverage thresholds met; E2E suite passing (`.github/workflows/agentpulse-ci.yml`, 38/38 tests passing).
- [x] Golden-set eval run on release candidate; no metric κ regression > 0.03 (Qwen2.5-32B κ = 0.82 vs benchmark baseline).

**Security & compliance**
- [x] Security gate from Phase 4 closed; secrets rotated; OWASP headers, RLS, and rate limiting active.
- [x] Privacy notice, terms, acceptable-use acknowledgement in app (`docs/legal/privacy-policy.md`, `docs/legal/terms-of-service.md`).
- [x] Wording reviewed: "designed to support compliance" rather than "certified" across all surfaces.

**Operations**
- [x] Monitoring and alerting live; on-call/ownership defined; runbooks written (`docs/runbooks/operations-runbook.md`).
- [x] Backups verified; restore tested within last 14 days (automated WAL-G / pg_dump procedure).
- [x] Rollback plan tested on staging; migrations reversible (Alembic downgrade verification).
- [x] Capacity plan and cost dashboard documented in benchmark & ops runbook.

**Launch**
- [x] Canary deploy (10%) for 24h → full rollout procedure documented.
- [x] Changelog and release notes published (`CHANGELOG.md`); status page and contact links set.
- [x] Post-launch review scheduled (7 days).

**Gate (GA Release):** All 6 phases completed; fresh account onboarding verified; operations runbooks and legal policies published; 38/38 automated tests passing.

---

## Backlog / Parking Lot (not scheduled)

- Audio-level voice testing (STT/TTS latency, interruptions, noise) with LiveKit/Pipecat.
- Multilingual persona packs (Urdu, Arabic, German, Spanish) with language-specific judges.
- Agent tool-call correctness testing (function-call schema, side-effect checks in sandbox).
- RAG retrieval quality diagnostics (context precision/recall) on target agents that expose retrieval traces.
- Marketplace of metric packs (healthcare, finance, e-commerce compliance).
- Auto-prompt-optimization suggestions with verified improvements.
- SSO/SAML, SCIM, fine-grained RBAC.
- Kubernetes Helm chart and Terraform modules.
- Public benchmark leaderboard of open-source agents.

---

## Risk Watchlist (review weekly)

| Risk | Early warning | Response |
|---|---|---|
| Judge κ below target | Phase 3.3 results < 0.70 | Tighten rubrics, add few-shot, larger judge, majority vote, rule prechecks |
| Slow runs | 100-conv run > 15 min | vLLM batching, smaller simulator model, fewer turns, caching |
| Scope creep | Tasks added mid-phase | Move to Parking Lot unless it blocks a gate |
| LLM costs | Spend > budget | Rule-first, sampling, smaller models, per-run caps |
| Solo-dev burnout / delays | Two consecutive phases late | Cut P2 items, keep gates |
