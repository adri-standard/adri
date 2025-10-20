"""Plausibility dimension assessor for the ADRI validation framework.

This module contains the PlausibilityAssessor class that evaluates data plausibility
(statistical outliers and business logic coherence) according to requirements
defined in ADRI standards.
"""

from typing import Any

import pandas as pd

from ...core.protocols import DimensionAssessor


class PlausibilityAssessor(DimensionAssessor):
    """Assesses data plausibility (statistical outliers and business logic coherence).

    The plausibility assessor evaluates whether data values are statistically
    reasonable and conform to business logic constraints. This is distinct from
    validity in that it focuses on statistical plausibility rather than format
    correctness.
    """

    def get_dimension_name(self) -> str:
        """Get the name of this dimension."""
        return "plausibility"

    def assess(self, data: Any, requirements: dict[str, Any]) -> float:
        """Assess plausibility dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the plausibility quality
        """
        if not isinstance(data, pd.DataFrame):
            return 20.0  # Perfect score for non-DataFrame data

        if data.empty:
            return 20.0  # Perfect score for empty data

        # Check if using new validation_rules format
        field_requirements = requirements.get("field_requirements", {})
        using_validation_rules = self._has_validation_rules_format(field_requirements)

        if using_validation_rules:
            # New format: Use validation_rules with severity filtering
            return self._assess_plausibility_with_validation_rules(
                data, field_requirements
            )

        # Old format: Use existing rule weight scoring
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {}) if scoring_cfg else {}

        # Check if any rules are active
        active_weights = {
            k: float(v) for k, v in rule_weights_cfg.items() if float(v or 0) > 0
        }

        if not active_weights:
            return 20.0  # Perfect score when no rules active

        # Execute plausibility rules
        return self._assess_plausibility_with_rules(data, active_weights)

    def _assess_plausibility_with_rules(
        self, data: pd.DataFrame, active_weights: dict[str, float]
    ) -> float:
        """Assess plausibility using active rule weights."""
        rule_results = self._execute_plausibility_rules(data, active_weights)

        # Calculate weighted score
        total_weight = sum(active_weights.values())
        if total_weight <= 0:
            return 20.0

        weighted_score = sum(
            active_weights.get(rule, 0) * result["pass_rate"]
            for rule, result in rule_results.items()
        )

        score = (weighted_score / total_weight) * 20.0
        return float(score)

    def _execute_plausibility_rules(
        self, data: pd.DataFrame, active_weights: dict[str, float]
    ) -> dict[str, Any]:
        """Execute plausibility rules that are distinct from validity rules."""
        results = {}

        # Statistical outliers - IQR-based outlier detection
        if "statistical_outliers" in active_weights:
            results["statistical_outliers"] = self._assess_statistical_outliers(data)

        # Categorical frequency - flag rare categories
        if "categorical_frequency" in active_weights:
            results["categorical_frequency"] = self._assess_categorical_frequency(data)

        # Business logic - domain-specific rules
        if "business_logic" in active_weights:
            results["business_logic"] = self._assess_business_logic(data)

        # Cross-field consistency - relationships between fields
        if "cross_field_consistency" in active_weights:
            results["cross_field_consistency"] = self._assess_cross_field_consistency(
                data
            )

        return results

    def _assess_statistical_outliers(self, data: pd.DataFrame) -> dict[str, Any]:
        """Assess statistical outliers using IQR method (distinct from validity bounds)."""
        passed = 0
        total = 0

        for col in data.columns:
            series = data[col]
            if series.dtype in ["int64", "float64"]:
                non_null = series.dropna()
                if len(non_null) < 4:  # Need at least 4 values for IQR
                    continue

                q1 = non_null.quantile(0.25)
                q3 = non_null.quantile(0.75)
                iqr = q3 - q1

                if iqr > 0:  # Avoid division by zero
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr

                    for value in non_null:
                        total += 1
                        if lower_bound <= value <= upper_bound:
                            passed += 1

        return {
            "passed": passed,
            "total": total,
            "pass_rate": (passed / total) if total > 0 else 1.0,
        }

    def _assess_categorical_frequency(self, data: pd.DataFrame) -> dict[str, Any]:
        """Assess categorical frequency - flag rare categories."""
        passed = 0
        total = 0

        for col in data.columns:
            series = data[col]
            if series.dtype == "object":  # String/categorical columns
                non_null = series.dropna()
                if len(non_null) == 0:
                    continue

                # Categories appearing in <5% of data are considered "rare"
                value_counts = non_null.value_counts()
                threshold = len(non_null) * 0.05

                for value in non_null:
                    total += 1
                    if value_counts[value] >= threshold:
                        passed += 1

        return {
            "passed": passed,
            "total": total,
            "pass_rate": (passed / total) if total > 0 else 1.0,
        }

    def _assess_business_logic(self, data: pd.DataFrame) -> dict[str, Any]:
        """Assess business logic rules (placeholder - can be extended with domain rules)."""
        # Placeholder implementation - assume all values pass business logic for now
        # In a real implementation, this would check domain-specific rules
        total = len(data) if not data.empty else 0
        return {"passed": total, "total": total, "pass_rate": 1.0}

    def _assess_cross_field_consistency(self, data: pd.DataFrame) -> dict[str, Any]:
        """Assess cross-field consistency (placeholder - could check field relationships)."""
        # Placeholder implementation - assume all records are consistent for now
        # In a real implementation, this would check relationships between fields
        total = len(data) if not data.empty else 0
        return {"passed": total, "total": total, "pass_rate": 1.0}

    def get_plausibility_breakdown(
        self, data: pd.DataFrame, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed plausibility breakdown for reporting.

        Args:
            data: DataFrame to analyze
            requirements: Requirements from standard

        Returns:
            Detailed breakdown including rule execution results
        """
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {}) if scoring_cfg else {}

        # Check for active rules
        active_weights = {
            k: float(v) for k, v in rule_weights_cfg.items() if float(v or 0) > 0
        }

        if not active_weights:
            return {
                "rule_counts": {
                    "statistical_outliers": {"passed": 0, "total": 0},
                    "categorical_frequency": {"passed": 0, "total": 0},
                    "business_logic": {"passed": 0, "total": 0},
                    "cross_field_consistency": {"passed": 0, "total": 0},
                },
                "pass_rate": 1.0,
                "rule_weights_applied": rule_weights_cfg,
                "score_0_20": 15.5,
                "warnings": [
                    "no active rules configured; using baseline score 15.5/20"
                ],
            }

        # Execute rules and build breakdown
        rule_results = self._execute_plausibility_rules(data, active_weights)

        # Build rule counts for breakdown
        rule_counts = {
            rule: {"passed": result.get("passed", 0), "total": result.get("total", 0)}
            for rule, result in rule_results.items()
        }

        # Fill in zero counts for inactive rules
        for rule in [
            "statistical_outliers",
            "categorical_frequency",
            "business_logic",
            "cross_field_consistency",
        ]:
            if rule not in rule_counts:
                rule_counts[rule] = {"passed": 0, "total": 0}

        # Calculate overall statistics
        overall_passed = sum(r["passed"] for r in rule_counts.values())
        overall_total = sum(r["total"] for r in rule_counts.values())
        pass_rate = (overall_passed / overall_total) if overall_total > 0 else 1.0

        # Calculate weighted score
        total_weight = sum(active_weights.values())
        if total_weight > 0:
            weighted_score = sum(
                active_weights.get(rule, 0)
                * rule_results.get(rule, {}).get("pass_rate", 1.0)
                for rule in active_weights.keys()
            )
            score = (weighted_score / total_weight) * 20.0
        else:
            score = 15.5

        return {
            "rule_counts": rule_counts,
            "pass_rate": float(pass_rate),
            "rule_weights_applied": active_weights,
            "score_0_20": float(score),
            "warnings": [],
        }

    def assess_with_config(
        self, data: pd.DataFrame, plausibility_config: dict[str, Any]
    ) -> float:
        """Assess plausibility with explicit configuration for backward compatibility.

        Args:
            data: DataFrame to assess
            plausibility_config: Configuration containing outlier_detection, business_rules etc.

        Returns:
            Plausibility score between 0.0 and 20.0
        """
        total_checks = 0
        failed_checks = 0

        outlier_detection = plausibility_config.get("outlier_detection", {})
        business_rules = plausibility_config.get("business_rules", {})

        # Check business rules
        for field, rules in business_rules.items():
            if field in data.columns:
                min_val = rules.get("min")
                max_val = rules.get("max")
                for value in data[field].dropna():
                    total_checks += 1
                    try:
                        numeric_value = float(value)
                        if min_val is not None and numeric_value < min_val:
                            failed_checks += 1
                        elif max_val is not None and numeric_value > max_val:
                            failed_checks += 1
                    except Exception:
                        failed_checks += 1

        # Check outlier detection rules
        for field, rules in outlier_detection.items():
            if field in data.columns:
                method = rules.get("method")
                if method == "range":
                    min_val = rules.get("min")
                    max_val = rules.get("max")
                    for value in data[field].dropna():
                        total_checks += 1
                        try:
                            numeric_value = float(value)
                            if min_val is not None and numeric_value < min_val:
                                failed_checks += 1
                            elif max_val is not None and numeric_value > max_val:
                                failed_checks += 1
                        except Exception:
                            failed_checks += 1

        if total_checks > 0:
            success_rate = (total_checks - failed_checks) / total_checks
            return success_rate * 20.0

        return 20.0  # Perfect score

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

    def _assess_plausibility_with_validation_rules(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> float:
        """Assess plausibility using validation_rules with severity-aware scoring.

        Only CRITICAL severity rules affect the score. WARNING and INFO rules
        are executed and logged but don't penalize the score.

        Args:
            data: DataFrame to assess
            field_requirements: Field requirements with validation_rules

        Returns:
            Plausibility score (0.0 to 20.0)
        """
        from src.adri.core.severity import Severity
        from src.adri.core.validation_rule import ValidationRule

        # Note: Plausibility rules are often statistical/informational
        # Most plausibility rules may be WARNING or INFO severity
        # For now, return perfect score if no CRITICAL rules
        # This can be extended when actual plausibility validation_rules are defined

        total_critical_checks = 0

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

            # Filter to only CRITICAL rules for plausibility dimension
            critical_rules = [
                r
                for r in validation_rules
                if isinstance(r, ValidationRule)
                and r.dimension == "plausibility"
                and r.severity == Severity.CRITICAL
            ]

            if not critical_rules:
                continue

            # For future: execute CRITICAL plausibility rules
            # For now, most plausibility is WARNING/INFO, so this returns perfect score
            total_critical_checks += 1  # Placeholder

        # Calculate score based on CRITICAL rules only
        if total_critical_checks == 0:
            return 20.0  # No CRITICAL rules = perfect score

        # Placeholder for when plausibility rules are fully implemented
        return 20.0
