"""Consistency dimension assessor for the ADRI validation framework.

This module contains the ConsistencyAssessor class that evaluates data consistency
(referential integrity and internal coherence) according to requirements defined in
ADRI standards.
"""

from typing import Any, Dict, List

import pandas as pd

from ...core.protocols import DimensionAssessor


class ConsistencyAssessor(DimensionAssessor):
    """Assesses data consistency (referential integrity and internal coherence).

    The consistency assessor evaluates data consistency rules such as primary key
    uniqueness and referential integrity constraints.
    """

    def get_dimension_name(self) -> str:
        """Get the name of this dimension."""
        return "consistency"

    def assess(self, data: Any, requirements: Dict[str, Any]) -> float:
        """Assess consistency dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the consistency quality
        """
        if not isinstance(data, pd.DataFrame):
            return 16.0  # Default score for non-DataFrame data

        if data.empty:
            return 20.0  # Empty data is technically consistent

        # Get consistency configuration from requirements
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {}) if scoring_cfg else {}

        # Get primary key fields for uniqueness checking
        pk_fields = self._get_primary_key_fields(requirements)

        return self._assess_consistency_with_rules(data, rule_weights_cfg, pk_fields)

    def _get_primary_key_fields(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract primary key fields from requirements."""
        # Try to get from record_identification
        record_id = requirements.get("record_identification", {})
        if isinstance(record_id, dict):
            pk_fields = record_id.get("primary_key_fields", [])
            if isinstance(pk_fields, list):
                return pk_fields

        # Fallback: no primary key fields defined
        return []

    def _assess_consistency_with_rules(
        self,
        data: pd.DataFrame,
        rule_weights_cfg: Dict[str, float],
        pk_fields: List[str],
    ) -> float:
        """Assess consistency using configured rules."""
        # Check if primary key uniqueness rule is active
        pk_weight = 0.0
        try:
            pk_weight = float(rule_weights_cfg.get("primary_key_uniqueness", 0.0))
        except Exception:
            pk_weight = 0.0

        if pk_weight < 0.0:
            pk_weight = 0.0

        # If no active rules or no primary key fields, return baseline score
        if not pk_fields or pk_weight <= 0.0:
            return 16.0  # Default baseline score

        # Assess primary key uniqueness
        return self._assess_primary_key_uniqueness(data, pk_fields)

    def _assess_primary_key_uniqueness(
        self, data: pd.DataFrame, pk_fields: List[str]
    ) -> float:
        """Assess primary key uniqueness constraint."""
        # Check if all primary key fields exist in data
        missing_pk_fields = [field for field in pk_fields if field not in data.columns]
        if missing_pk_fields:
            return 0.0  # Can't check uniqueness if key fields are missing

        try:
            # For primary key uniqueness, we need to check for duplicate combinations
            failures = self._check_primary_key_uniqueness(data, pk_fields)

            total_records = len(data)
            if total_records == 0:
                return 20.0

            # Calculate how many records are affected by duplicates
            failed_rows = 0
            for failure in failures:
                affected_rows = failure.get("affected_rows", 0)
                failed_rows += (
                    int(affected_rows) if isinstance(affected_rows, (int, float)) else 0
                )

            # Cap failed rows at total (safety check)
            if failed_rows > total_records:
                failed_rows = total_records

            passed_rows = total_records - failed_rows
            pass_rate = (passed_rows / total_records) if total_records > 0 else 1.0

            return float(pass_rate * 20.0)

        except Exception:
            # If there's an error in checking, return conservative score
            return 10.0

    def _check_primary_key_uniqueness(
        self, data: pd.DataFrame, pk_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for primary key uniqueness violations.

        Args:
            data: DataFrame to check
            pk_fields: List of primary key field names

        Returns:
            List of failure records describing uniqueness violations
        """
        failures = []

        try:
            # Create composite key from primary key fields
            if len(pk_fields) == 1:
                # Single field primary key
                field = pk_fields[0]
                if field in data.columns:
                    # Find duplicates (excluding NaN values)
                    non_null_data = data[data[field].notna()]
                    if len(non_null_data) > 0:
                        value_counts = non_null_data[field].value_counts()
                        duplicates = value_counts[value_counts > 1]

                        for value, count in duplicates.items():
                            failures.append(
                                {
                                    "validation_id": f"pk_uniqueness_{len(failures):03d}",
                                    "dimension": "consistency",
                                    "field": field,
                                    "issue": "duplicate_primary_key",
                                    "affected_rows": int(count),
                                    "affected_percentage": (count / len(data)) * 100.0,
                                    "samples": [str(value)],
                                    "remediation": f"Remove or correct duplicate values for primary key field '{field}'",
                                }
                            )
            else:
                # Composite primary key
                pk_data = data[pk_fields].copy()

                # Only consider rows where all PK fields are non-null
                complete_pk_mask = pk_data.notna().all(axis=1)
                complete_pk_data = pk_data[complete_pk_mask]

                if len(complete_pk_data) > 0:
                    # Find duplicate combinations
                    duplicates = complete_pk_data[
                        complete_pk_data.duplicated(keep=False)
                    ]

                    if len(duplicates) > 0:
                        # Group by duplicate key combinations
                        duplicate_groups = duplicates.groupby(pk_fields).size()

                        for key_combo, count in duplicate_groups.items():
                            if count > 1:
                                # Create sample representation of the key
                                if isinstance(key_combo, tuple):
                                    sample_key = ":".join(str(k) for k in key_combo)
                                else:
                                    sample_key = str(key_combo)

                                failures.append(
                                    {
                                        "validation_id": f"pk_uniqueness_{len(failures):03d}",
                                        "dimension": "consistency",
                                        "field": ":".join(pk_fields),
                                        "issue": "duplicate_composite_primary_key",
                                        "affected_rows": int(count),
                                        "affected_percentage": (count / len(data))
                                        * 100.0,
                                        "samples": [sample_key],
                                        "remediation": f"Remove or correct duplicate combinations for composite primary key ({', '.join(pk_fields)})",
                                    }
                                )

        except Exception:
            # If there's an error in the detailed check, return a generic failure
            failures.append(
                {
                    "validation_id": "pk_uniqueness_error",
                    "dimension": "consistency",
                    "field": ":".join(pk_fields),
                    "issue": "primary_key_check_error",
                    "affected_rows": len(data),
                    "affected_percentage": 100.0,
                    "samples": [],
                    "remediation": "Unable to verify primary key uniqueness due to data processing error",
                }
            )

        return failures

    def get_consistency_breakdown(
        self, data: pd.DataFrame, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed consistency breakdown for reporting.

        Args:
            data: DataFrame to analyze
            requirements: Requirements from standard

        Returns:
            Detailed breakdown including rule execution results
        """
        pk_fields = self._get_primary_key_fields(requirements)
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {}) if scoring_cfg else {}

        pk_weight = 0.0
        try:
            pk_weight = float(rule_weights_cfg.get("primary_key_uniqueness", 0.0))
        except Exception:
            pk_weight = 0.0
        if pk_weight < 0.0:
            pk_weight = 0.0

        if not pk_fields or pk_weight <= 0.0:
            return {
                "pk_fields": pk_fields,
                "counts": {"passed": len(data), "failed": 0, "total": len(data)},
                "pass_rate": 1.0 if len(data) > 0 else 0.0,
                "rule_weights_applied": {"primary_key_uniqueness": 0.0},
                "score_0_20": 16.0,
                "warnings": [
                    "no active rules configured; using baseline score 16.0/20"
                ],
            }

        # Execute primary key uniqueness check
        failures = self._check_primary_key_uniqueness(data, pk_fields)

        total = len(data)
        failed_rows = sum(int(f.get("affected_rows", 0) or 0) for f in failures)
        if failed_rows > total:
            failed_rows = total
        passed = total - failed_rows
        pass_rate = (passed / total) if total > 0 else 1.0
        score = float(pass_rate * 20.0)

        return {
            "pk_fields": pk_fields,
            "counts": {
                "passed": int(passed),
                "failed": int(failed_rows),
                "total": total,
            },
            "pass_rate": float(pass_rate),
            "rule_weights_applied": {"primary_key_uniqueness": float(pk_weight)},
            "score_0_20": float(score),
            "failure_details": failures,
        }

    def assess_with_rules(
        self, data: pd.DataFrame, consistency_rules: Dict[str, Any]
    ) -> float:
        """Assess consistency with explicit rules for backward compatibility.

        Args:
            data: DataFrame to assess
            consistency_rules: Rules dictionary containing format_rules etc.

        Returns:
            Consistency score between 0.0 and 20.0
        """
        # Handle legacy format rules
        total_checks = 0
        failed_checks = 0

        format_rules = consistency_rules.get("format_rules", {})
        for field, rule in format_rules.items():
            if field in data.columns:
                for value in data[field].dropna():
                    total_checks += 1
                    # Simple format checking
                    if rule == "title_case" and not str(value).istitle():
                        failed_checks += 1
                    elif rule == "lowercase" and str(value) != str(value).lower():
                        failed_checks += 1

        if total_checks > 0:
            success_rate = (total_checks - failed_checks) / total_checks
            return success_rate * 20.0

        return 16.0  # Default score
