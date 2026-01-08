# @ADRI_FEATURE[validator_modes, scope=SHARED]
# Description: Mode detection system for ADRI templates (reasoning, conversation, deterministic)
"""
ADRI Mode Detection System.

Provides automatic detection of ADRI template modes based on their structure:
- REASONING: AI-driven analysis with context_requirements/field_requirements
- CONVERSATION: Interactive dialogues with schema.context/required_outputs
- DETERMINISTIC: Structured transformations with input_requirements/output_requirements
- NONE: Generic templates without mode-specific sections
"""

from enum import Enum
from typing import Any


class ADRIMode(Enum):
    """ADRI template modes for different validation contexts."""

    REASONING = "reasoning"
    CONVERSATION = "conversation"
    DETERMINISTIC = "deterministic"
    NONE = "none"

    @classmethod
    def from_string(cls, mode_str: str) -> "ADRIMode":
        """Convert string to ADRIMode enum.

        Args:
            mode_str: Mode string (case-insensitive)

        Returns:
            ADRIMode enum value

        Raises:
            ValueError: If mode string is invalid
        """
        mode_str = mode_str.lower()
        for mode in cls:
            if mode.value == mode_str:
                return mode
        raise ValueError(
            f"Invalid mode: {mode_str}. Valid modes: {[m.value for m in cls]}"
        )


def detect_mode(adri_spec: dict[str, Any]) -> ADRIMode:
    """Auto-detect ADRI template mode from structure.

    Detection rules (in priority order):
    1. Conversation: Has 'schema.context' section
    2. Deterministic: Has 'input_requirements' or 'output_requirements'
    3. Reasoning: Has 'context_requirements' or 'field_requirements'
    4. None: No mode-specific sections present

    Args:
        adri_spec: ADRI template specification dictionary

    Returns:
        Detected ADRIMode

    Example:
        >>> template = {'schema': {'context': {...}}}
        >>> detect_mode(template)
        ADRIMode.CONVERSATION
    """
    if not isinstance(adri_spec, dict):
        return ADRIMode.NONE

    # Check for conversation mode indicators
    if "schema" in adri_spec:
        schema = adri_spec["schema"]
        if isinstance(schema, dict) and "context" in schema:
            return ADRIMode.CONVERSATION

    # Check for deterministic mode indicators (top level)
    if "input_requirements" in adri_spec or "output_requirements" in adri_spec:
        return ADRIMode.DETERMINISTIC

    # Check for reasoning mode indicators (top level)
    if "context_requirements" in adri_spec or "field_requirements" in adri_spec:
        return ADRIMode.REASONING

    # Check inside requirements section (common nested pattern)
    if "requirements" in adri_spec:
        requirements = adri_spec["requirements"]
        if isinstance(requirements, dict):
            # Check for deterministic mode in requirements section
            if (
                "input_requirements" in requirements
                or "output_requirements" in requirements
            ):
                return ADRIMode.DETERMINISTIC
            # Check for reasoning mode in requirements section
            if (
                "context_requirements" in requirements
                or "field_requirements" in requirements
            ):
                return ADRIMode.REASONING

    # No mode-specific sections found
    return ADRIMode.NONE


def get_mode_description(mode: ADRIMode) -> str:
    """Get human-readable description of mode.

    Args:
        mode: ADRIMode to describe

    Returns:
        Description string
    """
    descriptions = {
        ADRIMode.REASONING: "Reasoning mode for AI-driven analysis and decision-making",
        ADRIMode.CONVERSATION: "Conversation mode for interactive user dialogues",
        ADRIMode.DETERMINISTIC: "Deterministic mode for structured data transformations",
        ADRIMode.NONE: "Generic template without mode-specific sections",
    }
    return descriptions.get(mode, "Unknown mode")


def get_mode_sections(mode: ADRIMode) -> dict[str, list[str]]:
    """Get expected sections for a mode.

    Args:
        mode: ADRIMode to get sections for

    Returns:
        Dictionary with 'required' and 'optional' section lists

    Example:
        >>> get_mode_sections(ADRIMode.CONVERSATION)
        {'required': ['schema.context'], 'optional': ['schema.required_outputs', 'schema.can_modify']}
    """
    sections = {
        ADRIMode.CONVERSATION: {
            "required": ["schema.context"],
            "optional": ["schema.required_outputs", "schema.can_modify"],
        },
        ADRIMode.REASONING: {
            "required": [],
            "optional": [
                "context_requirements",
                "field_requirements",
                "requirements.context_requirements",
                "requirements.field_requirements",
            ],
        },
        ADRIMode.DETERMINISTIC: {
            "required": [],
            "optional": ["input_requirements", "output_requirements"],
        },
        ADRIMode.NONE: {"required": [], "optional": []},
    }
    return sections.get(mode, {"required": [], "optional": []})


def is_valid_mode_transition(from_mode: ADRIMode, to_mode: ADRIMode) -> bool:
    """Check if mode transition is valid.

    Used when expected_mode is provided to validator to check if
    auto-detected mode matches expectation.

    Args:
        from_mode: Auto-detected mode
        to_mode: Expected mode

    Returns:
        True if transition is allowed

    Example:
        >>> is_valid_mode_transition(ADRIMode.CONVERSATION, ADRIMode.CONVERSATION)
        True
        >>> is_valid_mode_transition(ADRIMode.REASONING, ADRIMode.CONVERSATION)
        False
    """
    # Exact match always valid
    if from_mode == to_mode:
        return True

    # NONE mode can be considered valid for any expected mode (permissive)
    if from_mode == ADRIMode.NONE:
        return True

    # All other transitions are invalid (strict mode checking)
    return False


# @ADRI_FEATURE_END[validator_modes]
