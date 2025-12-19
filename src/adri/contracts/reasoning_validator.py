"""
ADRI Reasoning Validator.

Specialized validator for AI/LLM-generated outputs that validates reasoning
outputs against business rules and confidence thresholds.
"""

import logging
from typing import Any

import pandas as pd

from ..validator.engine import AssessmentResult, DataQualityAssessor, DimensionScore

logger = logging.getLogger(__name__)


class ReasoningValidator:
    """
    Validator for AI/LLM reasoning outputs.

    Validates AI-generated data against reasoning standards, focusing on:
    - Confidence score validation
    - Risk level validation
    - Recommendation quality checks
    - AI-specific field requirements
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize reasoning validator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Use DataQualityAssessor for underlying validation
        self.assessor = DataQualityAssessor(config)

    def validate_ai_output(
        self, data: pd.DataFrame, standard_path: str
    ) -> AssessmentResult:
        """
        Validate AI-generated output against reasoning standard.

        Validates fields like AI_RISK_LEVEL, AI_CONFIDENCE_SCORE,
        AI_RECOMMENDATIONS against allowed values and constraints.

        Args:
            data: DataFrame with AI-generated outputs
            standard_path: Path to reasoning ADRI standard

        Returns:
            AssessmentResult with quality scores
        """
        # Use standard validation for comprehensive assessment
        result = self.assessor.assess(data, standard_path)

        # Add reasoning-specific validations
        self._validate_confidence_scores(data, result)
        self._validate_risk_levels(data, result)

        return result

    def _validate_confidence_scores(
        self, data: pd.DataFrame, result: AssessmentResult
    ) -> None:
        """
        Validate AI confidence scores are within expected ranges.

        Args:
            data: DataFrame with AI outputs
            result: Assessment result to update
        """
        # Look for confidence score fields (common naming patterns)
        confidence_fields = [
            col
            for col in data.columns
            if "confidence" in str(col).lower() or "score" in str(col).lower()
        ]

        if not confidence_fields:
            return

        # Validate confidence scores are between 0 and 1 (or 0 and 100)
        for field in confidence_fields:
            try:
                series = pd.to_numeric(data[field], errors="coerce")
                non_null = series.dropna()

                if len(non_null) == 0:
                    continue

                # Detect if scores are 0-1 or 0-100 range
                max_val = non_null.max()
                if max_val <= 1.0:
                    # 0-1 range
                    invalid = ((non_null < 0) | (non_null > 1)).sum()
                else:
                    # 0-100 range
                    invalid = ((non_null < 0) | (non_null > 100)).sum()

                if invalid > 0:
                    self.logger.warning(
                        f"Field '{field}' has {invalid} invalid confidence scores"
                    )

            except Exception as e:
                self.logger.debug(f"Could not validate confidence field {field}: {e}")

    def _validate_risk_levels(
        self, data: pd.DataFrame, result: AssessmentResult
    ) -> None:
        """
        Validate AI risk levels are within expected categories.

        Args:
            data: DataFrame with AI outputs
            result: Assessment result to update
        """
        # Look for risk level fields
        risk_fields = [
            col
            for col in data.columns
            if "risk" in str(col).lower() and "level" in str(col).lower()
        ]

        if not risk_fields:
            return

        # Common risk level categories
        valid_risk_levels = {
            "low",
            "medium",
            "high",
            "critical",
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
            "Low",
            "Medium",
            "High",
            "Critical",
        }

        for field in risk_fields:
            try:
                series = data[field].dropna()

                if len(series) == 0:
                    continue

                # Check for invalid risk levels
                invalid = ~series.isin(valid_risk_levels)
                invalid_count = invalid.sum()

                if invalid_count > 0:
                    self.logger.warning(
                        f"Field '{field}' has {invalid_count} invalid risk levels"
                    )

            except Exception as e:
                self.logger.debug(f"Could not validate risk field {field}: {e}")

    def check_ai_field_requirements(
        self, data: pd.DataFrame, field_requirements: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Check AI-specific field requirements.

        Args:
            data: DataFrame with AI outputs
            field_requirements: Field requirement specifications

        Returns:
            List of validation issues found
        """
        issues = []

        for field_name, requirements in field_requirements.items():
            if field_name not in data.columns:
                continue

            series = data[field_name]

            # Check allowed values for categorical AI outputs
            if "allowed_values" in requirements:
                allowed = set(requirements["allowed_values"])
                invalid = ~series.isin(allowed)
                invalid_count = invalid.sum()

                if invalid_count > 0:
                    issues.append(
                        {
                            "field": field_name,
                            "issue": "invalid_values",
                            "affected_rows": int(invalid_count),
                            "affected_percentage": float(
                                invalid_count / len(data) * 100
                            ),
                            "expected": list(allowed),
                        }
                    )

            # Check min/max values for numeric AI outputs
            if "min_value" in requirements or "max_value" in requirements:
                try:
                    numeric = pd.to_numeric(series, errors="coerce")

                    if "min_value" in requirements:
                        below_min = (numeric < requirements["min_value"]).sum()
                        if below_min > 0:
                            issues.append(
                                {
                                    "field": field_name,
                                    "issue": "below_minimum",
                                    "affected_rows": int(below_min),
                                    "affected_percentage": float(
                                        below_min / len(data) * 100
                                    ),
                                    "min_value": requirements["min_value"],
                                }
                            )

                    if "max_value" in requirements:
                        above_max = (numeric > requirements["max_value"]).sum()
                        if above_max > 0:
                            issues.append(
                                {
                                    "field": field_name,
                                    "issue": "above_maximum",
                                    "affected_rows": int(above_max),
                                    "affected_percentage": float(
                                        above_max / len(data) * 100
                                    ),
                                    "max_value": requirements["max_value"],
                                }
                            )

                except Exception as e:
                    self.logger.debug(
                        f"Could not validate numeric field {field_name}: {e}"
                    )

        return issues

    def validate_reasoning_completeness(
        self, data: pd.DataFrame, required_ai_fields: list[str]
    ) -> DimensionScore:
        """
        Validate that required AI reasoning fields are present and complete.

        Args:
            data: DataFrame with AI outputs
            required_ai_fields: List of required field names

        Returns:
            DimensionScore for reasoning completeness
        """
        if not required_ai_fields:
            return DimensionScore(score=20.0)

        total_required_cells = len(data) * len(required_ai_fields)
        missing_cells = 0

        for field in required_ai_fields:
            if field in data.columns:
                missing_cells += data[field].isnull().sum()
            else:
                # Field completely missing
                missing_cells += len(data)

        if total_required_cells == 0:
            return DimensionScore(score=20.0)

        completeness_rate = (
            total_required_cells - missing_cells
        ) / total_required_cells
        score = completeness_rate * 20.0

        return DimensionScore(
            score=score,
            details={
                "total_required_cells": total_required_cells,
                "missing_cells": int(missing_cells),
                "completeness_rate": float(completeness_rate),
            },
        )
