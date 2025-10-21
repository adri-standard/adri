"""Validity dimension assessor for the ADRI validation framework.

This module contains the ValidityAssessor class that evaluates data validity
(format correctness and type compliance) according to field requirements
defined in ADRI standards.
"""

from collections import defaultdict
from typing import Any

import pandas as pd

from ...core.protocols import DimensionAssessor
from ..rules import (
    check_allowed_values,
    check_date_bounds,
    check_field_pattern,
    check_field_range,
    check_field_type,
    check_length_bounds,
)


class ValidityAssessor(DimensionAssessor):
    """Assesses data validity (format correctness and type compliance).

    The validity assessor evaluates whether data values conform to their expected
    types, patterns, ranges, and constraints as defined in the standard's field
    requirements.
    """

    def get_dimension_name(self) -> str:
        """Get the name of this dimension."""
        return "validity"

    def assess(self, data: Any, requirements: dict[str, Any]) -> float:
        """Assess validity dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the validity quality
        """
        if not isinstance(data, pd.DataFrame):
            return 20.0  # Perfect score for non-DataFrame data

        # Get field requirements
        field_requirements = requirements.get("field_requirements", {})
        if not field_requirements:
            return self._assess_validity_basic(data)

        # Check if using new validation_rules format
        using_validation_rules = self._has_validation_rules_format(field_requirements)

        if using_validation_rules:
            # New format: Use validation_rules with severity filtering
            return self._assess_validity_with_rules(data, field_requirements)

        # Old format: Use existing weighted/simple scoring
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {})
        field_overrides_cfg = scoring_cfg.get("field_overrides", {})

        if (
            not isinstance(rule_weights_cfg, dict)
            or len(rule_weights_cfg) == 0
            or not scoring_cfg
        ):
            return self._assess_validity_simple(data, field_requirements)

        return self._assess_validity_weighted(
            data, field_requirements, rule_weights_cfg, field_overrides_cfg
        )

    def _assess_validity_basic(self, data: pd.DataFrame) -> float:
        """Perform basic validity assessment without field requirements."""
        total_checks = 0
        failed_checks = 0

        for column in data.columns:
            column_str = str(column).lower()

            if "email" in column_str:
                for value in data[column].dropna():
                    total_checks += 1
                    if not self._is_valid_email(str(value)):
                        failed_checks += 1

            elif "age" in column_str:
                for value in data[column].dropna():
                    total_checks += 1
                    try:
                        age = float(value)
                        if age < 0 or age > 150:
                            failed_checks += 1
                    except (ValueError, TypeError):
                        failed_checks += 1

        if total_checks == 0:
            return 20.0

        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_validity_simple(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> float:
        """Perform simple validity assessment using field requirements."""
        total_checks = 0
        failed_checks = 0

        for column in data.columns:
            if column in field_requirements:
                field_req = field_requirements[column]
                for value in data[column].dropna():
                    total_checks += 1
                    if not check_field_type(value, field_req):
                        failed_checks += 1
                        continue
                    if not check_allowed_values(value, field_req):
                        failed_checks += 1
                        continue
                    if not check_length_bounds(value, field_req):
                        failed_checks += 1
                        continue
                    if not check_field_pattern(value, field_req):
                        failed_checks += 1
                        continue
                    if not check_field_range(value, field_req):
                        failed_checks += 1
                        continue
                    if not check_date_bounds(value, field_req):
                        failed_checks += 1
                        continue

        if total_checks == 0:
            return 20.0

        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_validity_weighted(
        self,
        data: pd.DataFrame,
        field_requirements: dict[str, Any],
        rule_weights_cfg: dict[str, float],
        field_overrides_cfg: dict[str, dict[str, float]],
    ) -> float:
        """Weighted validity assessment using rule weights."""
        RULE_KEYS = [
            "type",
            "allowed_values",
            "length_bounds",
            "pattern",
            "numeric_bounds",
            "date_bounds",
        ]

        counts, per_field_counts = self._compute_validity_rule_counts(
            data, field_requirements
        )

        # Apply global weights
        S_global, W_global, applied_global = self._apply_global_rule_weights(
            counts, rule_weights_cfg, RULE_KEYS
        )

        # Apply field overrides
        S_overrides, W_overrides = self._apply_field_overrides(
            per_field_counts, field_overrides_cfg, RULE_KEYS
        )

        S_raw = S_global + S_overrides
        W = W_global + W_overrides

        if W <= 0.0:
            return 20.0

        S = S_raw / W
        return S * 20.0

    def _compute_validity_rule_counts(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> tuple:
        """Compute totals and passes per rule type and per field."""
        RULE_KEYS = [
            "type",
            "allowed_values",
            "length_bounds",
            "pattern",
            "numeric_bounds",
            "date_bounds",
        ]

        counts = {rk: {"passed": 0, "total": 0} for rk in RULE_KEYS}
        per_field_counts: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: {rk: {"passed": 0, "total": 0} for rk in RULE_KEYS}
        )

        for column in data.columns:
            if column not in field_requirements:
                continue
            field_req = field_requirements[column]
            series = data[column].dropna()

            for value in series:
                # Type check (always performed)
                counts["type"]["total"] += 1
                per_field_counts[column]["type"]["total"] += 1
                if not check_field_type(value, field_req):
                    continue
                counts["type"]["passed"] += 1
                per_field_counts[column]["type"]["passed"] += 1

                # Allowed values (only if rule present)
                if "allowed_values" in field_req:
                    counts["allowed_values"]["total"] += 1
                    per_field_counts[column]["allowed_values"]["total"] += 1
                    if not check_allowed_values(value, field_req):
                        continue
                    counts["allowed_values"]["passed"] += 1
                    per_field_counts[column]["allowed_values"]["passed"] += 1

                # Length bounds (only if present)
                if ("min_length" in field_req) or ("max_length" in field_req):
                    counts["length_bounds"]["total"] += 1
                    per_field_counts[column]["length_bounds"]["total"] += 1
                    if not check_length_bounds(value, field_req):
                        continue
                    counts["length_bounds"]["passed"] += 1
                    per_field_counts[column]["length_bounds"]["passed"] += 1

                # Pattern (only if present)
                if "pattern" in field_req:
                    counts["pattern"]["total"] += 1
                    per_field_counts[column]["pattern"]["total"] += 1
                    if not check_field_pattern(value, field_req):
                        continue
                    counts["pattern"]["passed"] += 1
                    per_field_counts[column]["pattern"]["passed"] += 1

                # Numeric bounds (only if present)
                if ("min_value" in field_req) or ("max_value" in field_req):
                    counts["numeric_bounds"]["total"] += 1
                    per_field_counts[column]["numeric_bounds"]["total"] += 1
                    if not check_field_range(value, field_req):
                        continue
                    counts["numeric_bounds"]["passed"] += 1
                    per_field_counts[column]["numeric_bounds"]["passed"] += 1

                # Date bounds (only if present)
                date_keys = [
                    "after_date",
                    "before_date",
                    "after_datetime",
                    "before_datetime",
                ]
                if any(k in field_req for k in date_keys):
                    counts["date_bounds"]["total"] += 1
                    per_field_counts[column]["date_bounds"]["total"] += 1
                    if not check_date_bounds(value, field_req):
                        continue
                    counts["date_bounds"]["passed"] += 1
                    per_field_counts[column]["date_bounds"]["passed"] += 1

        return counts, per_field_counts

    def _apply_global_rule_weights(
        self,
        counts: dict[str, dict[str, int]],
        rule_weights_cfg: dict[str, float],
        rule_keys: list[str],
    ) -> tuple:
        """Apply normalized global rule weights to aggregate score."""
        S_raw = 0.0
        W = 0.0
        applied_global = self._normalize_rule_weights(
            rule_weights_cfg, rule_keys, counts
        )

        for rule_name, weight in applied_global.items():
            total = counts.get(rule_name, {}).get("total", 0)
            if total <= 0:
                continue
            passed = counts[rule_name]["passed"]
            score_r = passed / total
            S_raw += float(weight) * score_r
            W += float(weight)

        return S_raw, W, applied_global

    def _apply_field_overrides(
        self,
        per_field_counts: dict[str, dict[str, dict[str, int]]],
        overrides_cfg: dict[str, dict[str, float]],
        rule_keys: list[str],
    ) -> tuple:
        """Apply field-level overrides to aggregate score."""
        S_add = 0.0
        W_add = 0.0

        if isinstance(overrides_cfg, dict):
            for field_name, overrides in overrides_cfg.items():
                if field_name not in per_field_counts or not isinstance(
                    overrides, dict
                ):
                    continue
                for rule_name, weight in overrides.items():
                    if rule_name not in rule_keys:
                        continue
                    try:
                        fw = float(weight)
                    except Exception:
                        fw = 0.0
                    if fw <= 0.0:
                        continue
                    c = per_field_counts[field_name].get(rule_name)
                    if not c or c.get("total", 0) <= 0:
                        continue
                    passed = c["passed"]
                    total = c["total"]
                    score_fr = passed / total
                    S_add += fw * score_fr
                    W_add += fw

        return S_add, W_add

    def _normalize_rule_weights(
        self,
        rule_weights_cfg: dict[str, float],
        rule_keys: list[str],
        counts: dict[str, dict[str, int]],
    ) -> dict[str, float]:
        """Normalize rule weights: clamp negatives, drop unknowns, equalize when zero."""
        applied: dict[str, float] = {}
        for rk, w in (rule_weights_cfg or {}).items():
            if rk not in rule_keys:
                continue
            try:
                fw = float(w)
            except Exception:
                fw = 0.0
            if fw < 0.0:
                fw = 0.0
            applied[rk] = fw

        # Keep only rule types that had evaluations
        active = {
            rk: applied.get(rk, 0.0)
            for rk in rule_keys
            if counts.get(rk, {}).get("total", 0) > 0
        }

        if active and sum(active.values()) <= 0.0:
            for rk in active.keys():
                active[rk] = 1.0

        return active

    def _is_valid_email(self, email: str) -> bool:
        """Check if email format is valid."""
        import re

        if email.count("@") != 1:
            return False

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def get_validation_failures(
        self, data: pd.DataFrame, requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract detailed validation failures for audit logging.

        Args:
            data: DataFrame to analyze
            requirements: Field requirements from standard

        Returns:
            List of failure records with details about each validation failure
        """
        failures = []
        field_requirements = requirements.get("field_requirements", {})

        if not field_requirements:
            return failures

        # Check if using validation_rules format
        using_validation_rules = self._has_validation_rules_format(field_requirements)

        if using_validation_rules:
            # Extract failures from validation_rules format
            return self._get_validation_rules_failures(data, field_requirements)

        # Track failures by field and rule type (old format)
        failure_tracking = defaultdict(
            lambda: defaultdict(lambda: {"count": 0, "samples": [], "row_indices": []})
        )

        for column in data.columns:
            if column not in field_requirements:
                continue

            field_req = field_requirements[column]
            series = data[column]

            for idx, value in series.items():
                # Skip null values (handled by completeness dimension)
                if pd.isna(value):
                    continue

                # Check each validation rule
                # 1. Type check
                if not check_field_type(value, field_req):
                    failure_tracking[column]["type"]["count"] += 1
                    if len(failure_tracking[column]["type"]["samples"]) < 3:
                        failure_tracking[column]["type"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["type"]["row_indices"].append(idx)
                    continue

                # 2. Allowed values
                if "allowed_values" in field_req and not check_allowed_values(
                    value, field_req
                ):
                    failure_tracking[column]["allowed_values"]["count"] += 1
                    if len(failure_tracking[column]["allowed_values"]["samples"]) < 3:
                        failure_tracking[column]["allowed_values"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["allowed_values"]["row_indices"].append(
                        idx
                    )
                    continue

                # 3. Length bounds
                if (
                    ("min_length" in field_req) or ("max_length" in field_req)
                ) and not check_length_bounds(value, field_req):
                    failure_tracking[column]["length_bounds"]["count"] += 1
                    if len(failure_tracking[column]["length_bounds"]["samples"]) < 3:
                        failure_tracking[column]["length_bounds"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["length_bounds"]["row_indices"].append(idx)
                    continue

                # 4. Pattern
                if "pattern" in field_req and not check_field_pattern(value, field_req):
                    failure_tracking[column]["pattern"]["count"] += 1
                    if len(failure_tracking[column]["pattern"]["samples"]) < 3:
                        failure_tracking[column]["pattern"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["pattern"]["row_indices"].append(idx)
                    continue

                # 5. Numeric bounds
                if (
                    ("min_value" in field_req) or ("max_value" in field_req)
                ) and not check_field_range(value, field_req):
                    failure_tracking[column]["numeric_bounds"]["count"] += 1
                    if len(failure_tracking[column]["numeric_bounds"]["samples"]) < 3:
                        failure_tracking[column]["numeric_bounds"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["numeric_bounds"]["row_indices"].append(
                        idx
                    )
                    continue

                # 6. Date bounds
                date_keys = [
                    "after_date",
                    "before_date",
                    "after_datetime",
                    "before_datetime",
                ]
                if any(k in field_req for k in date_keys) and not check_date_bounds(
                    value, field_req
                ):
                    failure_tracking[column]["date_bounds"]["count"] += 1
                    if len(failure_tracking[column]["date_bounds"]["samples"]) < 3:
                        failure_tracking[column]["date_bounds"]["samples"].append(
                            str(value)[:50]
                        )
                    failure_tracking[column]["date_bounds"]["row_indices"].append(idx)

        # Convert tracking to failure records
        total_rows = len(data)
        for field_name, rule_failures in failure_tracking.items():
            for rule_type, failure_info in rule_failures.items():
                if failure_info["count"] > 0:
                    failures.append(
                        {
                            "dimension": "validity",
                            "field": field_name,
                            "issue": f"{rule_type}_failed",
                            "affected_rows": failure_info["count"],
                            "affected_percentage": (failure_info["count"] / total_rows)
                            * 100.0,
                            "samples": failure_info["samples"],
                            "remediation": self._get_remediation_text(
                                rule_type, field_name, field_requirements[field_name]
                            ),
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

            # Get validity rules for this field (all severities for logging)
            validity_rules = [
                r
                for r in validation_rules
                if isinstance(r, ValidationRule) and r.dimension == "validity"
            ]

            if not validity_rules:
                continue

            # Execute each rule and track failures
            series = data[column]
            for idx, value in series.items():
                # Skip null values (completeness dimension)
                if pd.isna(value):
                    continue

                for rule in validity_rules:
                    if not execute_validation_rule(value, rule, field_config):
                        # Track failure
                        rule_key = f"{rule.rule_type}_{rule.severity.value}"
                        failure_tracking[column][rule_key]["count"] += 1

                        if len(failure_tracking[column][rule_key]["samples"]) < 3:
                            failure_tracking[column][rule_key]["samples"].append(
                                str(value)[:50]
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
                            "dimension": "validity",
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

    def _get_remediation_text(
        self, rule_type: str, field_name: str, field_req: dict[str, Any]
    ) -> str:
        """Generate remediation text for a specific validation failure."""
        if rule_type == "type":
            expected_type = field_req.get("type", "unknown")
            return f"Fix {field_name} to match expected type: {expected_type}"
        elif rule_type == "allowed_values":
            allowed = field_req.get("allowed_values", [])
            return f"Use only allowed values for {field_name}: {', '.join(str(v) for v in allowed[:5])}"
        elif rule_type == "length_bounds":
            min_len = field_req.get("min_length")
            max_len = field_req.get("max_length")
            if min_len and max_len:
                return f"Ensure {field_name} length is between {min_len} and {max_len} characters"
            elif min_len:
                return f"Ensure {field_name} length is at least {min_len} characters"
            else:
                return f"Ensure {field_name} length is at most {max_len} characters"
        elif rule_type == "pattern":
            pattern = field_req.get("pattern", "")
            return f"Ensure {field_name} matches required pattern: {pattern}"
        elif rule_type == "numeric_bounds":
            min_val = field_req.get("min_value")
            max_val = field_req.get("max_value")
            if min_val is not None and max_val is not None:
                return f"Ensure {field_name} is between {min_val} and {max_val}"
            elif min_val is not None:
                return f"Ensure {field_name} is at least {min_val}"
            else:
                return f"Ensure {field_name} is at most {max_val}"
        elif rule_type == "date_bounds":
            after = field_req.get("after_date") or field_req.get("after_datetime")
            before = field_req.get("before_date") or field_req.get("before_datetime")
            if after and before:
                return f"Ensure {field_name} is between {after} and {before}"
            elif after:
                return f"Ensure {field_name} is after {after}"
            else:
                return f"Ensure {field_name} is before {before}"
        else:
            return f"Fix validation issue with {field_name}"

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

    def _assess_validity_with_rules(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> float:
        """Assess validity using validation_rules with severity-aware scoring.

        Only CRITICAL severity rules affect the score. WARNING and INFO rules
        are executed and logged but don't penalize the score.

        Args:
            data: DataFrame to assess
            field_requirements: Field requirements with validation_rules

        Returns:
            Validity score (0.0 to 20.0)
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

            # Filter to only CRITICAL rules for this dimension
            critical_rules = [
                r
                for r in validation_rules
                if isinstance(r, ValidationRule)
                and r.dimension == "validity"
                and r.severity == Severity.CRITICAL
            ]

            if not critical_rules:
                continue

            # Execute CRITICAL rules against data
            series = data[column].dropna()
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
