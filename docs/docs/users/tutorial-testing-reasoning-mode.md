# Tutorial Testing Guide for Reasoning Mode

## Overview

This guide provides recommendations for adding reasoning mode functionality to ADRI's tutorial testing framework. Tutorial tests demonstrate real-world usage patterns and serve as living documentation for users.

## Suggested Tutorial Additions

### 1. Basic Reasoning Workflow Tutorial

**File**: `ADRI/tutorials/reasoning-basic/`

**Purpose**: Demonstrate simple AI workflow with reasoning mode

**Components**:
```
ADRI/tutorials/reasoning-basic/
├── README.md                           # Tutorial overview
├── data/
│   └── sample_projects.csv            # Sample data
├── standards/
│   └── ai_project_risk_standard.yaml  # Reasoning standard
├── scripts/
│   └── analyze_projects.py            # Tutorial script
└── expected_output/
    ├── assessment_log.csv             # Expected assessment
    ├── prompts_log.csv                # Expected prompts
    └── responses_log.csv              # Expected responses
```

**Tutorial Script Example**:
```python
"""
Tutorial: Basic AI Project Risk Analysis with Reasoning Mode

Demonstrates:
- Setting up reasoning mode
- Logging prompts and responses
- Validating AI outputs
- Checking CSV audit trails
"""

import pandas as pd
from adri import adri_protected

# Sample AI model (mock for tutorial)
class MockRiskAnalyzer:
    def analyze(self, projects):
        # Simulate AI analysis
        results = projects.copy()
        results['ai_risk_level'] = ['HIGH', 'MEDIUM', 'LOW']
        results['ai_confidence_score'] = [0.85, 0.72, 0.91]
        results['ai_recommendations'] = [
            'Increase oversight',
            'Monitor closely',
            'Standard review'
        ]
        return results

ai_analyzer = MockRiskAnalyzer()

@adri_protected(
    standard="ai_project_risk",
    data_param="projects",
    reasoning_mode=True,
    store_prompt=True,
    store_response=True,
    llm_config={
        "model": "mock-ai-model",
        "temperature": 0.1,
        "seed": 42
    }
)
def analyze_project_risks(projects):
    """Analyze project risks with AI reasoning mode."""
    return ai_analyzer.analyze(projects)

if __name__ == "__main__":
    # Load sample data
    projects = pd.read_csv("data/sample_projects.csv")

    # Run analysis
    results = analyze_project_risks(projects)

    # Verify outputs
    print("✓ Analysis complete")
    print(f"✓ Processed {len(results)} projects")
    print(f"✓ CSV logs created in ADRI/dev/audit-logs/")
```

### 2. Multi-Step Reasoning Tutorial

**File**: `ADRI/tutorials/reasoning-multi-step/`

**Purpose**: Show chained reasoning steps with separate validations

**Workflow**:
```python
"""
Tutorial: Multi-Step AI Reasoning

Demonstrates:
- Chaining multiple reasoning steps
- Independent validation per step
- Relational linking across steps
"""

@adri_protected(
    standard="step1_data_extraction",
    data_param="documents",
    reasoning_mode=True,
    llm_config={"model": "extraction-model", "temperature": 0.05}
)
def step1_extract_entities(documents):
    """Step 1: Extract entities from documents."""
    return ai_extractor.extract(documents)

@adri_protected(
    standard="step2_entity_classification",
    data_param="entities",
    reasoning_mode=True,
    llm_config={"model": "classification-model", "temperature": 0.1}
)
def step2_classify_entities(entities):
    """Step 2: Classify extracted entities."""
    return ai_classifier.classify(entities)

@adri_protected(
    standard="step3_risk_assessment",
    data_param="classified_entities",
    reasoning_mode=True,
    llm_config={"model": "risk-model", "temperature": 0.1}
)
def step3_assess_risk(classified_entities):
    """Step 3: Assess risk based on classified entities."""
    return ai_risk_assessor.assess(classified_entities)

# Execute pipeline
documents = load_documents()
entities = step1_extract_entities(documents)
classified = step2_classify_entities(entities)
risk_assessment = step3_assess_risk(classified)
```

### 3. Meta-Validation Tutorial

**File**: `ADRI/tutorials/reasoning-meta-validation/`

**Purpose**: Demonstrate self-validating audit logs

**Example**:
```python
"""
Tutorial: Meta-Validation of Reasoning Logs

Demonstrates:
- Reading reasoning CSV logs
- Validating logs against meta-standards
- Ensuring audit trail quality
"""

import pandas as pd
from adri import adri_protected

# Read reasoning logs
prompts_log = pd.read_csv("ADRI/dev/audit-logs/adri_reasoning_prompts.csv")
responses_log = pd.read_csv("ADRI/dev/audit-logs/adri_reasoning_responses.csv")

# Validate prompts log against meta-standard
@adri_protected(
    standard="adri_reasoning_prompts",
    data_param="prompts"
)
def validate_prompts(prompts):
    """Validate prompts log meets meta-standard."""
    return prompts

# Validate responses log against meta-standard
@adri_protected(
    standard="adri_reasoning_responses",
    data_param="responses"
)
def validate_responses(responses):
    """Validate responses log meets meta-standard."""
    return responses

# Run meta-validation
validated_prompts = validate_prompts(prompts_log)
validated_responses = validate_responses(responses_log)

print("✓ Prompts log validated")
print("✓ Responses log validated")
print("✓ Audit trail meets quality standards")
```

### 4. Backward Compatibility Tutorial

**File**: `ADRI/tutorials/reasoning-backward-compat/`

**Purpose**: Show gradual adoption and zero-impact when disabled

**Example**:
```python
"""
Tutorial: Backward Compatibility

Demonstrates:
- Existing code works unchanged
- Gradual adoption of reasoning mode
- Zero overhead when disabled
"""

# Original function (no reasoning)
@adri_protected(
    standard="customer_data",
    data_param="customers"
)
def process_customers_v1(customers):
    """Original version without reasoning."""
    return process(customers)

# Same function with reasoning enabled
@adri_protected(
    standard="customer_data",
    data_param="customers",
    reasoning_mode=True,  # Only addition needed
    llm_config={"model": "customer-ai", "temperature": 0.1}
)
def process_customers_v2(customers):
    """Enhanced version with reasoning."""
    return process(customers)  # Same processing logic

# Both work identically, v2 adds logging
customers = load_customers()

result_v1 = process_customers_v1(customers)  # No reasoning overhead
result_v2 = process_customers_v2(customers)  # With reasoning logs

assert result_v1.equals(result_v2)  # Results identical
```

### 5. Error Handling Tutorial

**File**: `ADRI/tutorials/reasoning-error-handling/`

**Purpose**: Show how errors are logged and handled

**Example**:
```python
"""
Tutorial: Error Handling in Reasoning Mode

Demonstrates:
- Error logging in response CSV
- Exception propagation
- Debugging failed AI calls
"""

@adri_protected(
    standard="document_analysis",
    data_param="documents",
    reasoning_mode=True,
    on_failure="raise",  # Fail fast
    llm_config={"model": "analyzer", "temperature": 0.1}
)
def analyze_documents(documents):
    """Analyze documents with error handling."""
    try:
        return ai_model.analyze(documents)
    except AIModelError as e:
        # Error logged in responses CSV
        # Exception re-raised for handling
        raise

# Check error log
try:
    result = analyze_documents(problematic_docs)
except Exception as e:
    # Error details in response CSV
    responses = pd.read_csv("ADRI/dev/audit-logs/adri_reasoning_responses.csv")
    error_entries = responses[responses['response_text'].str.contains('ERROR')]
    print(f"Found {len(error_entries)} error entries")
```

## Tutorial Test Framework Integration

### Test Structure

```python
# tests/fixtures/TUTORIAL_SCENARIOS.md addition

## Reasoning Mode Scenarios

### Scenario: Basic Reasoning
**Directory**: `ADRI/tutorials/reasoning-basic/`
**Tests**:
- CSV files created correctly
- Relational integrity (IDs link properly)
- Prompts/responses captured
- Assessment includes reasoning metadata

### Scenario: Multi-Step Reasoning
**Directory**: `ADRI/tutorials/reasoning-multi-step/`
**Tests**:
- Each step creates separate logs
- Run IDs track multi-step workflows
- Step IDs increment correctly
- All steps link to same run

### Scenario: Meta-Validation
**Directory**: `ADRI/tutorials/reasoning-meta-validation/`
**Tests**:
- Reasoning logs validate against meta-standards
- Field types match expectations
- Required fields present
- Hash integrity verified
```

### Test Implementation

```python
# tests/test_tutorial_reasoning.py

"""
Tutorial tests for reasoning mode functionality.
"""

import os
import pandas as pd
import pytest
from pathlib import Path

class TestReasoningTutorials:
    """Test reasoning mode tutorials."""

    def test_basic_reasoning_tutorial(self):
        """Test basic reasoning workflow tutorial."""
        tutorial_dir = Path("ADRI/tutorials/reasoning-basic")

        # Run tutorial script
        os.chdir(tutorial_dir)
        import scripts.analyze_projects as tutorial

        # Verify CSV files created
        assert Path("../../dev/audit-logs/adri_reasoning_prompts.csv").exists()
        assert Path("../../dev/audit-logs/adri_reasoning_responses.csv").exists()

        # Verify content matches expected
        prompts = pd.read_csv("../../dev/audit-logs/adri_reasoning_prompts.csv")
        assert len(prompts) > 0
        assert "model" in prompts.columns
        assert prompts.iloc[0]["model"] == "mock-ai-model"

    def test_multi_step_reasoning_tutorial(self):
        """Test multi-step reasoning tutorial."""
        tutorial_dir = Path("ADRI/tutorials/reasoning-multi-step")

        # Run tutorial
        os.chdir(tutorial_dir)
        import scripts.multi_step_pipeline as tutorial

        # Verify multiple steps logged
        prompts = pd.read_csv("../../dev/audit-logs/adri_reasoning_prompts.csv")

        # Should have 3 prompts (one per step)
        assert len(prompts) >= 3

        # All should share same run_id
        run_ids = prompts["run_id"].unique()
        assert len(run_ids) == 1  # Same run

        # Step IDs should increment
        step_ids = prompts["step_id"].tolist()
        assert "step_001" in step_ids
        assert "step_002" in step_ids
        assert "step_003" in step_ids

    def test_meta_validation_tutorial(self):
        """Test meta-validation tutorial."""
        tutorial_dir = Path("ADRI/tutorials/reasoning-meta-validation")

        # Run meta-validation
        os.chdir(tutorial_dir)
        import scripts.validate_logs as tutorial

        # Verify validation passed
        assert tutorial.validation_passed

        # Check for validation errors
        assert len(tutorial.validation_errors) == 0
```

## Integration with Existing Tutorial Framework

### 1. Update Tutorial Discovery

```python
# tests/test_tutorial_auto_discovery.py addition

def test_discover_reasoning_tutorials():
    """Test that reasoning tutorials are discovered."""
    tutorials_dir = Path("ADRI/tutorials")

    reasoning_tutorials = [
        "reasoning-basic",
        "reasoning-multi-step",
        "reasoning-meta-validation",
        "reasoning-backward-compat",
        "reasoning-error-handling"
    ]

    for tutorial_name in reasoning_tutorials:
        tutorial_path = tutorials_dir / tutorial_name
        assert tutorial_path.exists(), f"Tutorial {tutorial_name} should exist"
        assert (tutorial_path / "README.md").exists(), f"{tutorial_name} needs README"
```

### 2. CLI Integration

```python
# Add to tests/test_tutorial_cli_decorator_parity.py

def test_reasoning_mode_cli_parity():
    """Test CLI and decorator produce same reasoning logs."""

    # Via decorator
    @adri_protected(
        standard="test_std",
        data_param="data",
        reasoning_mode=True,
        llm_config={"model": "test", "temperature": 0.1}
    )
    def process_with_decorator(data):
        return data

    # Via CLI (simulated)
    # adri protect-function --reasoning-mode --model test ...

    # Both should produce identical log structure
```

### 3. Framework Validation

```python
# tests/test_tutorial_framework.py addition

def test_reasoning_tutorials_framework_compliance():
    """Test reasoning tutorials comply with framework standards."""

    reasoning_tutorials = discover_reasoning_tutorials()

    for tutorial in reasoning_tutorials:
        # Check required structure
        assert has_readme(tutorial)
        assert has_data_dir(tutorial)
        assert has_standards_dir(tutorial)
        assert has_scripts_dir(tutorial)
        assert has_expected_output(tutorial)

        # Check reasoning-specific requirements
        assert has_reasoning_standard(tutorial)
        assert has_sample_csv_outputs(tutorial)
```

## Best Practices for Tutorial Tests

### 1. Isolation

```python
@pytest.fixture
def isolated_tutorial_env(tmp_path):
    """Create isolated environment for each tutorial test."""
    adri_dir = tmp_path / "ADRI"
    adri_dir.mkdir()

    # Set up minimal structure
    (adri_dir / "dev" / "standards").mkdir(parents=True)
    (adri_dir / "dev" / "audit-logs").mkdir(parents=True)

    yield adri_dir
```

### 2. Verification

```python
def verify_reasoning_output(tutorial_dir):
    """Verify tutorial produced correct reasoning output."""
    audit_dir = tutorial_dir / "../../dev/audit-logs"

    # Check all expected files
    assert (audit_dir / "adri_assessment_logs.csv").exists()
    assert (audit_dir / "adri_reasoning_prompts.csv").exists()
    assert (audit_dir / "adri_reasoning_responses.csv").exists()

    # Verify relational integrity
    assessments = pd.read_csv(audit_dir / "adri_assessment_logs.csv")
    prompts = pd.read_csv(audit_dir / "adri_reasoning_prompts.csv")
    responses = pd.read_csv(audit_dir / "adri_reasoning_responses.csv")

    # Check IDs link correctly
    assert assessments.iloc[0]["prompt_id"] in prompts["prompt_id"].values
    assert assessments.iloc[0]["response_id"] in responses["response_id"].values
```

### 3. Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_tutorial_artifacts():
    """Clean up tutorial artifacts after tests."""
    yield

    # Remove generated CSV files
    audit_dir = Path("ADRI/dev/audit-logs")
    if audit_dir.exists():
        for csv_file in audit_dir.glob("*.csv"):
            csv_file.unlink()
```

## Tutorial Documentation Template

```markdown
# Tutorial: [Tutorial Name]

## Overview
Brief description of what this tutorial demonstrates.

## Learning Objectives
- Objective 1
- Objective 2
- Objective 3

## Prerequisites
- ADRI installed
- Basic Python knowledge
- Understanding of [concept]

## Tutorial Steps

### Step 1: Setup
```python
# Setup code
```

### Step 2: [Action]
```python
# Action code
```

### Step 3: Verification
```python
# Verification code
```

## Expected Output

### Console Output
```
Expected console output
```

### CSV Files
- `adri_reasoning_prompts.csv`: [description]
- `adri_reasoning_responses.csv`: [description]

## Verification Checklist
- [ ] CSV files created
- [ ] Relational integrity verified
- [ ] Validation passed
- [ ] Expected results match

## Troubleshooting
Common issues and solutions.

## Next Steps
- Try [related tutorial]
- Explore [feature]
- Read [documentation]
```

## Automated Tutorial Testing

```python
# scripts/test-tutorials.sh

#!/bin/bash
# Automated tutorial testing script

echo "Testing ADRI Reasoning Tutorials..."

# Test each reasoning tutorial
for tutorial in reasoning-*; do
    echo "Testing $tutorial..."
    cd "ADRI/tutorials/$tutorial"

    # Run tutorial script
    python scripts/*.py

    # Verify outputs
    python -m pytest ../../tests/test_tutorial_$tutorial.py

    # Clean up
    rm -f ../../dev/audit-logs/*.csv

    cd -
done

echo "✓ All reasoning tutorials passed"
```

## Summary

### Recommended Additions

1. **5 New Tutorial Directories**:
   - `reasoning-basic/`
   - `reasoning-multi-step/`
   - `reasoning-meta-validation/`
   - `reasoning-backward-compat/`
   - `reasoning-error-handling/`

2. **3 New Test Files**:
   - `tests/test_tutorial_reasoning.py`
   - `tests/test_tutorial_reasoning_integration.py`
   - `tests/test_tutorial_meta_validation.py`

3. **Documentation Updates**:
   - Tutorial README files
   - TUTORIAL_SCENARIOS.md additions
   - Integration with existing framework docs

4. **CI Integration**:
   - Add reasoning tutorials to test matrix
   - Verify CSV output structure
   - Check relational integrity

### Benefits

- **Living Documentation**: Tutorials serve as examples and tests
- **Regression Prevention**: Catch breaking changes early
- **User Education**: Show real-world usage patterns
- **Quality Assurance**: Verify end-to-end workflows

### Next Steps

1. Create tutorial directories
2. Write tutorial scripts
3. Add test cases
4. Update documentation
5. Integrate with CI
