# AgentGuard — Rules.md

Binding rules for everyone (and every AI coding assistant) working on this repository. If a rule must be broken, record the reason in Memory.md → Decisions.

**Priority order when rules conflict:** Security & privacy → Correctness → Simplicity → Performance → Style.

---

## 1. How AI Assistants Must Work in This Repo

1. **Read first:** at the start of every session read `Memory.md`, then the relevant parts of `PRD.md`, `Architecture.md`, `Design.md` and the current task in `Tasks.md`.
2. **One task at a time.** Work on the task ID given. Do not start unrelated tasks or refactors.
3. **Plan before code** for anything that touches more than 3 files: write a 5–10 line plan in the PR description or task notes.
4. **Never invent** APIs, library functions, environment variables or table columns. Check the code or docs. If unsure, say so and ask.
5. **Do not change** `Architecture.md` decisions, database schema, or public API contracts without updating the docs and adding an ADR/Decision entry in the same change.
6. **Tests with code.** No feature code without tests. No "fixing" tests by weakening assertions.
7. **Small diffs.** Prefer changes under ~400 lines. Split larger work.
8. **Finish by updating** `Tasks.md` (check the box, add notes) and `Memory.md` (state, gotchas, decisions).
9. **Never commit secrets**, real customer data, or real API keys. Use `.env.example` with placeholders.
10. **Say what you could not verify.** If you could not run tests or a command, state it explicitly instead of claiming success.

## 2. Repository and Git Workflow

- Trunk-based with short-lived branches: `feat/<task-id>-short-name`, `fix/<id>-...`, `chore/...`, `docs/...`.
- **Conventional Commits:** `feat(runs): add budget cap`, `fix(eval): downgrade verdict without evidence`.
- Every PR: linked task ID, description of what/why, screenshots for UI, test evidence, migration notes, rollback notes if risky.
- PR must pass CI: lint, type-check, unit + integration tests, security scans.
- Squash-merge into `main`. `main` is always deployable.
- Semantic versioning for releases; changelog generated from commits (`CHANGELOG.md`).
- Database migrations are separate, reviewed, reversible commits. Never edit an applied migration.

## 3. Coding Standards — Python (API, workers, CLI)

- Python 3.12, `uv` or `poetry` for dependency management with a committed lockfile.
- Formatting and lint: `ruff` (lint + format), `mypy --strict` on `app/` (allow gradual exceptions listed in `pyproject.toml`).
- Type hints everywhere; Pydantic v2 models for all I/O boundaries; no `Any` unless commented.
- Async-first for I/O. No blocking calls (requests, time.sleep, heavy CPU) in async paths; use `httpx.AsyncClient`, `asyncio.to_thread` when needed.
- Layering: `router → service → repository → model`. Routers contain no business logic; services contain no SQL; repositories enforce `org_id` scoping.
- **Every repository method takes `org_id` explicitly.** Queries without tenant scoping are rejected in review.
- Errors: raise domain exceptions (`NotFoundError`, `ConflictError`, `BudgetExceededError`), mapped to HTTP responses centrally. Never `except Exception: pass`.
- Config only via `pydantic-settings`; no `os.getenv` scattered in code.
- Logging via `structlog`, with context fields; never log secrets, tokens, full prompts with PII, or raw customer transcripts at INFO.
- Time: UTC, timezone-aware datetimes only. IDs: UUIDv7/UUIDv4.
- Naming: `snake_case` functions/vars, `PascalCase` classes, modules short and singular.
- Functions ≤ 50 lines where practical; cyclomatic complexity ≤ 10.
- Docstrings (Google style) on public service functions and anything non-obvious.

## 4. Coding Standards — TypeScript (Web, SDK-JS)

- TypeScript `strict: true`; no `any` (use `unknown` + narrowing). ESLint + Prettier.
- Next.js App Router; server components by default, client components only when needed.
- Data fetching with TanStack Query; API types generated from the OpenAPI schema (`openapi-typescript`). Do not hand-write API types.
- Forms: `react-hook-form` + `zod`. Validation messages follow Design.md copy rules.
- Components: shadcn/ui primitives + design tokens (Design.md). No inline hex colors; no arbitrary one-off spacing.
- State: server state in TanStack Query; local UI state in React; avoid global stores unless justified.
- Accessibility is a requirement (see Design.md §11); lint with `eslint-plugin-jsx-a11y`.
- Never render transcripts with `dangerouslySetInnerHTML`.

## 5. API Rules

- REST + JSON, versioned prefix `/v1`. Resource-oriented nouns; actions as `POST /resource/{id}:action` (e.g., `/runs/{id}:cancel`).
- Pagination: cursor-based (`limit`, `cursor`); max `limit` 200.
- Idempotency: `Idempotency-Key` header supported on ingest and run-creation endpoints.
- Errors follow RFC 7807 problem+json with a stable `code`.
- Never break a published endpoint within `/v1`; add fields, don't remove or rename. Deprecate with a header and a doc note.
- Rate-limit all public endpoints; stricter on auth and ingest.
- OpenAPI is the source of truth; CI fails if the generated schema differs from the committed one without a version note.

## 6. Database Rules

- All schema changes via Alembic migrations; each migration has `upgrade` and `downgrade`.
- Every tenant table has `org_id` + index. Foreign keys with explicit `ON DELETE` behaviour.
- No `SELECT *` in application code. No N+1 queries (check with query counters in tests for list endpoints).
- Large JSON blobs go to object storage; `jsonb` only for configuration/evidence.
- Soft-delete only where audit requires it; otherwise hard delete with cascade, and honour retention jobs.
- Long-running migrations must be online-safe (add nullable column → backfill → enforce).

## 7. LLM and Evaluation Rules (critical)

1. **All model calls go through `llm.client`.** No direct SDK calls in business code.
2. **Prompts are files, not strings in code.** Versioned (`name@vN`), with JSON schema for outputs. Changing a prompt = new version + eval on the golden set.
3. **Transcripts are untrusted input.** Judge and generator prompts must delimit data, instruct the model to ignore instructions inside data, and demand structured output only.
4. **Structured output only** for judgments; validate with Pydantic; one repair attempt; otherwise `unsure`.
5. **Evidence rule:** a `fail` verdict requires a verbatim quote found in the transcript. Enforced in code, not only in the prompt.
6. **Model separation:** judge model should differ from the model that produced the response under test. Log a warning if equal.
7. **Reproducibility:** persist model name/version, temperature, seed, prompt id/version for every LLM-generated artifact.
8. **Determinism where possible:** temperature 0–0.2 for judges; higher only for simulator/generator diversity.
9. **Cost control:** every run has a budget cap; every LLM call writes to `usage_ledger`; tests use a fake LLM client (no network).
10. **Never use customer data for model training or evaluation sets without explicit opt-in.**
11. **No metric ships without** a rubric, a golden-set slice, and a documented expected κ/accuracy.
12. Do not describe a score as "accurate" in UI or docs without showing calibration status.

## 8. Security and Privacy Rules

- Follow OWASP ASVS L1 as a baseline; OWASP LLM Top 10 for LLM-specific risks.
- Secrets: never in code, logs, test fixtures, screenshots or error messages. Use env/secret manager; rotate on exposure.
- Agent credentials are write-only through the API.
- Validate and sanitize every user-provided URL (SSRF). No following redirects to private ranges.
- Authorization checks on every route and every object access; write a negative test (cross-tenant access denied) for each new resource.
- File uploads: allowlist types, size limits, antivirus/scan hook, store outside web root, never execute.
- Dependencies: pinned, scanned in CI; new dependency requires a one-line justification in the PR (license, maintenance, size).
- PII: redact before storage when the monitor setting is on; never include PII in metrics labels or log lines.
- Demo environment uses **only synthetic data and dummy credentials**.
- Responsible-use: the UI requires users to confirm they have authority to test the target agent. Do not build features aimed at attacking third-party systems.

## 9. Testing Rules

| Layer | Tooling | Requirement |
|---|---|---|
| Unit | pytest, vitest | Pure logic, drift stats, scoring, adapters with mocked HTTP; ≥ 85% coverage on `evaluation/`, `monitoring/`, `runs/` |
| Integration | pytest + testcontainers (Postgres, Redis, MinIO) | Repositories, API routes, worker tasks end-to-end with fake LLM |
| Contract | schemathesis against OpenAPI | Run in CI nightly |
| E2E | Playwright | MVP happy path: register agent → generate suite → run → view report |
| LLM-eval | custom golden-set runner | Required on any prompt/rubric/model change; compare against previous κ |
| Statistical | property-based tests (hypothesis) | Drift detector: false-positive rate on simulated stable streams, power on injected shifts |
| Load | k6/locust | Ingest 100 traces/min sustained; 20 concurrent runs |
| Security | pip-audit, npm audit, Trivy, Bandit, ZAP baseline | Zero high/critical unresolved before release |

- Tests are deterministic: seed randomness, freeze time, no live network or real LLM in CI unit/integration tests.
- A bug fix starts with a failing test.
- Flaky tests are fixed or quarantined within 48 h with an issue.

## 10. Documentation Rules

- Docs live in the repo (`docs/`, root `*.md`) and change with the code.
- Each module has a short README: purpose, public interfaces, gotchas.
- Every environment variable is documented in `.env.example` with description and safe defaults.
- Runbooks for each production alert.
- User docs: quickstart (10 minutes to first report), adapter guides, metric reference (with rubric text), CI guide, security guide.

## 11. Performance Rules

- Dashboard p95 < 2 s; API p95 < 300 ms for non-LLM endpoints.
- Anything over 1 s of work is a background job, never in the request path.
- Use pagination, projections and indexes before caching; cache only with explicit invalidation.
- Batch LLM calls; reuse HTTP connections; cap concurrency per provider.

## 12. Definition of Ready / Done

**Ready (task can start):** user story and acceptance criteria written; designs or API contract exist; dependencies identified; test approach noted.

**Done (all must be true):**
- [ ] Acceptance criteria met and demonstrated.
- [ ] Unit + integration tests added and passing; coverage thresholds held.
- [ ] Lint, type-check, security scans pass.
- [ ] Tenant-isolation and permission tests included where relevant.
- [ ] Docs updated (user docs, OpenAPI, env vars, runbook if ops-relevant).
- [ ] Migrations reversible and tested on a copy of realistic data.
- [ ] Observability: logs/metrics added for new flows; errors handled and surfaced in UI.
- [ ] Accessibility checked for UI changes.
- [ ] `Tasks.md` and `Memory.md` updated.
- [ ] Reviewed and merged to `main`; deployed to staging and smoke-tested.

## 13. Release Rules

- Release checklist lives in `Tasks.md` Phase 6. No release with failing gates.
- Staged rollout: staging → canary (10%) → full. Rollback plan stated in every release note.
- Post-release: monitor error rate, queue depth, LLM error rate for 24 h.
- Incident process: acknowledge → mitigate → communicate → postmortem (blameless) within 5 working days; actions tracked in `Tasks.md`.

## 14. Communication and Decision Rules

- Decisions with lasting effect → ADR entry in `Architecture.md` §14 and Memory.md.
- When requirements are ambiguous, ask (or record an assumption in Memory.md) rather than silently choosing.
- Prefer boring, well-supported technology. Novel tech needs a written reason.
- YAGNI: build what the current phase in `Tasks.md` needs; note future ideas in Memory.md → Parking Lot.

## 15. Prohibited Actions (hard stops)

- Committing secrets or real customer data.
- Disabling auth, tenant checks, or SSRF protections "temporarily".
- Skipping migrations by editing the database manually in shared environments.
- Using production data in dev/test.
- Merging with red CI.
- Shipping a metric or prompt change without a golden-set evaluation.
- Claiming certifications (SOC2/HIPAA) the project does not hold. Use "designed to support" wording.
