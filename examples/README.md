# ADRI Examples

This directory contains examples demonstrating various features and use cases of the Agent Data Readiness Index (ADRI).

## Core Examples (Numbered Sequence)

These examples are designed to be followed in order, building from basic to advanced usage:

1. **[01_basic_assessment.py](01_basic_assessment.py)** - Your first ADRI assessment
   - Load a CSV file
   - Run basic assessment
   - View overall score and findings

2. **[02_requirements_as_code.py](02_requirements_as_code.py)** - Define data quality requirements
   - Set custom thresholds
   - Create reusable requirements
   - Check if data meets requirements

3. **[03_data_team_contract.py](03_data_team_contract.py)** - Establish data contracts
   - Define team agreements
   - Set SLAs for data quality
   - Monitor compliance

4. **[04_multi_source.py](04_multi_source.py)** - Assess multiple data sources
   - Compare quality across sources
   - Identify best data source
   - Aggregate findings

5. **[05_production_guard.py](05_production_guard.py)** - Protect production workflows
   - Use ADRI Guard decorator
   - Prevent bad data from entering pipelines
   - Set up quality gates

6. **[06_metadata_generation.py](06_metadata_generation.py)** - Generate ADRI metadata
   - Create companion metadata files
   - Document data characteristics
   - Enable enhanced assessments

7. **[07_status_auditor_demo.py](07_status_auditor_demo.py)** - AI agent use case
   - Demonstrate agent-ready data
   - Show business impact analysis
   - Generate actionable insights

8. **[08_template_compliance.py](08_template_compliance.py)** - Check template compliance
   - Use pre-built templates
   - Verify compliance status
   - Get remediation guidance

9. **[09_agent_view_pattern.py](09_agent_view_pattern.py)** - Create agent-optimized views
   - Design denormalized datasets
   - Optimize for agent consumption
   - Apply custom validation

10. **[10_template_discovery_demo.py](10_template_discovery_demo.py)** - Template discovery
    - Automatically discover applicable templates
    - Match data to templates
    - Get template recommendations

## Custom Rules Examples

Examples demonstrating how to create custom ADRI rules:

- **[custom_rules/](custom_rules/)** - Custom rule implementations
  - Business email validation rule
  - Duplicate record detection rule
  - Revenue calculation logic rule
  - Sample test data for each rule

See the [Custom Rules Guide](../docs/CUSTOM_RULES_GUIDE.md) for detailed documentation.

## Integration Examples

Examples showing how to integrate ADRI with popular AI/ML frameworks:

- **[integrations/langchain/](integrations/langchain/)** - LangChain integration
- **[integrations/crewai/](integrations/crewai/)** - CrewAI integration
- **[integrations/dspy/](integrations/dspy/)** - DSPy integration
- **[integrations/guard/](integrations/guard/)** - Guard pattern examples
- **[integrations/interactive/](integrations/interactive/)** - Interactive CLI examples

## Example Data

Sample datasets and metadata files used by the examples:

- **[data/](data/)** - Sample CSV files
- **[data/metadata/](data/metadata/)** - Example metadata files organized by dimension
  - `completeness/` - Completeness metadata examples
  - `consistency/` - Consistency metadata examples
  - `freshness/` - Freshness metadata examples
  - `plausibility/` - Plausibility metadata examples

## Legacy Examples

Older examples maintained for backward compatibility:

- **[legacy/](legacy/)** - Previous example implementations

## Running the Examples

1. **Install ADRI**:
   ```bash
   pip install adri
   ```

2. **Run any example**:
   ```bash
   python examples/01_basic_assessment.py
   ```

3. **Explore the output** to understand how ADRI evaluates data quality

## Learning Path

### Beginner
Start with examples 01-03 to understand basic assessment and requirements.

### Intermediate
Work through examples 04-06 to learn about multi-source assessment and metadata.

### Advanced
Explore examples 07-09 and integration examples to see real-world applications.

## Contributing

If you have a useful example to share:
1. Follow the numbered naming convention for core examples
2. Place integration examples in the appropriate subdirectory
3. Include clear documentation in your code
4. Submit a pull request

For more information, see the [main documentation](../docs/).
