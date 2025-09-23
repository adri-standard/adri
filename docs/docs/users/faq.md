---
sidebar_position: 3
---

# ADRI – Frequently Asked Questions

## What is ADRI?

ADRI stands for **Agent Data Readiness Index**. It is an open-source standard and toolset that evaluates how ready a dataset is for use by AI agents. ADRI ensures that data is valid, complete, fresh, consistent, and plausible before agents use it. This improves agent reliability, reduces errors, and prevents wasted cycles.

## Why was ADRI created?

AI agents often fail not because of poor models, but because of bad data inputs. ADRI was developed to solve this problem by providing a living quality contract between data teams, engineers, and agent workflows.

## Who founded ADRI?

ADRI was founded by Verodat, under Thomas Russell's leadership, as part of a broader mission to improve agent workflow reliability. It is released as an open-source project on PyPI so the community can contribute, extend, and adopt it widely.

## Who is ADRI for?

- **Agent Builders & AI Engineers** → Ensure reliable agent execution
- **Data Engineers & Platform Teams** → Apply standardized readiness checks
- **Business Owners & Compliance Teams** → Gain confidence, trust, and auditability
- **Researchers & Contributors** → Extend ADRI for benchmarking and innovation
- **Enterprises & SMBs** → Adopt lightweight, out-of-the-box quality checks

## How does ADRI work?

1. **Define a Standard** → YAML spec (auto-generated or custom-authored)
2. **Validate Data** → ADRI CLI or Python decorator checks dataset
3. **Generate Logs & Reports** → Console, log files, JSON reports, and failure logs
4. **Guardrail Enforcement** → Blocks bad data from reaching agents
5. **Continuous Improvement** → Standards evolve with business and compliance needs

## What logging does ADRI provide?

ADRI generates multiple log types depending on how far you are in the adoption journey:

- **Console Output** → Immediate pass/fail feedback for developers
- **Assessment Reports** (`ADRI/**/assessments`) → JSON summaries you can diff or feed into dashboards
- **Optional CSV Audit Logs** (`ADRI/**/audit-logs`) → Detailed row-level evidence when local auditing is enabled
- **Enterprise Streaming Logs** → When you connect to Verodat MCP (Step 5 onward in the [Adoption Journey](adoption-journey.md)), ADRI ships every assessment to your governed workspace
- **Verbose/Debug Output** → Turn on with `@adri_protected(..., verbose=True)` to trace decision making

## Does ADRI block all bad data, or just the dirty records?

ADRI is flexible and can be configured in three modes:
See also: [Core Concepts](core-concepts.md) for definitions of protection modes and how the five dimensions are scored.

1. **Fail-Fast (Hard Stop)**
   - Blocks the entire dataset if critical checks fail
   - Use this in compliance-critical workflows (finance, pharma, regulated environments)

2. **Selective Blocking (Row-Level Stop)**
   - Removes only dirty records and passes clean ones through
   - Generates logs so teams can remediate errors later
   - Ideal for operational workflows like support tickets, sales leads, or invoices

3. **Warn-Only (Non-Blocking)**
   - All data flows through, but ADRI reports issues in logs
   - Useful for pilots and observability — lets teams see problems without disrupting pipelines

This flexibility means you can **start light in warn-only mode**, then tighten guardrails to selective or fail-fast as your workflow matures.

## What's a practical use case for ADRI?

**Example: Customer Support Agent with CRM Data**

- **Problem**: CRM records contain missing emails, stale updates, and inconsistent IDs
- **Without ADRI**: The agent misroutes replies or hallucinates answers
- **With ADRI**: Dataset is checked for completeness, freshness, and validity before the agent sees it. Failures are logged, CRM team is alerted, and agents only use clean, verified data
- **Result**: Reliable, auditable, and accurate AI outputs

## What industries benefit most?

- **Pharma** → Compliance reporting and data governance
- **Finance** → Risk analysis and regulatory checks
- **Manufacturing** → Process automation with consistent, fresh data
- **Customer Service** → Agents powered by accurate CRM records
- **Any AI-driven workflow** → where data quality equals reliability

## How does ADRI integrate with existing workflows?

ADRI fits into:

- **CI/CD pipelines** → runs as part of automated validation
- **Data warehouses** → checks SQL tables before release
- **Slack & GitHub** → sends alerts and generates compliance tickets
- **Verodat platform** → manages and supplies ADRI standards at scale

## Does ADRI slow down agent execution?

No — ADRI is designed to be lightweight and fast. It runs before the agent step as a fail-fast guard, which typically saves time by blocking bad inputs early instead of letting agents waste cycles.

## Can ADRI run on streaming or real-time data?

Currently ADRI is optimized for batch checks (CSV, JSON, DWH queries).

Real-time / streaming validation is on the roadmap for future versions.

Standards already support freshness checks that approximate "real-time" quality.

## How customizable are ADRI Standards?

Very. Teams can:

- Define field-level rules (regex, ranges, required fields)
- Set dimension thresholds (e.g., "completeness must be >95%")
- Encode compliance-specific constraints (e.g., GDPR, HIPAA)
- Extend with business rules unique to their domain

## Is ADRI a fixed standard or evolving?

ADRI has five baseline dimensions (Validity, Completeness, Consistency, Plausibility, Freshness). See [Core Concepts](core-concepts.md).

These are stable, but the framework is open for extensions.

Community and industry contributors can propose new rules and dimensions.

## Where are ADRI Standards stored?

- Locally (in project repos)
- In Verodat-managed supply chains for enterprise governance
- In an open ADRI standards repo (planned) for sharing community standards

## Can I contribute my own ADRI Standards?

Yes. ADRI is open-source — you can contribute standards, rules, and improvements via GitHub. Community-driven growth is part of the roadmap.

## How does ADRI support compliance and audits?

- YAML standards act as codified rules
- Logs and JSON reports provide a verifiable audit trail
- Supports proving readiness for ISO 27001, SOC2, HIPAA, pharma regulations, etc.

## How is ADRI different from existing data quality tools?

- **Agent-focused** → designed for AI workflows, not just ETL pipelines
- **Zero-config adoption** → auto-generates standards from first "good" dataset
- **Lightweight & open-source** → fast to deploy, no heavy platform overhead
- **Guardrail approach** → blocks bad data at runtime, not just offline monitoring

## What happens if ADRI blocks my dataset?

1. ADRI generates a failure log + remediation guidance
2. The issue is surfaced to the data/ops team
3. Once fixed, rerun the assessment and the agent proceeds
4. Nothing is lost — ADRI protects the system from bad execution

## Will ADRI work with multi-agent workflows?

Yes. ADRI is designed for scalable agent workflows:

- Each workflow step can be protected with `@adri_protected(standard=..., data_param=...)`
- Standards can be applied per dataset, per agent, or across pipelines

## What's on the ADRI roadmap?

- Streaming & real-time checks
- Expanded standards library (shared community YAMLs)
- Deeper Verodat integration for enterprise supply chains
- Agent-to-Agent (A2A) interoperability compliance
- Dashboard for monitoring ADRI scores across workflows

## How can I start using ADRI?

**Install from PyPI:**
```bash
pip install adri
```

**Bootstrap the project (folders + tutorial data):**
```bash
adri setup --guide
```

**Generate a standard from a good dataset:**
```bash
adri generate-standard examples/data/invoice_data.csv \
  --output examples/standards/invoice_data_ADRI_standard.yaml
```

**Assess new data before your agent sees it:**
```bash
adri assess examples/data/test_invoice_data.csv \
  --standard examples/standards/invoice_data_ADRI_standard.yaml
```

**Protect your agent workflow:**
```python
from adri import adri_protected

@adri_protected(standard="invoice_data_standard", data_param="invoice_rows")
def run_agent(invoice_rows):
    ...
```

When you outgrow local logging, continue to Step 5 of the [Adoption Journey](adoption-journey.md) to stream assessments into Verodat MCP.

## Is there an enterprise version of ADRI?

Yes. **Verodat offers ADRI Enterprise** for teams that need advanced features such as:
- Centralized compliance logging and dashboards
- Enterprise audit trails
- Managed data supply and real-time pipelines
- SLA-backed support

The **open-source edition** of ADRI is fully featured for standalone use and always free.

You can start with ADRI OSS today and upgrade later if your organization requires scale, compliance, or managed services.

Learn more: [ADRI Enterprise](https://verodat.com/adri-enterprise/)

---

✅ **In short: ADRI is your data quality gatekeeper for AI agents — lightweight, open-source, and built for reliability.**
