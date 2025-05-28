# Freshness Dimension

## Overview

The freshness dimension evaluates whether data is current enough for the intended decision and, most importantly, whether this information is explicitly communicated to agents. This dimension is critical for ensuring that AI systems have accurate information about how recently the data was updated and whether it meets defined freshness service-level agreements (SLAs).

## Scoring Components

The freshness dimension is scored on a scale from 0 to 20 points, with the following components:

1. **Timestamp Information** (0-4 points)
   - Whether the data includes clear timestamp information about when it was last updated
   - Full points for explicit timestamp metadata
   - Partial points (70%) for implicit detection of timestamps from file system metadata

2. **Data Age** (0-3 points)
   - How recent the data is based on the timestamp
   - Very fresh (≤1 hour): 3 points
   - Reasonably fresh (≤24 hours): 2 points
   - Somewhat stale (≤72 hours): 1 point
   - Stale (>72 hours): 0 points

3. **Freshness SLA Definition** (0-4 points)
   - Whether there are explicit definitions of how fresh the data should be
   - Full points for explicit SLA definitions
   - Partial points (50%) for inferred SLAs based on update patterns

4. **SLA Compliance** (0-3 points)
   - Whether the data meets the defined freshness SLAs
   - Full points for meeting explicit SLAs
   - Partial points (70%) for meeting inferred SLAs
   - 1 point for not meeting SLAs but having clear SLA definitions
   - 0 points if SLA compliance cannot be determined

5. **Explicit Agent Communication** (0-6 points)
   - Whether freshness information is explicitly communicated to agents in a machine-readable format
   - Full points for explicit freshness metadata
   - Partial points (50%) for implicit detection when allowed by configuration
   - 0 points when no freshness information is available or when explicit metadata is required but not provided

## Explicit vs. Implicit Assessment

The freshness dimension can be assessed using two approaches:

### Explicit Assessment

Explicit assessment relies on dedicated metadata that explicitly describes the freshness of the data. This is the preferred approach as it provides agents with clear, machine-readable information about data freshness.

Benefits of explicit assessment:
- Full scoring points in all categories
- Clear communication to agents about data currency
- Reliable information about freshness SLAs and compliance

Example explicit metadata fields:
- `file_modified_time`: ISO 8601 timestamp of when the data was last updated
- `file_age_hours`: Age of the data in hours
- `max_age_hours`: Maximum acceptable age in hours (SLA)
- `is_fresh`: Boolean indicating whether data meets its freshness SLA

### Implicit Assessment

When explicit metadata is not available, the system can attempt to infer freshness information from implicit sources such as file system metadata or data content analysis.

Characteristics of implicit assessment:
- Receives partial points (typically 50-70% of maximum)
- Only available when `REQUIRE_EXPLICIT_METADATA` configuration is set to `false`
- Less reliable but provides some insight when explicit information is unavailable

Example implicit detection methods:
- File system last modified timestamp
- Analysis of date columns in the data
- Inference of update frequency from time-series patterns

## Configuration Options

The freshness dimension assessment can be configured using the following options:

| Option | Default Value | Description |
|--------|---------------|-------------|
| `MAX_HAS_TIMESTAMP_SCORE` | 4 | Maximum points for having timestamp information |
| `MAX_DATA_AGE_SCORE` | 3 | Maximum points for data age assessment |
| `MAX_HAS_SLA_SCORE` | 4 | Maximum points for having defined freshness SLAs |
| `MAX_MEETS_SLA_SCORE` | 3 | Maximum points for meeting defined SLAs |
| `MAX_EXPLICIT_COMMUNICATION_SCORE` | 6 | Maximum points for explicit agent communication |
| `REQUIRE_EXPLICIT_METADATA` | false | When true, only explicit metadata gets full points |

These options can be configured in the `adri/config/defaults.py` file or through a custom configuration file.

## Companion File Format

To provide explicit freshness metadata, create a `.freshness.json` file alongside the data source with the same base name.

For example, if your data file is `customer_data.csv`, create a companion file named `customer_data.freshness.json`.

### Basic Example

```json
{
  "has_explicit_freshness_info": true,
  "file_modified_time": "2025-05-20T14:30:00Z",
  "file_age_hours": 24.5,
  "max_age_hours": 48,
  "is_fresh": true,
  "update_frequency": "daily"
}
```

### Comprehensive Example

```json
{
  "has_explicit_freshness_info": true,
  "file_modified_time": "2025-05-20T14:30:00Z",
  "file_age_hours": 24.5,
  "max_age_hours": 48,
  "is_fresh": true,
  "update_frequency": "daily",
  "temporal_coverage": {
    "start_date": "2024-01-01",
    "end_date": "2025-04-30"
  },
  "version_info": {
    "version": "2.3.1",
    "release_date": "2025-05-20"
  },
  "freshness_sla": {
    "critical_data_max_age_hours": 12,
    "standard_data_max_age_hours": 48,
    "meets_critical_sla": false,
    "meets_standard_sla": true
  },
  "time_series_info": {
    "frequency": "daily",
    "typical_lag_hours": 8
  },
  "notes": [
    "This dataset is updated once daily at approximately 14:00 UTC",
    "Some metrics may have up to 12 hour reporting lag",
    "Weekend updates may be delayed by up to 24 hours"
  ]
}
```

## Best Practices

To achieve high scores in the freshness dimension:

1. **Provide explicit metadata**:
   - Create a `.freshness.json` companion file
   - Include all key timestamp and SLA information

2. **Define clear freshness SLAs**:
   - Specify the maximum acceptable age for the data
   - Different SLAs may be appropriate for different types of data

3. **Keep data updated**:
   - Implement processes to update data within defined SLA windows
   - Include automatic freshness validation in data pipelines

4. **Communicate freshness to agents**:
   - Ensure freshness information is explicitly available in a machine-readable format
   - Include fields that help agents understand if the data is fresh enough for their needs

5. **Monitor freshness compliance**:
   - Track whether data meets defined freshness SLAs
   - Implement alerts for stale data

## Impact on Agent Decision Making

Agents need to understand data freshness to make appropriate decisions:

- For time-sensitive decisions (e.g., stock trading, emergency response), agents need to know if data is minutes or hours old
- For long-term analysis, agents might accept data that is days or weeks old
- Knowledge of update frequency helps agents plan when to check for new information
- SLA information helps agents judge the reliability and currentness of the data source

By scoring highly in the freshness dimension, data providers enable agents to make informed decisions about whether the data is current enough for their specific use case.

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive documentation on the Freshness dimension, which evaluates whether data is current enough for the intended decision and whether this information is explicitly communicated to agents.

**Key responsibilities**:
- Explain how freshness assessment works in ADRI
- Detail scoring components for data currency evaluation
- Document explicit vs. implicit timestamp detection
- Provide companion file format and examples
- Guide best practices for maintaining fresh data

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [freshness_dimension_test_coverage.md](./test_coverage/freshness_dimension_test_coverage.md)
