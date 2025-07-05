"""
Template-driven report generator for ADRI assessment reports.

This module provides functionality to generate assessment reports using
compiled ADRI Standard templates for efficient runtime performance.
"""

import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict

from .report_templates import ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0


class ReportGenerator:
    """
    Template-driven report generator for ADRI assessment reports.

    Uses compiled ADRI Standard templates to generate standardized assessment
    reports that comply with ADRI v0.1.0 reporting standards.
    """

    def __init__(self):
        """Initialize the report generator with compiled template."""
        self.template: Dict[str, Any] = ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0

    def generate_report(self, assessment_result) -> Dict[str, Any]:
        """
        Generate a standardized assessment report using the compiled ADRI template.

        Args:
            assessment_result: Assessment result object with scores and metadata

        Returns:
            Dictionary containing the formatted assessment report
        """
        # Generate assessment ID
        timestamp = datetime.now(timezone.utc)
        assessment_id = self._generate_assessment_id(timestamp)

        # Build report according to ADRI v0.1.0 template structure
        report = {
            "adri_assessment_report": {
                "metadata": self._build_metadata(
                    assessment_result, assessment_id, timestamp
                ),
                "summary": self._build_summary(assessment_result),
                "rule_execution_log": self._build_rule_execution_log(assessment_result),
                "field_analysis": self._build_field_analysis(assessment_result),
            }
        }

        return report

    def _generate_assessment_id(self, timestamp: datetime) -> str:
        """
        Generate a unique assessment ID following the template pattern.

        Args:
            timestamp: UTC timestamp for the assessment

        Returns:
            Formatted assessment ID
        """
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        random_str = "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6)
        )

        return f"adri_{date_str}_{time_str}_{random_str}"

    def _build_metadata(
        self, assessment_result, assessment_id: str, timestamp: datetime
    ) -> Dict[str, Any]:
        """Build the metadata section of the report."""
        return {
            "assessment_id": assessment_id,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "adri_version": self.template.get("standard_metadata", {}).get(
                "version", "0.1.0"
            ),
            "standard_applied": {
                "id": getattr(assessment_result, "standard_id", "unknown-standard"),
                "version": getattr(assessment_result, "standard_version", "1.0.0"),
                "domain": getattr(assessment_result, "standard_domain", "data_quality"),
            },
            "dataset": {
                "name": getattr(assessment_result, "dataset_name", "unknown-dataset"),
                "total_records": getattr(assessment_result, "total_records", 0),
                "total_fields": getattr(assessment_result, "total_fields", 0),
                "size_mb": getattr(assessment_result, "dataset_size_mb", None),
            },
            "execution": {
                "duration_ms": getattr(assessment_result, "execution_time_ms", 0),
                "rules_executed": getattr(assessment_result, "rules_executed", 0),
                "total_validations": getattr(assessment_result, "total_validations", 0),
            },
        }

    def _build_summary(self, assessment_result) -> Dict[str, Any]:
        """Build the summary section of the report."""
        # Extract dimension scores - handle both dict and object formats
        if (
            hasattr(assessment_result, "dimension_scores")
            and assessment_result.dimension_scores is not None
        ):
            dim_scores = assessment_result.dimension_scores
            if hasattr(dim_scores, "__dict__"):
                # Convert object to dict
                dimension_scores = {
                    "validity": getattr(dim_scores, "validity", 0.0),
                    "completeness": getattr(dim_scores, "completeness", 0.0),
                    "consistency": getattr(dim_scores, "consistency", 0.0),
                    "freshness": getattr(dim_scores, "freshness", 0.0),
                    "plausibility": getattr(dim_scores, "plausibility", 0.0),
                }
            elif isinstance(dim_scores, dict):
                # Already a dict - extract scores from DimensionScore objects if needed
                dimension_scores = {}
                for dim_name, dim_value in dim_scores.items():
                    if hasattr(dim_value, "score"):
                        # It's a DimensionScore object
                        dimension_scores[dim_name] = float(dim_value.score)
                    else:
                        # It's already a number
                        dimension_scores[dim_name] = (
                            float(dim_value)
                            if isinstance(dim_value, (int, float))
                            else 0.0
                        )

                # Ensure all required dimensions are present
                for dim in [
                    "validity",
                    "completeness",
                    "consistency",
                    "freshness",
                    "plausibility",
                ]:
                    if dim not in dimension_scores:
                        dimension_scores[dim] = 0.0
            else:
                # Not a dict or object, fallback to zero scores
                dimension_scores = {
                    "validity": 0.0,
                    "completeness": 0.0,
                    "consistency": 0.0,
                    "freshness": 0.0,
                    "plausibility": 0.0,
                }
        else:
            # Fallback to zero scores
            dimension_scores = {
                "validity": 0.0,
                "completeness": 0.0,
                "consistency": 0.0,
                "freshness": 0.0,
                "plausibility": 0.0,
            }

        # Determine failed dimensions (assuming minimum score of 15.0)
        failed_dimensions = [
            dim for dim, score in dimension_scores.items() if score < 15.0
        ]

        # Handle None values in overall_score
        overall_score = getattr(assessment_result, "overall_score", 0.0)
        if overall_score is None:
            overall_score = 0.0

        # Handle None values in passed status
        passed = getattr(assessment_result, "passed", False)
        if passed is None:
            passed = False

        return {
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "pass_fail_status": {
                "overall_passed": passed,
                "failed_dimensions": failed_dimensions,
                "critical_issues": getattr(assessment_result, "critical_issues", 0),
                "total_failures": getattr(assessment_result, "total_failures", 0),
            },
        }

    def _build_rule_execution_log(self, assessment_result) -> list[Any]:
        """Build the rule execution log section of the report."""
        # Check if assessment_result has rule execution details
        if hasattr(assessment_result, "rule_executions"):
            rule_executions = getattr(assessment_result, "rule_executions", [])
            if isinstance(rule_executions, list):
                return rule_executions
            else:
                return []

        # Generate basic rule execution log from dimension scores
        rule_log = []

        if hasattr(assessment_result, "dimension_scores"):
            dim_scores = assessment_result.dimension_scores

            # Create basic rule entries for each dimension
            dimensions = [
                "validity",
                "completeness",
                "consistency",
                "freshness",
                "plausibility",
            ]

            for dimension in dimensions:
                if hasattr(dim_scores, dimension):
                    score_obj = getattr(dim_scores, dimension)
                elif isinstance(dim_scores, dict):
                    score_obj = dim_scores.get(dimension, 0.0)
                else:
                    score_obj = 0.0

                # Extract numeric score from DimensionScore object if needed
                if hasattr(score_obj, "score"):
                    score = float(score_obj.score)
                else:
                    score = (
                        float(score_obj) if isinstance(score_obj, (int, float)) else 0.0
                    )

                # Create a basic rule execution entry
                rule_entry = {
                    "rule_id": f"{dimension}_basic_check",
                    "dimension": dimension,
                    "field": "overall",
                    "rule_definition": f"Basic {dimension} validation rules",
                    "execution": {
                        "total_records": getattr(assessment_result, "total_records", 0),
                        "passed": int(
                            (score / 20.0)
                            * getattr(assessment_result, "total_records", 0)
                        ),
                        "failed": int(
                            ((20.0 - score) / 20.0)
                            * getattr(assessment_result, "total_records", 0)
                        ),
                        "rule_score": score,
                        "rule_weight": 1.0,
                    },
                }

                rule_log.append(rule_entry)

        return rule_log

    def _build_field_analysis(self, assessment_result) -> Dict[str, Any]:
        """Build the field analysis section of the report."""
        # Check if assessment_result has field analysis details
        if (
            hasattr(assessment_result, "field_analysis")
            and assessment_result.field_analysis
        ):
            field_analysis_attr = getattr(assessment_result, "field_analysis", {})
            if isinstance(field_analysis_attr, dict):
                field_analysis = field_analysis_attr.copy()
            else:
                field_analysis = {}
        else:
            field_analysis = {}

        # Always ensure we have an "overall" field analysis
        if "overall" not in field_analysis:
            overall_score = getattr(assessment_result, "overall_score", 0.0)
            field_analysis["overall"] = {
                "rules_applied": ["overall_quality_check"],
                "overall_field_score": min(overall_score / 5.0, 20.0),  # Scale to 0-20
                "total_failures": getattr(assessment_result, "total_failures", 0),
                "ml_readiness": self._assess_ml_readiness(overall_score),
                "recommended_actions": [],
            }

        # If we have field-level information, add it
        if hasattr(assessment_result, "field_scores"):
            field_scores_attr = getattr(assessment_result, "field_scores", {})
            if isinstance(field_scores_attr, dict):
                for field_name, field_data in field_scores_attr.items():
                    if field_name not in field_analysis:
                        field_analysis[field_name] = {
                            "rules_applied": getattr(
                                field_data,
                                "rules_applied",
                                [f"{field_name}_validation"],
                            ),
                            "overall_field_score": getattr(field_data, "score", 0.0),
                            "total_failures": getattr(field_data, "failures", 0),
                            "ml_readiness": self._assess_ml_readiness(
                                getattr(field_data, "score", 0.0)
                            ),
                            "recommended_actions": [],
                        }

        return field_analysis

    def _assess_ml_readiness(self, score: float) -> str:
        """
        Assess ML readiness based on quality score.

        Args:
            score: Quality score (0-100 or 0-20 depending on context)

        Returns:
            ML readiness assessment
        """
        # Normalize score to 0-100 scale
        if score <= 20:
            normalized_score = (score / 20.0) * 100
        else:
            normalized_score = score

        if normalized_score >= 90:
            return "ready"
        elif normalized_score >= 70:
            return "needs_cleanup"
        elif normalized_score >= 50:
            return "not_ready"
        else:
            return "not_ready"

    def validate_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generated report against ADRI template requirements.

        Args:
            report: Generated report dictionary

        Returns:
            Validation results
        """
        validation_results: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Basic structure validation
        if "adri_assessment_report" not in report:
            validation_results["errors"].append(
                "Missing root object 'adri_assessment_report'"
            )
            validation_results["valid"] = False
            return validation_results

        root = report["adri_assessment_report"]

        # Check required sections from template
        try:
            field_requirements = self.template.get("field_requirements", {})
            if isinstance(field_requirements, dict):
                adri_report_reqs = field_requirements.get("adri_assessment_report", {})
                if isinstance(adri_report_reqs, dict):
                    required_sections = adri_report_reqs.get("required_fields", [])
                else:
                    required_sections = []
            else:
                required_sections = []
        except (KeyError, TypeError, AttributeError):
            # Fallback to basic required sections
            required_sections = [
                "metadata",
                "summary",
                "rule_execution_log",
                "field_analysis",
            ]

        for section in required_sections:
            if section not in root:
                validation_results["errors"].append(
                    f"Missing required section: {section}"
                )
                validation_results["valid"] = False

        # Validate mathematical consistency
        if "summary" in root:
            summary = root["summary"]
            if "dimension_scores" in summary and "overall_score" in summary:
                dim_scores = summary["dimension_scores"]
                calculated_total = sum(dim_scores.values())
                reported_total = summary["overall_score"]

                if abs(calculated_total - reported_total) > 0.1:
                    validation_results["errors"].append(
                        f"Mathematical inconsistency: dimension sum ({calculated_total:.1f}) != overall_score ({reported_total:.1f})"
                    )
                    validation_results["valid"] = False

        return validation_results
