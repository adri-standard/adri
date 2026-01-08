"""Standard builder for ADRI standard generation.

This module contains the StandardBuilder class that handles the overall
construction and assembly of ADRI standards from analyzed components.
"""

from datetime import datetime
from typing import Any

import pandas as pd

from ..rule_inference import detect_primary_key, InferenceConfig
from .dimension_builder import DimensionRequirementsBuilder
from .field_inference import FieldInferenceEngine


class ContractBuilder:
    """Builds complete ADRI standards from component analysis.

    The StandardBuilder orchestrates the creation of complete ADRI standards
    by coordinating field inference, dimension requirements, and metadata
    generation into a cohesive YAML standard structure.
    """

    def __init__(self):
        """Initialize the standard builder with component engines."""
        self.field_engine = FieldInferenceEngine()
        self.dimension_builder = DimensionRequirementsBuilder()

    def build_standard(
        self,
        data: pd.DataFrame,
        data_name: str,
        data_profile: dict[str, Any],
        generation_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a complete ADRI standard from data and profile.

        Args:
            data: DataFrame containing the source data
            data_name: Name for the generated standard
            data_profile: Data profile from DataProfiler
            generation_config: Configuration for generation thresholds and inference

        Returns:
            Complete ADRI standard dictionary
        """
        # Extract configuration
        config = generation_config or {}
        thresholds = config.get("default_thresholds", {})
        inference_config = InferenceConfig(**(config.get("inference", {}) or {}))

        # Build standard metadata
        standards_metadata = self._build_standards_metadata(data_name)

        # Detect primary key fields
        pk_fields = self._detect_primary_key_fields(data, inference_config)

        # Generate field requirements
        field_requirements = self.field_engine.infer_field_requirements(
            data, data_profile, inference_config, pk_fields=pk_fields
        )

        # Detect and enhance derived fields with derivation rules
        field_requirements = self._enhance_derived_fields(
            data, field_requirements, inference_config
        )

        # Generate dimension requirements
        dimension_requirements = self.dimension_builder.build_dimension_requirements(
            thresholds
        )

        # Build record identification
        record_identification = self._build_record_identification(pk_fields)

        # Build complete requirements section
        requirements = {
            "overall_minimum": thresholds.get("overall_minimum", 75.0),
            "field_requirements": field_requirements,
            "dimension_requirements": dimension_requirements,
        }

        # Assemble the standard
        standard = {
            "contracts": standards_metadata,
            "record_identification": record_identification,
            "requirements": requirements,
            "metadata": self._build_base_metadata(),
        }

        # Populate rule weights dynamically based on detected rules
        self._populate_rule_weights(standard)

        return standard

    def _enhance_derived_fields(
        self,
        data: pd.DataFrame,
        field_requirements: dict[str, Any],
        config: InferenceConfig,
    ) -> dict[str, Any]:
        """Detect derived fields and enhance with derivation rules.

        Args:
            data: DataFrame containing the source data
            field_requirements: Field requirements to enhance
            config: Inference configuration

        Returns:
            Enhanced field requirements with derivation rules
        """
        try:
            # Detect fields that appear to be derived from other fields
            derived_fields = self.field_engine.detect_derived_fields(
                data, field_requirements
            )

            # Enhance each derived field with derivation rules
            for field_name, derivation_metadata in derived_fields.items():
                if field_name not in field_requirements:
                    continue

                # Generate enhanced allowed_values with derivation rules
                enhanced_values = self.field_engine.generate_derivation_rules(
                    field_name, derivation_metadata, data
                )

                # Update field requirement with enhanced structure
                field_req = field_requirements[field_name]
                field_req["is_derived"] = True
                field_req["allowed_values"] = enhanced_values

                # Add metadata about the derivation
                field_req["derivation_metadata"] = {
                    "confidence": derivation_metadata["confidence"],
                    "input_fields": derivation_metadata["input_fields"],
                    "auto_generated": True,
                    "note": "Review and refine derivation rules based on business logic",
                }

        except Exception as e:
            # Non-fatal - if derived field detection fails, just use standard field requirements
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Derived field detection skipped: {e}")

        return field_requirements

    def _build_standards_metadata(self, data_name: str) -> dict[str, Any]:
        """Build the standards section metadata.

        Args:
            data_name: Name for the standard

        Returns:
            Standards metadata dictionary
        """
        return {
            "id": f"{data_name}_standard",
            "name": f"{data_name.replace('_', ' ').title()} ADRI Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": f"Auto-generated standard for {data_name} data",
        }

    def _detect_primary_key_fields(
        self, data: pd.DataFrame, config: InferenceConfig
    ) -> list[str]:
        """Detect primary key fields in the data.

        Args:
            data: DataFrame to analyze
            config: Inference configuration

        Returns:
            List of primary key field names
        """
        pk_fields = detect_primary_key(data, max_combo=config.max_pk_combo_size)

        # Fallback to first column if no primary key detected
        if not pk_fields and len(data.columns) > 0:
            pk_fields = [data.columns[0]]

        return pk_fields or []

    def _build_record_identification(self, pk_fields: list[str]) -> dict[str, Any]:
        """Build record identification configuration.

        Args:
            pk_fields: Primary key field names

        Returns:
            Record identification dictionary
        """
        return {
            "primary_key_fields": pk_fields,
            "strategy": "primary_key_with_fallback",
        }

    def _build_base_metadata(self) -> dict[str, Any]:
        """Build base metadata structure for the standard.

        Returns:
            Base metadata dictionary
        """
        return {
            "explanations_note": "Explanations are for human review; only requirements.field_requirements are enforced.",
            "explanations_glossary": {
                "iqr": "Interquartile Range (Q3 - Q1): a robust measure of spread, less sensitive to outliers.",
                "q1": "25th percentile of the training values.",
                "q3": "75th percentile of the training values.",
                "coverage": "Share of non-null training values that satisfy the rule.",
                "unique_count": "Number of distinct non-null values observed in training.",
            },
            "explanations": {},  # Will be populated by ExplanationGenerator
        }

    def _populate_rule_weights(self, standard: dict[str, Any]) -> None:
        """Populate rule weights dynamically based on detected rules.

        Now supports both old format (field constraints) and new format (validation_rules).
        Counts validation_rules by dimension and rule_type for weight population.

        Args:
            standard: Standard dictionary to populate
        """
        try:
            dimension_reqs = standard["requirements"]["dimension_requirements"]
            field_reqs = standard["requirements"]["field_requirements"]
            pk_fields = standard["record_identification"]["primary_key_fields"]

            # Check if using new validation_rules format
            using_validation_rules = any(
                isinstance(field_req, dict) and "validation_rules" in field_req
                for field_req in field_reqs.values()
            )

            if using_validation_rules:
                # New format: Count validation_rules by dimension and rule_type
                self._populate_rule_weights_from_validation_rules(
                    dimension_reqs, field_reqs, pk_fields
                )
            else:
                # Old format: Count field constraints (backward compatible)
                self._populate_rule_weights_from_constraints(
                    dimension_reqs, field_reqs, pk_fields
                )

        except Exception:
            # Non-fatal - dimension weights will remain empty or with default values
            pass

    def _populate_rule_weights_from_validation_rules(
        self,
        dimension_reqs: dict[str, Any],
        field_reqs: dict[str, Any],
        pk_fields: list[str],
    ) -> None:
        """Populate rule weights from validation_rules structure.

        Args:
            dimension_reqs: Dimension requirements dictionary
            field_reqs: Field requirements dictionary with validation_rules
            pk_fields: Primary key field names
        """
        # Count rules by dimension and rule_type
        rule_counts = {}

        for field_name, field_req in field_reqs.items():
            if not isinstance(field_req, dict):
                continue

            validation_rules = field_req.get("validation_rules", [])
            if not validation_rules:
                continue

            for rule in validation_rules:
                if not isinstance(rule, dict):
                    continue

                dimension = rule.get("dimension")
                rule_type = rule.get("rule_type")

                if dimension and rule_type:
                    rule_counts.setdefault(dimension, {})
                    rule_counts[dimension][rule_type] = (
                        rule_counts[dimension].get(rule_type, 0) + 1
                    )

        # Add consistency rules (dataset-level, not in field validation_rules)
        consistency_counts = rule_counts.setdefault("consistency", {})

        if pk_fields:
            consistency_counts["primary_key_uniqueness"] = 1.0

        has_string_fields = any(
            field_req.get("type") == "string"
            for field_req in field_reqs.values()
            if isinstance(field_req, dict)
        )
        if has_string_fields:
            consistency_counts["format_consistency"] = 1.0

        if len(field_reqs) >= 2:
            consistency_counts["cross_field_logic"] = 1.0

        # Populate weights for each dimension
        for dimension_name, dimension_config in dimension_reqs.items():
            if not isinstance(dimension_config, dict):
                continue

            scoring = dimension_config.get("scoring", {})
            if not isinstance(scoring, dict):
                continue

            rule_weights = scoring.get("rule_weights", {})
            if not isinstance(rule_weights, dict):
                continue

            # Set weights based on rule counts for this dimension
            dimension_rule_counts = rule_counts.get(dimension_name, {})
            for rule_type, count in dimension_rule_counts.items():
                rule_weights[rule_type] = float(count)

            # Normalize weights
            self.dimension_builder.normalize_rule_weights(
                dimension_reqs, dimension_name
            )

    def _populate_rule_weights_from_constraints(
        self,
        dimension_reqs: dict[str, Any],
        field_reqs: dict[str, Any],
        pk_fields: list[str],
    ) -> None:
        """Populate rule weights from old-style field constraints (backward compatible).

        Args:
            dimension_reqs: Dimension requirements dictionary
            field_reqs: Field requirements dictionary with constraints
            pk_fields: Primary key field names
        """
        # Original logic for old format
        validity_weights = dimension_reqs["validity"]["scoring"]["rule_weights"]
        for field_name, field_req in field_reqs.items():
            if not isinstance(field_req, dict):
                continue

            # Type rule
            if "type" in field_req:
                validity_weights["type"] = validity_weights.get("type", 0) + 1

            # Allowed values rule
            if "allowed_values" in field_req:
                validity_weights["allowed_values"] = (
                    validity_weights.get("allowed_values", 0) + 1
                )

            # Pattern rule
            if "pattern" in field_req:
                validity_weights["pattern"] = validity_weights.get("pattern", 0) + 1

            # Length bounds rule
            if "min_length" in field_req or "max_length" in field_req:
                validity_weights["length_bounds"] = (
                    validity_weights.get("length_bounds", 0) + 1
                )

            # Numeric bounds rule
            if "min_value" in field_req or "max_value" in field_req:
                validity_weights["numeric_bounds"] = (
                    validity_weights.get("numeric_bounds", 0) + 1
                )

            # Date bounds rule
            if "after_date" in field_req or "before_date" in field_req:
                validity_weights["date_bounds"] = (
                    validity_weights.get("date_bounds", 0) + 1
                )

        # Normalize validity weights
        self.dimension_builder.normalize_rule_weights(dimension_reqs, "validity")

        # Populate consistency rule weights
        consistency_weights = dimension_reqs["consistency"]["scoring"]["rule_weights"]

        if pk_fields:
            consistency_weights["primary_key_uniqueness"] = 1.0

        has_string_fields = any(
            field_req.get("type") == "string"
            for field_req in field_reqs.values()
            if isinstance(field_req, dict)
        )
        if has_string_fields:
            consistency_weights["format_consistency"] = 1.0

        if len(field_reqs) >= 2:
            consistency_weights["cross_field_logic"] = 1.0

        self.dimension_builder.normalize_rule_weights(dimension_reqs, "consistency")

        # Populate plausibility rule weights
        plausibility_weights = dimension_reqs["plausibility"]["scoring"]["rule_weights"]
        has_numeric = False
        has_categorical = False

        for field_name, field_req in field_reqs.items():
            if not isinstance(field_req, dict):
                continue
            field_type = field_req.get("type", "")
            if field_type in ["number", "integer"]:
                has_numeric = True
            elif field_type == "string":
                has_categorical = True

        if has_numeric:
            plausibility_weights["statistical_outliers"] = 0.4
        if has_categorical:
            plausibility_weights["categorical_frequency"] = 0.3
        if has_numeric or has_categorical:
            plausibility_weights["business_logic"] = 0.2
            plausibility_weights["cross_field_consistency"] = 0.1

        self.dimension_builder.normalize_rule_weights(dimension_reqs, "plausibility")

    def enforce_training_pass_guarantee(
        self, data: pd.DataFrame, standard: dict[str, Any]
    ) -> dict[str, Any]:
        """Ensure the generated standard passes on its training data.

        Args:
            data: Training data that must pass validation
            standard: Standard to validate and potentially adjust

        Returns:
            Modified standard that passes on training data
        """
        field_reqs = standard.get("requirements", {}).get("field_requirements", {})
        if not isinstance(field_reqs, dict):
            return standard

        # Prepare adjustment logging
        metadata = standard.setdefault("metadata", {})
        adjustments_log = metadata.setdefault("explanations", {})

        # Get observed statistics for relaxation
        observed_stats = self.field_engine.prepare_observed_stats(data)

        # Iterate until stable (max 2 passes for safety)
        for iteration in range(2):
            any_changes = False

            for col in data.columns:
                if col not in field_reqs:
                    continue

                field_req = field_reqs[col]

                # Ensure nullable aligns with actual data
                if not field_req.get("nullable", True) and data[col].isnull().any():
                    field_req["nullable"] = True
                    any_changes = True

                # Validate each non-null value and relax failing constraints
                for val in data[col].dropna():
                    failing_rule = self.field_engine.validate_field_against_rules(
                        val, field_req
                    )
                    if failing_rule:
                        self.field_engine.relax_constraint_for_failure(
                            col,
                            failing_rule,
                            field_req,
                            observed_stats.get(col, {}),
                            adjustments_log,
                        )
                        any_changes = True
                        # Continue to next value after relaxation
                        continue

                # Update field requirements
                field_reqs[col] = field_req

            if not any_changes:
                break  # Converged

        return standard

    def detect_and_configure_freshness(
        self, data: pd.DataFrame, standard: dict[str, Any]
    ) -> dict[str, Any]:
        """Detect date fields and configure freshness checking if appropriate.

        Args:
            data: DataFrame to analyze for date fields
            standard: Standard to potentially configure

        Returns:
            Modified standard with freshness configuration
        """
        # Find the best date field candidate
        candidate_col = None
        best_coverage = 0.0

        for col in data.columns:
            series = data[col]

            # Skip numeric columns - they are not date fields
            # This prevents selecting fields like 'amount' (1250.00, 2500.00) as date
            # candidates
            if series.dtype in ["int64", "float64", "int32", "float32", "int", "float"]:
                continue

            # Calculate non-null count
            try:
                non_null_count = int(series.notna().sum())
            except Exception:
                non_null_count = 0

            if non_null_count <= 0:
                continue

            # Try to parse as dates (only for date/datetime/object types)
            parsed = pd.to_datetime(series, errors="coerce", format="ISO8601")
            parsed_count = int(parsed.notna().sum())

            # Calculate coverage (what percentage of non-null values are valid dates)
            coverage = (parsed_count / non_null_count) if non_null_count > 0 else 0.0

            # Use field with highest date coverage (>= 90%)
            if coverage >= 0.9 and coverage > best_coverage:
                best_coverage = coverage
                candidate_col = col

        # Configure freshness if a good date field was found
        metadata = standard.setdefault("metadata", {})

        if candidate_col:
            # Get the max date from the data to use as as_of
            # This ensures training data always passes freshness checks
            max_date = None
            try:
                parsed = pd.to_datetime(
                    data[candidate_col], errors="coerce", format="ISO8601"
                )
                max_date = parsed.max()
                if pd.notna(max_date):
                    # Convert to datetime and add a small buffer (e.g., 1 day)
                    max_date = max_date.to_pydatetime()
                    from datetime import timedelta

                    max_date = max_date + timedelta(days=1)
            except Exception:
                pass

            # Enable freshness checking
            freshness_metadata = self.dimension_builder.create_freshness_metadata(
                candidate_col, as_of_date=max_date
            )
            metadata["freshness"] = freshness_metadata

            # Activate freshness rule weight
            try:
                freshness_reqs = standard["requirements"]["dimension_requirements"][
                    "freshness"
                ]
                freshness_reqs["scoring"]["rule_weights"]["recency_window"] = 1.0
            except Exception:
                pass  # Non-fatal if structure is different
        else:
            # Provide scaffolding for manual configuration
            metadata["freshness_scaffolding"] = (
                self.dimension_builder.create_freshness_scaffolding()
            )

        return standard

    def add_generation_metadata(
        self, standard: dict[str, Any], data_name: str
    ) -> dict[str, Any]:
        """Add generation-specific metadata to the standard.

        Args:
            standard: Standard to enhance with metadata
            data_name: Name of the data source

        Returns:
            Standard with added generation metadata
        """
        current_timestamp = datetime.now().isoformat()

        generation_metadata = {
            "created_by": "ADRI Framework",
            "created_date": current_timestamp,
            "last_modified": current_timestamp,
            "generation_method": "auto_generated",
            "tags": ["data_quality", "auto_generated", f"{data_name}_data"],
        }

        # Add severity config lineage for traceability
        severity_config_info = self._get_severity_config_lineage()
        if severity_config_info:
            generation_metadata["severity_config"] = severity_config_info

        # Merge with existing metadata
        existing_metadata = standard.get("metadata", {}) or {}
        standard["metadata"] = {**generation_metadata, **existing_metadata}

        return standard

    def _get_severity_config_lineage(self) -> dict[str, Any] | None:
        """Get lineage information for severity config used in generation.

        Returns:
            Dictionary with config file path, checksum, and timestamp
        """
        try:
            import hashlib
            import os
            from pathlib import Path

            # Determine which config file was used
            env_config = os.environ.get("ADRI_SEVERITY_CONFIG")
            if env_config and os.path.exists(env_config):
                config_path = Path(env_config)
            else:
                # Default config path
                config_path = (
                    Path(__file__).parent.parent.parent
                    / "config"
                    / "severity_defaults.yaml"
                )

            if not config_path.exists():
                return None

            # Calculate checksum
            with open(config_path, "rb") as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()

            # Get file modification time
            mtime = config_path.stat().st_mtime
            modified_date = datetime.fromtimestamp(mtime).isoformat()

            return {
                "config_file": str(config_path.resolve()),
                "config_checksum": f"sha256:{checksum[:16]}",
                "loaded_at": datetime.now().isoformat(),
                "modified_date": modified_date,
                "version": "1.0.0",
            }

        except Exception:
            # Non-fatal - just skip lineage if can't be determined
            return None

    def add_plausibility_templates(self, standard: dict[str, Any]) -> dict[str, Any]:
        """Add plausibility configuration templates to metadata.

        Args:
            standard: Standard to enhance

        Returns:
            Standard with plausibility templates
        """
        try:
            metadata = standard.setdefault("metadata", {})
            metadata["plausibility_templates"] = (
                self.dimension_builder.create_plausibility_templates()
            )
        except Exception:
            pass  # Non-fatal

        return standard

    def sanitize_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame to handle unhashable object types.

        Args:
            data: DataFrame to sanitize

        Returns:
            Sanitized DataFrame with JSON-serialized complex objects
        """
        df = data.copy()

        for col in df.columns:
            series = df[col]
            if series.dtype == object:
                try:
                    # Check for complex objects in sample
                    sample = series.dropna().head(50)
                    has_complex = sample.apply(
                        lambda v: isinstance(v, (dict, list, set))
                    ).any()

                    if has_complex:

                        def coerce_complex(v):
                            if isinstance(v, (dict, list)):
                                try:
                                    import json

                                    return json.dumps(v, sort_keys=True)
                                except Exception:
                                    return str(v)
                            elif isinstance(v, set):
                                try:
                                    return ",".join(sorted(map(str, v)))
                                except Exception:
                                    return str(v)
                            else:
                                return (
                                    v
                                    if v is None
                                    or isinstance(v, (str, int, float, bool))
                                    else str(v)
                                )

                        df[col] = series.apply(coerce_complex)

                except Exception:
                    # Last resort: stringify entire column
                    try:
                        df[col] = series.astype(str)
                    except Exception:
                        pass  # Give up on this column

        return df

    def validate_standard_structure(self, standard: dict[str, Any]) -> list[str]:
        """Validate the structure of a generated standard.

        Args:
            standard: Standard dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check top-level sections
        required_sections = ["standards", "requirements", "record_identification"]
        for section in required_sections:
            if section not in standard:
                errors.append(f"Missing required section: {section}")

        # Validate standards section
        if "standards" in standard:
            standards_section = standard["standards"]
            if not isinstance(standards_section, dict):
                errors.append("'standards' section must be a dictionary")
            else:
                required_fields = ["id", "name", "version", "authority"]
                for field in required_fields:
                    if field not in standards_section:
                        errors.append(f"Missing required field in standards: {field}")

        # Validate requirements section
        if "requirements" in standard:
            reqs = standard["requirements"]
            if not isinstance(reqs, dict):
                errors.append("'requirements' section must be a dictionary")
            else:
                if "overall_minimum" not in reqs:
                    errors.append("Missing 'overall_minimum' in requirements")
                if "field_requirements" not in reqs:
                    errors.append("Missing 'field_requirements' in requirements")
                if "dimension_requirements" not in reqs:
                    errors.append("Missing 'dimension_requirements' in requirements")

        # Validate record identification
        if "record_identification" in standard:
            record_id = standard["record_identification"]
            if not isinstance(record_id, dict):
                errors.append("'record_identification' section must be a dictionary")
            else:
                if "primary_key_fields" not in record_id:
                    errors.append(
                        "Missing 'primary_key_fields' in record_identification"
                    )

        # Validate dimension requirements if present
        if (
            "requirements" in standard
            and "dimension_requirements" in standard["requirements"]
        ):
            dim_reqs = standard["requirements"]["dimension_requirements"]
            dim_errors = self.dimension_builder.validate_dimension_requirements(
                dim_reqs
            )
            errors.extend(dim_errors)

        return errors

    def get_generation_summary(self, standard: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of the created standard.

        Args:
            standard: Generated standard to summarize

        Returns:
            Summary dictionary with key statistics
        """
        summary = {
            "standard_name": standard.get("standards", {}).get("name", "Unknown"),
            "standard_id": standard.get("standards", {}).get("id", "Unknown"),
            "total_fields": 0,
            "field_types": {},
            "dimension_count": 0,
            "primary_key_fields": [],
            "has_freshness": False,
            "generation_warnings": [],
        }

        try:
            # Field analysis
            field_reqs = standard.get("requirements", {}).get("field_requirements", {})
            if isinstance(field_reqs, dict):
                summary["total_fields"] = len(field_reqs)

                # Count field types
                type_counts = {}
                for field_config in field_reqs.values():
                    if isinstance(field_config, dict):
                        field_type = field_config.get("type", "unknown")
                        type_counts[field_type] = type_counts.get(field_type, 0) + 1
                summary["field_types"] = type_counts

            # Dimension analysis
            dim_reqs = standard.get("requirements", {}).get(
                "dimension_requirements", {}
            )
            if isinstance(dim_reqs, dict):
                summary["dimension_count"] = len(dim_reqs)

            # Primary key analysis
            record_id = standard.get("record_identification", {})
            if isinstance(record_id, dict):
                pk_fields = record_id.get("primary_key_fields", [])
                if isinstance(pk_fields, list):
                    summary["primary_key_fields"] = pk_fields

            # Freshness analysis
            metadata = standard.get("metadata", {})
            if isinstance(metadata, dict):
                has_freshness_config = "freshness" in metadata
                has_freshness_scaffolding = "freshness_scaffolding" in metadata
                summary["has_freshness"] = has_freshness_config

                if has_freshness_scaffolding:
                    summary["generation_warnings"].append(
                        "Freshness scaffolding provided for manual configuration"
                    )

            # Check for adjustments
            if isinstance(metadata, dict) and "explanations" in metadata:
                explanations = metadata["explanations"]
                if isinstance(explanations, dict):
                    adjusted_fields = [
                        field
                        for field, exp in explanations.items()
                        if isinstance(exp, dict) and "adjustments" in exp
                    ]
                    if adjusted_fields:
                        summary["generation_warnings"].append(
                            f"Training-pass adjustments made to {len(adjusted_fields)} fields"
                        )

        except Exception:
            summary["generation_warnings"].append("Error analyzing generated standard")

        return summary
