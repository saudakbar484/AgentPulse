# AgentPulse Privacy Policy & Data Sovereignty Statement

> **Effective Date:** October 2, 2026  
> **Version:** 1.0.0 (GA)

---

## 1. Zero-Retention PII Scrubbing Protocol

AgentPulse is engineered with privacy-by-design principles:
- **Client-Side / Gateway Redaction**: All live production traces ingested via `POST /v1/ingest/traces` pass through an in-memory deterministic regex redaction pipeline before reaching database tables or LLM judge evaluators.
- **Sanitized Patterns**:
  - Credit Card Numbers: Replaced with `[PII_CARD_REDACTED]`
  - Social Security Numbers: Replaced with `[PII_SSN_REDACTED]`
  - Personal Identification Secrets: Replaced with `[PII_REDACTED]`

---

## 2. Multi-Tenant Data Sovereignty & Isolation

- **PostgreSQL Row-Level Security (RLS)**: Enforces physical database engine isolation. Queries executed on behalf of Organization A are cryptographically and logically prohibited from accessing Organization B's traces, suites, or evaluations.
- **Tenant Encryption at Rest**: Secrets and outbound adapter tokens are encrypted with Fernet AES-128-CBC authenticated with HMAC-SHA256.

---

## 3. Self-Hosted & Air-Gapped Deployments

For organizations operating under HIPAA, SOC 2 Type II, or GDPR constraints:
- AgentPulse supports **100% self-hosted open-weight inference** (e.g. Qwen2.5-32B via vLLM on premise).
- Zero telemetry or transcript payloads are ever transmitted to third-party cloud providers unless explicitly configured by the customer.
