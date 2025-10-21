"""Completeness dimension assessor for the ADRI validation framework.

This module contains the CompletenessAssessor class that evaluates data completeness
(missing values and data availability) according to field requirements defined in
ADRI standards.
"""

from typing import Any

import pandas as pd

from ...core.protocols import DimensionAssessor


class CompletenessAssessor(DimensionAssessor):
    """Assesses data completeness (missing values and data availability).

    The completeness assessor evaluates the presence or absence of data values,
    focusing on required fields that should not be null according to the standard.
    """

    def get_dimension_name(self) -> str:
        """Get the name of this dimension."""
        return "completeness"

    def assess(self, data: Any, requirements: dict[str, Any]) -> float:
        """Assess completeness dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the completeness quality
        """
        if not isinstance(data, pd.DataFrame):
            return 20.0  # Perfect score for non-DataFrame data

        if data.empty:
            return 0.0

        # Get field requirements
        field_requirements = requirements.get("field_requirements", {})
        if not field_requirements:
            return self._assess_completeness_basic(data)

        # Check if using new validation_rules format
        using_validation_rules = self._has_validation_rules_format(field_requirements)

        if using_validation_rules:
            # New format: Use validation_rules with severity filtering
            return self._assess_completeness_with_rules(data, field_requirements)

        # Old format: Use nullable-based assessment
        return self._assess_completeness_with_requirements(data, field_requirements)

    def _assess_completeness_basic(self, data: pd.DataFrame) -> float:
        """Perform basic completeness assessment without field requirements."""
        total_cells = int(data.size)
        missing_cells = int(data.isnull().sum().sum())
        completeness_rate = (total_cells - missing_cells) / total_cells
        return float(completeness_rate * 20.0)

    def _assess_completeness_with_requirements(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> float:
        """Assess completeness using field requirements (focusing on non-nullable fields)."""
        # Identify required (non-nullable) fields
        required_fields = [
            col
            for col, cfg in field_requirements.items()
            if isinstance(cfg, dict) and not cfg.get("nullable", True)
        ]

        if not required_fields:
            # If no fields are marked as required, fall back to basic assessment
            return self._assess_completeness_basic(data)

        # Calculate completeness for required fields only
        required_total = len(data) * len(required_fields) if len(data) > 0 else 0
        missing_required = 0

        for col in required_fields:
            if col in data.columns:
                try:
                    missing_required += int(data[col].isnull().sum())
                except Exception:
                    # If there's an error counting nulls, assume all are missing
                    missing_required += len(data)

        if required_total <= 0:
            return self._assess_completeness_basic(data)

        completeness_rate = (required_total - missing_required) / required_total
        return float(completeness_rate * 20.0)

    def get_completeness_breakdown(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed completeness breakdown for reporting.

        Args:
            data: DataFrame to analyze
            field_requirements: Field requirements from standard

        Returns:
            Detailed breakdown including per-field statistics
        """
        required_fields = [
            col
            for col, cfg in field_requirements.items()
            if isinstance(cfg, dict) and not cfg.get("nullable", True)
        ]

        required_total = len(data) * len(required_fields) if len(data) > 0 else 0
        per_field_missing: dict[str, int] = {}

        for col in required_fields:
            if col in data.columns:
                try:
                    per_field_missing[col] = int(data[col].isnull().sum())
                except Exception:
                    per_field_missing[col] = len(data)
            else:
                per_field_missing[col] = len(data)  # Column missing entirely

        missing_required = sum(per_field_missing.values()) if per_field_missing else 0
        pass_rate = (
            ((required_total - missing_required) / required_total)
            if required_total > 0
            else 1.0
        )

        # Top 5 fields with most missing values
        top_missing_fields = sorted(
            [{"field": k, "missing": v} for k, v in per_field_missing.items()],
            key=lambda x: x["missing"],
            reverse=True,
        )[:5]

        return {
            "required_total": int(required_total),
            "missing_required": int(missing_required),
            "pass_rate": float(pass_rate),
            "score_0_20": float(pass_rate * 20.0),
            "per_field_missing": per_field_missing,
            "top_missing_fields": top_missing_fields,
            "required_fields": required_fields,
            "total_required_fields": len(required_fields),
        }

    def assess_with_requirements(
        self, data: pd.DataFrame, requirements: dict[str, Any]
    ) -> float:
        """Assess completeness with explicit requirements for backward compatibility.

        Args:
            data: DataFrame to assess
            requirements: Requirements dictionary that may contain mandatory_fields

        Returns:
            Completeness score between 0.0 and 20.0
        """
        # Handle legacy format where mandatory fields are specified directly
        mandatory_fields = requirements.get("mandatory_fields", [])
        if mandatory_fields:
            total_required_cells = len(data) * len(mandatory_fields)
            missing_required_cells = sum(
                data[field].isnull().sum()
                for field in mandatory_fields
                if field in data.columns
            )
            if total_required_cells > 0:
                completeness_rate = (
                    total_required_cells - missing_required_cells
                ) / total_required_cells
                return float(completeness_rate * 20.0)

        return self._assess_completeness_basic(data)

    def get_validation_failures(
        self, data: pd.DataFrame, requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract detailed completeness failures for audit logging.

        Args:
            data: DataFrame to analyze
            requirements: Field requirements from standard

        Returns:
            List of failure records with details about missing required values
        """

        failures: list[dict[str, Any]] = []
        field_requirements = requirements.get("field_requirements", {})

        if not field_requirements:
            return failures

        # Check if using validation_rules format
        using_validation_rules = self._has_validation_rules_format(field_requirements)

        if using_validation_rules:
            # Extract failures from validation_rules format
            return self._get_validation_rules_failures(data, field_requirements)

        # Identify required (non-nullable) fields (old format)
        required_fields = [
            col
            for col, cfg in field_requirements.items()
            if isinstance(cfg, dict) and not cfg.get("nullable", True)
        ]

        if not required_fields:
            return failures

        total_rows = len(data)

        # Check each required field for missing values
        for field_name in required_fields:
            if field_name not in data.columns:
                # Field completely missing from data
                failures.append(
                    {
                        "dimension": "completeness",
                        "field": field_name,
                        "issue": "field_missing",
                        "affected_rows": total_rows,
                        "affected_percentage": 100.0,
                        "samples": ["<entire field missing>"],
                        "remediation": f"Add {field_name} column to dataset",
                    }
                )
            else:
                # Count null values in this field
                null_mask = data[field_name].isnull()
                null_count = int(null_mask.sum())

                if null_count > 0:
                    # Collect sample row indices (up to 3)
                    null_indices = data[null_mask].index.tolist()[:3]

                    failures.append(
                        {
                            "dimension": "completeness",
                            "field": field_name,
                            "issue": "missing_required",
                            "affected_rows": null_count,
                            "affected_percentage": (
                                (null_count / total_rows) * 100.0
                                if total_rows > 0
                                else 0.0
                            ),
                            "samples": [f"Row {idx}" for idx in null_indices],
                            "remediation": f"Fill missing {field_name} values",
                        }
                    )

        return failures

    def _get_validation_rules_failures(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract failures from validation_rules format.

        This handles the new severity-aware validation_rules format where
        each field has a list of ValidationRule objects.

        Args:
            data: DataFrame to analyze
            field_requirements: Field requirements with validation_rules

        Returns:
            List of failure records with details
        """
        from collections import defaultdict

        from src.adri.core.validation_rule import ValidationRule

        from ..rules import execute_validation_rule

        failures = []
        total_rows = len(data)

        # Track failures by field and rule
        failure_tracking = defaultdict(
            lambda: defaultdict(lambda: {"count": 0, "samples": [], "row_indices": []})
        )

        for column in data.columns:
            if column not in field_requirements:
                continue

            field_config = field_requirements[column]
            if not isinstance(field_config, dict):
                continue

            validation_rules = field_config.get("validation_rules", [])
            if not validation_rules:
                continue

            # Get completeness rules for this field (all severities for logging)
            completeness_rules = [
                r
                for r in validation_rules
                if isinstance(r, ValidationRule) and r.dimension == "completeness"
            ]

            if not completeness_rules:
                continue

            # Execute each rule and track failures
            series = data[column]
            for idx, value in series.items():
                for rule in completeness_rules:
                    if not execute_validation_rule(value, rule, field_config):
                        # Track failure
                        rule_key = f"{rule.rule_type}_{rule.severity.value}"
                        failure_tracking[column][rule_key]["count"] += 1

                        if len(failure_tracking[column][rule_key]["samples"]) < 3:
                            sample_val = "<null>" if pd.isna(value) else str(value)[:50]
                            failure_tracking[column][rule_key]["samples"].append(
                                sample_val
                            )
                        failure_tracking[column][rule_key]["row_indices"].append(idx)

        # Convert tracking to failure records
        for field_name, rule_failures in failure_tracking.items():
            for rule_key, failure_info in rule_failures.items():
                if failure_info["count"] > 0:
                    # Extract rule type and severity from key
                    parts = rule_key.rsplit("_", 1)
                    rule_type = parts[0] if len(parts) > 1 else rule_key
                    severity = parts[1] if len(parts) > 1 else "CRITICAL"

                    failures.append(
                        {
                            "dimension": "completeness",
                            "field": field_name,
                            "issue": f"{rule_type}_failed",
                            "severity": severity,
                            "affected_rows": failure_info["count"],
                            "affected_percentage": (failure_info["count"] / total_rows)
                            * 100.0,
                            "samples": failure_info["samples"],
                            "remediation": f"Fix {field_name} to pass {rule_type} validation ({severity} severity)",
                        }
                    )

        return failures

    def _has_validation_rules_format(self, field_requirements: dict[str, Any]) -> bool:
        """Check if field_requirements use new validation_rules format.

        Args:
            field_requirements: Field requirements dictionary

        Returns:
            True if using validation_rules format, False for old format
        """
        # Check if any field has validation_rules
        for field_config in field_requirements.values():
            if isinstance(field_config, dict) and "validation_rules" in field_config:
                return True
        return False

    def _assess_completeness_with_rules(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> float:
        """Assess completeness using validation_rules with severity-aware scoring.

        Only CRITICAL severity rules affect the score. WARNING and INFO rules
        are executed and logged but don't penalize the score.

        Args:
            data: DataFrame to assess
            field_requirements: Field requirements with validation_rules

        Returns:
            Completeness score (0.0 to 20.0)
        """
        from src.adri.core.severity import Severity
        from src.adri.core.validation_rule import ValidationRule

        from ..rules import execute_validation_rule

        total_critical_checks = 0
        failed_critical_checks = 0

        # Process each field
        for column in data.columns:
            if column not in field_requirements:
                continue

            field_config = field_requirements[column]
            if not isinstance(field_config, dict):
                continue

            validation_rules = field_config.get("validation_rules", [])
            if not validation_rules:
                continue

            # Filter to only CRITICAL rules for completeness dimension
            critical_rules = [
                r
                for r in validation_rules
                if isinstance(r, ValidationRule)
                and r.dimension == "completeness"
                and r.severity == Severity.CRITICAL
            ]

            if not critical_rules:
                continue

            # Execute CRITICAL completeness rules against data
            series = data[column]  # Include nulls for completeness checking
            for value in series:
                for rule in critical_rules:
                    total_critical_checks += 1
                    if not execute_validation_rule(value, rule, field_config):
                        failed_critical_checks += 1

        # Calculate score based on CRITICAL rules only
        if total_critical_checks == 0:
            return 20.0  # No CRITICAL rules = perfect score

        success_rate = (
            total_critical_checks - failed_critical_checks
        ) / total_critical_checks
        return success_rate * 20.0
