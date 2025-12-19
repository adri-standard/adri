"""Data Contract Compliance Validation - Schema Validation Module.

This module provides contract compliance validation to detect when data field names
don't match the standard's field_requirements keys (contract terms), preventing
silent failures where validation rules don't execute.

ADRI standards represent data contracts - formal agreements between data providers
and the system. This module validates that incoming data complies with the contract
schema before quality assessment begins.

Contract Compliance Checks:
- Field names match contract terms exactly (case-sensitive)
- Required fields are present in data
- Data structure fulfills contract obligations

This is a fundamental property of ADRI - always runs, not configurable.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import pandas as pd


class SchemaWarningType(str, Enum):
    """Types of schema validation warnings."""

    FIELD_CASE_MISMATCH = "FIELD_CASE_MISMATCH"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    UNEXPECTED_FIELDS = "UNEXPECTED_FIELDS"
    NO_MATCHING_FIELDS = "NO_MATCHING_FIELDS"


class SchemaWarningSeverity(str, Enum):
    """Severity levels for schema warnings."""

    CRITICAL = "CRITICAL"  # Blocks validation completely
    ERROR = "ERROR"  # Prevents rules from running
    WARNING = "WARNING"  # Informational only


@dataclass
class SchemaWarning:
    """Represents a schema validation warning."""

    type: SchemaWarningType
    severity: SchemaWarningSeverity
    message: str
    affected_fields: List[str]
    remediation: str
    auto_fix_available: bool = False
    case_insensitive_matches: Optional[Dict[str, str]] = None


@dataclass
class SchemaValidationResult:
    """Result of schema validation before assessment."""

    exact_matches: int
    case_insensitive_matches: int
    total_standard_fields: int
    total_data_fields: int
    match_percentage: float
    warnings: List[SchemaWarning] = field(default_factory=list)
    matched_fields: Set[str] = field(default_factory=set)
    unmatched_standard_fields: Set[str] = field(default_factory=set)
    unmatched_data_fields: Set[str] = field(default_factory=set)

    def has_critical_issues(self) -> bool:
        """Check if there are critical schema issues."""
        return any(w.severity == SchemaWarningSeverity.CRITICAL for w in self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "exact_matches": self.exact_matches,
            "case_insensitive_matches": self.case_insensitive_matches,
            "total_standard_fields": self.total_standard_fields,
            "total_data_fields": self.total_data_fields,
            "match_percentage": self.match_percentage,
            "warnings": [
                {
                    "type": w.type.value,
                    "severity": w.severity.value,
                    "message": w.message,
                    "affected_fields": w.affected_fields[:10],  # Limit for logging
                    "remediation": w.remediation,
                    "auto_fix_available": w.auto_fix_available,
                    "case_insensitive_matches": w.case_insensitive_matches,
                }
                for w in self.warnings
            ],
            "matched_fields": list(self.matched_fields)[:10],
            "unmatched_standard_fields": list(self.unmatched_standard_fields)[:10],
            "unmatched_data_fields": list(self.unmatched_data_fields)[:10],
        }


def validate_schema_compatibility(
    data: pd.DataFrame, field_requirements: Dict[str, Any], strict_mode: bool = False
) -> SchemaValidationResult:
    """Validate data contract compliance - check if data fulfills contract schema.

    Compares data column names to standard field_requirements keys (contract terms)
    to detect exact matches, case-insensitive matches, and contract breaches.
    Generates warnings with remediation suggestions for non-compliance.

    This is a prerequisite check that runs before quality validation. If field names
    don't match the contract, quality rules cannot execute meaningfully.

    Args:
        data: DataFrame with data to validate against contract
        field_requirements: Dictionary of contract field requirements (terms)
        strict_mode: If True, escalate ERROR to CRITICAL severity

    Returns:
        SchemaValidationResult with contract compliance statistics and warnings
    """
    # Get field names
    data_fields = set(data.columns)
    standard_fields = set(field_requirements.keys())

    # Find exact matches
    exact_matches = data_fields & standard_fields

    # Find case-insensitive matches (excluding exact matches)
    case_matches = _find_case_insensitive_matches(
        data_fields - exact_matches, standard_fields - exact_matches
    )

    # Calculate statistics
    total_matches = len(exact_matches)
    case_insensitive_count = len(case_matches)
    match_percentage = (
        (total_matches / len(standard_fields) * 100) if standard_fields else 100.0
    )

    # Find unmatched fields
    unmatched_standard = standard_fields - exact_matches - set(case_matches.values())
    unmatched_data = data_fields - exact_matches - set(case_matches.keys())

    # Generate warnings
    warnings = _generate_schema_warnings(
        exact_matches=total_matches,
        case_matches=case_matches,
        data_fields=data_fields,
        standard_fields=standard_fields,
        unmatched_standard=unmatched_standard,
        unmatched_data=unmatched_data,
        strict_mode=strict_mode,
    )

    return SchemaValidationResult(
        exact_matches=total_matches,
        case_insensitive_matches=case_insensitive_count,
        total_standard_fields=len(standard_fields),
        total_data_fields=len(data_fields),
        match_percentage=match_percentage,
        warnings=warnings,
        matched_fields=exact_matches,
        unmatched_standard_fields=unmatched_standard,
        unmatched_data_fields=unmatched_data,
    )


def _find_case_insensitive_matches(
    data_fields: Set[str], standard_fields: Set[str]
) -> Dict[str, str]:
    """Find case-insensitive matches between field names.

    Args:
        data_fields: Set of data column names
        standard_fields: Set of standard field names

    Returns:
        Dictionary mapping data_field -> standard_field for case-insensitive matches
    """
    matches = {}

    # Create lowercase lookup for standard fields
    standard_lower = {f.lower(): f for f in standard_fields}

    for data_field in data_fields:
        data_lower = data_field.lower()
        if data_lower in standard_lower:
            matches[data_field] = standard_lower[data_lower]

    return matches


def _generate_schema_warnings(
    exact_matches: int,
    case_matches: Dict[str, str],
    data_fields: Set[str],
    standard_fields: Set[str],
    unmatched_standard: Set[str],
    unmatched_data: Set[str],
    strict_mode: bool = False,
) -> List[SchemaWarning]:
    """Generate appropriate warnings based on matching results.

    Args:
        exact_matches: Number of exact field name matches
        case_matches: Dictionary of case-insensitive matches
        data_fields: Set of data column names
        standard_fields: Set of standard field names
        unmatched_standard: Standard fields not found in data
        unmatched_data: Data fields not in standard
        strict_mode: If True, escalate warning severity

    Returns:
        List of SchemaWarning objects
    """
    warnings = []

    # CRITICAL: No matching fields at all
    if exact_matches == 0 and not case_matches:
        warnings.append(
            SchemaWarning(
                type=SchemaWarningType.NO_MATCHING_FIELDS,
                severity=SchemaWarningSeverity.CRITICAL,
                message=(
                    f"No matching fields found between data and standard. "
                    f"Data has {len(data_fields)} fields, standard expects {len(standard_fields)} fields. "
                    f"Validation rules will not execute."
                ),
                affected_fields=list(data_fields)[:10],
                remediation=(
                    "Field names must match exactly (case-sensitive). "
                    "Check that your data column names match the standard field names. "
                    "Review the standard's field_requirements section for expected field names."
                ),
                auto_fix_available=False,
            )
        )
        return warnings  # No point in further warnings if nothing matches

    # ERROR: Case mismatch detected - rules won't execute but could be fixed
    if case_matches:
        sample_mismatches = list(case_matches.items())[:5]

        warnings.append(
            SchemaWarning(
                type=SchemaWarningType.FIELD_CASE_MISMATCH,
                severity=(
                    SchemaWarningSeverity.ERROR
                    if not strict_mode
                    else SchemaWarningSeverity.CRITICAL
                ),
                message=(
                    f"Found {len(case_matches)} field(s) with case mismatch. "
                    f"These fields exist in data but don't match standard case exactly. "
                    f"Validation rules will not execute for these fields."
                ),
                affected_fields=list(case_matches.keys())[:10],
                remediation=(
                    "Rename the following fields to match standard case:\n"
                    + "\n".join(
                        f"  • {data} → {std}" for data, std in sample_mismatches
                    )
                ),
                auto_fix_available=True,
                case_insensitive_matches=case_matches,
            )
        )

    # WARNING: Missing required fields from standard
    if unmatched_standard:
        # Determine if these are truly required or optional
        warnings.append(
            SchemaWarning(
                type=SchemaWarningType.MISSING_REQUIRED_FIELDS,
                severity=SchemaWarningSeverity.WARNING,
                message=(
                    f"Data is missing {len(unmatched_standard)} field(s) defined in standard. "
                    f"Validation rules for these fields will be skipped."
                ),
                affected_fields=list(unmatched_standard)[:10],
                remediation=(
                    "Consider adding the following fields to your data:\n"
                    + "\n".join(
                        f"  • {f}" for f in sorted(list(unmatched_standard)[:10])
                    )
                ),
                auto_fix_available=False,
            )
        )

    # WARNING: Unexpected fields in data
    if unmatched_data:
        warnings.append(
            SchemaWarning(
                type=SchemaWarningType.UNEXPECTED_FIELDS,
                severity=SchemaWarningSeverity.WARNING,
                message=(
                    f"Data contains {len(unmatched_data)} field(s) not defined in standard. "
                    f"These fields will be ignored during validation."
                ),
                affected_fields=list(unmatched_data)[:10],
                remediation=(
                    "The following fields are not in the standard and will be ignored:\n"
                    + "\n".join(f"  • {f}" for f in sorted(list(unmatched_data)[:10]))
                ),
                auto_fix_available=False,
            )
        )

    return warnings


# ADRI v2.0 Field Category Validation

VALID_FIELD_CATEGORIES = {"ai_decision", "ai_narrative", "standard"}
VALID_DERIVATION_STRATEGIES = {
    "ordered_precedence",
    "explicit_lookup",
    "direct_mapping",
    "calculated",
}


class FieldSpecValidationError(Exception):
    """Raised when a field specification has invalid ADRI v2.0 properties."""

    pass


def validate_field_spec_v2(field_name: str, field_spec: Dict[str, Any]) -> List[str]:
    """Validate ADRI v2.0 field specification properties.

    Validates the optional v2.0 properties: field_category, derivation, reasoning_guidance.
    These are metadata properties that don't affect how data is validated, but must be
    well-formed if present.

    Args:
        field_name: Name of the field
        field_spec: Field specification dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate field_category if present
    if "field_category" in field_spec:
        category = field_spec["field_category"]
        if category not in VALID_FIELD_CATEGORIES:
            errors.append(
                f"Field '{field_name}': invalid field_category '{category}'. "
                f"Must be one of: {', '.join(sorted(VALID_FIELD_CATEGORIES))}"
            )

    # Validate derivation if present
    if "derivation" in field_spec:
        derivation = field_spec["derivation"]

        if not isinstance(derivation, dict):
            errors.append(
                f"Field '{field_name}': derivation must be an object/dictionary"
            )
        else:
            # Check strategy is present
            if "strategy" not in derivation:
                errors.append(
                    f"Field '{field_name}': derivation must have 'strategy' property"
                )
            else:
                strategy = derivation["strategy"]
                if strategy not in VALID_DERIVATION_STRATEGIES:
                    errors.append(
                        f"Field '{field_name}': invalid derivation strategy '{strategy}'. "
                        f"Must be one of: {', '.join(sorted(VALID_DERIVATION_STRATEGIES))}"
                    )
                else:
                    # Validate strategy-specific structure
                    strategy_errors = _validate_derivation_strategy(
                        field_name, derivation, strategy
                    )
                    errors.extend(strategy_errors)

    # Validate reasoning_guidance if present
    if "reasoning_guidance" in field_spec:
        guidance = field_spec["reasoning_guidance"]
        if not isinstance(guidance, str):
            errors.append(f"Field '{field_name}': reasoning_guidance must be a string")

    return errors


def _validate_derivation_strategy(
    field_name: str, derivation: Dict, strategy: str
) -> List[str]:
    """Validate strategy-specific derivation structure.

    Args:
        field_name: Name of the field
        derivation: Derivation specification
        strategy: Strategy name

    Returns:
        List of validation error messages
    """
    errors = []

    if strategy == "ordered_precedence":
        # Must have inputs and rules
        if "inputs" not in derivation:
            errors.append(
                f"Field '{field_name}': ordered_precedence strategy requires 'inputs' array"
            )
        elif not isinstance(derivation["inputs"], list):
            errors.append(f"Field '{field_name}': 'inputs' must be an array")

        if "rules" not in derivation:
            errors.append(
                f"Field '{field_name}': ordered_precedence strategy requires 'rules' array"
            )
        elif not isinstance(derivation["rules"], list):
            errors.append(f"Field '{field_name}': 'rules' must be an array")
        elif not derivation["rules"]:
            errors.append(f"Field '{field_name}': 'rules' array cannot be empty")

    elif strategy == "explicit_lookup":
        # Must have inputs and lookup_table
        if "inputs" not in derivation:
            errors.append(
                f"Field '{field_name}': explicit_lookup strategy requires 'inputs' array"
            )
        elif not isinstance(derivation["inputs"], list):
            errors.append(f"Field '{field_name}': 'inputs' must be an array")

        if "lookup_table" not in derivation:
            errors.append(
                f"Field '{field_name}': explicit_lookup strategy requires 'lookup_table' array"
            )
        elif not isinstance(derivation["lookup_table"], list):
            errors.append(f"Field '{field_name}': 'lookup_table' must be an array")
        elif not derivation["lookup_table"]:
            errors.append(f"Field '{field_name}': 'lookup_table' array cannot be empty")

    elif strategy == "direct_mapping":
        # Must have source_field and mappings
        if "source_field" not in derivation:
            errors.append(
                f"Field '{field_name}': direct_mapping strategy requires 'source_field' string"
            )
        elif not isinstance(derivation["source_field"], str):
            errors.append(f"Field '{field_name}': 'source_field' must be a string")

        if "mappings" not in derivation:
            errors.append(
                f"Field '{field_name}': direct_mapping strategy requires 'mappings' object"
            )
        elif not isinstance(derivation["mappings"], dict):
            errors.append(
                f"Field '{field_name}': 'mappings' must be an object/dictionary"
            )
        elif not derivation["mappings"]:
            errors.append(f"Field '{field_name}': 'mappings' object cannot be empty")

    elif strategy == "calculated":
        # Must have formula and variables
        if "formula" not in derivation:
            errors.append(
                f"Field '{field_name}': calculated strategy requires 'formula' string"
            )
        elif not isinstance(derivation["formula"], str):
            errors.append(f"Field '{field_name}': 'formula' must be a string")

        if "variables" not in derivation:
            errors.append(
                f"Field '{field_name}': calculated strategy requires 'variables' object"
            )
        elif not isinstance(derivation["variables"], dict):
            errors.append(
                f"Field '{field_name}': 'variables' must be an object/dictionary"
            )

    return errors


def validate_standard_schema_v2(
    field_requirements: Dict[str, Any],
) -> Dict[str, List[str]]:
    """Validate all field specifications in a standard for ADRI v2.0 compliance.

    This validates the standard's schema itself (the contract definition), not the data.
    Checks that any ADRI v2.0 properties (field_category, derivation, reasoning_guidance)
    are well-formed if present.

    Args:
        field_requirements: Dictionary of field specifications from standard

    Returns:
        Dictionary mapping field_name -> list of error messages (empty dict if all valid)
    """
    all_errors = {}

    for field_name, field_spec in field_requirements.items():
        if not isinstance(field_spec, dict):
            all_errors[field_name] = [
                "Field specification must be an object/dictionary"
            ]
            continue

        errors = validate_field_spec_v2(field_name, field_spec)
        if errors:
            all_errors[field_name] = errors

    return all_errors


def _extract_field_requirements(standard: Dict[str, Any]) -> Dict[str, Any]:
    """Extract field_requirements from reasoning/deterministic mode standard.

    Handles multiple format variations:
    - Format 1: requirements.field_requirements
    - Format 2: field_requirements at top level
    - Format 3: requirements.output_requirements (deterministic mode)
    - Format 4: output_requirements at top level (deterministic mode)

    Args:
        standard: Complete ADRI standard dictionary

    Returns:
        Dictionary of field requirements, or empty dict if not found
    """
    # Format 1: requirements.field_requirements
    if "requirements" in standard:
        reqs = standard["requirements"]
        if isinstance(reqs, dict) and "field_requirements" in reqs:
            return reqs["field_requirements"]

    # Format 2: field_requirements at top level
    if "field_requirements" in standard:
        return standard["field_requirements"]

    # Format 3: requirements.output_requirements (deterministic mode)
    if "requirements" in standard:
        reqs = standard["requirements"]
        if isinstance(reqs, dict) and "output_requirements" in reqs:
            return reqs["output_requirements"]

    # Format 4: output_requirements at top level
    if "output_requirements" in standard:
        return standard["output_requirements"]

    return {}


def validate_conversation_structure(schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate conversation mode schema structure.

    Checks required conversation mode sections per ADR-008:
    - schema.context (required) - INPUT data field definitions for Q&A
    - schema.can_modify (required) - BEHAVIOR field definition
    - schema.required_outputs (optional) - OUTPUT data field definitions

    Note: In conversation mode standards, these are field DEFINITIONS (schema),
    not actual data values. For example, can_modify is defined as:
      can_modify:
        type: boolean
        required: true

    Args:
        schema: The 'schema' section from conversation mode standard

    Returns:
        Dictionary mapping section_name -> list of error messages
        Empty dict if valid

    Example:
        >>> schema = {
        ...     'context': {'title': {'type': 'string', 'required': True}},
        ...     'can_modify': {'type': 'boolean', 'required': True}
        ... }
        >>> errors = validate_conversation_structure(schema)
        >>> assert not errors  # Valid structure
    """
    errors = {}

    # Check required: schema.context (field definitions for input data)
    if "context" not in schema:
        errors["schema"] = ["Conversation mode requires 'context' section"]
    elif not isinstance(schema["context"], dict):
        errors["schema.context"] = ["Must be an object/dictionary"]
    elif not schema["context"]:
        errors["schema.context"] = ["Cannot be empty - must define input data fields"]

    # Check required: schema.can_modify (field definition for behavior)
    if "can_modify" not in schema:
        if "schema" in errors:
            errors["schema"].append(
                "Conversation mode requires 'can_modify' field definition"
            )
        else:
            errors["schema"] = [
                "Conversation mode requires 'can_modify' field definition"
            ]
    elif not isinstance(schema["can_modify"], dict):
        errors["schema.can_modify"] = ["Must be a field definition (object/dictionary)"]
    else:
        # Validate can_modify field definition structure
        can_modify_def = schema["can_modify"]
        if "type" not in can_modify_def:
            errors["schema.can_modify"] = ["Field definition must have 'type' property"]
        elif can_modify_def.get("type") != "boolean":
            errors["schema.can_modify"] = [
                f"Field type must be 'boolean', got '{can_modify_def.get('type')}'"
            ]

    # Check optional: schema.required_outputs (field definitions for output data)
    if "required_outputs" in schema:
        if not isinstance(schema["required_outputs"], dict):
            errors["schema.required_outputs"] = [
                "Must be an object/dictionary if present"
            ]

    return errors


def validate_standard(standard: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate any ADRI standard regardless of mode.

    Auto-detects mode and applies appropriate validation:
    - REASONING/DETERMINISTIC: Validates field_requirements structure
    - CONVERSATION: Validates schema.context/can_modify/required_outputs
    - NONE: Returns error for incomplete standard

    This is the unified validation API that all ADRI Enterprise consumers
    should use. It handles mode detection internally and returns consistent
    error format for all modes.

    Args:
        standard: Complete ADRI standard dictionary

    Returns:
        Dictionary mapping section_name -> list of error messages
        Empty dict if all valid

    Example:
        >>> # Works for conversation mode
        >>> standard = yaml.safe_load(open('ADRI_conv_approval_in.yaml'))
        >>> errors = validate_standard(standard)
        >>> if errors:
        ...     print(f"Validation failed: {errors}")

        >>> # Works for reasoning mode
        >>> standard = yaml.safe_load(open('ADRI_rsn_example_sentiment_out.yaml'))
        >>> errors = validate_standard(standard)
        >>> if errors:
        ...     print(f"Validation failed: {errors}")
    """
    from adri.validator.modes import detect_mode, ADRIMode

    mode = detect_mode(standard)

    if mode == ADRIMode.CONVERSATION:
        # Validate conversation mode structure
        schema = standard.get("schema", {})
        return validate_conversation_structure(schema)

    elif mode in [ADRIMode.REASONING, ADRIMode.DETERMINISTIC]:
        # Validate field_requirements structure
        field_reqs = _extract_field_requirements(standard)
        if not field_reqs:
            return {
                "_standard": [
                    f"Missing field_requirements section for {mode.value} mode. "
                    "Expected 'field_requirements' or 'output_requirements' section."
                ]
            }
        return validate_standard_schema_v2(field_reqs)

    else:  # ADRIMode.NONE
        return {
            "_standard": [
                "Invalid or incomplete standard - no mode-specific sections found. "
                "Expected one of: 'schema.context' (conversation), "
                "'field_requirements' (reasoning), or 'output_requirements' (deterministic)."
            ]
        }


class SchemaValidator:
    """Data contract compliance validator for ADRI assessments.

    Validates that incoming data complies with the data contract (standard)
    schema before quality assessment begins. This ensures validation rules
    can execute properly by confirming field names match contract terms.
    """

    def __init__(self, strict_mode: bool = False):
        """Initialize contract compliance validator.

        Args:
            strict_mode: If True, escalate ERROR (case mismatch) to CRITICAL
        """
        self.strict_mode = strict_mode

    def validate(
        self, data: pd.DataFrame, field_requirements: Dict[str, Any]
    ) -> SchemaValidationResult:
        """Validate data contract compliance.

        Args:
            data: DataFrame to validate against contract
            field_requirements: Contract field requirements (terms)

        Returns:
            SchemaValidationResult with compliance details and warnings
        """
        return validate_schema_compatibility(data, field_requirements, self.strict_mode)

    def format_warning_message(self, warning: SchemaWarning) -> str:
        """Format a schema warning for display.

        Args:
            warning: SchemaWarning to format

        Returns:
            Formatted warning message
        """
        lines = [
            f"[{warning.severity.value}] {warning.type.value}",
            f"{warning.message}",
            "",
            "Remediation:",
            warning.remediation,
        ]

        if warning.auto_fix_available:
            lines.extend(["", "Note: Auto-fix suggestions available for this issue."])

        return "\n".join(lines)

    def suggest_auto_fix(self, warning: SchemaWarning) -> Optional[str]:
        """Generate auto-fix suggestion for a warning.

        Args:
            warning: SchemaWarning to generate fix for

        Returns:
            Auto-fix code suggestion or None if not available
        """
        if not warning.auto_fix_available:
            return None

        if (
            warning.type == SchemaWarningType.FIELD_CASE_MISMATCH
            and warning.case_insensitive_matches
        ):
            rename_dict = {
                data: std for data, std in warning.case_insensitive_matches.items()
            }
            return (
                "# Auto-fix suggestion: Rename columns to match standard case\n"
                f"data = data.rename(columns={rename_dict})\n"
            )

        return None
