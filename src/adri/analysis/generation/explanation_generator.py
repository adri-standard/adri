"""Explanation generator for ADRI standard generation.

This module contains the ExplanationGenerator class that creates human-readable
explanations for generated field requirements and validation rules.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from ..rule_inference import InferenceConfig


class ExplanationGenerator:
    """Generates human-readable explanations for field requirements.

    The ExplanationGenerator creates detailed explanations for why specific
    validation rules were generated, providing transparency and understanding
    for users reviewing generated standards.
    """

    def __init__(self):
        """Initialize the explanation generator."""

    def build_explanations(
        self,
        data: pd.DataFrame,
        data_profile: dict[str, Any],
        field_requirements: dict[str, Any],
        config: InferenceConfig,
    ) -> dict[str, Any]:
        """Build comprehensive explanations for all field requirements.

        Args:
            data: Source DataFrame
            data_profile: Data profile from DataProfiler
            field_requirements: Generated field requirements
            config: Inference configuration used during generation

        Returns:
            Dictionary mapping field names to their explanations
        """
        explanations: dict[str, Any] = {}

        for col, field_req in field_requirements.items():
            series = data[col] if col in data.columns else pd.Series([], dtype=object)
            field_explanation = self._build_field_explanation(series, field_req, config)

            if field_explanation:
                explanations[col] = field_explanation

        return explanations

    def _build_field_explanation(
        self, series: pd.Series, field_req: dict[str, Any], config: InferenceConfig
    ) -> dict[str, Any]:
        """Build explanation for a single field's requirements.

        Args:
            series: Field data
            field_req: Field requirements dictionary
            config: Inference configuration

        Returns:
            Field explanation dictionary
        """
        explanation: dict[str, Any] = {}

        # Type explanation
        type_exp = self._explain_type(field_req)
        if type_exp is not None:
            explanation["type"] = type_exp

        # Nullability explanation
        nullable_exp = self._explain_nullable(series, field_req)
        if nullable_exp is not None:
            explanation["nullable"] = nullable_exp

        # Allowed values explanation
        allowed_values_exp = self._explain_allowed_values(series, field_req, config)
        if allowed_values_exp is not None:
            explanation["allowed_values"] = allowed_values_exp

        # Length bounds explanation
        length_exp = self._explain_length_bounds(series, field_req)
        if length_exp is not None:
            explanation["length_bounds"] = length_exp

        # Numeric range explanation
        range_exp = self._explain_range(series, field_req, config)
        if range_exp is not None:
            explanation["range"] = range_exp

        # Date bounds explanation
        date_exp = self._explain_date_bounds(series, field_req, config)
        if date_exp is not None:
            explanation["date_bounds"] = date_exp

        # Pattern explanation
        pattern_exp = self._explain_pattern(series, field_req)
        if pattern_exp is not None:
            explanation["pattern"] = pattern_exp

        return explanation

    def _explain_type(self, field_req: dict[str, Any]) -> str | None:
        """Explain type requirement.

        Args:
            field_req: Field requirements

        Returns:
            Type explanation string or None
        """
        return str(field_req.get("type")) if "type" in field_req else None

    def _explain_nullable(
        self, series: pd.Series, field_req: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Explain nullability requirement.

        Args:
            series: Field data
            field_req: Field requirements

        Returns:
            Nullability explanation dictionary or None
        """
        if "nullable" not in field_req:
            return None

        try:
            null_count = int(series.isnull().sum())
            total_count = int(len(series))
        except Exception:
            null_count = total_count = 0

        nullable = field_req["nullable"]
        reason = (
            "Required because 0% nulls observed in training"
            if not nullable
            else "Nulls were observed in training, so this field is allowed to be null"
        )

        return {
            "active": bool(nullable),
            "reason": reason,
            "stats": {"null_count": null_count, "total": total_count},
        }

    def _explain_allowed_values(
        self, series: pd.Series, field_req: dict[str, Any], config: InferenceConfig
    ) -> dict[str, Any] | None:
        """Explain allowed values (enum) requirement.

        Args:
            series: Field data
            field_req: Field requirements
            config: Inference configuration

        Returns:
            Allowed values explanation dictionary or None
        """
        if "allowed_values" not in field_req:
            return None

        try:
            non_null = series.dropna()
            allowed_values = field_req["allowed_values"]
            in_set = non_null.isin(allowed_values)
            coverage = float(in_set.sum() / len(non_null)) if len(non_null) > 0 else 1.0
            unique_count = int(non_null.nunique())
        except Exception:
            coverage = None
            unique_count = None

        reason = (
            "High coverage stable set"
            if coverage is None or coverage >= config.enum_min_coverage
            else "Coverage below threshold"
        )

        return {
            "values": list(field_req.get("allowed_values", [])),
            "reason": reason,
            "stats": {
                "coverage": coverage,
                "unique_count": unique_count,
                "strategy": getattr(config, "enum_strategy", "coverage"),
            },
        }

    def _explain_length_bounds(
        self, series: pd.Series, field_req: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Explain length bounds requirement.

        Args:
            series: Field data
            field_req: Field requirements

        Returns:
            Length bounds explanation dictionary or None
        """
        if "min_length" not in field_req and "max_length" not in field_req:
            return None

        try:
            lengths = series.dropna().astype(str).str.len()
            observed_min = int(lengths.min()) if len(lengths) else None
            observed_max = int(lengths.max()) if len(lengths) else None
        except Exception:
            observed_min = observed_max = None

        return {
            "active_min": (
                int(field_req.get("min_length", 0))
                if field_req.get("min_length") is not None
                else None
            ),
            "active_max": (
                int(field_req.get("max_length", 0))
                if field_req.get("max_length") is not None
                else None
            ),
            "stats": {"observed_min": observed_min, "observed_max": observed_max},
        }

    def _explain_range(
        self, series: pd.Series, field_req: dict[str, Any], config: InferenceConfig
    ) -> dict[str, Any] | None:
        """Explain numeric range requirement.

        Args:
            series: Field data
            field_req: Field requirements
            config: Inference configuration

        Returns:
            Range explanation dictionary or None
        """
        if not (
            field_req.get("type") in ("integer", "float")
            and ("min_value" in field_req or "max_value" in field_req)
        ):
            return None

        strategy = getattr(config, "range_strategy", "iqr")
        stats: dict[str, Any] = {}

        try:
            numeric_data = pd.to_numeric(series.dropna(), errors="coerce").dropna()
            if len(numeric_data) > 0:
                if strategy == "iqr":
                    q1 = float(numeric_data.quantile(0.25))
                    q3 = float(numeric_data.quantile(0.75))
                    stats.update(
                        {"q1": q1, "q3": q3, "iqr_k": getattr(config, "iqr_k", 1.5)}
                    )
                elif strategy == "quantile":
                    stats.update(
                        {
                            "q_low": float(
                                numeric_data.quantile(
                                    getattr(config, "quantile_low", 0.005)
                                )
                            ),
                            "q_high": float(
                                numeric_data.quantile(
                                    getattr(config, "quantile_high", 0.995)
                                )
                            ),
                        }
                    )
                elif strategy == "mad":
                    median = float(numeric_data.median())
                    stats.update(
                        {"median": median, "mad_k": getattr(config, "mad_k", 3.0)}
                    )

                stats.update(
                    {
                        "observed_min": float(numeric_data.min()),
                        "observed_max": float(numeric_data.max()),
                    }
                )
        except Exception:
            pass

        reason = (
            "Robust range (IQR/Quantile/MAD) clamped to training min/max for pass guarantee"
            if strategy != "span"
            else "Span-based range with margin"
        )

        return {
            "strategy": strategy,
            "active_min": (
                float(field_req.get("min_value"))
                if field_req.get("min_value") is not None
                else None
            ),
            "active_max": (
                float(field_req.get("max_value"))
                if field_req.get("max_value") is not None
                else None
            ),
            "reason": reason,
            "stats": stats,
        }

    def _explain_date_bounds(
        self, series: pd.Series, field_req: dict[str, Any], config: InferenceConfig
    ) -> dict[str, Any] | None:
        """Explain date bounds requirement.

        Args:
            series: Field data
            field_req: Field requirements
            config: Inference configuration

        Returns:
            Date bounds explanation dictionary or None
        """
        if not (
            field_req.get("type") in ("date", "datetime")
            and any(
                k in field_req
                for k in [
                    "after_date",
                    "before_date",
                    "after_datetime",
                    "before_datetime",
                ]
            )
        ):
            return None

        try:
            date_data = pd.to_datetime(series.dropna(), errors="coerce")
            observed_min = (
                date_data.min().date().isoformat()
                if len(date_data) and pd.notna(date_data.min())
                else None
            )
            observed_max = (
                date_data.max().date().isoformat()
                if len(date_data) and pd.notna(date_data.max())
                else None
            )
        except Exception:
            observed_min = observed_max = None

        return {
            "active_after": field_req.get("after_date")
            or field_req.get("after_datetime"),
            "active_before": field_req.get("before_date")
            or field_req.get("before_datetime"),
            "reason": "Plausible date window widened by margin days",
            "stats": {
                "observed_min": observed_min,
                "observed_max": observed_max,
                "margin_days": getattr(config, "date_margin_days", 3),
            },
        }

    def _explain_pattern(
        self, series: pd.Series, field_req: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Explain pattern (regex) requirement.

        Args:
            series: Field data
            field_req: Field requirements

        Returns:
            Pattern explanation dictionary or None
        """
        if "pattern" not in field_req:
            return None

        try:
            non_null = series.dropna().astype(str)
            import re

            pattern = field_req["pattern"]
            compiled_pattern = re.compile(pattern)
            matches = non_null.apply(lambda v: bool(compiled_pattern.match(v)))
            coverage = float(matches.mean()) if len(non_null) > 0 else 1.0
        except Exception:
            coverage = None

        reason = (
            "100% coverage on training non-nulls"
            if coverage is None or coverage == 1.0
            else "Less than full coverage"
        )

        return {
            "regex": field_req["pattern"],
            "reason": reason,
            "stats": {"coverage": coverage},
        }

    def create_glossary(self) -> dict[str, str]:
        """Create a glossary of explanation terms.

        Returns:
            Dictionary mapping terms to their definitions
        """
        return {
            "iqr": "Interquartile Range (Q3 - Q1): a robust measure of spread, less sensitive to outliers.",
            "q1": "25th percentile of the training values.",
            "q3": "75th percentile of the training values.",
            "coverage": "Share of non-null training values that satisfy the rule.",
            "unique_count": "Number of distinct non-null values observed in training.",
            "mad": "Median Absolute Deviation: robust measure of variability around the median.",
            "quantile": "Statistical measure dividing data into equal-sized intervals.",
            "training_pass": "Guarantee that generated rules pass on the training data used for generation.",
            "enum_strategy": "Method used for allowed values inference (coverage or tolerant).",
            "margin_days": "Buffer added to date ranges to allow for reasonable variations.",
        }

    def create_explanation_note(self) -> str:
        """Create a note explaining the purpose of explanations.

        Returns:
            Explanation note string
        """
        return "Explanations are for human review; only requirements.field_requirements are enforced."

    def format_adjustment_summary(self, explanations: dict[str, Any]) -> dict[str, Any]:
        """Format a summary of training-pass adjustments made.

        Args:
            explanations: Field explanations containing adjustments

        Returns:
            Summary of adjustments made during generation
        """
        summary = {
            "total_fields_adjusted": 0,
            "adjustment_types": {},
            "fields_by_adjustment": {},
        }

        for field_name, field_exp in explanations.items():
            if isinstance(field_exp, dict) and "adjustments" in field_exp:
                adjustments = field_exp["adjustments"]
                if isinstance(adjustments, list) and len(adjustments) > 0:
                    summary["total_fields_adjusted"] += 1

                    for adjustment in adjustments:
                        if isinstance(adjustment, dict):
                            rule = adjustment.get("rule", "unknown")
                            action = adjustment.get("action", "unknown")

                            # Count adjustment types
                            adj_key = f"{rule}_{action}"
                            summary["adjustment_types"][adj_key] = (
                                summary["adjustment_types"].get(adj_key, 0) + 1
                            )

                            # Track fields by adjustment type
                            if adj_key not in summary["fields_by_adjustment"]:
                                summary["fields_by_adjustment"][adj_key] = []
                            summary["fields_by_adjustment"][adj_key].append(field_name)

        return summary

    def add_explanations_to_standard(
        self,
        standard: dict[str, Any],
        data: pd.DataFrame,
        data_profile: dict[str, Any],
        config: InferenceConfig,
    ) -> dict[str, Any]:
        """Add comprehensive explanations to a standard.

        Args:
            standard: Standard to enhance with explanations
            data: Source data
            data_profile: Data profile
            config: Inference configuration

        Returns:
            Standard with added explanations
        """
        # Get field requirements
        field_requirements = standard.get("requirements", {}).get(
            "field_requirements", {}
        )

        if not isinstance(field_requirements, dict):
            return standard

        # Generate explanations
        explanations = self.build_explanations(
            data, data_profile, field_requirements, config
        )

        # Add to metadata
        metadata = standard.setdefault("metadata", {})
        metadata["explanations"] = explanations
        metadata["explanations_note"] = self.create_explanation_note()
        metadata["explanations_glossary"] = self.create_glossary()

        # Add adjustment summary if adjustments were made
        adjustment_summary = self.format_adjustment_summary(explanations)
        if adjustment_summary["total_fields_adjusted"] > 0:
            metadata["training_pass_adjustments"] = adjustment_summary

        return standard

    def validate_explanations(self, explanations: dict[str, Any]) -> list[str]:
        """Validate explanation structure and content.

        Args:
            explanations: Explanations dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not isinstance(explanations, dict):
            errors.append("Explanations must be a dictionary")
            return errors

        for field_name, field_exp in explanations.items():
            if not isinstance(field_exp, dict):
                errors.append(
                    f"Field explanation for '{field_name}' must be a dictionary"
                )
                continue

            # Check for valid explanation types
            valid_keys = [
                "type",
                "nullable",
                "allowed_values",
                "length_bounds",
                "range",
                "date_bounds",
                "pattern",
                "adjustments",
            ]

            for key in field_exp.keys():
                if key not in valid_keys:
                    errors.append(
                        f"Unknown explanation key '{key}' for field '{field_name}'"
                    )

            # Validate adjustment structure if present
            if "adjustments" in field_exp:
                adjustments = field_exp["adjustments"]
                if not isinstance(adjustments, list):
                    errors.append(
                        f"Adjustments for field '{field_name}' must be a list"
                    )
                else:
                    for i, adj in enumerate(adjustments):
                        if not isinstance(adj, dict):
                            errors.append(
                                f"Adjustment {i} for field '{field_name}' must be a dictionary"
                            )
                        else:
                            required_adj_keys = ["rule", "action", "reason"]
                            for req_key in required_adj_keys:
                                if req_key not in adj:
                                    errors.append(
                                        f"Missing '{req_key}' in adjustment {i} for field '{field_name}'"
                                    )

        return errors

    def create_generation_report(
        self, standard: dict[str, Any], generation_stats: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a comprehensive generation report.

        Args:
            standard: Generated standard
            generation_stats: Optional statistics from generation process

        Returns:
            Generation report dictionary
        """
        report = {
            "generation_timestamp": datetime.now().isoformat(),
            "standard_summary": {},
            "field_analysis": {},
            "dimension_analysis": {},
            "quality_indicators": {},
        }

        try:
            # Standard summary
            standards_section = standard.get("standards", {})
            report["standard_summary"] = {
                "name": standards_section.get("name", "Unknown"),
                "id": standards_section.get("id", "Unknown"),
                "version": standards_section.get("version", "Unknown"),
                "description": standards_section.get("description", ""),
            }

            # Field analysis
            field_reqs = standard.get("requirements", {}).get("field_requirements", {})
            if isinstance(field_reqs, dict):
                field_analysis = {
                    "total_fields": len(field_reqs),
                    "types_distribution": {},
                    "constraints_applied": {},
                }

                for field_name, field_config in field_reqs.items():
                    if isinstance(field_config, dict):
                        # Count field types
                        field_type = field_config.get("type", "unknown")
                        field_analysis["types_distribution"][field_type] = (
                            field_analysis["types_distribution"].get(field_type, 0) + 1
                        )

                        # Count constraint types
                        constraint_keys = [
                            "allowed_values",
                            "min_length",
                            "max_length",
                            "pattern",
                            "min_value",
                            "max_value",
                            "after_date",
                            "before_date",
                        ]
                        for constraint in constraint_keys:
                            if constraint in field_config:
                                field_analysis["constraints_applied"][constraint] = (
                                    field_analysis["constraints_applied"].get(
                                        constraint, 0
                                    )
                                    + 1
                                )

                report["field_analysis"] = field_analysis

            # Dimension analysis
            dim_reqs = standard.get("requirements", {}).get(
                "dimension_requirements", {}
            )
            if isinstance(dim_reqs, dict):
                report["dimension_analysis"] = {
                    "total_dimensions": len(dim_reqs),
                    "weights_summary": {
                        dim: config.get("weight", 1.0)
                        for dim, config in dim_reqs.items()
                    },
                    "minimums_summary": {
                        dim: config.get("minimum_score", 15.0)
                        for dim, config in dim_reqs.items()
                    },
                }

            # Quality indicators
            metadata = standard.get("metadata", {})
            if isinstance(metadata, dict):
                explanations = metadata.get("explanations", {})
                adjustment_count = 0
                if isinstance(explanations, dict):
                    for field_exp in explanations.values():
                        if isinstance(field_exp, dict) and "adjustments" in field_exp:
                            adjustments = field_exp["adjustments"]
                            if isinstance(adjustments, list):
                                adjustment_count += len(adjustments)

                report["quality_indicators"] = {
                    "training_pass_adjustments": adjustment_count,
                    "has_freshness_config": "freshness" in metadata,
                    "has_plausibility_templates": "plausibility_templates" in metadata,
                }

        except Exception as e:
            report["generation_errors"] = [f"Error creating report: {str(e)}"]

        return report
