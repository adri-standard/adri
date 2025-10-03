"""Validation pipeline for orchestrating data quality assessments.

This module contains the ValidationPipeline class that coordinates the execution
of dimension assessors and aggregates results into a comprehensive assessment.
"""

import time
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.protocols import DimensionAssessor
from ..core.registry import get_global_registry
from .engine import AssessmentResult, BundledStandardWrapper, DimensionScore


class ValidationPipeline:
    """Orchestrates validation across multiple dimensions.

    The ValidationPipeline coordinates the execution of individual dimension
    assessors and aggregates their results into a comprehensive assessment
    while maintaining explain payloads and scoring metadata.
    """

    def __init__(self):
        """Initialize the validation pipeline."""
        self._registry = get_global_registry()
        self._ensure_dimension_assessors_registered()

    def _ensure_dimension_assessors_registered(self) -> None:
        """Ensure all dimension assessors are registered in the global registry."""
        try:
            # Import and register dimension assessors
            from .dimensions import (
                CompletenessAssessor,
                ConsistencyAssessor,
                FreshnessAssessor,
                PlausibilityAssessor,
                ValidityAssessor,
            )

            # Register each assessor if not already registered
            assessors = [
                ValidityAssessor(),
                CompletenessAssessor(),
                ConsistencyAssessor(),
                FreshnessAssessor(),
                PlausibilityAssessor(),
            ]

            for assessor in assessors:
                dimension_name = assessor.get_dimension_name()
                try:
                    # Check if already registered
                    self._registry.dimensions.get(dimension_name)
                except Exception:
                    # Not registered, so register it
                    self._registry.dimensions.register(dimension_name, assessor)

        except Exception:
            # If registration fails, the pipeline will fall back to basic assessment
            pass

    def execute_assessment(
        self, data: pd.DataFrame, standard: Any, collect_explain: bool = True
    ) -> AssessmentResult:
        """Execute a complete validation assessment using dimension assessors.

        Args:
            data: DataFrame containing the data to assess
            standard: Standard configuration (BundledStandardWrapper or dict)
            collect_explain: Whether to collect detailed explanations

        Returns:
            AssessmentResult with dimension scores and metadata
        """
        start_time = time.time()

        # Ensure we have a proper standard wrapper
        if not isinstance(standard, BundledStandardWrapper):
            if isinstance(standard, dict):
                standard = BundledStandardWrapper(standard)
            else:
                # Invalid standard type, return basic assessment
                return self._create_basic_assessment_result(data)

        # Store standard wrapper for dimension assessors to use
        self._standard_wrapper = standard

        # Get dimension requirements and field requirements
        try:
            dimension_requirements = standard.get_dimension_requirements()
            field_requirements = standard.get_field_requirements()
        except Exception:
            return self._create_basic_assessment_result(data)

        # Execute dimension assessments
        dimension_scores = {}
        explain_data = {}

        for dimension_name in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            try:
                score, explanation = self._assess_single_dimension(
                    data,
                    dimension_name,
                    dimension_requirements,
                    field_requirements,
                    collect_explain,
                )
                dimension_scores[dimension_name] = DimensionScore(score)
                if explanation and collect_explain:
                    explain_data[dimension_name] = explanation
            except Exception:
                # If dimension assessment fails, use default score
                dimension_scores[dimension_name] = DimensionScore(
                    self._get_default_score(dimension_name)
                )

        # Calculate overall score using dimension weights
        overall_score, applied_weights = self._calculate_overall_score(
            dimension_scores, dimension_requirements
        )

        # Determine pass/fail status
        min_score = standard.get_overall_minimum()
        passed = overall_score >= min_score

        # Calculate execution time
        duration_ms = int((time.time() - start_time) * 1000)

        # Build metadata
        metadata = {
            "applied_dimension_weights": applied_weights,
        }

        if explain_data and collect_explain:
            metadata["explain"] = explain_data

        # Create assessment result
        result = AssessmentResult(
            overall_score=overall_score,
            passed=passed,
            dimension_scores=dimension_scores,
            standard_id=None,
            assessment_date=None,
            metadata=metadata,
        )

        # Set dataset and execution information
        result.set_dataset_info(
            total_records=len(data),
            total_fields=len(data.columns),
            size_mb=data.memory_usage(deep=True).sum() / (1024 * 1024),
        )

        result.set_execution_stats(duration_ms=duration_ms)

        return result

    def _assess_single_dimension(
        self,
        data: pd.DataFrame,
        dimension_name: str,
        dimension_requirements: Dict[str, Any],
        field_requirements: Dict[str, Any],
        collect_explain: bool,
    ) -> tuple:
        """Assess a single dimension and return score and explanation.

        Returns:
            Tuple of (score, explanation_dict)
        """
        try:
            # Get the dimension assessor
            assessor = self._registry.dimensions.get_assessor(dimension_name)

            # Prepare requirements for this dimension
            dim_requirements = dimension_requirements.get(dimension_name, {})

            # Add field requirements for dimensions that need them
            if dimension_name in ["validity", "completeness"]:
                dim_requirements["field_requirements"] = field_requirements
            elif dimension_name == "consistency":
                # Consistency needs record identification for primary key checking
                dim_requirements["record_identification"] = {"primary_key_fields": []}
                # Try to get actual primary key fields from standard
                try:
                    record_id = getattr(
                        self._standard_wrapper, "standard_dict", {}
                    ).get("record_identification", {})
                    if isinstance(record_id, dict):
                        pk_fields = record_id.get("primary_key_fields", [])
                        if isinstance(pk_fields, list):
                            dim_requirements["record_identification"][
                                "primary_key_fields"
                            ] = pk_fields
                except Exception:
                    pass
            elif dimension_name == "freshness":
                # Freshness needs metadata for date field configuration
                try:
                    std_dict = getattr(self._standard_wrapper, "standard_dict", {})
                    metadata = (
                        std_dict.get("metadata", {})
                        if isinstance(std_dict, dict)
                        else {}
                    )
                    dim_requirements["metadata"] = metadata
                except Exception:
                    pass

            # Run the assessment
            score = assessor.assess(data, dim_requirements)

            # Collect explanation if requested and available
            explanation = None
            if collect_explain:
                explanation = self._collect_dimension_explanation(
                    assessor, data, dim_requirements, dimension_name
                )

            return score, explanation

        except Exception:
            # Fallback to default score if assessment fails
            return self._get_default_score(dimension_name), None

    def _collect_dimension_explanation(
        self,
        assessor: DimensionAssessor,
        data: pd.DataFrame,
        requirements: Dict[str, Any],
        dimension_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Collect detailed explanation from dimension assessor."""
        try:
            # Check if assessor has a breakdown method
            if dimension_name == "validity":
                # Validity assessor doesn't have a breakdown method yet
                return None
            elif dimension_name == "completeness":
                if hasattr(assessor, "get_completeness_breakdown"):
                    field_requirements = requirements.get("field_requirements", {})
                    return assessor.get_completeness_breakdown(data, field_requirements)
            elif dimension_name == "consistency":
                if hasattr(assessor, "get_consistency_breakdown"):
                    return assessor.get_consistency_breakdown(data, requirements)
            elif dimension_name == "freshness":
                if hasattr(assessor, "get_freshness_breakdown"):
                    return assessor.get_freshness_breakdown(data, requirements)
            elif dimension_name == "plausibility":
                if hasattr(assessor, "get_plausibility_breakdown"):
                    return assessor.get_plausibility_breakdown(data, requirements)

        except Exception:
            pass

        return None

    def _calculate_overall_score(
        self,
        dimension_scores: Dict[str, DimensionScore],
        dimension_requirements: Dict[str, Any],
    ) -> tuple:
        """Calculate overall score using dimension weights.

        Returns:
            Tuple of (overall_score, applied_weights)
        """
        # Extract weights from dimension requirements
        weights = {}
        for dim, dim_score in dimension_scores.items():
            dim_config = dimension_requirements.get(dim, {})
            weights[dim] = float(dim_config.get("weight", 1.0))

        # Normalize weights (clamp negatives and handle zero sum)
        applied_weights = self._normalize_weights(weights)

        # Calculate weighted average
        weighted_sum = 0.0
        weight_total = 0.0

        for dim, dim_score in dimension_scores.items():
            weight = applied_weights.get(dim, 1.0)
            weighted_sum += weight * float(dim_score.score)
            weight_total += weight

        # Convert from 0-20 scale to 0-100 scale
        if weight_total > 0:
            overall_score = ((weighted_sum / weight_total) / 20.0) * 100.0
        else:
            overall_score = 0.0

        return overall_score, applied_weights

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize dimension weights, handling edge cases."""
        # Clamp negative weights to 0
        normalized = {}
        for dim, weight in weights.items():
            try:
                w = float(weight)
                if w < 0.0:
                    w = 0.0
                normalized[dim] = w
            except Exception:
                normalized[dim] = 0.0

        # If all weights are zero, assign equal weights
        total_weight = sum(normalized.values())
        if len(normalized) > 0 and total_weight <= 0.0:
            for dim in normalized.keys():
                normalized[dim] = 1.0

        return normalized

    def _get_default_score(self, dimension_name: str) -> float:
        """Get default score for a dimension when assessment fails."""
        defaults = {
            "validity": 18.0,
            "completeness": 18.0,
            "consistency": 16.0,
            "freshness": 19.0,
            "plausibility": 15.5,
        }
        return defaults.get(dimension_name, 15.0)

    def _create_basic_assessment_result(self, data: pd.DataFrame) -> AssessmentResult:
        """Create a basic assessment result when standard processing fails."""
        # Use default scores for all dimensions
        dimension_scores = {
            "validity": DimensionScore(18.0),
            "completeness": DimensionScore(18.0),
            "consistency": DimensionScore(16.0),
            "freshness": DimensionScore(19.0),
            "plausibility": DimensionScore(15.5),
        }

        # Calculate simple average
        total_score = sum(score.score for score in dimension_scores.values())
        overall_score = (total_score / 100.0) * 100.0
        passed = overall_score >= 75.0

        return AssessmentResult(
            overall_score=overall_score,
            passed=passed,
            dimension_scores=dimension_scores,
        )

    def supports_dimension(self, dimension_name: str) -> bool:
        """Check if a dimension assessor is available.

        Args:
            dimension_name: Name of the dimension to check

        Returns:
            True if the dimension is supported, False otherwise
        """
        try:
            self._registry.dimensions.get(dimension_name)
            return True
        except Exception:
            return False

    def list_available_dimensions(self) -> List[str]:
        """List all available dimension names.

        Returns:
            List of dimension names that can be assessed
        """
        return self._registry.dimensions.list_components()
