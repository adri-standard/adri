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

            # Add length constraints
            if "max_length" in field_profile:
                max_len = field_profile["max_length"]
                if max_len < 1000:  # Only add if reasonable
                    requirement["max_length"] = int(
                        float(max_len) * 1.2
                    )  # Allow 20% buffer

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

        # Generate standard from profile
        return self.generate_standard(data_profile, data_name, generation_config)


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
