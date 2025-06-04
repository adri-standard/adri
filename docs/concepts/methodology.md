# Methodology

> **📄 This content has been merged into [UNDERSTANDING_DIMENSIONS.md](./UNDERSTANDING_DIMENSIONS.md)**
> 
> To reduce redundancy and provide a single source of truth, the methodology content has been consolidated into the comprehensive dimensions guide. Please refer to UNDERSTANDING_DIMENSIONS.md for:
> - The five assessment dimensions and their definitions
> - Scoring criteria and components
> - Explicit vs implicit assessment approaches
> - Overall index calculation methodology
> - Use in practice guidelines

## Quick Reference

The Agent Data Readiness Index (ADRI) evaluates data sources based on five critical dimensions:

1. **Validity** (0-20 points): Data adherence to types, formats, and ranges
2. **Completeness** (0-20 points): Presence of expected data
3. **Freshness** (0-20 points): Data currency for decision-making
4. **Consistency** (0-20 points): Logical relationships between data elements
5. **Plausibility** (0-20 points): Reasonableness of data values

**Overall Score** (0-100): Sum of all dimension scores

### Score Interpretation:
- **80-100**: Advanced - Ready for critical agentic applications
- **60-79**: Proficient - Suitable for most production agent uses
- **40-59**: Basic - Requires caution in agent applications
- **20-39**: Limited - Significant agent blindness risk
- **0-19**: Inadequate - Not recommended for agentic use

For detailed methodology, scoring breakdowns, and examples, see [UNDERSTANDING_DIMENSIONS.md](./UNDERSTANDING_DIMENSIONS.md).

## Purpose & Test Coverage

**Why this file exists**: Originally defined the core assessment methodology. Now serves as a redirect to the consolidated dimensions documentation to avoid content duplication.

**Key responsibilities**:
- Redirect to comprehensive dimensions documentation
- Provide quick reference for dimension scoring
- Maintain backward compatibility for existing links

**Test coverage**: The methodology content is now covered by tests documented in [UNDERSTANDING_DIMENSIONS_test_coverage.md](./test_coverage/UNDERSTANDING_DIMENSIONS_test_coverage.md)
