"""Dimension requirements builder for ADRI standard generation.

This module contains the DimensionRequirementsBuilder class that handles
the creation of dimension-specific requirements and scoring configurations
for ADRI standards.
"""

from datetime import datetime
from typing import Any


class DimensionRequirementsBuilder:
    """Builds dimension requirements and scoring configurations.

    The DimensionRequirementsBuilder focuses on creating the dimension_requirements
    section of ADRI standards, including weights, minimum scores, and scoring
    policies for each of the 5 quality dimensions.
    """

    def __init__(self):
        """Initialize the dimension requirements builder."""

    def build_dimension_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate comprehensive dimension requirements with scoring policies.

        Args:
            thresholds: Configuration containing dimension minimum scores

        Returns:
            Complete dimension_requirements dictionary
        """
        return {
            "validity": self._build_validity_requirements(thresholds),
            "completeness": self._build_completeness_requirements(thresholds),
            "consistency": self._build_consistency_requirements(thresholds),
            "freshness": self._build_freshness_requirements(thresholds),
            "plausibility": self._build_plausibility_requirements(thresholds),
        }

    def _build_validity_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Build validity dimension requirements with rule weights.

        Args:
            thresholds: Configuration containing minimum scores

        Returns:
            Validity dimension configuration
        """
        return {
            "minimum_score": thresholds.get("validity_min", 15.0),
            "weight": 1.0,
            "scoring": {
                "rule_weights": {},  # Populated dynamically by StandardGenerator
                "field_overrides": {},  # Placeholder for field-specific rule weights
            },
        }

    def _build_completeness_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Build completeness dimension requirements.

        Args:
            thresholds: Configuration containing minimum scores

        Returns:
            Completeness dimension configuration
        """
        return {
            "minimum_score": thresholds.get("completeness_min", 15.0),
            "weight": 1.0,
            "scoring": {
                "rule_weights": {"missing_required": 1.0},  # Primary completeness rule
                "field_overrides": {},
            },
        }

    def _build_consistency_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Build consistency dimension requirements.

        Args:
            thresholds: Configuration containing minimum scores

        Returns:
            Consistency dimension configuration
        """
        return {
            "minimum_score": thresholds.get("consistency_min", 12.0),
            "weight": 1.0,
            "scoring": {
                "rule_weights": {},  # Populated dynamically by StandardGenerator
                "field_overrides": {},
            },
        }

    def _build_freshness_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Build freshness dimension requirements.

        Args:
            thresholds: Configuration containing minimum scores

        Returns:
            Freshness dimension configuration
        """
        return {
            "minimum_score": thresholds.get("freshness_min", 15.0),
            "weight": 1.0,
            "scoring": {
                "rule_weights": {
                    # Inactive by default; will be enabled by freshness detection
                    "recency_window": 0.0
                },
                "field_overrides": {},
            },
        }

    def _build_plausibility_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Build plausibility dimension requirements with distinct rule types.

        Args:
            thresholds: Configuration containing minimum scores

        Returns:
            Plausibility dimension configuration
        """
        return {
            "minimum_score": thresholds.get("plausibility_min", 12.0),
            "weight": 1.0,
            "scoring": {
                "rule_weights": {},  # Populated dynamically by StandardGenerator
                "field_overrides": {},
            },
        }

    def normalize_rule_weights(
        self, dimension_config: dict[str, Any], dimension_name: str
    ) -> None:
        """Normalize rule weights so active rules sum to 1.0.

        Args:
            dimension_config: Full dimension requirements dict
            dimension_name: Name of dimension (validity, consistency, etc.)
        """
        if dimension_name not in dimension_config:
            return

        rule_weights = dimension_config[dimension_name]["scoring"]["rule_weights"]
        active_weights = {k: v for k, v in rule_weights.items() if v > 0}

        if not active_weights:
            return  # No active rules - dimension returns perfect score

        total = sum(active_weights.values())
        if total > 0:
            for rule_type in active_weights:
                rule_weights[rule_type] = active_weights[rule_type] / total

    def enable_freshness_checking(
        self, dimension_reqs: dict[str, Any], date_field: str, window_days: int = 365
    ) -> None:
        """Enable freshness checking for a detected date field.

        Args:
            dimension_reqs: Dimension requirements dictionary to modify
            date_field: Name of the date field to use for freshness
            window_days: Recency window in days
        """
        if "freshness" in dimension_reqs:
            freshness_config = dimension_reqs["freshness"]
            scoring_config = freshness_config.setdefault("scoring", {})
            rule_weights = scoring_config.setdefault("rule_weights", {})
            rule_weights["recency_window"] = 1.0

    def create_freshness_metadata(
        self, date_field: str, window_days: int = 365, as_of_date: Any | None = None
    ) -> dict[str, Any]:
        """Create freshness metadata configuration.

        Args:
            date_field: Name of the field to use for freshness checking
            window_days: Recency window in days
            as_of_date: Optional datetime to use as reference point (defaults to now)

        Returns:
            Freshness metadata dictionary
        """
        # Use provided as_of_date or default to current time
        if as_of_date is not None:
            as_of_str = as_of_date.isoformat() + "Z"
        else:
            as_of_str = datetime.now().isoformat() + "Z"

        return {
            "as_of": as_of_str,
            "window_days": window_days,
            "date_field": date_field,
        }

    def create_freshness_scaffolding(self) -> str:
        """Create commented template for manual freshness configuration.

        Returns:
            Multi-line string with freshness configuration template
        """
        return (
            "# freshness:\n"
            "#   as_of: " + datetime.now().isoformat() + "Z\n"
            "#   window_days: 365\n"
            "#   date_field: <your_date_field>\n"
            "#   how_to_enable: set requirements.dimension_requirements.freshness.scoring.rule_weights.recency_window to 1.0\n"
        )

    def create_plausibility_templates(self) -> str:
        """Create commented templates for plausibility configuration.

        Returns:
            Multi-line string with plausibility configuration template
        """
        return (
            "# plausibility:\n"
            "#   scoring:\n"
            "#     rule_weights:\n"
            "#       numeric_sigma: 1.0      # enable if not overlapping with validity numeric_bounds\n"
            "#       categorical_tail: 1.0   # enable to flag rare categories\n"
            '#   notes: "Disabled by default to avoid overlap with Validity. Review before enabling."\n'
        )

    def apply_dimension_preset(
        self, dimension_reqs: dict[str, Any], preset: str
    ) -> dict[str, str]:
        """Apply a dimension scoring preset to modify weights and minimums.

        Args:
            dimension_reqs: Dimension requirements to modify
            preset: Preset name ('balanced', 'strict', 'lenient')

        Returns:
            Dictionary describing changes made
        """
        presets = self._get_dimension_presets()

        if preset not in presets:
            raise ValueError(
                f"Unknown preset: {preset}. Available: {list(presets.keys())}"
            )

        preset_config = presets[preset]
        changes = []

        for dim in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            if dim in dimension_reqs:
                dim_cfg = dimension_reqs[dim]

                # Update weight
                old_weight = dim_cfg.get("weight")
                new_weight = preset_config["weights"].get(dim, 1.0)
                dim_cfg["weight"] = float(new_weight)

                # Update minimum score
                old_min = dim_cfg.get("minimum_score")
                new_min = preset_config["minimums"].get(dim, 15.0)
                dim_cfg["minimum_score"] = float(new_min)

                changes.append(
                    f"{dim} (weight {old_weight}→{new_weight}, min {old_min}→{new_min})"
                )

                # Update validity rule weights if this is the validity dimension
                if dim == "validity" and "validity_rule_weights" in preset_config:
                    scoring = dim_cfg.setdefault("scoring", {})
                    scoring["rule_weights"] = {
                        k: float(v)
                        for k, v in preset_config["validity_rule_weights"].items()
                    }

        return {f"preset_{preset}_applied": changes}

    def _get_dimension_presets(self) -> dict[str, dict[str, Any]]:
        """Get predefined dimension scoring presets.

        Returns:
            Dictionary of preset configurations
        """
        return {
            "balanced": {
                "weights": {
                    "validity": 1.0,
                    "completeness": 1.0,
                    "consistency": 1.0,
                    "freshness": 1.0,
                    "plausibility": 1.0,
                },
                "minimums": {
                    "validity": 15.0,
                    "completeness": 15.0,
                    "consistency": 12.0,
                    "freshness": 15.0,
                    "plausibility": 12.0,
                },
                "validity_rule_weights": {
                    "type": 0.30,
                    "allowed_values": 0.20,
                    "pattern": 0.20,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.20,
                    "date_bounds": 0.20,
                },
            },
            "strict": {
                "weights": {
                    "validity": 1.3,
                    "completeness": 1.2,
                    "consistency": 1.1,
                    "freshness": 1.0,
                    "plausibility": 0.9,
                },
                "minimums": {
                    "validity": 17.0,
                    "completeness": 17.0,
                    "consistency": 14.0,
                    "freshness": 16.0,
                    "plausibility": 14.0,
                },
                "validity_rule_weights": {
                    "type": 0.35,
                    "allowed_values": 0.15,
                    "pattern": 0.25,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.25,
                    "date_bounds": 0.25,
                },
            },
            "lenient": {
                "weights": {
                    "validity": 0.9,
                    "completeness": 0.8,
                    "consistency": 1.0,
                    "freshness": 1.0,
                    "plausibility": 1.0,
                },
                "minimums": {
                    "validity": 12.0,
                    "completeness": 12.0,
                    "consistency": 10.0,
                    "freshness": 12.0,
                    "plausibility": 10.0,
                },
                "validity_rule_weights": {
                    "type": 0.25,
                    "allowed_values": 0.25,
                    "pattern": 0.15,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.25,
                    "date_bounds": 0.25,
                },
            },
        }

    def validate_dimension_requirements(
        self, dimension_reqs: dict[str, Any]
    ) -> list[str]:
        """Validate dimension requirements for completeness and correctness.

        Args:
            dimension_reqs: Dimension requirements to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        required_dimensions = [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]

        for dim in required_dimensions:
            if dim not in dimension_reqs:
                errors.append(f"Missing dimension: {dim}")
                continue

            dim_config = dimension_reqs[dim]
            if not isinstance(dim_config, dict):
                errors.append(f"Invalid dimension config for {dim}: must be dict")
                continue

            # Check required fields
            if "minimum_score" not in dim_config:
                errors.append(f"Missing minimum_score for dimension {dim}")
            if "weight" not in dim_config:
                errors.append(f"Missing weight for dimension {dim}")

            # Validate weight values
            try:
                weight = float(dim_config.get("weight", 1.0))
                if weight < 0:
                    errors.append(f"Negative weight for dimension {dim}: {weight}")
            except (ValueError, TypeError):
                errors.append(f"Invalid weight for dimension {dim}: must be numeric")

            # Validate minimum score values
            try:
                min_score = float(dim_config.get("minimum_score", 15.0))
                if min_score < 0 or min_score > 20:
                    errors.append(
                        f"Invalid minimum_score for dimension {dim}: {min_score} (must be 0-20)"
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"Invalid minimum_score for dimension {dim}: must be numeric"
                )

        return errors
