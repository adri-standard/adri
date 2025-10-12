"""
Core validation engine for ADRI standard files.

This module provides comprehensive validation of ADRI standard files with
smart caching and thread-safe operation.
"""

import os
import threading
from typing import Any, Dict, Optional

from .exceptions import ValidationResult
from .schema import StandardSchema


class StandardValidator:
    """
    Thread-safe validator for ADRI standard files with intelligent caching.

    The validator performs comprehensive schema validation including:
    - Structure validation (required sections, fields)
    - Type validation (correct Python types)
    - Range validation (weights 0-5, scores 0-100)
    - Cross-field consistency checks

    Validation results are cached with mtime-based invalidation for performance.
    """

    def __init__(self):
        """Initialize the validator with empty cache and thread lock."""
        self._cache: Dict[str, tuple[ValidationResult, float]] = {}
        self._cache_lock = threading.RLock()

    def validate_standard(
        self,
        standard: Dict[str, Any],
        standard_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> ValidationResult:
        """
        Validate an ADRI standard with optional caching.

        Args:
            standard: Parsed standard dictionary
            standard_path: Optional path to standard file (for caching)
            use_cache: Whether to use cached results if available

        Returns:
            ValidationResult with errors and warnings

        Raises:
            SchemaValidationError: If standard is invalid and fail_fast is True
        """
        # Try cache if path provided and caching enabled
        if use_cache and standard_path:
            cached_result = self._get_cached_result(standard_path)
            if cached_result is not None:
                return cached_result

        # Perform validation
        result = ValidationResult(is_valid=True, standard_path=standard_path)

        # Validate top-level structure
        self._validate_structure(standard, result)

        # If structure is valid, validate contents
        if result.is_valid:
            self._validate_standards_section(standard, result)
            self._validate_requirements_section(standard, result)

        # Cache result if path provided
        if standard_path:
            self._cache_result(standard_path, result)

        return result

    def validate_standard_file(
        self, file_path: str, use_cache: bool = True
    ) -> ValidationResult:
        """
        Validate a standard file (loads and validates).

        Args:
            file_path: Path to standard YAML file
            use_cache: Whether to use cached results

        Returns:
            ValidationResult with errors and warnings
        """
        # Import here to avoid circular dependency
        from adri.validator.loaders import load_standard

        # Load the standard (this handles YAML syntax errors)
        try:
            standard = load_standard(file_path)
        except Exception as e:
            result = ValidationResult(is_valid=False, standard_path=file_path)
            result.add_error(
                message=f"Failed to load standard file: {str(e)}",
                path="<file>",
                suggestion="Check YAML syntax and file encoding",
            )
            return result

        # Validate the loaded standard
        return self.validate_standard(standard, file_path, use_cache)

    def _validate_structure(
        self, standard: Dict[str, Any], result: ValidationResult
    ) -> None:
        """
        Validate top-level structure of the standard.

        Args:
            standard: Standard dictionary
            result: ValidationResult to populate with errors
        """
        # Check basic type
        if not isinstance(standard, dict):
            result.add_error(
                message="Standard must be a dictionary/mapping",
                path="<root>",
                expected="dict",
                actual=type(standard).__name__,
            )
            return

        # Validate using schema
        errors = StandardSchema.validate_top_level_structure(standard)
        for error_msg in errors:
            result.add_error(message=error_msg, path="<root>")

    def _validate_standards_section(
        self, standard: Dict[str, Any], result: ValidationResult
    ) -> None:
        """
        Validate the 'standards' metadata section.

        Args:
            standard: Standard dictionary
            result: ValidationResult to populate with errors
        """
        if "standards" not in standard:
            return  # Already reported in structure validation

        standards_section = standard["standards"]

        # Validate type
        if not isinstance(standards_section, dict):
            result.add_error(
                message="'standards' section must be a dictionary",
                path="standards",
                expected="dict",
                actual=type(standards_section).__name__,
            )
            return

        # Get schema for standards section
        schema = StandardSchema.get_standards_section_schema()

        # Check required fields
        for field_name, field_schema in schema.items():
            if not field_schema.required:
                continue

            if field_name not in standards_section:
                result.add_error(
                    message=f"Missing required field: '{field_name}'",
                    path=f"standards.{field_name}",
                    suggestion=f"Add '{field_name}' field to standards section",
                )

        # Validate each field
        for field_name, value in standards_section.items():
            if field_name not in schema:
                result.add_warning(
                    message=f"Unknown field: '{field_name}'",
                    path=f"standards.{field_name}",
                    suggestion="This field is not part of the standard schema",
                )
                continue

            field_schema = schema[field_name]
            field_path = f"standards.{field_name}"

            # Type validation
            type_error = StandardSchema.validate_field_type(
                value, field_schema.field_type, field_path
            )
            if type_error:
                result.add_error(message=type_error, path=field_path)
                continue

            # Special validation for version
            if field_name == "version":
                version_error = StandardSchema.validate_version_string(value)
                if version_error:
                    result.add_error(
                        message=version_error,
                        path=field_path,
                        suggestion="Use semantic versioning format (e.g., '1.0.0')",
                    )

    def _validate_requirements_section(
        self, standard: Dict[str, Any], result: ValidationResult
    ) -> None:
        """
        Validate the 'requirements' section.

        Args:
            standard: Standard dictionary
            result: ValidationResult to populate with errors
        """
        if "requirements" not in standard:
            return  # Already reported in structure validation

        requirements = standard["requirements"]

        # Validate type
        if not isinstance(requirements, dict):
            result.add_error(
                message="'requirements' section must be a dictionary",
                path="requirements",
                expected="dict",
                actual=type(requirements).__name__,
            )
            return

        # Check required subsections
        for subsection in StandardSchema.REQUIREMENTS_REQUIRED_SUBSECTIONS:
            if subsection not in requirements:
                result.add_error(
                    message=f"Missing required subsection: '{subsection}'",
                    path=f"requirements.{subsection}",
                    suggestion=f"Add '{subsection}' to requirements section",
                )

        # Validate dimension_requirements
        if "dimension_requirements" in requirements:
            self._validate_dimension_requirements(
                requirements["dimension_requirements"], result
            )

        # Validate overall_minimum
        if "overall_minimum" in requirements:
            overall_min = requirements["overall_minimum"]
            error_msg = StandardSchema.validate_overall_minimum(overall_min)
            if error_msg:
                result.add_error(
                    message=error_msg,
                    path="requirements.overall_minimum",
                    expected="Number between 0 and 100",
                    actual=str(overall_min),
                    suggestion="Set overall_minimum to a value between 0 and 100",
                )

    def _validate_dimension_requirements(
        self, dimension_requirements: Any, result: ValidationResult
    ) -> None:
        """
        Validate dimension requirements subsection.

        Args:
            dimension_requirements: Dimension requirements dictionary
            result: ValidationResult to populate with errors
        """
        base_path = "requirements.dimension_requirements"

        # Validate type
        if not isinstance(dimension_requirements, dict):
            result.add_error(
                message="dimension_requirements must be a dictionary",
                path=base_path,
                expected="dict",
                actual=type(dimension_requirements).__name__,
            )
            return

        # Check that at least one dimension is specified
        if len(dimension_requirements) == 0:
            result.add_error(
                message="At least one dimension requirement must be specified",
                path=base_path,
                suggestion=f"Add at least one dimension from: {', '.join(sorted(StandardSchema.VALID_DIMENSIONS))}",
            )
            return

        # Validate each dimension
        for dimension_name, dimension_config in dimension_requirements.items():
            dimension_path = f"{base_path}.{dimension_name}"

            # Check if dimension name is valid
            if not StandardSchema.is_valid_dimension(dimension_name):
                result.add_error(
                    message=f"Invalid dimension name: '{dimension_name}'",
                    path=dimension_path,
                    expected=f"One of: {', '.join(sorted(StandardSchema.VALID_DIMENSIONS))}",
                    actual=dimension_name,
                    suggestion="Use a valid ADRI dimension name",
                )
                continue

            # Validate dimension configuration
            if not isinstance(dimension_config, dict):
                result.add_error(
                    message=f"Dimension '{dimension_name}' configuration must be a dictionary",
                    path=dimension_path,
                    expected="dict",
                    actual=type(dimension_config).__name__,
                )
                continue

            # Get dimension schema
            schema = StandardSchema.get_dimension_requirement_schema()

            # Check required fields
            for field_name, field_schema in schema.items():
                if not field_schema.required:
                    continue

                if field_name not in dimension_config:
                    result.add_error(
                        message=f"Missing required field: '{field_name}'",
                        path=f"{dimension_path}.{field_name}",
                        suggestion=f"Add '{field_name}' field to {dimension_name} dimension",
                    )

            # Validate each field in dimension config
            for field_name, value in dimension_config.items():
                field_path = f"{dimension_path}.{field_name}"

                if field_name not in schema:
                    result.add_warning(
                        message=f"Unknown field: '{field_name}'",
                        path=field_path,
                        suggestion="This field is not part of the dimension schema",
                    )
                    continue

                field_schema = schema[field_name]

                # Type validation
                type_error = StandardSchema.validate_field_type(
                    value, field_schema.field_type, field_path
                )
                if type_error:
                    result.add_error(message=type_error, path=field_path)
                    continue

                # Range validation for numeric fields
                if isinstance(value, (int, float)):
                    range_error = StandardSchema.validate_numeric_range(
                        value,
                        field_schema.min_value,
                        field_schema.max_value,
                        field_path,
                    )
                    if range_error:
                        result.add_error(
                            message=range_error,
                            path=field_path,
                            expected=f"Value between {field_schema.min_value} and {field_schema.max_value}",
                            actual=str(value),
                            suggestion=f"Set {field_name} to a value between {field_schema.min_value} and {field_schema.max_value}",
                        )

                # Validate field_requirements if present
                if field_name == "field_requirements" and isinstance(value, dict):
                    self._validate_field_requirements(
                        value, f"{dimension_path}.field_requirements", result
                    )

    def _validate_field_requirements(
        self,
        field_requirements: Dict[str, Any],
        base_path: str,
        result: ValidationResult,
    ) -> None:
        """
        Validate field-specific requirements.

        Args:
            field_requirements: Dictionary of field requirements
            base_path: Path prefix for error reporting
            result: ValidationResult to populate with errors
        """
        for field_name, requirements in field_requirements.items():
            field_path = f"{base_path}.{field_name}"

            if not isinstance(requirements, dict):
                result.add_warning(
                    message=f"Field requirements for '{field_name}' should be a dictionary",
                    path=field_path,
                )
                continue

            # Validate requirement rules
            for rule_name, rule_config in requirements.items():
                rule_path = f"{field_path}.{rule_name}"

                # Basic structure check
                if rule_name not in StandardSchema.VALID_RULE_TYPES:
                    result.add_warning(
                        message=f"Unknown rule type: '{rule_name}'",
                        path=rule_path,
                        suggestion=f"Valid rule types: {', '.join(sorted(StandardSchema.VALID_RULE_TYPES))}",
                    )

    def _get_cached_result(self, file_path: str) -> Optional[ValidationResult]:
        """
        Get cached validation result if valid.

        Args:
            file_path: Path to standard file

        Returns:
            Cached ValidationResult if valid, None otherwise
        """
        with self._cache_lock:
            if file_path not in self._cache:
                return None

            cached_result, cached_mtime = self._cache[file_path]

            # Check if cache is still valid
            if self._is_cache_valid(file_path, cached_mtime):
                return cached_result
            else:
                # Remove stale cache entry
                del self._cache[file_path]
                return None

    def _cache_result(self, file_path: str, result: ValidationResult) -> None:
        """
        Cache a validation result.

        Args:
            file_path: Path to standard file
            result: ValidationResult to cache
        """
        try:
            mtime = os.path.getmtime(file_path)
            with self._cache_lock:
                self._cache[file_path] = (result, mtime)
        except OSError:
            # If we can't get mtime, don't cache
            pass

    def _is_cache_valid(self, file_path: str, cached_mtime: float) -> bool:
        """
        Check if cached result is still valid.

        Args:
            file_path: Path to standard file
            cached_mtime: Cached modification time

        Returns:
            True if cache is valid, False otherwise
        """
        try:
            current_mtime = os.path.getmtime(file_path)
            return current_mtime == cached_mtime
        except OSError:
            # If file doesn't exist or can't be accessed, cache is invalid
            return False

    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """
        Clear validation cache.

        Args:
            file_path: Optional specific file to clear. If None, clears all cache.
        """
        with self._cache_lock:
            if file_path is None:
                self._cache.clear()
            elif file_path in self._cache:
                del self._cache[file_path]

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            return {
                "cached_files": len(self._cache),
                "file_paths": list(self._cache.keys()),
            }


# Global singleton instance
_validator_instance: Optional[StandardValidator] = None
_instance_lock = threading.Lock()


def get_validator() -> StandardValidator:
    """
    Get the global StandardValidator instance (singleton pattern).

    Returns:
        StandardValidator instance
    """
    global _validator_instance

    if _validator_instance is None:
        with _instance_lock:
            # Double-check locking pattern
            if _validator_instance is None:
                _validator_instance = StandardValidator()

    return _validator_instance
