"""
ADRI Standard Generator.

Automatic YAML standard generation from data analysis.
Migrated and updated for the new src/ layout architecture.
"""

from typing import Any, Dict, Optional

import pandas as pd

from .data_profiler import DataProfiler


class StandardGenerator:
    """
    Generates ADRI-compliant YAML standards from data analysis.

    This component creates validation rules based on data patterns,
    enabling automatic standard creation for any dataset.
    """

    def __init__(self):
        """Initialize the standard generator."""
        self.profiler = DataProfiler()

    def generate_standard(
        self,
        data_profile: Dict[str, Any],
        data_name: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete ADRI standard from a data profile.

        Args:
            data_profile: Data profile from DataProfiler
            data_name: Name for the generated standard
            generation_config: Configuration for generation thresholds

        Returns:
            Complete ADRI standard dictionary
        """
        config = generation_config or {}
        thresholds = config.get("default_thresholds", {})

        # Generate standard metadata
        standard_metadata = {
            "id": f"{data_name}_standard",
            "name": f"{data_name.replace('_', ' ').title()} ADRI Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": f"Auto-generated standard for {data_name} data",
            "effective_date": "2024-01-01T00:00:00Z",
        }

        # Generate requirements
        requirements = self._generate_requirements(data_profile, thresholds)

        # Build complete standard
        standard = {"standards": standard_metadata, "requirements": requirements}

        return standard

    def _generate_requirements(
        self, data_profile: Dict[str, Any], thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate requirements section from data profile."""
        requirements = {
            "overall_minimum": thresholds.get("overall_minimum", 75.0),
            "field_requirements": self._generate_field_requirements(data_profile),
            "dimension_requirements": self._generate_dimension_requirements(thresholds),
        }

        return requirements

    def _generate_field_requirements(
        self, data_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate field requirements from profiled fields."""
        field_requirements = {}
        fields = data_profile.get("fields", {})

        for field_name, field_profile in fields.items():
            field_req = self._generate_single_field_requirement(field_profile)
            field_requirements[field_name] = field_req

        return field_requirements

    def _generate_single_field_requirement(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate requirements for a single field."""
        requirement = {}

        # Determine data type
        dtype = field_profile.get("dtype", "object")
        if "int" in dtype:
            requirement["type"] = "integer"
        elif "float" in dtype:
            requirement["type"] = "float"
        elif "bool" in dtype:
            requirement["type"] = "boolean"
        elif "datetime" in dtype:
            requirement["type"] = "datetime"
        else:
            requirement["type"] = "string"

        # Determine nullable status
        null_percentage = field_profile.get("null_percentage", 0)
        requirement["nullable"] = null_percentage > 5  # Allow nulls if >5% are null

        # Add constraints based on data patterns
        if requirement["type"] in ["integer", "float"]:
            if "min_value" in field_profile and "max_value" in field_profile:
                # Ensure native Python types for YAML serialization
                requirement["min_value"] = float(field_profile["min_value"])
                requirement["max_value"] = float(field_profile["max_value"])

        elif requirement["type"] == "string":
            patterns = field_profile.get("common_patterns", [])
            if "email" in patterns:
                requirement["pattern"] = r"^[^@]+@[^@]+\.[^@]+$"
            elif "phone" in patterns:
                requirement["pattern"] = r"^[\+]?[0-9\s\-\(\)]+$"
            elif "date" in patterns:
                requirement["pattern"] = r"^\d{4}-\d{2}-\d{2}"

            # Add length constraints (emit both min_length and max_length when available)
            if "min_length" in field_profile:
                try:
                    requirement["min_length"] = int(field_profile["min_length"])
                except Exception:
                    pass
            if "max_length" in field_profile:
                max_len = field_profile["max_length"]
                try:
                    max_len_val = int(float(max_len))
                except Exception:
                    max_len_val = None
                if (
                    max_len_val is not None and max_len_val < 1000
                ):  # Only add if reasonable
                    # Keep the existing 20% buffer while ensuring it's >= min_length if present
                    widened = int(float(max_len) * 1.2)
                    if (
                        "min_length" in requirement
                        and widened < requirement["min_length"]
                    ):
                        widened = requirement["min_length"]
                    requirement["max_length"] = widened

        return requirement

    def _generate_dimension_requirements(
        self, thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate dimension requirements from thresholds."""
        return {
            "validity": {"minimum_score": thresholds.get("validity_min", 15.0)},
            "completeness": {"minimum_score": thresholds.get("completeness_min", 15.0)},
            "consistency": {"minimum_score": thresholds.get("consistency_min", 12.0)},
            "freshness": {"minimum_score": thresholds.get("freshness_min", 15.0)},
            "plausibility": {"minimum_score": thresholds.get("plausibility_min", 12.0)},
        }

    def generate_from_dataframe(
        self,
        data: pd.DataFrame,
        data_name: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate standard directly from a DataFrame.

        Args:
            data: DataFrame to analyze
            data_name: Name for the generated standard
            generation_config: Configuration for generation

        Returns:
            Complete ADRI standard dictionary
        """
        # Profile the data first
        data_profile = self.profiler.profile_data(data)
        config = generation_config or {}
        thresholds = config.get("default_thresholds", {})

        # Build standards metadata
        standard_metadata = {
            "id": f"{data_name}_standard",
            "name": f"{data_name.replace('_', ' ').title()} ADRI Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": f"Auto-generated standard for {data_name} data",
        }

        # Build field requirements with direct string-length fallback (guaranteed lengths for strings)
        field_requirements: Dict[str, Any] = {}
        prof_fields = (
            (data_profile.get("fields") or {}) if isinstance(data_profile, dict) else {}
        )

        for col in data.columns:
            fp = prof_fields.get(col, {"dtype": str(data[col].dtype)})
            # Baseline requirement using existing logic
            req = self._generate_single_field_requirement(fp)

            # Ensure string length bounds are emitted for strings
            try:
                if req.get("type") == "string":
                    non_null = data[col].dropna().astype(str)
                    if len(non_null) > 0:
                        min_len_observed = int(non_null.str.len().min())
                        max_len_observed = int(non_null.str.len().max())
                        # Emit min_length always
                        req["min_length"] = int(fp.get("min_length", min_len_observed))
                        # Emit max_length with 20% buffer but not below min_length
                        widened = int(max_len_observed * 1.2)
                        if widened < req["min_length"]:
                            widened = req["min_length"]
                        req["max_length"] = max(
                            int(fp.get("max_length", 0)) if "max_length" in fp else 0,
                            widened,
                        )
            except Exception:
                # Best-effort; keep whatever baseline we had
                pass

            field_requirements[col] = req

        # Build requirements with minimal dimension scaffolding
        requirements = {
            "overall_minimum": thresholds.get("overall_minimum", 75.0),
            "field_requirements": field_requirements,
            "dimension_requirements": self._generate_dimension_requirements(thresholds),
        }

        # Assemble final standard
        return {
            "standards": standard_metadata,
            "requirements": requirements,
        }


# Convenience function
def generate_standard_from_data(
    data: pd.DataFrame,
    data_name: str,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate an ADRI standard from DataFrame using default generator.

    Args:
        data: DataFrame to analyze
        data_name: Name for the generated standard
        generation_config: Configuration for generation

    Returns:
        Complete ADRI standard dictionary
    """
    generator = StandardGenerator()
    return generator.generate_from_dataframe(data, data_name, generation_config)
