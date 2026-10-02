# AgentGuard — Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Product | AgentGuard — testing, evaluation and monitoring for deployed AI agents |
| Version | PRD v1.0 (draft for build start) |
| Owner | Product/Engineering lead (you) |
| Status | Approved for MVP build |
| Related docs | Architecture.md, Design.md, Rules.md, Tasks.md, Memory.md |

---

## 1. Summary

AgentGuard is an open-source-first platform that **tests AI chatbots and voice agents before launch and monitors them after launch**. You point it at an agent (an HTTP endpoint, an OpenAI-compatible API, or a transcript feed). AgentGuard then:

1. Generates hundreds of realistic and adversarial customer conversations (angry, confused, off-topic, jailbreaking, multilingual).
2. Runs them against the agent.
3. Scores every reply for correctness, hallucination, tone, policy compliance, safety and task completion.
4. Produces a pass/fail scorecard with failure reasons and fix suggestions.
5. After launch, samples live conversations, scores them continuously, and alerts the team when quality drifts.

One sentence: **"CI and uptime monitoring, but for the behaviour of AI agents."**

## 2. Problem Statement

Teams that build AI agents for clients (agencies, automation studios, internal AI teams) face four recurring problems:

- **No proof of quality.** Agents are tested by hand with 10–20 chats, so launch confidence is low and regressions go unnoticed.
- **Silent degradation.** Prompts, knowledge bases, model versions and client data change. The agent gets worse and nobody finds out until a customer complains.
- **Adversarial blind spots.** Prompt injection, data leakage, policy violations and off-brand tone are rarely tested systematically.
- **No client-facing evidence.** Agencies sell "monitor & improve" but have no objective report to show clients that agents keep working.

Existing tools are mostly developer-centric (prompt or trace tooling), single-project, or hosted SaaS that is hard to use with regulated data. Gaps we target: **multi-client management, black-box endpoint testing, drift alerts with plain-language reports, and self-hosting for HIPAA/SOC2-sensitive work.**

> Competitive note: Promptfoo, DeepEval, Ragas, Langfuse, Braintrust, LangSmith and voice-testing startups cover parts of this space. Verify their current features before positioning. AgentGuard's angle is the combination in §4 rather than any single feature.

## 3. Vision, Goals and Non-Goals

**Vision:** every deployed AI agent has an automated, auditable quality gate and a health dashboard.

**Goals (v1):**
- G1. Run a 50–500 conversation test suite against any chat agent in under 15 minutes and give a clear verdict.
- G2. Detect real quality regressions with few false alarms.
- G3. Give agencies a multi-client workspace and shareable "Agent Health Reports".
- G4. Run fully self-hosted with open-weight models. No data has to leave the customer's infrastructure.
- G5. Plug into CI so a bad prompt change fails the build.

**Non-goals (v1):**
- Building or hosting the agents themselves (not an agent builder).
- Real audio processing (STT/TTS quality, latency of speech) in v1. Voice agents are tested via transcripts or text channel; audio-level testing is v2.
- Fine-tuning models or automatic prompt rewriting (suggestions only).
- A general LLM observability suite competing with Langfuse (we integrate with it).

## 4. Differentiators

1. **Black-box testing** — needs only an endpoint, no code changes in the agent.
2. **Agency-first multi-tenancy** — Organization → Client → Agent → Suite hierarchy.
3. **Test + Monitor in one loop** — failures found in production become new regression tests with one click.
4. **Calibrated judges** — LLM judges are measured against human labels, and the agreement score is shown in the UI.
5. **CI gate** — `agentguard run --fail-under 90` for GitHub Actions or GitLab CI.
6. **Self-hosted & open-weight by default** — suitable for sensitive client data.

## 5. Users and Personas

| Persona | Role | Goals | Pain today |
|---|---|---|---|
| **Aisha — AI Engineer** (primary) | Builds and ships agents for clients | Catch regressions before deploy, debug failures quickly | Manual testing, no repeatable suites |
| **Bilal — QA / Delivery Lead** | Signs off releases | A trustworthy pass/fail gate and a report for the client | Subjective sign-off |
| **Chloe — Account/Client Manager** | Talks to clients monthly | Evidence that the agent is working, trend charts | "Monitor & improve" is hard to prove |
| **Dev — Client Stakeholder** (read-only) | Business owner | See health at a glance, get alerted on real problems | Black-box vendor |
| **Admin** | Org owner | Users, API keys, retention, budgets | — |

## 6. Core Concepts (domain glossary)

- **Organization** — the tenant (e.g., an agency).
- **Client** — an end customer of the organization (optional grouping).
- **Agent** — a registered target: connection config, description, knowledge sources, policies.
- **Persona** — a simulated user profile (traits, emotion, language, knowledge level).
- **Scenario** — persona + goal + tactic + success criteria.
- **Suite** — a named collection of scenarios (generated or hand-written).
- **Run** — one execution of a suite against an agent version.
- **Conversation / Turn** — simulated dialogue and its messages.
- **Metric / Evaluator** — a rule-based or LLM-judge check that scores a turn or conversation.
- **Scorecard** — aggregated results per metric and category.
- **Trace** — a real production conversation ingested for monitoring.
- **Monitor** — a rule that evaluates traces on a rolling window and raises alerts.
- **Baseline** — reference scores (from a passing run or the last N days) for drift comparison.

## 7. User Stories and Functional Requirements

Priority: **M** = must (MVP), **S** = should (v1), **C** = could (v1.x/v2).

### 7.1 Agents and connections
| ID | Requirement | Pri |
|---|---|---|
| FR-A1 | Register an agent with name, description, intended use, tone guidelines and prohibited behaviours | M |
| FR-A2 | Connect via generic HTTP JSON adapter (configurable URL, headers, request template, response JSONPath) | M |
| FR-A3 | Connect via OpenAI-compatible chat completions endpoint | M |
| FR-A4 | "Test connection" button with sample exchange and latency | M |
| FR-A5 | Secure storage of the agent's credentials (encrypted at rest, never shown after save) | M |
| FR-A6 | Attach knowledge sources (PDF/MD/TXT/URL) as ground truth for factuality checks | M |
| FR-A7 | WebSocket adapter and Vapi/Retell/LiveKit transcript adapters | S |
| FR-A8 | Agent versions: tag each run with the agent's prompt/model version for comparison | S |
| FR-A9 | Mock agent included for demo and onboarding | M |

### 7.2 Scenarios and suites
| ID | Requirement | Pri |
|---|---|---|
| FR-S1 | Auto-generate scenarios from the agent description and knowledge docs across a category taxonomy | M |
| FR-S2 | Category taxonomy: happy path, ambiguous/confused, angry/frustrated, off-topic, prompt injection/jailbreak, data extraction/PII, policy edge cases, multi-turn memory, long context, multilingual | M |
| FR-S3 | Manually create and edit scenarios (persona, goal, opening line, success criteria, max turns) | M |
| FR-S4 | Import/export suites as YAML/JSON | M |
| FR-S5 | Deduplicate near-identical scenarios (embedding similarity) | S |
| FR-S6 | Convert a failed production trace into a regression scenario | S |
| FR-S7 | Scenario difficulty tags and weights | C |

### 7.3 Simulation and runs
| ID | Requirement | Pri |
|---|---|---|
| FR-R1 | Start a run: select agent, suite, concurrency, budget cap and seed | M |
| FR-R2 | User-simulator LLM plays the persona turn by turn until goal reached, give-up, or max turns | M |
| FR-R3 | Live progress view (completed/failed/in-progress, running cost and latency) | M |
| FR-R4 | Cancel and resume runs, retry failed conversations | M |
| FR-R5 | Reproducibility: store model names, prompts, temperature and seed per run | M |
| FR-R6 | Rate limiting and backoff towards the target agent | M |
| FR-R7 | Scheduled runs (nightly regression) | S |
| FR-R8 | Run comparison (A vs B): per-metric delta and newly failing scenarios | S |

### 7.4 Evaluation
| ID | Requirement | Pri |
|---|---|---|
| FR-E1 | Built-in metrics: **Correctness/Faithfulness**, **Hallucination**, **Tone/Brand**, **Policy compliance**, **Safety/Jailbreak resistance**, **PII leakage**, **Task completion**, **Relevancy**, **Latency** | M |
| FR-E2 | Rule-based checks: regex, forbidden phrases, JSON schema, max latency, required disclosures | M |
| FR-E3 | LLM-judge checks using rubric prompts that return structured JSON (verdict, score, reasoning, evidence quote) | M |
| FR-E4 | Pass/fail thresholds per metric and per suite; overall verdict | M |
| FR-E5 | Failure explanation with the exact turn and quote highlighted | M |
| FR-E6 | Custom metric builder (rubric text + scale) | S |
| FR-E7 | **Judge calibration**: upload human labels, compute agreement (Cohen's kappa, accuracy) and show it | S |
| FR-E8 | Human override of verdicts with audit trail; overrides feed calibration | S |
| FR-E9 | Fix suggestions: group failures by root cause and propose prompt/knowledge changes | C |

### 7.5 Reporting
| ID | Requirement | Pri |
|---|---|---|
| FR-P1 | Run scorecard: overall score, per-metric, per-category, worst failures | M |
| FR-P2 | Export report as HTML and PDF | S |
| FR-P3 | Shareable read-only link with expiry for client stakeholders | S |
| FR-P4 | Trend charts across runs and across production days | S |
| FR-P5 | JUnit/JSON output for CI | S |

### 7.6 Monitoring
| ID | Requirement | Pri |
|---|---|---|
| FR-M1 | Trace ingest API/SDK (conversation id, turns, timestamps, metadata, tool calls) | S |
| FR-M2 | Sampling policy (percent, per-segment, always-score on negative feedback) | S |
| FR-M3 | Online evaluation of sampled traces using the same metrics | S |
| FR-M4 | Baselines: pick a passing run or the trailing 7-day window | S |
| FR-M5 | Drift detection with minimum sample sizes and statistical tests (see Architecture §8) | S |
| FR-M6 | Alert rules (absolute threshold, relative drop, category spike, latency, error rate) with cooldown and dedupe | S |
| FR-M7 | Notification channels: Slack webhook, email, generic webhook | S |
| FR-M8 | Incident view: affected metric, time window, example traces, probable cause hints | S |
| FR-M9 | Optional Langfuse pull-based ingest | C |
| FR-M10 | PII redaction on ingest (configurable) | S |

### 7.7 Platform
| ID | Requirement | Pri |
|---|---|---|
| FR-X1 | Email/password and OAuth login, organization invites | M |
| FR-X2 | Roles: Owner, Admin, Engineer, Viewer | S |
| FR-X3 | API keys for CLI/CI and ingest | M |
| FR-X4 | CLI: `agentguard run`, `agentguard suites push`, `agentguard report` | S |
| FR-X5 | GitHub Action wrapper | S |
| FR-X6 | Audit log of sensitive actions | S |
| FR-X7 | Data retention settings, delete-my-data | S |
| FR-X8 | One-command self-hosting via Docker Compose | M |

## 8. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Performance | 100-conversation suite (8 turns avg) completes in ≤ 15 min on a single 24 GB GPU or hosted open-weight API; dashboard pages load < 2 s (p95) |
| Scalability | v1 target: 20 concurrent runs, 1M stored turns, 100 traces/min ingest on one node; horizontally scalable workers |
| Reliability | Runs are resumable after worker crash; ingest is at-least-once with idempotency keys; API availability target 99.5% (v1) |
| Security | Encrypted secrets; tenant isolation on every query; SSRF protection for user-supplied URLs; no secrets in logs; OWASP ASVS L1 checks |
| Privacy | Self-hostable; PII redaction option; retention and deletion controls; no training on customer data |
| Cost | Cost per 100-conversation run shown before and after execution; hard budget cap per run |
| Accessibility | WCAG 2.1 AA for core flows |
| Observability | Structured logs, Prometheus metrics, tracing of the platform's own LLM calls |
| Portability | Judge/simulator models swappable via configuration (LiteLLM) |
| Compliance posture | Designed to support SOC2/HIPAA-aligned deployments (audit logs, access control, encryption). Certification itself is out of scope |

## 9. Success Metrics

| Metric | Target at v1 |
|---|---|
| Judge–human agreement (Cohen's κ) on golden set | ≥ 0.70 for correctness, safety, tone |
| Injected-regression detection (we deliberately degrade a demo agent) | ≥ 90% detected within 100 live-sampled conversations |
| False alert rate on a stable agent | ≤ 1 per week per monitor |
| Time to first value (new user → first scorecard) | ≤ 15 minutes |
| Suite generation acceptance (scenarios kept without edits) | ≥ 70% |
| Cost per 100-conversation run (open-weight, self-hosted) | tracked and published; target < $1 on a rented GPU |
| Pilot adoption | ≥ 3 real agents monitored in a pilot |

## 10. Release Plan

| Release | Scope | Exit criteria |
|---|---|---|
| **MVP (≈ 2 weeks)** | FR-A1–A6, A9; S1–S4; R1–R6; E1–E5; P1; X1, X3, X8 | Public demo link: run 50 simulated personas against the demo bot, see pass/fail report with failure reasons |
| **Alpha (weeks 3–5)** | Monitoring ingest, online eval, baselines, drift, alerts, trend charts, CLI | Injected-regression demo detected and alerted in Slack |
| **Beta (weeks 6–8)** | Calibration, reports/PDF, share links, roles, scheduled runs, comparison, regression-from-trace | κ numbers published; 2 pilot agents |
| **v1.0 Production (weeks 9–12)** | Hardening, security review, load test, docs, backups, observability, onboarding | Production checklist (Tasks.md Phase 6) green |
| **v1.x/v2** | Audio-level voice testing, WebSocket adapters, fix suggestions, Langfuse sync, marketplace of metric packs | — |

## 11. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM-judge unreliability or bias | Wrong verdicts erode trust | Rubrics with evidence quotes; calibration set; judge ≠ target model; majority vote for borderline; show κ in UI |
| Simulator produces unrealistic users | Weak tests | Persona libraries, few-shot real transcripts, human review of generated suites, diversity checks |
| Target agent rate limits / cost | Failed runs | Concurrency caps, backoff, budget caps, dry-run |
| Local model quality/latency | Slow or low-quality evals | LiteLLM abstraction, support hosted open-weight APIs, tiered judging (cheap rules first, LLM only when needed) |
| Alert fatigue | Users ignore alerts | Statistical tests, min sample sizes, cooldowns, severity levels |
| Sensitive data in traces | Compliance exposure | Redaction on ingest, retention limits, encryption, RBAC |
| Scope creep | Never ships | MoSCoW discipline, MVP exit criteria, Tasks.md gates |
| Name conflicts ("AgentGuard" may exist) | Branding/legal | Check trademarks/domains before launch; code uses a neutral package name |

## 12. Assumptions and Dependencies

- Target agents can be reached via HTTP from the AgentGuard host (or via a self-hosted runner inside the client's network).
- Open-weight models (e.g., Qwen2.5-Instruct, Llama 3.x) are good enough as judges for the metrics above when combined with rubrics and rules. This is validated in Phase 2 of Tasks.md.
- Permission to test the target agent is held by the user (the app displays an acceptable-use acknowledgement).

## 13. Open Questions

See Memory.md → "Open Questions".

## 14. Acceptance Criteria for MVP (demo-ready)

1. A new user can sign up, register the bundled demo bot, auto-generate a 50-scenario suite, and start a run in ≤ 5 clicks.
2. The run completes with live progress, and the report shows overall verdict, per-metric scores, per-category breakdown and at least one failure with a highlighted quote and reason.
3. A deliberately weakened demo bot (e.g., one with "no refusal" prompt) fails safety metrics visibly compared to the baseline bot.
4. Everything runs from `docker compose up` with documented environment variables.
5. A public, working link with dummy credentials is available (required by the application form).
