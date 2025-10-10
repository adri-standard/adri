---
title: Onboarding Guide (10‑minute happy path)
description: CLI‑first path to generate a standard from known‑good data, assess new data, and add a one‑line decorator with warn‑first ramp.
---

# Onboarding Guide

Goal: get a green validation and a protected function in 10 minutes.

This path is CLI‑first. It sequencess Install → Generate Standard → Assess → Decorate, with a warn‑first ramp to avoid breaking flows while you tune.

See also:
- What each feature buys you: [Feature ➝ Benefit](feature-benefits.md)
- Concepts and protection modes: [Core Concepts](core-concepts.md)
- Longer journey with teams: [Adoption Journey](adoption-journey.md)
- When to enable enterprise: [Flip to Enterprise](flip-to-enterprise.md)

---

## Step 1 — Install and Bootstrap

```bash
pip install adri

# Create ADRI project folders and sample data
adri setup --guide
```

What this does:
- Creates `ADRI/dev` and `ADRI/prod` with `standards`, `assessments`, `training-data`
- Drops sample invoice data so you can see ADRI working immediately

Tip: You can keep these folders in your repo for versioning and PR review.

---

## Step 2 — Generate a Standard from Known‑Good Data

Use a clean dataset that represents “what good looks like” for your agent.

```bash
adri generate-standard examples/data/invoice_data.csv \
  --output examples/standards/invoice_data_ADRI_standard.yaml --guide
```

Result:
- A YAML standard encoding fields, value ranges, enumerations, and freshness
- Human‑readable and easy to review in a PR

You can place standards under `ADRI/dev/standards` or `ADRI/prod/standards`:
```bash
adri generate-standard examples/data/invoice_data.csv \
  --output ADRI/dev/standards/invoice_data_ADRI_standard.yaml --guide
```

---

## Step 3 — Assess New Data Against the Standard

Validate test or live data before you call your agent.

```bash
adri assess examples/data/test_invoice_data.csv \
  --standard ADRI/dev/standards/invoice_data_ADRI_standard.yaml --guide
```

Expected output examples:
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 89.5/100 (Required: 80.0/100)
```
or
```
🛡️ ADRI Protection: BLOCKED ❌
📊 Quality Score: 62.4/100 (Required: 80.0/100)
⚠️ Issues: amount must be > 0, status must be lowercase paid/pending/...
```

Artifacts written:
- JSON assessment reports under `ADRI/**/assessments`
- Optional CSV audit trail when enabled in config

---

## Step 4 — Protect One Function (Warn‑First)

Add the decorator where your agent consumes the dataset. Start with `on_failure="warn"` to avoid breaking flows.

```python
from adri import adri_protected

@adri_protected(
    standard="invoice_data_ADRI_standard",   # file name without .yaml
    data_param="invoice_rows",               # argument containing your data
    on_failure="warn"                        # ramp mode: log issues only
)
def process_invoices(invoice_rows):
    return ai_agent(invoice_rows)
```

Once tuned and stable, switch critical paths to `raise` (default) to fail fast:
```python
@adri_protected(standard="invoice_data_ADRI_standard", data_param="invoice_rows")
def process_invoices(invoice_rows):
    return ai_agent(invoice_rows)
```

Options you can control:
- `min_score` — override the default score threshold
- `on_failure` — `"raise"`, `"warn"`, or `"continue"`

---

## Troubleshooting and Tips

- Standard file not found
  - Check your path; use `adri list-standards` or move files into `ADRI/**/standards`
- Wrong `data_param`
  - Ensure it matches the function argument name containing the dataset
- Threshold too strict for pilots
  - Lower temporarily with `min_score=60` while you iterate
- See exactly what ADRI checks
  - `adri show-standard invoice_data_ADRI_standard`
- Validate different formats
  - ADRI supports CSV/JSON/Parquet for both generation and assessment

---

## Appendix — Decorator‑First Path

For teams who prefer to start in code, you can decorate first and let ADRI look up standards from your configured paths:

```python
@adri_protected(
  standard="invoice_data_ADRI_standard",
  data_param="invoice_rows",
  on_failure="warn",
  min_score=70,
)
def your_agent(invoice_rows):
    ...
```

Then iterate:
1) Generate or refine the YAML in `ADRI/dev/standards`
2) Run your function and watch logs and JSON results
3) Switch to `raise` on critical paths

---

## Next Steps

- Understand why this works and where each feature helps: [Feature ➝ Benefit](feature-benefits.md)
- Explore framework examples (LangChain, CrewAI, LlamaIndex): [Framework Playbooks](frameworks.md)
- Plan when to enable governed visibility and analytics: [Flip to Enterprise](flip-to-enterprise.md)
