---
sidebar_position: 5
---

# ADRI API Reference

**Stop AI agents breaking on bad data**
One decorator. Consistent CLI commands. Predictable logs.

## Quick Reference

```python
from adri import adri_protected

@adri_protected(
    standard="invoice_data_standard",
    data_param="invoice_rows",
    min_score=85,
    on_failure="warn",
)
def process_invoices(invoice_rows):
    return pipeline(invoice_rows)
```

```bash
# Generate a standard from a known-good dataset
adri generate-standard examples/data/invoice_data.csv \
  --output examples/standards/invoice_data_ADRI_standard.yaml

# Assess an inbound dataset against that standard
adri assess examples/data/test_invoice_data.csv \
  --standard examples/standards/invoice_data_ADRI_standard.yaml
```

> Standard reference: The decorator uses a logical name (omit `.yaml`), while the CLI expects a filesystem path. See [Core Concepts](core-concepts.md) for details and the five dimensions.

---

## Decorator API

### `adri.adri_protected`

Protect any callable with pre-execution data quality checks.

```python
adri_protected(
    standard: str,
    data_param: str = "data",
    min_score: float | None = None,
    dimensions: dict[str, float] | None = None,
    on_failure: str | None = None,  # "raise", "warn", or "continue"
    auto_generate: bool = True,
    cache_assessments: bool | None = None,
    verbose: bool | None = None,
    reasoning_mode: bool = False,
    store_prompt: bool = True,
    store_response: bool = True,
    llm_config: dict | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `standard` | `str` | required | Name of the YAML standard to load (omit `.yaml`). Must exist in `ADRI/**/standards` or be auto-generated. |
| `data_param` | `str` | `"data"` | Name of the function argument that contains the dataset. Required when your argument isn’t literally called `data`. |
| `min_score` | `float` | config default | Minimum overall score (0–100). When omitted ADRI reads `default_min_score` from configuration. |
| `dimensions` | `dict[str, float]` | `None` | Optional per-dimension minimums (each value 0–20). Example: `{ "validity": 18, "freshness": 16 }`. |
| `on_failure` | `str` | config default | Values: `"raise"`, `"warn"`, or `"continue"`. Controls how ADRI responds when data fails validation. |
| `auto_generate` | `bool` | `True` | Allow ADRI to create a standard automatically if the referenced file does not exist. |
| `cache_assessments` | `bool` | config default | Toggle short-term caching of assessment results for identical inputs. |
| `verbose` | `bool` | config default | Emit detailed protection logs for debugging. |
| `reasoning_mode` | `bool` | `False` | Enable AI/LLM reasoning workflow with prompt and response logging. See [Reasoning Mode](#reasoning-mode) below. |
| `store_prompt` | `bool` | `True` | When `reasoning_mode=True`, log AI prompts to JSONL audit logs. |
| `store_response` | `bool` | `True` | When `reasoning_mode=True`, log AI responses to JSONL audit logs. |
| `llm_config` | `dict` | `None` | LLM configuration dict with keys: `model` (required), `temperature` (required), `seed` (optional), `max_tokens` (optional, default: 4000). |

Returns the wrapped function. Raises `ProtectionError` when `on_failure="raise"` and the data does not pass requirements.

#### Usage Patterns

```python
# Strict production workflow
@adri_protected(standard="financial_data_standard", data_param="ledger", min_score=95)

def reconcile(ledger):
    ...

# Warn-only for a pilot rollout
@adri_protected(
    standard="support_tickets_standard",
    data_param="tickets",
    on_failure="warn",
    verbose=True,
)
def summarize_tickets(tickets):
    ...

# Apply per-dimension minimums
@adri_protected(
    standard="customer_profile_standard",
    data_param="rows",
    dimensions={"validity": 18, "freshness": 15},
)
def update_profiles(rows):
    ...

# Enable AI reasoning mode with prompt/response logging
@adri_protected(
    standard="ai_risk_analysis",
    data_param="projects",
    reasoning_mode=True,
    llm_config={
        "model": "claude-3-5-sonnet",
        "temperature": 0.1,
        "seed": 42
    }
)
def analyze_project_risks(projects):
    # AI reasoning logic here
    enhanced_data = ai_model.analyze(projects)
    return enhanced_data
```

### Reasoning Mode

**Reasoning mode** extends ADRI's quality validation to AI/LLM workflows by capturing prompts and responses to JSONL audit logs. This feature is **decorator-only by design** — it wraps functions that execute AI calls, not CLI commands that validate existing data.

**Key Features:**
- Automatic prompt and response logging to `adri_reasoning_prompts.jsonl` and `adri_reasoning_responses.jsonl`
- SHA-256 hash verification for content integrity
- Relational linking to quality assessments via `prompt_id` and `response_id`
- Thread-safe CSV operations for production use

**When to Use:**
- Wrapping functions that make AI/LLM calls
- Capturing AI reasoning steps for audit trails
- Validating AI-generated outputs (confidence scores, risk levels, etc.)
- Ensuring reproducibility with LLM configuration tracking

**Why Decorator-Only:**

The CLI validates data that already exists. Reasoning mode requires capturing prompts **before** AI execution and responses **after** AI execution. This only makes sense when wrapping the function that performs the AI call, not when checking data quality post-facto.

For complete details, examples, and best practices, see the [Reasoning Mode Guide](./reasoning-mode-guide.md).

---

## CLI Commands

ADRI ships with a streamlined Click-based CLI (`adri`). All commands can be run from any subdirectory inside your project thanks to automatic root detection.

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `adri setup` | Create ADRI folder structure (`ADRI/dev`, `ADRI/prod`) and optional sample data. | `--guide`, `--force`, `--project-name` |
| `adri generate-standard <data>` | Profile a dataset and write a YAML standard. | `--output`, `--force`, `--guide` |
| `adri assess <data> --standard <path>` | Validate data against a standard and emit reports. | `--output`, `--guide` |
| `adri list-standards` | List available standards in the active environment. | – |
| `adri show-standard <name>` | Display requirements for a particular standard. | – |
| `adri validate-standard <path>` | Validate the structure of a YAML standard. | – |
| `adri show-config` | Print the active configuration (paths, protection defaults, environments). | `--paths-only`, `--environment` |
| `adri list-assessments` | View recent assessment runs from `ADRI/**/assessments`. | `--recent`, `--verbose` |
| `adri view-logs` | Tail audit logs when logging is enabled. | – |
| `adri help-guide` | Re-display the guided tutorial walkthrough. | – |

All commands support relative paths (e.g. `examples/data/test_invoice_data.csv`) because ADRI resolves them against the detected project root. Use `adri show-config --paths-only` to confirm where reports and standards are written.

---

## Standards & Validation Engine

### `adri.standards.parser.StandardsParser`

Loads, validates, and caches YAML standards. Set the environment variable `ADRI_STANDARDS_PATH` to point at the directory that contains your YAML files before instantiating the parser.

```python
import os
os.environ['ADRI_STANDARDS_PATH'] = '/path/to/ADRI/dev/standards'

from adri.standards.parser import StandardsParser

parser = StandardsParser()
standard = parser.parse_standard('customer_data_standard')
metadata = parser.get_standard_metadata('customer_data_standard')
```

### `adri.validator.engine.ValidationEngine`

Core engine that scores datasets against rules.

```python
from adri.validator.engine import ValidationEngine

engine = ValidationEngine()
result = engine.assess(dataframe, standard_dict)
print(result.overall_score)
```

### `adri.validator.engine.DataQualityAssessor`

High-level helper used by the CLI to combine loading, scoring, and reporting.

```python
from adri.validator.engine import DataQualityAssessor

assessor = DataQualityAssessor()
assessment = assessor.assess(df, "ADRI/dev/standards/customer_data_standard.yaml")
print(assessment.dimension_scores["validity"].score)
```

All assessment results expose `overall_score`, `dimension_scores`, `passed`, `failed_checks`, and formatting helpers (`to_standard_dict`, `to_json`).

---

## Protection Engine Internals

### `adri.guard.modes.DataProtectionEngine`

```python
from adri.guard.modes import DataProtectionEngine, ProtectionError

engine = DataProtectionEngine()
try:
    result = engine.protect_function_call(
        func=process_data,
        args=(dataset,),
        kwargs={},
        data_param="dataset",
        function_name="process_data",
        standard_name="customer_data_standard",
        min_score=80,
        on_failure="raise",
    )
except ProtectionError as exc:
    handle_failure(exc)
```

`DataProtectionEngine` chooses the appropriate protection mode (fail-fast, warn-only, or selective) based on configuration or overrides and ensures audit logs are captured when configured.

---

## Configuration Loader

### `adri.config.loader.ConfigurationLoader`

```python
from adri.config.loader import ConfigurationLoader

loader = ConfigurationLoader()
config_path = loader.find_config_file()
config = loader.load_config(config_path) if config_path else None

if not config:
    config = loader.create_default_config(project_name="customer-agents")
    loader.save_config(config, "ADRI/config.yaml")

active = loader.get_active_config()
print(active["adri"]["protection"]["default_min_score"])
```

The loader understands the schema documented in [Getting Started](getting-started.md#configure-adri-optional) and merges environment overrides automatically.

---

## Logging

ADRI supports local CSV logging and Verodat Enterprise logging through:

- `adri.logging.local.LocalLogger` – writes CSV audit artifacts under `ADRI/**/audit-logs` and is enabled when local audit logging is turned on in configuration.
- `adri.logging.enterprise.EnterpriseLogger` – streams structured events to Verodat MCP workspaces once Verodat credentials are configured.

Configure these behaviours in `ADRI/config.yaml` under `adri.audit` and `adri.verodat`. See the [Adoption Journey](adoption-journey.md) for when to enable enterprise logging.

---

## Exceptions

- `adri.guard.modes.ProtectionError` – Raised when fail-fast protection blocks execution.
- `adri.standards.exceptions.StandardNotFoundError` – Triggered when the requested standard cannot be located.
- `adri.standards.exceptions.InvalidStandardError` – Raised when a malformed standard fails validation.
- `adri.standards.exceptions.StandardsDirectoryNotFoundError` – Raised when `ADRI_STANDARDS_PATH` is missing or incorrect.

Always catch `ProtectionError` around guarded functions if your workflow needs custom remediation. Use the standards exceptions to surface configuration issues early in CI.

---

*API reference for ADRI v3.x. If the code changes, update this document alongside the implementation.*
