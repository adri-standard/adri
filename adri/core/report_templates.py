"""
Compiled ADRI assessment report templates.

This module contains Python constants compiled from ADRI Standard YAML files
for efficient runtime usage while maintaining standards compliance.

Source: adri_assessment_report_standard_v0.1.0.yaml
"""

# ADRI Assessment Report Standard v0.1.0 - Compiled Template
ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0 = {
    "standard_metadata": {
        "id": "adri-assessment-report-standard-v0.1.0",
        "version": "0.1.0",
        "name": "ADRI Assessment Report Standard v0.1.0",
        "description": "Initial release defining structure, requirements, and validation rules for ADRI assessment report outputs focusing on rule execution facts",
        "domain": "data_quality_reporting",
        "created_date": "2025-07-03",
        "created_by": "ADRI Standards Committee",
        "purpose": "Standardize assessment report format for logging, analysis, and compliance verification",
    },
    "schema_requirements": {
        "root_object": "adri_assessment_report",
        "format": "json",
        "encoding": "utf-8",
        "file_extension": ".json",
    },
    "field_requirements": {
        # Root object
        "adri_assessment_report": {
            "type": "object",
            "nullable": False,
            "description": "Root container for ADRI assessment report",
            "required_fields": [
                "metadata",
                "summary",
                "rule_execution_log",
                "field_analysis",
            ],
        },
        # ===== METADATA SECTION =====
        "metadata": {
            "type": "object",
            "nullable": False,
            "description": "Assessment execution metadata",
            "required_fields": [
                "assessment_id",
                "timestamp",
                "adri_version",
                "standard_applied",
                "dataset",
                "execution",
            ],
        },
        "metadata.assessment_id": {
            "type": "string",
            "nullable": False,
            "pattern": r"^adri_[0-9]{8}_[0-9]{6}_[a-zA-Z0-9]{6}$",
            "description": "Unique assessment identifier in format: adri_YYYYMMDD_HHMMSS_RANDOM",
            "example": "adri_20250703_173015_abc123",
        },
        "metadata.timestamp": {
            "type": "string",
            "nullable": False,
            "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
            "description": "ISO 8601 UTC timestamp when assessment was completed",
            "example": "2025-07-03T17:30:15Z",
        },
        "metadata.adri_version": {
            "type": "string",
            "nullable": False,
            "pattern": r"^0\.[0-9]+\.[0-9]+$",
            "description": "ADRI framework version used for assessment",
            "example": "0.1.0",
        },
        "metadata.standard_applied": {
            "type": "object",
            "nullable": False,
            "description": "Information about the data quality standard used",
            "required_fields": ["id", "version", "domain"],
        },
        "metadata.dataset": {
            "type": "object",
            "nullable": False,
            "description": "Information about the assessed dataset",
            "required_fields": ["name", "total_records", "total_fields"],
        },
        "metadata.execution": {
            "type": "object",
            "nullable": False,
            "description": "Assessment execution statistics",
            "required_fields": ["duration_ms", "rules_executed", "total_validations"],
        },
        # ===== SUMMARY SECTION =====
        "summary": {
            "type": "object",
            "nullable": False,
            "description": "High-level assessment results summary",
            "required_fields": [
                "overall_score",
                "dimension_scores",
                "pass_fail_status",
            ],
        },
        "summary.overall_score": {
            "type": "number",
            "nullable": False,
            "min_value": 0.0,
            "max_value": 100.0,
            "description": "Overall assessment score (sum of dimension scores)",
        },
        "summary.dimension_scores": {
            "type": "object",
            "nullable": False,
            "description": "Scores for each of the five ADRI dimensions",
            "required_fields": [
                "validity",
                "completeness",
                "consistency",
                "freshness",
                "plausibility",
            ],
        },
        "summary.pass_fail_status": {
            "type": "object",
            "nullable": False,
            "description": "Pass/fail status information",
            "required_fields": [
                "overall_passed",
                "failed_dimensions",
                "critical_issues",
                "total_failures",
            ],
        },
        # ===== RULE EXECUTION LOG =====
        "rule_execution_log": {
            "type": "array",
            "nullable": False,
            "min_items": 1,
            "item_type": "object",
            "description": "Detailed log of each rule execution with results",
        },
        # ===== FIELD ANALYSIS =====
        "field_analysis": {
            "type": "object",
            "nullable": False,
            "description": "Per-field analysis aggregating results from all rules applied to each field",
        },
    },
    "business_rules": {
        "mathematical_consistency": [
            {
                "name": "passed_plus_failed_equals_total",
                "description": "For each rule execution: passed + failed must equal total_records",
                "validation": "rule.execution.passed + rule.execution.failed == rule.execution.total_records",
                "severity": "critical",
            },
            {
                "name": "dimension_score_calculation",
                "description": "Dimension score must equal weighted sum of its rule scores",
                "validation": "dimension_score == sum(rule_score * rule_weight) for rules in dimension",
                "severity": "critical",
            },
            {
                "name": "overall_score_calculation",
                "description": "Overall score must equal sum of all dimension scores",
                "validation": "overall_score == validity + completeness + consistency + freshness + plausibility",
                "severity": "critical",
            },
        ],
        "data_integrity": [
            {
                "name": "no_negative_scores",
                "description": "All scores must be non-negative",
                "validation": "all scores >= 0",
                "severity": "critical",
            },
            {
                "name": "score_ranges_valid",
                "description": "Scores must be within valid ranges",
                "validation": "dimension_scores <= 20.0 AND overall_score <= 100.0",
                "severity": "critical",
            },
        ],
    },
    "dimension_requirements": {
        "validity": {
            "minimum_score": 20.0,
            "weight": 0.3,
            "description": "Report structure must be 100% valid according to schema",
        },
        "completeness": {
            "minimum_score": 20.0,
            "weight": 0.3,
            "description": "All required fields must be present and non-null",
        },
        "consistency": {
            "minimum_score": 20.0,
            "weight": 0.2,
            "description": "Mathematical consistency rules must all pass",
        },
        "freshness": {
            "minimum_score": 18.0,
            "weight": 0.1,
            "description": "Timestamps must be recent and properly formatted",
        },
        "plausibility": {
            "minimum_score": 18.0,
            "weight": 0.1,
            "description": "All values must be within reasonable ranges",
        },
    },
    "overall_minimum": 98.0,
    "usage_guidelines": {
        "file_naming": "adri_YYYYMMDD_HHMMSS_dataset-name_RANDOM.json",
        "storage_recommendations": [
            "Store in date-partitioned directories for efficient querying",
            "Compress older reports to save storage space",
            "Index by assessment_id, timestamp, and standard_id for fast retrieval",
        ],
        "integration_notes": [
            "This format is designed for log aggregation systems",
            "All timestamps are in UTC for consistency",
            "Rule execution details enable precise debugging",
            "Field analysis supports ML pipeline integration",
        ],
    },
}

# Dimension score ranges for validation
DIMENSION_SCORE_RANGES = {
    "validity": {"min": 0.0, "max": 20.0},
    "completeness": {"min": 0.0, "max": 20.0},
    "consistency": {"min": 0.0, "max": 20.0},
    "freshness": {"min": 0.0, "max": 20.0},
    "plausibility": {"min": 0.0, "max": 20.0},
}

# Overall score range
OVERALL_SCORE_RANGE = {"min": 0.0, "max": 100.0}

# Assessment ID pattern for validation
ASSESSMENT_ID_PATTERN = r"^adri_[0-9]{8}_[0-9]{6}_[a-zA-Z0-9]{6}$"

# Timestamp pattern for validation
TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
