"""Consistency dimension assessor for the ADRI validation framework.

This module contains the ConsistencyAssessor class that evaluates data consistency
(referential integrity and internal coherence) according to requirements defined in
ADRI standards.
"""

from typing import Any, Dict, List, Optional

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
            return 20.0  # Perfect score for non-DataFrame data

        if data.empty:
            return 20.0  # Empty data is technically consistent

        # Get consistency configuration from requirements
        scoring_cfg = requirements.get("scoring", {})
        rule_weights_cfg = scoring_cfg.get("rule_weights", {}) if scoring_cfg else {}

        # Get primary key fields for uniqueness checking
        pk_fields = self._get_primary_key_fields(requirements)

        # Get format rules if defined
        format_rules = requirements.get("format_rules", {})

        return self._assess_consistency_with_rules(
            data, rule_weights_cfg, pk_fields, format_rules
        )

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
        format_rules: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Assess consistency using configured rules with weighted scoring."""
        # Extract and validate rule weights
        pk_weight = max(0.0, float(rule_weights_cfg.get("primary_key_uniqueness", 0.0)))
        ref_weight = max(0.0, float(rule_weights_cfg.get("referential_integrity", 0.0)))
        logic_weight = max(0.0, float(rule_weights_cfg.get("cross_field_logic", 0.0)))
        format_weight = max(0.0, float(rule_weights_cfg.get("format_consistency", 0.0)))

        total_weight = pk_weight + ref_weight + logic_weight + format_weight

        # If no active rules, return baseline score
        if total_weight <= 0.0:
            return 20.0

        # Assess each rule type and compute weighted score
        weighted_sum = 0.0

        # 1. Primary key uniqueness
        if pk_weight > 0.0 and pk_fields:
            pk_pass_rate = self._get_primary_key_pass_rate(data, pk_fields)
            weighted_sum += pk_pass_rate * pk_weight
        elif pk_weight > 0.0:
            # No PK fields defined, treat as passing
            weighted_sum += 1.0 * pk_weight

        # 2. Referential integrity (optional - may not be configured)
        if ref_weight > 0.0:
            ref_pass_rate = self._get_referential_integrity_pass_rate(data)
            weighted_sum += ref_pass_rate * ref_weight

        # 3. Cross-field logic
        if logic_weight > 0.0:
            logic_pass_rate = self._get_cross_field_logic_pass_rate(data)
            weighted_sum += logic_pass_rate * logic_weight

        # 4. Format consistency
        if format_weight > 0.0:
            format_pass_rate = self._get_format_consistency_pass_rate(
                data, format_rules
            )
            weighted_sum += format_pass_rate * format_weight

        # Calculate final score (0-20 scale)
        overall_pass_rate = weighted_sum / total_weight if total_weight > 0 else 1.0
        return float(overall_pass_rate * 20.0)

    def _get_primary_key_pass_rate(
        self, data: pd.DataFrame, pk_fields: List[str]
    ) -> float:
        """Get pass rate for primary key uniqueness rule."""
        failures = self._check_primary_key_uniqueness(data, pk_fields)
        total = len(data)
        if total == 0:
            return 1.0

        failed_rows = sum(int(f.get("affected_rows", 0) or 0) for f in failures)
        failed_rows = min(failed_rows, total)  # Cap at total
        passed = total - failed_rows
        return (passed / total) if total > 0 else 1.0

    def _get_referential_integrity_pass_rate(self, data: pd.DataFrame) -> float:
        """Get pass rate for referential integrity rule.

        Note: This is a placeholder for future FK constraint checking.
        Returns 1.0 (100% pass) by default since FK relationships are optional.
        """
        # TODO: Implement FK checking when standards support FK definitions
        # For now, treat as passing since FK relationships are not yet defined in standards
        return 1.0

    def _get_cross_field_logic_pass_rate(self, data: pd.DataFrame) -> float:
        """Get pass rate for cross-field logic rule.

        Checks common logical relationships between fields such as:
        - Date ranges (end_date >= start_date)
        - Numeric totals (total = subtotal + tax)
        - Status consistency
        """
        if data.empty:
            return 1.0

        total_checks = 0
        passed_checks = 0

        # Check for common date range patterns
        date_pairs = [
            ("end_date", "start_date"),
            ("completion_date", "start_date"),
            ("due_date", "created_date"),
            ("updated_date", "created_date"),
        ]

        for end_col, start_col in date_pairs:
            if end_col in data.columns and start_col in data.columns:
                # Only check rows where both dates are present
                mask = data[end_col].notna() & data[start_col].notna()
                subset = data[mask]
                if len(subset) > 0:
                    try:
                        # Convert to datetime for comparison
                        end_dates = pd.to_datetime(subset[end_col], errors="coerce")
                        start_dates = pd.to_datetime(subset[start_col], errors="coerce")
                        valid_mask = end_dates.notna() & start_dates.notna()
                        valid_subset = subset[valid_mask]

                        if len(valid_subset) > 0:
                            total_checks += len(valid_subset)
                            passed_checks += (
                                end_dates[valid_mask] >= start_dates[valid_mask]
                            ).sum()
                    except Exception:
                        pass  # Skip this pair if conversion fails

        # Check for common numeric sum patterns
        numeric_triplets = [
            ("total", "subtotal", "tax"),
            ("total_amount", "base_amount", "tax_amount"),
            ("grand_total", "subtotal", "shipping"),
        ]

        for total_col, part1_col, part2_col in numeric_triplets:
            if all(col in data.columns for col in [total_col, part1_col, part2_col]):
                # Only check rows where all values are present
                mask = (
                    data[total_col].notna()
                    & data[part1_col].notna()
                    & data[part2_col].notna()
                )
                subset = data[mask]
                if len(subset) > 0:
                    try:
                        total_checks += len(subset)
                        # Allow small floating point tolerance (0.01)
                        computed_total = subset[part1_col] + subset[part2_col]
                        matches = abs(subset[total_col] - computed_total) < 0.01
                        passed_checks += matches.sum()
                    except Exception:
                        pass  # Skip if numeric conversion fails

        # If no checks were performed, return 100% (no issues found)
        if total_checks == 0:
            return 1.0

        return float(passed_checks / total_checks)

    def _get_format_consistency_pass_rate(
        self, data: pd.DataFrame, format_rules: Optional[Dict[str, Any]] = None
    ) -> float:
        """Get pass rate for format consistency rule.

        Checks that values within each field follow consistent formatting:
        - Phone numbers all use same format
        - Dates all use same format
        - IDs all use same pattern structure

        Note: Returns 1.0 (100%) by default when no explicit format rules exist.
        Only applies heuristic checks when the standard defines format requirements.
        """
        if data.empty:
            return 1.0

        # IMPORTANT: Only apply heuristics when explicit format rules are defined
        # This prevents training data from failing its own generated standard
        if not format_rules or len(format_rules) == 0:
            return 1.0

        # Apply format heuristics since explicit rules are defined
        total_fields_checked = 0
        consistent_fields = 0

        for col in data.columns:
            if data[col].dtype == "object":  # Only check string columns
                non_null = data[col].dropna()
                if len(non_null) < 2:  # Need at least 2 values to check consistency
                    continue

                total_fields_checked += 1

                # Sample up to 100 values for performance
                sample = non_null.head(100)

                # Check format consistency by looking at common patterns
                # 1. Length consistency (within 20% variation)
                lengths = sample.astype(str).str.len()
                avg_length = lengths.mean()
                if avg_length > 0:
                    length_variance = lengths.std() / avg_length
                    if length_variance < 0.2:  # Less than 20% variation
                        consistent_fields += (
                            0.5  # Partial credit for length consistency
                        )

                # 2. Character type consistency (all numeric, all alpha, all alphanumeric)
                str_sample = sample.astype(str)
                numeric_pct = str_sample.str.isnumeric().mean()
                alpha_pct = str_sample.str.isalpha().mean()
                alnum_pct = str_sample.str.isalnum().mean()

                # If >80% follow same character type pattern, award credit
                if max(numeric_pct, alpha_pct, alnum_pct) > 0.8:
                    consistent_fields += (
                        0.5  # Partial credit for character type consistency
                    )

        # If no fields were checked, return 100% (no issues found)
        if total_fields_checked == 0:
            return 1.0

        # Average consistency score across checked fields
        return float(consistent_fields / total_fields_checked)

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

        return 20.0  # Perfect score

    def get_validation_failures(
        self, data: pd.DataFrame, requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract detailed consistency failures for audit logging.

        Args:
            data: DataFrame to analyze
            requirements: Requirements from standard

        Returns:
            List of failure records with details about consistency violations
        """
        failures = []

        # Get primary key fields
        pk_fields = self._get_primary_key_fields(requirements)

        if pk_fields:
            # Check for primary key duplicates
            pk_failures = self._check_primary_key_uniqueness(data, pk_fields)
            failures.extend(pk_failures)

        # Check cross-field logic issues (date ranges, numeric totals)
        logic_failures = self._get_cross_field_logic_failures(data)
        failures.extend(logic_failures)

        # Check format consistency issues
        format_failures = self._get_format_consistency_failures(data)
        failures.extend(format_failures)

        return failures

    def _get_cross_field_logic_failures(
        self, data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Get failures from cross-field logic validation."""
        failures = []

        if data.empty:
            return failures

        total_rows = len(data)

        # Check date range violations
        date_pairs = [
            ("end_date", "start_date"),
            ("completion_date", "start_date"),
            ("due_date", "created_date"),
            ("updated_date", "created_date"),
        ]

        for end_col, start_col in date_pairs:
            if end_col in data.columns and start_col in data.columns:
                mask = data[end_col].notna() & data[start_col].notna()
                subset = data[mask]
                if len(subset) > 0:
                    try:
                        end_dates = pd.to_datetime(subset[end_col], errors="coerce")
                        start_dates = pd.to_datetime(subset[start_col], errors="coerce")
                        valid_mask = end_dates.notna() & start_dates.notna()

                        if valid_mask.any():
                            invalid_mask = (
                                end_dates[valid_mask] < start_dates[valid_mask]
                            )
                            invalid_count = invalid_mask.sum()

                            if invalid_count > 0:
                                # Get sample indices
                                invalid_indices = subset[valid_mask][
                                    invalid_mask
                                ].index.tolist()[:3]

                                failures.append(
                                    {
                                        "dimension": "consistency",
                                        "field": f"{end_col},{start_col}",
                                        "issue": "invalid_date_range",
                                        "affected_rows": int(invalid_count),
                                        "affected_percentage": (
                                            invalid_count / total_rows
                                        )
                                        * 100.0,
                                        "samples": [
                                            f"Row {idx}: {end_col} < {start_col}"
                                            for idx in invalid_indices
                                        ],
                                        "remediation": f"Ensure {end_col} >= {start_col}",
                                    }
                                )
                    except Exception:
                        pass

        # Check numeric total violations
        numeric_triplets = [
            ("total", "subtotal", "tax"),
            ("total_amount", "base_amount", "tax_amount"),
            ("grand_total", "subtotal", "shipping"),
        ]

        for total_col, part1_col, part2_col in numeric_triplets:
            if all(col in data.columns for col in [total_col, part1_col, part2_col]):
                mask = (
                    data[total_col].notna()
                    & data[part1_col].notna()
                    & data[part2_col].notna()
                )
                subset = data[mask]
                if len(subset) > 0:
                    try:
                        computed_total = subset[part1_col] + subset[part2_col]
                        mismatch_mask = abs(subset[total_col] - computed_total) >= 0.01
                        mismatch_count = mismatch_mask.sum()

                        if mismatch_count > 0:
                            mismatch_indices = subset[mismatch_mask].index.tolist()[:3]

                            failures.append(
                                {
                                    "dimension": "consistency",
                                    "field": f"{total_col}",
                                    "issue": "incorrect_total",
                                    "affected_rows": int(mismatch_count),
                                    "affected_percentage": (mismatch_count / total_rows)
                                    * 100.0,
                                    "samples": [
                                        f"Row {idx}" for idx in mismatch_indices
                                    ],
                                    "remediation": f"Ensure {total_col} = {part1_col} + {part2_col}",
                                }
                            )
                    except Exception:
                        pass

        return failures

    def _get_format_consistency_failures(
        self, data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Get failures from format consistency validation."""
        failures = []

        if data.empty:
            return failures

        total_rows = len(data)

        for col in data.columns:
            if data[col].dtype == "object":
                non_null = data[col].dropna()
                if len(non_null) < 2:
                    continue

                # Check if formats are inconsistent
                sample = non_null.head(100)
                lengths = sample.astype(str).str.len()
                avg_length = lengths.mean()

                if avg_length > 0:
                    length_variance = lengths.std() / avg_length

                    # If high variance (>20%), flag as inconsistent
                    if length_variance > 0.2:
                        failures.append(
                            {
                                "dimension": "consistency",
                                "field": col,
                                "issue": "inconsistent_format",
                                "affected_rows": len(non_null),
                                "affected_percentage": (len(non_null) / total_rows)
                                * 100.0,
                                "samples": sample.astype(str).tolist()[:3],
                                "remediation": f"Standardize format for {col}",
                            }
                        )

        return failures
