# Changelog

All notable changes to the **AgentPulse** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-02 - General Availability (GA)

### Added
- **Foundations & Architecture (Phase 0)**:
  - Monorepo structure: `apps/api`, `apps/web`, `apps/cli`, `packages/sdk-python`, `demo/`, `deploy/`.
  - Docker Compose dev stack (PostgreSQL 16 + pgvector, Redis, MinIO, API, Worker, Next.js).
  - High-definition Neumorphic Light UI design tokens in `apps/web` (Porcelain `#EEF2F6`, Electric Sapphire Blue `#2563EB`, tactile dual shadows, WCAG 2.1 AA compliant).
- **Core Engine & Pre-Deploy CI (Phase 1)**:
  - Base repository with mandatory `org_id` multi-tenant scoping and SQLAlchemy 2 async domain models.
  - Outbound adapters (`http_json`, `openai_compat`, `mock`) with socket-level zero-trust SSRF IP firewall.
  - Combinatorial scenario generator (Persona × Goal × Tactic) with deduplication.
  - Multi-turn conversation simulator with stop tokens (`[GOAL_REACHED]`, `[GIVE_UP]`, `max_turns`).
  - LLM-as-a-judge framework with strict code-level verbatim quote verification and 3-sample majority voting.
- **Continuous Behavioral Observability (Phase 2)**:
  - High-throughput trace ingestion API (`POST /v1/ingest/traces`) with deterministic PII scrubbing (CC/SSN).
  - Statistical Drift Detector using two-proportion $z$-test ($p < 0.01$, $\Delta \ge 5\%$, $n \ge 30$) and Welch's $t$-test.
  - Alert manager with 6-hour deduplication cooldown and auto-resolution after 3 consecutive healthy windows.
  - Slack incoming webhook integration with rich attachments and citation cards.
  - 1-click synthesis of permanent CI regression scenarios from production failure traces.
  - Official Python Ingestion SDK (`packages/sdk-python/agentpulse`).
  - Standalone AgentPulse CLI with `--fail-under` gate, exit codes (0/1), and JUnit XML reporting.
- **Quality, Collaboration & Calibration (Phase 3)**:
  - Golden benchmark dataset (`demo/datasets/golden_set_v1.json`) with 200 expert-labeled turns.
  - Statistical calibration engine computing Cohen's kappa ($\kappa$), precision, recall, and confusion matrices.
  - Published multi-model empirical benchmark (`docs/eval-report.md`) confirming Qwen2.5-32B achieves $\kappa = 0.82$.
  - Multi-run diff comparison engine (`GET /v1/runs/compare/diff`) for pre-deploy regression verification.
  - Human review queue with audit-locked verdict overrides (`POST /v1/metrics/evaluations/{id}/override`).
  - Hierarchical Role-Based Access Control (Owner > Admin > Engineer > Viewer).
  - Shareable reports with 14-day tokenized links and standalone HTML exports.
- **Hardening, Resilience & Performance (Phase 4)**:
  - PostgreSQL Row-Level Security (RLS) DDL generator and runtime session boundary enforcement.
  - OWASP defense-in-depth security headers (`nosniff`, `DENY`, `CSP`, `HSTS`).
  - Sliding-window rate limiting (120 req/min general, 20 req/min auth) with RFC 7807 problem JSON dispatches.
  - Adversarial prompt-injection firewall for judges using cryptographic nonce XML sandboxing.
  - Downstream circuit breakers (`CLOSED -> OPEN -> HALF-OPEN`) for LLM gateway, target agents, and webhooks.
  - Zero-dependency Prometheus metrics registry exposing `/metrics` with request counts and duration histograms.
  - Production load test harness (`demo/load_test.py`) validating sustained throughput (>100 req/min).
- **Docs, Pilot & Release Polish (Phase 5 & 6)**:
  - 3 Enterprise Pilot Agents: Foremost E-Commerce, Apex Financial Advisory (SEC/FINRA rules), and CarePulse Clinical Triage (911 escalation & zero prescribing liability).
  - Interactive "Docs & Guides" tab in the dashboard and REST API `/v1/docs-content`.
  - GitHub Actions CI/CD workflow template `.github/workflows/agentpulse-ci.yml`.
  - Operational runbooks for incident response, disaster recovery, and capacity planning.
  - 35+ automated tests passing with 100% green exit gates.
