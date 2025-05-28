# Methodology

## Core Framework

The Agent Data Readiness Index (ADRI) evaluates data sources based on five critical dimensions that impact agent performance. For each dimension, we assess not just the raw quality of the data, but more importantly **whether quality attributes are explicitly communicated to agents** - addressing the unique "blindness" problem in agentic systems.

## The Five Dimensions

### 1. Validity

**Definition**: Whether data adheres to required types, formats, and ranges.

**Key Assessment Criteria**:
- Does the data source define expected formats/ranges?
- Are violations explicitly flagged to agents?
- Can agents detect when validity checks were not performed?

**Scoring Components (0-20 points total)**:
- Types Defined (0-5): Whether data types are explicitly defined for all fields
- Formats Defined (0-3): Whether format patterns are defined for applicable fields
- Ranges Defined (0-3): Whether valid value ranges are defined for applicable fields
- Validation Performed (0-3): Whether validation is performed on the data source
- Validation Communicated (0-6): Whether validation results are properly communicated to agents

**Explicit vs. Implicit Assessment**:
- ADRI prioritizes explicit metadata but can also perform automated assessment
- Full documentation available in [validity_dimension.md](validity_dimension.md)

**Scoring Ranges**:
- 0-5: No explicit format definitions or validation signals
- 6-10: Basic validation exists but not communicated to agents
- 11-15: Validation errors explicitly communicated to agents
- 16-20: Complete validation metadata available to agents in machine-readable format

### 2. Completeness

**Definition**: Whether all expected data is present.

**Key Assessment Criteria**:
- Are missing values explicitly marked as null vs. absent?
- Can agents determine if entire expected sections are missing?
- Is completeness percentage calculated and exposed?

**Scoring Components (0-20 points total)**:
- Overall Completeness (0-5): The percentage of non-missing values across the dataset
- Null Distinction (0-5): Whether missing values are explicitly distinguished from nulls
- Explicit Metrics (0-5): Whether completeness metrics are explicitly available to agents
- Section Awareness (0-5): Whether completeness is tracked at the section level

**Explicit vs. Implicit Assessment**:
- ADRI prioritizes explicit metadata but can also perform automated assessment
- Full documentation available in [completeness_dimension.md](completeness_dimension.md)

**Scoring Ranges**:
- 0-5: Missing values not distinguished from nulls
- 6-10: Basic null indicators but no completeness metrics
- 11-15: Clear null vs. missing distinction with completeness metrics
- 16-20: Full completeness metadata with section-level awareness

### 3. Freshness

**Definition**: Whether data is current enough for the decision.

**Key Assessment Criteria**:
- Is last update timestamp explicitly available to agents?
- Can agents verify recency requirements are met?
- Are freshness SLAs defined and tracked?

**Scoring (0-20 points)**:
- 0-5: No timestamp or freshness information available
- 6-10: Basic timestamps but no recency context
- 11-15: Defined freshness metrics with clear update information
- 16-20: Complete freshness framework with SLA tracking accessible to agents

### 4. Consistency

**Definition**: Whether data elements maintain logical relationships.

**Key Assessment Criteria**:
- Can agents detect contradictory information?
- Are cross-field validation results exposed to agents?
- Is consistency tracked across related datasets?

**Scoring (0-20 points)**:
- 0-5: No consistency checks or contradictions flagged
- 6-10: Basic validation but not exposed to agents
- 11-15: Consistency metrics available but limited to single datasets
- 16-20: Cross-dataset consistency framework with agent-accessible indicators

### 5. Plausibility

**Definition**: Whether data values are reasonable based on context.

**Key Assessment Criteria**:
- Are outlier detection results available to agents?
- Can agents access historical norms for comparison?
- Are implausible values explicitly flagged?

**Scoring (0-20 points)**:
- 0-5: No plausibility checks performed
- 6-10: Basic outlier detection but not communicated to agents
- 11-15: Outliers and anomalies explicitly flagged
- 16-20: Comprehensive plausibility framework with historical norms and context

## Overall Index Calculation

The Agent Data Readiness Index score is calculated as the sum of all five dimension scores, resulting in a value between 0-100.

### Interpretation Guide:

- **80-100**: Advanced - Ready for critical agentic applications
- **60-79**: Proficient - Suitable for most production agent uses
- **40-59**: Basic - Requires caution in agent applications
- **20-39**: Limited - Significant agent blindness risk
- **0-19**: Inadequate - Not recommended for agentic use

## Assessment Methodology

Organizations can assess their data sources using:

1. **Self-assessment**: Using the ADRI toolkit to evaluate internal data sources
2. **Automated scanning**: Running the ADRI analysis tools against sample datasets
3. **Manual audit**: Following the assessment checklist for each dimension

The assessment produces both quantitative scores and qualitative findings that identify specific blindness areas requiring attention.

## Use in Practice

Teams should conduct an ADRI assessment:
- When developing new agentic systems
- Before moving experimental agents to production
- After significant data source changes
- Periodically to ensure continued data readiness

## Methodology Evolution

This methodology is designed to evolve through community input. We welcome contributions to refine the dimensions, scoring system, and assessment approach.

## Purpose & Test Coverage

**Why this file exists**: Defines the core assessment methodology and scoring framework for ADRI, establishing how data quality is measured across five dimensions specifically for AI agent use cases.

**Key responsibilities**:
- Define the five assessment dimensions and their scoring
- Establish scoring criteria and interpretation guidelines
- Explain explicit vs implicit assessment approaches
- Provide the overall index calculation methodology
- Guide practical use and evolution of the framework

**Test coverage**: This document's methodology, scoring systems, and assessment approaches should be verified by tests documented in [Methodology_test_coverage.md](./test_coverage/Methodology_test_coverage.md)
