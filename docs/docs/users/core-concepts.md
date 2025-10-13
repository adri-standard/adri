---
id: core-concepts
title: Core Concepts
slug: /users/core-concepts
---

This page summarizes four core ideas you need on Day‑0:
- How to reference a standard (name vs path)
- The five assessment dimensions
- Protection modes for the decorator
- Audit trail and logging

Use this as a single reference and link to it from other pages instead of duplicating explanations.

## Standards: name vs path

There are two ways to reference a standard depending on the interface:

- Decorator (logical name)
  - Use the standard&#39;s logical name (omit the .yaml extension).
  - Example: `standard="invoice_data_standard"`
- CLI (filesystem path)
  - Use a file path to the standard YAML on disk.
  - Example: `examples/standards/invoice_data_ADRI_standard.yaml`

Why two forms?
- Code (decorator) should be stable and human‑readable: logical names travel well in source control and reviews.
- CLI commands operate on actual files: paths make it explicit which artifact is being read/written.

Examples:
- Decorator
  ```python
  from adri.decorator import adri_protected

  @adri_protected(
      standard="invoice_data_standard",   # logical name (no .yaml)
      data_param="invoice_rows",          # your function&#39;s data parameter
      on_failure="warn"                   # protection mode (see below)
  )
  def process_invoices(invoice_rows: list[dict]):
      ...
  ```
- CLI
  ```bash
  # Generate a standard from sample data
  adri generate-standard examples/data/invoice_data.csv \
    -o examples/standards/invoice_data_ADRI_standard.yaml

  # Assess data against a standard
  adri assess \
    --standard examples/standards/invoice_data_ADRI_standard.yaml \
    --data examples/data/test_invoice_data.csv
  ```

## The five dimensions

ADRI computes scores across five complementary dimensions. Together they roll up into an overall quality signal.

```mermaid
flowchart TB
    DATA[Your Data] --> ASSESS[ADRI Assessment]

    ASSESS --> V[✅ Validity<br/>Correct Formats]
    ASSESS --> C[✅ Completeness<br/>No Missing Fields]
    ASSESS --> S[✅ Consistency<br/>Same Format]
    ASSESS --> P[✅ Plausibility<br/>Realistic Values]
    ASSESS --> F[✅ Freshness<br/>Recent Data]

    V --> SCORE[Overall Quality Score<br/>0-100]
    C --> SCORE
    S --> SCORE
    P --> SCORE
    F --> SCORE

    SCORE --> DECISION{Score ≥ Threshold?}
    DECISION -->|Yes| ALLOW[✅ Allow Function]
    DECISION -->|No| BLOCK[❌ Block/Warn]

    style DATA fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style ASSESS fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style V fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style S fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style P fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style F fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style SCORE fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    style DECISION fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style ALLOW fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
    style BLOCK fill:#ffcdd2,stroke:#f44336,stroke-width:3px
```

### What Each Dimension Checks

- **Validity**: Values conform to declared types and formats (emails, dates, enumerations)
- **Completeness**: Required fields are present and populated (no missing critical data)
- **Consistency**: Values respect relationships and invariants across rows/fields
- **Plausibility**: Values fall within reasonable real-world ranges or patterns (age 0-120, not -5)
- **Freshness**: Data is timely relative to expectations (not stale or outdated)

**Tip:**
- Start with validity and completeness for a fast Day‑0 win.
- Expand to consistency, plausibility, and freshness as you harden your pipelines.

## Protection modes

Protection modes control what happens when validations fail at runtime (via the decorator).

| Mode     | Behavior                                                                 | Typical use                                           |
|----------|---------------------------------------------------------------------------|-------------------------------------------------------|
| raise    | Fail fast. Raise an error and block the protected function.               | Production enforcement; stop bad data early.          |
| warn     | Log warnings and proceed with the function.                               | Staging/experimentation; surface issues without fail. |
| continue | Proceed silently and record results in logs only.                         | Local/dev flows; never block.                         |

```mermaid
flowchart TB
  A[Assessment Score] -->|≥ min_score| ALLOW[ALLOW: run function]
  A -->|< min_score| FAIL[Quality Failure]
  FAIL -->|on_failure = "raise"| RAISE[BLOCK: raise error]
  FAIL -->|on_failure = "warn"| WARN[Proceed + warn]
  FAIL -->|on_failure = "continue"| CONTINUE[Proceed silently + log]
  style ALLOW fill:#e8ffe8,stroke:#4CAF50
  style RAISE fill:#ffe8e8,stroke:#f44336
  style WARN fill:#fff8e1,stroke:#ff9800
  style CONTINUE fill:#e3f2fd,stroke:#2196f3
```

Notes:
- Default policy is configurable; commonly "raise" in production.
- Set on the decorator with `on_failure="raise" | "warn" | "continue"`.

Example:
```python
@adri_protected(standard="invoice_data_standard", data_param="invoice_rows", on_failure="raise")
def process_invoices(invoice_rows):
    ...
```

## Audit trail

ADRI logs every assessment in 5 interconnected files, creating a complete audit trail for compliance, debugging, and AI transparency:

| File | Format | Purpose |
|------|--------|---------|
| adri_assessment_logs.jsonl | JSONL | Main audit trail with overall results |
| adri_dimension_scores.jsonl | JSONL | Breakdown across 5 quality dimensions |
| adri_failed_validations.jsonl | JSONL | Specific validation failures with remediation suggestions |
| adri_reasoning_prompts.jsonl | JSONL | AI prompts sent to LLM with cryptographic hashes |
| adri_reasoning_responses.jsonl | JSONL | AI responses with performance metrics |

All files are linked via `assessment_id`, providing complete lineage from assessment → dimensions → failures → AI reasoning.

```mermaid
flowchart TB
  A[Assessment Log] --> D[Dimension Scores]
  A --> F[Failed Validations]
  A --> P[AI Prompts]
  P --> R[AI Responses]
  style A fill:#eef,stroke:#88f,stroke-width:2px
  style D fill:#efe,stroke:#8f8
  style F fill:#fee,stroke:#f88
  style P fill:#ffe,stroke:#ff8
  style R fill:#ffe,stroke:#ff8
```

Key benefits:
- **Compliance**: Complete lineage for regulatory audits
- **AI Transparency**: Full visibility into AI decisions with cryptographic verification
- **Debugging**: Detailed failure tracking with remediation suggestions
- **Performance**: Token usage, processing times, and cost metrics

See [Audit Trail & Logging](audit-and-logging.md) for detailed documentation on all log files, query examples, and integration patterns.

## Quick reference
## Quick reference

- Use a logical name for the decorator (no .yaml).
- Use a filesystem path for CLI commands.
- Canonical example variable: `invoice_rows`.
- Dimensions: validity, completeness, consistency, plausibility, freshness.
- Protection modes: raise | warn | continue.
- Audit logs: 5 files (all JSONL format) linked via `assessment_id`.
