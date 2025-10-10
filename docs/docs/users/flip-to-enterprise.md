---
title: Flip to Enterprise (Verodat MCP)
description: Objective triggers for moving from local-first OSS to a governed workspace, and the steps to enable Verodat MCP.
---

# Flip to Enterprise

Audience: AI Agent Engineers and Tech Leads who have validated ADRI locally and now need shared visibility, compliance evidence, and operational scale.

Local-first OSS remains the default. Flip to enterprise when the operating model requires governance and shared analytics.

See also:
- Day‑0 path: [Onboarding Guide](onboarding-guide.md)
- Why features matter: [Feature ➝ Benefit](feature-benefits.md)
- Overall journey: [Adoption Journey](adoption-journey.md)

---

## When to Flip (Objective Indicators)

Flip from OSS-only to an enterprise workspace when one or more of the following become true:
- Multi‑team visibility: multiple services/teams need a shared view of data quality trends and agent behavior.
- Formal audit requirements: you need retained evidence of checks, failure reasons, and thresholds over time.
- Repeated triage: recurring quality incidents require centralized dashboards and alerting to shorten MTTR.
- Centralized observability: leadership and SRE need a single source of truth across products.
- Business‑critical blocking: you must block production actions on objective data quality gates with clean roll‑up metrics.

---

## What Enterprise Adds (Verodat MCP)

- Governed logging: stream assessments and reasoning telemetry to a workspace with RBAC and retention policies.
- Standards as datasets: publish ADRI YAML standards so other teams can reference, compare, and reuse them.
- Shared analytics: organization‑wide dashboards for dimension scores, failure categories, and threshold drift.
- Marketplace distribution: ship curated standards and mappings to internal or partner consumers.
- Scale & safety: centralized monitoring, audit trails, and operational controls.

Local‑first remains supported: you still keep YAML standards in git and run ADRI in your repos. Enterprise augments this with shared visibility.

---

## Prerequisites

- ADRI integrated locally with at least one green assessment.
- Access to a Verodat account and workspace (ask your admin).
- Service credentials (RBAC) for your CI/CD or runtime to stream logs.

---

## Step‑by‑Step Enablement

1) Enable Enterprise Logging
   - Configure credentials for your service (CI, container, or function runtime).
   - Turn on streaming of assessment results and (optionally) reasoning telemetry.
   - Outcome: every local JSON report also has a governed counterpart in your workspace.

2) Publish Standards as Datasets
   - Register your ADRI YAML standards as datasets in the workspace.
   - Keep YAML as the source of truth; use the workspace for discovery, version comparison, and lineage.
   - Outcome: teams can search, compare, and subscribe to standards.

3) Connect Dashboards and Analytics
   - Use workspace dashboards to track validity, completeness, consistency, plausibility, freshness over time.
   - Correlate failure categories with incident timelines to reduce triage time.
   - Optional: connect your Claude project or other analysis tools to run queries across datasets.

4) Govern Agent Supply
   - Manage access (RBAC), rate limits, and retention for agent data.
   - Define alerts on critical quality thresholds to page the right owners.

---

## Operational Checklist

- Credentials stored securely (secrets manager or CI env).
- Stream verified in non‑prod first; audit logs confirmed in workspace.
- Standards published and tagged by service/component.
- Dashboards pinned for teams; alerts tuned to reduce noise.
- Runbooks updated: “What to do when ADRI blocks data” (who to page, where to look, how to fix).

---

## Expected Outcomes

- Single source of truth for agent data quality across teams.
- Reduced MTTR via shared failure categorizations and trends.
- Compliance evidence with retained, queryable records.
- Faster onboarding for new teams by reusing proven standards.

---

## Next Steps

- Still on day‑0? Start with the [Onboarding Guide](onboarding-guide.md).
- Want to understand the value mapping? Read [Feature ➝ Benefit](feature-benefits.md).
- Ready to operationalize? Roll enterprise logging to your top 1–2 agent services first, then expand.
