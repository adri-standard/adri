# Test Coverage for FAQ.md

This document maps features and claims in FAQ.md to their corresponding test coverage.

## General Questions

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| ADRI as measurement tool | tests/unit/test_assessor.py | ✅ Covered |
| 0-100 scoring scale | tests/unit/test_report.py | ✅ Covered |
| Protocol and tool duality | tests/unit/test_assessor.py | ⚠️ Partial Coverage |

## The Gap ADRI Fills

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| Last-mile data quality | tests/unit/integrations/test_guard.py | ✅ Covered |
| Agent-specific validation | tests/unit/integrations/test_guard.py | ✅ Covered |
| Preventive vs reactive | tests/unit/integrations/test_guard.py | ✅ Covered |
| Guard decorators | tests/unit/integrations/test_guard.py | ✅ Covered |

## Multi-Dataset Questions

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| Single dataset focus | tests/unit/test_assessor.py | ✅ Covered |
| No relationship validation | N/A (by design) | ✅ Not Applicable |
| Agent View pattern | tests/unit/examples/test_09_agent_view_pattern.py | ❌ No Coverage |
| Denormalized views | tests/unit/examples/test_09_agent_view_pattern.py | ❌ No Coverage |

## Technical Questions

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| CSV connector | tests/unit/connectors/test_file_connector.py | ✅ Covered |
| JSON connector | tests/unit/connectors/test_file_connector.py | ✅ Covered |
| Database connector | tests/unit/connectors/test_database_connector.py | ✅ Covered |
| API connector | tests/unit/connectors/test_api_connector.py | ✅ Covered |
| Custom assessment criteria | tests/unit/config/test_config.py | ⚠️ Partial Coverage |

## Framework Integration

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| LangChain integration | tests/unit/integrations/langchain/test_guard.py | ✅ Covered |
| CrewAI integration | tests/unit/integrations/crewai/test_guard.py | ✅ Covered |
| DSPy integration | tests/unit/integrations/dspy/test_guard.py | ✅ Covered |

## Methodology Questions

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| Five dimensions | tests/unit/dimensions/ | ✅ Covered |
| Dimension weighting | tests/unit/config/test_config.py | ⚠️ Partial Coverage |
| Scoring system | tests/unit/test_report.py | ✅ Covered |

## Growing with ADRI

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| Progressive complexity | Examples in tests/unit/examples/ | ✅ Covered |
| Template system | tests/unit/templates/ | ✅ Covered |
| Contract layer concept | Documentation only | ❌ No Coverage |

## Coverage Gaps

The following features require additional test coverage:

1. **Agent View Pattern**:
   - Need tests for example 09_agent_view_pattern.py
   - Tests for denormalized view assessment
   - Tests for custom templates for agent views

2. **Protocol Implementation**:
   - Tests demonstrating protocol vs tool separation
   - Tests for metadata communication format

3. **Contract Layer**:
   - Tests for source-agnostic workflows
   - Tests for requirement specification

4. **Configuration Customization**:
   - More comprehensive tests for dimension weight adjustment
   - Tests for custom threshold configuration

## Next Steps

Based on the identified gaps, the following test development priorities are recommended:

1. Create tests for agent view pattern example
2. Enhance configuration customization tests
3. Add tests demonstrating protocol aspects
4. Document contract layer concepts with examples
