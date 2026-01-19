# @ADRI_FEATURE[validator_structure, scope=SHARED]
# Description: Structure validation for ADRI templates based on detected mode
"""
ADRI Structure Validation.

Validates ADRI template structure matches mode requirements:
- Checks required sections are present
- Checks optional sections are valid for mode
- Detects cross-mode contamination
- Provides helpful error messages
"""

from dataclasses import dataclass
from typing import Any

from .modes import ADRIMode, get_mode_sections


@dataclass
class StructureValidationResult:
    """Result of structure validation."""

    is_valid: bool
    mode: ADRIMode
    errors: list[str]
    warnings: list[str]

    def __bool__(self) -> bool:
        """Allow boolean evaluation."""
        return self.is_valid


def _get_nested_value(data: dict[str, Any], path: str) -> tuple[bool, Any]:
    """Get value from nested dictionary using dot notation.

    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., 'schema.context')

    Returns:
        Tuple of (found, value)
    """
    parts = path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return (False, None)

    return (True, current)


def _check_required_sections(
    adri_spec: dict[str, Any], required_sections: list[str]
) -> list[str]:
    """Check that required sections are present.

    Args:
        adri_spec: ADRI template specification
        required_sections: List of required section paths

    Returns:
        List of error messages for missing sections
    """
    errors = []

    for section_path in required_sections:
        found, _ = _get_nested_value(adri_spec, section_path)
        if not found:
            errors.append(f"Required section '{section_path}' is missing")

    return errors


def _check_optional_sections(
    adri_spec: dict[str, Any], optional_sections: list[str]
) -> list[str]:
    """Check that present sections are valid for mode.

    Args:
        adri_spec: ADRI template specification
        optional_sections: List of valid optional section paths

    Returns:
        List of warning messages for unexpected sections
    """
    warnings = []

    # Define ALL mode-specific section indicators
    all_mode_indicators = {
        "conversation": [
            "schema.context",
            "schema.required_outputs",
            "schema.can_modify",
        ],
        "reasoning": [
            "context_requirements",
            "field_requirements",
            "requirements.context_requirements",
            "requirements.field_requirements",
        ],
        "deterministic": ["input_requirements", "output_requirements"],
    }

    # Flatten to get all possible mode indicators
    all_indicators = set()
    for indicators in all_mode_indicators.values():
        all_indicators.update(indicators)

    # Check for indicators that are present but not valid for current mode
    for indicator in all_indicators:
        if indicator not in optional_sections:  # Not valid for current mode
            found, _ = _get_nested_value(adri_spec, indicator)
            if found:
                # Determine which mode this indicator belongs to
                indicator_mode = None
                for mode_name, indicators in all_mode_indicators.items():
                    if indicator in indicators:
                        indicator_mode = mode_name
                        break

                warnings.append(
                    f"Section '{indicator}' found but is for {indicator_mode} mode, "
                    f"not expected in this template"
                )

    return warnings


def validate_structure(
    adri_spec: dict[str, Any], mode: ADRIMode, strict: bool = False
) -> StructureValidationResult:
    """Validate ADRI template structure matches mode requirements.

    Args:
        adri_spec: ADRI template specification dictionary
        mode: Detected or expected mode
        strict: If True, warnings are treated as errors

    Returns:
        StructureValidationResult with validation outcome

    Example:
        >>> from .modes import detect_mode
        >>> template = {'schema': {'context': {...}}}
        >>> mode = detect_mode(template)
        >>> result = validate_structure(template, mode)
        >>> result.is_valid
        True
    """
    errors = []
    warnings = []

    # Get expected sections for mode
    sections = get_mode_sections(mode)
    required_sections = sections["required"]
    optional_sections = sections["optional"]

    # Combine required and optional to get all valid sections for this mode
    all_valid_sections = required_sections + optional_sections

    # Check required sections
    if required_sections:
        required_errors = _check_required_sections(adri_spec, required_sections)
        errors.extend(required_errors)

    # Check for cross-mode contamination (sections from other modes)
    if not strict:  # Only check in permissive mode
        section_warnings = _check_optional_sections(adri_spec, all_valid_sections)
        warnings.extend(section_warnings)

    # Mode-specific validation
    if mode == ADRIMode.CONVERSATION:
        # Validate conversation-specific requirements
        conv_errors, conv_warnings = _validate_conversation_structure(adri_spec)
        errors.extend(conv_errors)
        warnings.extend(conv_warnings)
    elif mode == ADRIMode.REASONING:
        # Validate reasoning-specific requirements
        reason_errors, reason_warnings = _validate_reasoning_structure(adri_spec)
        errors.extend(reason_errors)
        warnings.extend(reason_warnings)
    elif mode == ADRIMode.DETERMINISTIC:
        # Validate deterministic-specific requirements
        det_errors, det_warnings = _validate_deterministic_structure(adri_spec)
        errors.extend(det_errors)
        warnings.extend(det_warnings)

    # In strict mode, treat warnings as errors
    if strict and warnings:
        errors.extend(warnings)
        warnings = []

    is_valid = len(errors) == 0

    return StructureValidationResult(
        is_valid=is_valid, mode=mode, errors=errors, warnings=warnings
    )


def _validate_conversation_structure(
    adri_spec: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Validate conversation mode specific structure.

    Args:
        adri_spec: ADRI template specification

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check schema.context exists and is an object
    found, context = _get_nested_value(adri_spec, "schema.context")
    if found:
        if not isinstance(context, dict):
            errors.append("'schema.context' must be an object/dictionary")
        elif len(context) == 0:
            warnings.append("'schema.context' is empty - no context fields defined")

    # Check schema.required_outputs if present
    found, req_outputs = _get_nested_value(adri_spec, "schema.required_outputs")
    if found:
        if not isinstance(req_outputs, dict):
            errors.append("'schema.required_outputs' must be an object/dictionary")
        elif len(req_outputs) == 0:
            warnings.append(
                "'schema.required_outputs' is empty - no output fields defined"
            )

    # Check schema.can_modify if present
    found, can_modify = _get_nested_value(adri_spec, "schema.can_modify")
    if found:
        if not isinstance(can_modify, (bool, dict)):
            warnings.append(
                "'schema.can_modify' should be a boolean or object with 'type: boolean'"
            )

    return errors, warnings


def _validate_reasoning_structure(
    adri_spec: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Validate reasoning mode specific structure.

    Args:
        adri_spec: ADRI template specification

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check for at least one of context_requirements or field_requirements
    has_context = False
    has_fields = False

    # Check top-level
    if "context_requirements" in adri_spec:
        has_context = True
        if not isinstance(adri_spec["context_requirements"], dict):
            errors.append("'context_requirements' must be an object/dictionary")

    if "field_requirements" in adri_spec:
        has_fields = True
        if not isinstance(adri_spec["field_requirements"], dict):
            errors.append("'field_requirements' must be an object/dictionary")

    # Check inside requirements section (common pattern)
    if "requirements" in adri_spec and isinstance(adri_spec["requirements"], dict):
        req = adri_spec["requirements"]

        if "context_requirements" in req:
            has_context = True
            if not isinstance(req["context_requirements"], dict):
                errors.append(
                    "'requirements.context_requirements' must be an object/dictionary"
                )

        if "field_requirements" in req:
            has_fields = True
            if not isinstance(req["field_requirements"], dict):
                errors.append(
                    "'requirements.field_requirements' must be an object/dictionary"
                )

    # Warn if neither section present (though mode detection should catch this)
    if not has_context and not has_fields:
        warnings.append(
            "Reasoning mode template should have either 'context_requirements' "
            "or 'field_requirements' (or both)"
        )

    return errors, warnings


def _validate_deterministic_structure(
    adri_spec: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Validate deterministic mode specific structure.

    Args:
        adri_spec: ADRI template specification

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check for at least one of input_requirements or output_requirements
    has_input = False
    has_output = False

    if "input_requirements" in adri_spec:
        has_input = True
        if not isinstance(adri_spec["input_requirements"], dict):
            errors.append("'input_requirements' must be an object/dictionary")

    if "output_requirements" in adri_spec:
        has_output = True
        if not isinstance(adri_spec["output_requirements"], dict):
            errors.append("'output_requirements' must be an object/dictionary")

    # Warn if neither section present
    if not has_input and not has_output:
        warnings.append(
            "Deterministic mode template should have either 'input_requirements' "
            "or 'output_requirements' (or both)"
        )

    return errors, warnings


def format_validation_report(result: StructureValidationResult) -> str:
    """Format structure validation result as human-readable report.

    Args:
        result: Structure validation result

    Returns:
        Formatted report string
    """
    from .modes import get_mode_description

    lines = []
    lines.append("ADRI Structure Validation Report")
    lines.append(f"Mode: {result.mode.value}")
    lines.append(f"Description: {get_mode_description(result.mode)}")
    lines.append(f"Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
    lines.append("")

    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  ✗ {error}")
        lines.append("")

    if result.warnings:
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  ⚠ {warning}")
        lines.append("")

    if result.is_valid and not result.warnings:
        lines.append("✓ Template structure is valid for detected mode")

    return "\n".join(lines)


# @ADRI_FEATURE_END[validator_structure]
