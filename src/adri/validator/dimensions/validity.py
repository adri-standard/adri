"""Validity dimension assessor for the ADRI validation framework.

This module contains the ValidityAssessor class that evaluates data validity
(format correctness and type compliance) according to field requirements
defined in ADRI standards.
"""

from collections import defaultdict
from typing import Any, Dict, List

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

    def assess(self, data: Any, requirements: Dict[str, Any]) -> float:
        """Assess validity dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the validity quality
        """
        if not isinstance(data, pd.DataFrame):
            return 18.0  # Default score for non-DataFrame data

        # Get field requirements and scoring configuration
        field_requirements = requirements.get("field_requirements", {})
        if not field_requirements:
            return self._assess_validity_basic(data)

        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {})
        field_overrides_cfg = scoring_cfg.get("field_overrides", {})

        # If no rule weights provided, fall back to simple method
        if not isinstance(rule_weights_cfg, dict) or len(rule_weights_cfg) == 0:
            return self._assess_validity_simple(data, field_requirements)

        # Use weighted rule-type scoring
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
            return 18.0

        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_validity_simple(
        self, data: pd.DataFrame, field_requirements: Dict[str, Any]
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
            return 18.0

        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_validity_weighted(
        self,
        data: pd.DataFrame,
        field_requirements: Dict[str, Any],
        rule_weights_cfg: Dict[str, float],
        field_overrides_cfg: Dict[str, Dict[str, float]],
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
            return 18.0

        S = S_raw / W
        return S * 20.0

    def _compute_validity_rule_counts(
        self, data: pd.DataFrame, field_requirements: Dict[str, Any]
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
        per_field_counts: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
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
        counts: Dict[str, Dict[str, int]],
        rule_weights_cfg: Dict[str, float],
        rule_keys: List[str],
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
        per_field_counts: Dict[str, Dict[str, Dict[str, int]]],
        overrides_cfg: Dict[str, Dict[str, float]],
        rule_keys: List[str],
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
        rule_weights_cfg: Dict[str, float],
        rule_keys: List[str],
        counts: Dict[str, Dict[str, int]],
    ) -> Dict[str, float]:
        """Normalize rule weights: clamp negatives, drop unknowns, equalize when zero."""
        applied: Dict[str, float] = {}
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
