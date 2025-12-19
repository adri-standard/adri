# ADRI Enterprise Features

This document catalogs all features available in ADRI Enterprise, including both
open source features and enterprise-exclusive capabilities.

## Table of Contents

- [CLI Commands](#cli-command)
- [Decorator Parameters](#decorator-param)
- [Logging Features](#logging-feature)

---

## CLI Commands

### `adri assess` 🔵 Open Source

Assess command implementation for ADRI CLI.

**Usage:**
```python
adri assess [options]
```

**Location:** `src/adri/cli/commands/assess.py`

---

### `adri config` 🔵 Open Source

Configuration command implementation for ADRI CLI.

**Usage:**
```python
adri config [options]
```

**Location:** `src/adri/cli/commands/config.py`

---

### `adri generate-contract` 🔵 Open Source

Generate contract command implementation for ADRI CLI.

**Usage:**
```python
adri generate-contract [options]
```

**Location:** `src/adri/cli/commands/generate_contract.py`

---

### `adri guide` 🔵 Open Source

Guide command implementation for ADRI CLI.

**Usage:**
```python
adri guide [options]
```

**Location:** `src/adri/cli/commands/guide.py`

---

### `adri list-assessments` 🔵 Open Source

List assessments command implementation for ADRI CLI.

**Usage:**
```python
adri list-assessments [options]
```

**Location:** `src/adri/cli/commands/list_assessments.py`

---

### `adri scoring` 🔵 Open Source

Scoring command implementation for ADRI CLI.

**Usage:**
```python
adri scoring [options]
```

**Location:** `src/adri/cli/commands/scoring.py`

---

### `adri setup` 🔵 Open Source

Setup command implementation for ADRI CLI.

**Usage:**
```python
adri setup [options]
```

**Location:** `src/adri/cli/commands/setup.py`

---

### `adri view-logs` 🔵 Open Source

View logs command implementation for ADRI CLI.

**Usage:**
```python
adri view-logs [options]
```

**Location:** `src/adri/cli/commands/view_logs.py`

---

## Decorator Parameters

### `auto_generate` 🔵 Open Source

Whether to auto-generate missing contracts (default: True)

**Usage:**
```python
@adri_protected(auto_generate=...)
```

**Location:** `src/adri/decorator.py`

---

### `auto_generate` 🟢 Enterprise

Whether to auto-generate missing contracts (default: True)

**Usage:**
```python
@adri_protected(auto_generate=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `cache_assessments` 🔵 Open Source

Whether to cache assessment results (uses config default if None)

**Usage:**
```python
@adri_protected(cache_assessments=...)
```

**Location:** `src/adri/decorator.py`

---

### `cache_assessments` 🟢 Enterprise

Whether to cache assessment results

**Usage:**
```python
@adri_protected(cache_assessments=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `contract` 🔵 Open Source

Contract name (REQUIRED) - e.g., "customer_data" or "financial_data"

**Usage:**
```python
@adri_protected(contract=...)
```

**Location:** `src/adri/decorator.py`

---

### `contract` 🟢 Enterprise

Contract name (REQUIRED) - e.g., "customer_data"

**Usage:**
```python
@adri_protected(contract=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `data_param` 🔵 Open Source

Name of the parameter containing data to check (default: "data")

**Usage:**
```python
@adri_protected(data_param=...)
```

**Location:** `src/adri/decorator.py`

---

### `data_param` 🟢 Enterprise

Name of the parameter containing data to check (default: "data")

**Usage:**
```python
@adri_protected(data_param=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `data_provenance` 🟢 Enterprise

Data source provenance dict with keys:

**Usage:**
```python
@adri_protected(data_provenance=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `dimensions` 🔵 Open Source

Specific dimension requirements (e.g., {"validity": 19, "completeness": 18})

**Usage:**
```python
@adri_protected(dimensions=...)
```

**Location:** `src/adri/decorator.py`

---

### `dimensions` 🟢 Enterprise

Specific dimension requirements

**Usage:**
```python
@adri_protected(dimensions=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `llm_config` 🟢 Enterprise

LLM configuration dict with keys: model, temperature, seed, max_tokens

**Usage:**
```python
@adri_protected(llm_config=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `min_score` 🔵 Open Source

Minimum quality score required (0-100, uses config default if None)

**Usage:**
```python
@adri_protected(min_score=...)
```

**Location:** `src/adri/decorator.py`

---

### `min_score` 🟢 Enterprise

Minimum quality score required (0-100)

**Usage:**
```python
@adri_protected(min_score=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `on_assessment` 🔵 Open Source

Optional callback function to receive AssessmentResult after assessment completes.

**Usage:**
```python
@adri_protected(on_assessment=...)
```

**Location:** `src/adri/decorator.py`

---

### `on_assessment` 🟢 Enterprise

Optional callback function to receive AssessmentResult

**Usage:**
```python
@adri_protected(on_assessment=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `on_failure` 🔵 Open Source

How to handle quality failures ("raise", "warn", "continue", uses config default if None)

**Usage:**
```python
@adri_protected(on_failure=...)
```

**Location:** `src/adri/decorator.py`

---

### `on_failure` 🟢 Enterprise

How to handle quality failures ("raise", "warn", "continue")

**Usage:**
```python
@adri_protected(on_failure=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `reasoning_mode` 🟢 Enterprise

Enable AI/LLM reasoning step validation (default: False)

**Usage:**
```python
@adri_protected(reasoning_mode=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `store_prompt` 🟢 Enterprise

Store AI prompts to JSONL audit logs (default: True)

**Usage:**
```python
@adri_protected(store_prompt=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `store_response` 🟢 Enterprise

Store AI responses to JSONL audit logs (default: True)

**Usage:**
```python
@adri_protected(store_response=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `verbose` 🔵 Open Source

Whether to show detailed protection logs (uses config default if None)

**Usage:**
```python
@adri_protected(verbose=...)
```

**Location:** `src/adri/decorator.py`

---

### `verbose` 🟢 Enterprise

Whether to show detailed protection logs

**Usage:**
```python
@adri_protected(verbose=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

### `workflow_context` 🟢 Enterprise

Workflow execution metadata dict with keys:

**Usage:**
```python
@adri_protected(workflow_context=...)
```

**Location:** `src/adri_enterprise/decorator.py`

---

## Logging Features

### `LocalLogger` 🔵 Open Source

JSONL-based local audit logging for assessments

**Usage:**
```python
LocalLogger(config={'enabled': True, 'log_dir': './logs'})
```

**Location:** `src/adri/logging/local.py`

---

### `ReasoningLogger` 🟢 Enterprise

AI reasoning step logging for prompts and responses

**Usage:**
```python
ReasoningLogger(log_dir='./logs')
```

**Location:** `src/adri_enterprise/logging/reasoning.py`

---

### `VerodatLogger` 🟢 Enterprise

Centralized logging via Verodat API with batch processing

**Usage:**
```python
VerodatLogger(api_url='...', api_key='...')
```

**Location:** `src/adri_enterprise/logging/verodat.py`

---
