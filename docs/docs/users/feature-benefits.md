---
title: Feature ➝ Benefit Mapping for AI Agent Engineers
description: Concrete benefits of ADRI features, logical consume order, early adoption levers, and enterprise scale-up value.
---

# Feature ➝ Benefit Narrative

Audience: AI Agent Engineers integrating ADRI to make agent workflows reliable on day 0 and scalable for teams later.

This page maps ADRI features to their concrete benefits, shows the logical order to consume them, and clarifies the value inflection points for flipping from local-first OSS to an enterprise workspace.

- Day‑0 objective: a verified “first win” in 5–10 minutes
- Day‑N objective: minimal code changes to keep agents from breaking on bad data
- Team/Enterprise objective: shared visibility, governed audit, and repeatable standards at scale

See also:
- Onboarding: [Onboarding Guide](onboarding-guide.md)
- Concepts: [Core Concepts](core-concepts.md)
- Journey: [Adoption Journey](adoption-journey.md)
- Enterprise: [Flip to Enterprise](flip-to-enterprise.md)

---

## Features and Benefits Matrix

| Feature | What it does | Day‑0 Benefit | Scale‑up Benefit |
|---|---|---|---|
| Standard generation (`adri generate-standard`) | Profiles known‑good CSV/JSON/Parquet and writes a YAML contract of “what good looks like.” | Zero schema guesswork; turns example data into a contract you can version in git. | Stable baseline for quality; standards evolve with PRs; reproducible across teams. |
| Assessment (`adri assess`) | Validates new datasets against a chosen standard. Reports 5‑dimension scores and failures. | Deterministic, pre‑AI gate to catch bad data quickly. | Consistent triage; aggregate quality over time; objective signals for ops. |
| Single decorator (`@adri_protected`) | Protects any Python function with one decorator; validates at call boundary. | Minimal code change; drop‑in. | Framework‑agnostic (LangChain, CrewAI, LlamaIndex, etc.); standardized guardrail point. |
| Protection modes | `raise` (fail‑fast), `warn` (log only), `continue` (mark run). | Safe ramp: start in `warn`, switch to `raise` once tuned. | Gradual hardening in prod without branching agent code. |
| Multi‑format loaders | CSV/JSON/Parquet and common tabular shapes. | Use existing datasets immediately. | Integrates with heterogeneous data sources over time. |
| Local audit & reports | JSON reports and optional CSV audit trail stored under `ADRI/**`. | Clear local evidence for debugging. | Evidence trails for compliance; easy export to downstream systems. |
| Reasoning mode (optional) | Captures prompt/response artifacts and links to assessments. | Rapid diagnosis of logic failures vs. data failures. | Longitudinal analysis of agent behavior alongside data quality. |
| Enterprise (Verodat MCP) | Streams logs to governed workspace; publishes standards as datasets for shared analytics and marketplace. | Optional on day‑0. | Organization‑wide visibility, RBAC, retention, dashboards, distribution. |

5‑dimension scoring used across CLI and decorator:
- Validity, Completeness, Consistency, Plausibility, Freshness

---

## Logical Consumption Sequence

- Day‑0 (10 minutes)
  1) Install and bootstrap: `pip install adri` then `adri setup --guide`
  2) Generate a standard from known‑good data: `adri generate-standard <good.csv> --guide`
  3) Validate new data: `adri assess <new.csv> --standard <standard>.yaml --guide`
  4) Add `@adri_protected(..., on_failure="warn")` to one function; verify logs and outputs
- Week‑1
  - Tune thresholds (`min_score`) and field‑level expectations in YAML
  - Switch critical paths to `on_failure="raise"` once stable
  - Add reasoning capture where helpful to separate data vs. logic failures
- Team scale
  - Share standards via git; re‑use validator configs across services
  - When repeated triage or compliance needs emerge, [flip to enterprise](flip-to-enterprise.md)

---

## Early Adoption Value Levers

- Minimal surface area: a single decorator and two CLI commands
- Data‑first contract: derive the standard from “what good looks like” rather than reinvent schemas
- Deterministic gating: objective pass/fail + quality score before agent execution
- Progressive hardening: `warn → raise` without code forks
- Portable: yaml standards live in your repo; easy review and versioning
- Transparent: local JSON/CSV reports and optional reasoning mode for rapid diagnosis

---

## Why ADRI Works for Agent Engineers

- One line of protection: `@adri_protected(standard="...", data_param="...")`
- Five quality dimensions ensure robust checks beyond “does it parse?”
- Consistent behavior in scripts, frameworks, and services
- OSS first; enterprise when you need governed visibility and shared analytics

---

## Next Steps

- Do it now: follow the [Onboarding Guide](onboarding-guide.md) to get a green assessment today
- Understand guardrails: see [Core Concepts](core-concepts.md#protection-modes) for protection modes
- Plan for scale: read [Flip to Enterprise](flip-to-enterprise.md) to know when and how to enable Verodat MCP
