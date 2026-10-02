# AgentPulse Terms of Service & Acceptable Use Policy

> **Effective Date:** October 2, 2026  
> **Version:** 1.0.0 (GA)

---

## 1. Scope of Service & Compliance Disclaimers

1. **Design Intention**:
   AgentPulse is an automated behavioral observability, CI testing, and statistical drift monitoring tool designed to assist engineering teams in measuring model consistency and red-teaming AI agents.

2. **No Legal or Regulatory Certification**:
   **AgentPulse evaluations and reports are "designed to support compliance monitoring" and do NOT constitute legal advice, regulatory certification, or a guarantee of compliance with SEC, FINRA, HIPAA, FDA, or EU AI Act mandates.**
   Customers retain full responsibility for verifying autonomous agent outputs in production.

3. **Acceptable Use Guidelines**:
   Customers shall not use AgentPulse to intentionally evaluate, simulate, or generate:
   - Malicious malware, weaponized exploit code, or cyberattack payloads.
   - Deceptive impersonation intended for wire fraud or criminal evasion.
   - Unlawful surveillance or biometric harassment.

---

## 2. Service Level Objectives (SLOs)

- **Trace Ingestion Availability**: 99.9% monthly uptime.
- **Drift Detection Latency**: Statistical drift alerts processed within 15 minutes of sample window closure ($n \ge 30$).
- **API Performance**: 95th percentile API response time $< 250$ms under rated load.
