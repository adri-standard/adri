"""
Standard generation module for ADRI V2.

This module provides functionality to generate YAML standards from data profiles.
"""

import re
from datetime import datetime
from typing import Any, Dict


class StandardGenerator:
    """
    Generates YAML standards from data profiles.

    This class takes data profiling results and generates comprehensive
    YAML standards that can be used for data quality assessment.
    """

    def __init__(self):
        """Initialize the StandardGenerator."""
        pass

    def generate_standard(
        self,
        data_profile: Dict[str, Any],
        data_name: str,
        generation_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a YAML standard from a data profile.

        Args:
            data_profile: Profile results from DataProfiler
            data_name: Name of the data source
            generation_config: Configuration for generation thresholds

        Returns:
            Dictionary representing the YAML standard
        """
        # Generate standard structure
        standard = {
            "standards": self._generate_standards_metadata(data_name),
            "requirements": self._generate_requirements(
                data_profile, generation_config
            ),
            "metadata": self._generate_metadata(data_name, data_profile),
        }

        # Convert to serializable format
        serialized = self._convert_to_serializable(standard)
        # Ensure we return the correct type
        if isinstance(serialized, dict):
            return serialized
        else:
            # Fallback to empty dict if conversion failed
            return {}

    def _generate_standards_metadata(self, data_name: str) -> Dict[str, Any]:
        """Generate the standards metadata section."""
        # Clean data name for ID
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "-", data_name.lower())
        clean_name = re.sub(r"-+", "-", clean_name).strip("-")

        # Generate human-readable name
        display_name = data_name.replace("_", " ").replace("-", " ").title()
        if not display_name.endswith("Data"):
            display_name += " Data"

        return {
            "id": f"{clean_name}-v1",
            "name": f"{display_name} Quality Standard",
            "version": "1.0.0",
            "authority": "ADRI Auto-Generated",
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "description": f"Auto-generated data quality standard for {display_name.lower()}",
        }

    def _generate_requirements(
        self, data_profile: Dict[str, Any], generation_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the requirements section."""
        thresholds = generation_config.get("default_thresholds", {})

        return {
            "overall_minimum": self._calculate_overall_minimum(
                data_profile, thresholds
            ),
            "dimension_requirements": self._generate_dimension_requirements(thresholds),
            "field_requirements": self._generate_field_requirements(data_profile),
        }

    def _calculate_overall_minimum(
        self, data_profile: Dict[str, Any], thresholds: Dict[str, Any]
    ) -> float:
        """Calculate overall minimum score based on data quality."""
        # Base score from thresholds
        base_scores = [
            thresholds.get("completeness_min", 85),
            thresholds.get("validity_min", 90),
            thresholds.get("consistency_min", 80),
        ]

        # Adjust based on data characteristics
        fields = data_profile.get("fields", {})

        # Lower requirements if data has many nullable fields
        nullable_ratio = sum(
            1 for field in fields.values() if field.get("nullable", False)
        ) / max(len(fields), 1)
        if nullable_ratio > 0.3:  # More than 30% nullable fields
            adjustment = -5.0
        else:
            adjustment = 0.0

        # Calculate weighted average
        overall_min = sum(base_scores) / len(base_scores) + adjustment

        # Ensure reasonable bounds
        return float(max(60.0, min(95.0, overall_min)))

    def _generate_dimension_requirements(
        self, thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate dimension requirements."""

        # Convert percentage thresholds to 20-point scale
        def percentage_to_score(percentage: float) -> float:
            return (percentage / 100.0) * 20.0

        return {
            "validity": {
                "minimum_score": percentage_to_score(
                    thresholds.get("validity_min", 90)
                ),
                "description": "Data must conform to expected formats and constraints",
            },
            "completeness": {
                "minimum_score": percentage_to_score(
                    thresholds.get("completeness_min", 85)
                ),
                "description": "Required fields must be populated",
            },
            "consistency": {
                "minimum_score": percentage_to_score(
                    thresholds.get("consistency_min", 80)
                ),
                "description": "Data must be consistent across related fields",
            },
            "freshness": {
                "minimum_score": 15.0,  # Generally high requirement for freshness
                "description": "Data must be recent and up-to-date",
            },
            "plausibility": {
                "minimum_score": 12.0,  # Moderate requirement for plausibility
                "description": "Data values must be reasonable and realistic",
            },
        }

    def _generate_field_requirements(
        self, data_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate field requirements from data profile."""
        field_requirements = {}
        fields = data_profile.get("fields", {})

        for field_name, field_profile in fields.items():
            field_requirements[field_name] = self._generate_single_field_requirement(
                field_name, field_profile
            )

        return field_requirements

    def _generate_single_field_requirement(
        self, field_name: str, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate requirements for a single field."""
        field_type = field_profile.get("type", "string")
        nullable = field_profile.get("nullable", False)

        # Base requirement
        requirement = {
            "type": field_type,
            "nullable": nullable,
            "description": self._generate_field_description(field_name, field_type),
        }

        # Add type-specific constraints
        if field_type == "integer":
            requirement.update(self._generate_integer_constraints(field_profile))
        elif field_type == "float":
            requirement.update(self._generate_float_constraints(field_profile))
        elif field_type == "string":
            requirement.update(self._generate_string_constraints(field_profile))
        elif field_type == "date":
            requirement.update(self._generate_date_constraints(field_profile))

        return requirement

    def _generate_field_description(self, field_name: str, field_type: str) -> str:
        """Generate a description for a field."""
        # Convert field name to human readable
        readable_name = field_name.replace("_", " ").replace("-", " ").title()

        # Add type-specific context
        type_descriptions = {
            "integer": "numeric identifier or count",
            "float": "numeric value with decimal precision",
            "string": "text value",
            "boolean": "true/false indicator",
            "date": "date value",
        }

        type_desc = type_descriptions.get(field_type, "value")
        return f"{readable_name} - {type_desc}"

    def _generate_integer_constraints(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate constraints for integer fields."""
        constraints = {}

        if "min_value" in field_profile and "max_value" in field_profile:
            min_val = field_profile["min_value"]
            max_val = field_profile["max_value"]

            # Apply reasonable bounds for common field types
            if min_val >= 1 and max_val <= 1000000:  # Likely ID field
                constraints["min_value"] = max(1, min_val)
                constraints["max_value"] = min(1000000, max_val * 2)  # Allow for growth
            elif min_val >= 0 and max_val <= 150:  # Likely age field
                constraints["min_value"] = max(0, min_val - 5)
                constraints["max_value"] = min(150, max_val + 10)
            else:  # General numeric field
                constraints["min_value"] = min_val
                constraints["max_value"] = max_val

        return constraints

    def _generate_float_constraints(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate constraints for float fields."""
        constraints = {}

        if "min_value" in field_profile:
            min_val = field_profile["min_value"]
            # For financial fields, minimum is often 0
            if min_val >= 0:
                constraints["min_value"] = 0.0
            else:
                constraints["min_value"] = min_val

        # Don't set max_value for floats as they can vary widely

        return constraints

    def _generate_string_constraints(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate constraints for string fields."""
        constraints = {}

        # Length constraints
        if "min_length" in field_profile and "max_length" in field_profile:
            min_len = field_profile["min_length"]
            max_len = field_profile["max_length"]

            # Set reasonable bounds
            constraints["min_length"] = max(1, min_len - 1)  # Allow slightly shorter
            constraints["max_length"] = max_len + 10  # Allow for growth

        # Pattern constraints
        if "pattern" in field_profile:
            pattern = field_profile["pattern"]
            if "email" in pattern.lower() or "@" in pattern:
                # Use standard email pattern
                constraints["pattern"] = (
                    "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                )
            else:
                constraints["pattern"] = pattern

        return constraints

    def _generate_date_constraints(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate constraints for date fields."""
        constraints = {}

        # Add date format if detected
        if "date_format" in field_profile:
            date_format = field_profile["date_format"]
            if date_format != "unknown":
                constraints["format"] = date_format

        return constraints

    def _generate_metadata(
        self, data_name: str, data_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metadata section."""
        summary = data_profile.get("summary", {})

        # Generate tags based on data characteristics
        tags = ["auto-generated"]

        # Add tags based on field names and types
        fields = data_profile.get("fields", {})
        field_names = list(fields.keys())

        if any("customer" in name.lower() for name in field_names):
            tags.append("customer-data")
        if any("email" in name.lower() for name in field_names):
            tags.append("personal-data")
        if any(
            "balance" in name.lower() or "amount" in name.lower()
            for name in field_names
        ):
            tags.append("financial")
        if any(
            "date" in name.lower() or "time" in name.lower() for name in field_names
        ):
            tags.append("temporal")

        return {
            "created_by": "ADRI V2 Auto-Generation",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "last_modified": datetime.now().strftime("%Y-%m-%d"),
            "source_data_rows": summary.get("total_rows", 0),
            "source_data_columns": summary.get("total_columns", 0),
            "tags": tags,
        }

    def _convert_to_serializable(self, obj: Any) -> Any:
        """
        Convert numpy/pandas objects to JSON-serializable types.

        Args:
            obj: Object to convert

        Returns:
            JSON-serializable object
        """
        import numpy as np

        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, "item"):  # numpy scalar
            return obj.item()
        elif hasattr(obj, "tolist"):  # numpy array
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        else:
            return obj
