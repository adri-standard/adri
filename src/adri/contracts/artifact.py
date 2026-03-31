"""
Artifact declaration types and validation for ADRI contracts.

This module defines the ArtifactDeclaration dataclass and validation functions
for the optional artifact_declaration / artifact_declarations section in ADRI
contracts. This enables protocol compatibility with A2UI, MCP, WebMCP, and A2A
by declaring what validated data outputs are FOR — reports, UI components,
dataset pushes, notifications, etc.

See RFC Discussion #100 and Feature Issue #101 on adri-standard/adri.

New in v7.3.0.
"""

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Core artifact types (7 types)
VALID_ARTIFACT_TYPES: set[str] = {
    "report",  # Analysis or summary document
    "ui_component",  # Interactive UI element (A2UI-compatible)
    "dataset_push",  # Data to be written to external store
    "notification",  # Alert or status update
    "config_update",  # Configuration change
    "scaffold",  # Generated code/template artifact
    "certification_evidence",  # Certification run results with convergence data
}

# Extension prefix for platform-specific custom types
CUSTOM_TYPE_PREFIX: str = "x-custom-"

# Valid render hint formats
VALID_RENDER_FORMATS: set[str] = {"markdown", "json", "html", "a2ui_json", "text"}

# Valid lifecycle values
VALID_LIFECYCLES: set[str] = {"ephemeral", "persistent"}

# Default lifecycle value
DEFAULT_LIFECYCLE: str = "ephemeral"

# Section key names used in contracts
ARTIFACT_DECLARATION_KEY: str = "artifact_declaration"
ARTIFACT_DECLARATIONS_KEY: str = "artifact_declarations"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ArtifactDeclaration:
    """
    Represents a single artifact declaration in an ADRI contract.

    Declares what kind of actionable artifact the validated output represents
    and how it should be rendered/consumed by downstream platforms.

    Attributes:
        type: Artifact type — one of 7 core types or x-custom-* extension.
        render_hints: Dictionary of rendering hints (format required, others optional).
        channel_compatibility: Optional list of compatible rendering channels.
        lifecycle: "ephemeral" (run-scoped, default) or "persistent" (outlives run).
        retention_days: Optional retention period for persistent artifacts.
    """

    type: str
    render_hints: dict[str, Any] = field(default_factory=dict)
    channel_compatibility: list[str] | None = None
    lifecycle: str = DEFAULT_LIFECYCLE
    retention_days: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "type": self.type,
            "render_hints": self.render_hints,
            "lifecycle": self.lifecycle,
        }
        if self.channel_compatibility is not None:
            result["channel_compatibility"] = self.channel_compatibility
        if self.retention_days is not None:
            result["retention_days"] = self.retention_days
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactDeclaration":
        """Create ArtifactDeclaration from a dictionary."""
        return cls(
            type=data.get("type", ""),
            render_hints=data.get("render_hints", {}),
            channel_compatibility=data.get("channel_compatibility"),
            lifecycle=data.get("lifecycle", DEFAULT_LIFECYCLE),
            retention_days=data.get("retention_days"),
        )

    def is_custom_type(self) -> bool:
        """Check if this artifact uses a custom (x-custom-*) type."""
        return self.type.startswith(CUSTOM_TYPE_PREFIX)


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------


def validate_artifact_type(artifact_type: str, field_path: str) -> list[str]:
    """
    Validate an artifact type value.

    Accepts:
    - Any of the 7 core types in VALID_ARTIFACT_TYPES
    - Any string starting with CUSTOM_TYPE_PREFIX ("x-custom-")

    Args:
        artifact_type: The type value to validate.
        field_path: Dot-notation path for error messages.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []

    if not isinstance(artifact_type, str):
        errors.append(
            f"{field_path}.type must be a string, "
            f"got {type(artifact_type).__name__}"
        )
        return errors

    if not artifact_type:
        errors.append(f"{field_path}.type is required and must not be empty")
        return errors

    if artifact_type not in VALID_ARTIFACT_TYPES and not artifact_type.startswith(
        CUSTOM_TYPE_PREFIX
    ):
        valid_list = ", ".join(sorted(VALID_ARTIFACT_TYPES))
        errors.append(
            f"{field_path}.type '{artifact_type}' is not a valid artifact type. "
            f"Must be one of: {valid_list}, or start with '{CUSTOM_TYPE_PREFIX}'"
        )

    return errors


def validate_render_hints(render_hints: Any, field_path: str) -> list[str]:
    """
    Validate render_hints structure.

    The render_hints dict MUST contain a 'format' key with a value from
    VALID_RENDER_FORMATS. Other keys are allowed (platform-specific hints)
    and are not strictly validated.

    Args:
        render_hints: The render_hints value to validate.
        field_path: Dot-notation path for error messages.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    hints_path = f"{field_path}.render_hints"

    if not isinstance(render_hints, dict):
        errors.append(
            f"{hints_path} must be a dictionary, " f"got {type(render_hints).__name__}"
        )
        return errors

    if "format" not in render_hints:
        errors.append(
            f"{hints_path}.format is required. "
            f"Must be one of: {', '.join(sorted(VALID_RENDER_FORMATS))}"
        )
        return errors

    fmt = render_hints["format"]
    if not isinstance(fmt, str):
        errors.append(
            f"{hints_path}.format must be a string, " f"got {type(fmt).__name__}"
        )
    elif fmt not in VALID_RENDER_FORMATS:
        errors.append(
            f"{hints_path}.format '{fmt}' is not valid. "
            f"Must be one of: {', '.join(sorted(VALID_RENDER_FORMATS))}"
        )

    return errors


def validate_lifecycle(
    lifecycle: Any, field_path: str, has_retention_days: bool
) -> tuple[list[str], list[str]]:
    """
    Validate lifecycle value and retention_days consistency.

    Args:
        lifecycle: The lifecycle value to validate.
        field_path: Dot-notation path for error messages.
        has_retention_days: Whether retention_days is present in the declaration.

    Returns:
        Tuple of (errors, warnings). Warnings are non-fatal issues.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if lifecycle is None:
        # lifecycle is optional; defaults to "ephemeral"
        return errors, warnings

    if not isinstance(lifecycle, str):
        errors.append(
            f"{field_path}.lifecycle must be a string, "
            f"got {type(lifecycle).__name__}"
        )
        return errors, warnings

    if lifecycle not in VALID_LIFECYCLES:
        errors.append(
            f"{field_path}.lifecycle '{lifecycle}' is not valid. "
            f"Must be one of: {', '.join(sorted(VALID_LIFECYCLES))}"
        )
        return errors, warnings

    # Warn if persistent without retention_days (non-fatal)
    if lifecycle == "persistent" and not has_retention_days:
        warnings.append(
            f"{field_path}.lifecycle is 'persistent' but no retention_days specified. "
            "Consider adding retention_days for data governance."
        )

    return errors, warnings


def validate_single_artifact_declaration(
    declaration: Any, field_path: str
) -> tuple[list[str], list[str]]:
    """
    Validate a single artifact declaration dictionary.

    Args:
        declaration: The artifact declaration dict to validate.
        field_path: Dot-notation path for error messages.

    Returns:
        Tuple of (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(declaration, dict):
        errors.append(
            f"{field_path} must be a dictionary, " f"got {type(declaration).__name__}"
        )
        return errors, warnings

    # Validate type (required)
    if "type" not in declaration:
        errors.append(f"{field_path}.type is required")
    else:
        type_errors = validate_artifact_type(declaration["type"], field_path)
        errors.extend(type_errors)

    # Validate render_hints (required)
    if "render_hints" not in declaration:
        errors.append(
            f"{field_path}.render_hints is required and must contain a 'format' key"
        )
    else:
        hints_errors = validate_render_hints(declaration["render_hints"], field_path)
        errors.extend(hints_errors)

    # Validate lifecycle (optional)
    has_retention_days = "retention_days" in declaration
    lifecycle_val = declaration.get("lifecycle")
    if lifecycle_val is not None:
        lifecycle_errors, lifecycle_warnings = validate_lifecycle(
            lifecycle_val, field_path, has_retention_days
        )
        errors.extend(lifecycle_errors)
        warnings.extend(lifecycle_warnings)
    elif has_retention_days:
        # retention_days present without explicit lifecycle
        warnings.append(
            f"{field_path} has retention_days but lifecycle defaults to 'ephemeral'. "
            "Set lifecycle to 'persistent' if retention is intended."
        )

    # Validate retention_days type if present
    if has_retention_days:
        retention = declaration["retention_days"]
        if not isinstance(retention, int) or isinstance(retention, bool):
            errors.append(
                f"{field_path}.retention_days must be a positive integer, "
                f"got {type(retention).__name__}"
            )
        elif retention <= 0:
            errors.append(
                f"{field_path}.retention_days must be a positive integer, got {retention}"
            )

    # Validate channel_compatibility type if present
    if "channel_compatibility" in declaration:
        channels = declaration["channel_compatibility"]
        if not isinstance(channels, list):
            errors.append(
                f"{field_path}.channel_compatibility must be a list, "
                f"got {type(channels).__name__}"
            )
        elif not all(isinstance(c, str) for c in channels):
            errors.append(
                f"{field_path}.channel_compatibility must contain only strings"
            )

    return errors, warnings


def validate_artifact_declaration_section(
    contract: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """
    Validate the artifact_declaration / artifact_declarations section of a contract.

    Supports both forms:
    - artifact_declaration (singular, dict) — treated as single-element array
    - artifact_declarations (plural, list of dicts) — array of declarations

    The two forms are mutually exclusive.

    Args:
        contract: The full contract dictionary.

    Returns:
        Tuple of (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    has_singular = ARTIFACT_DECLARATION_KEY in contract
    has_plural = ARTIFACT_DECLARATIONS_KEY in contract

    # Neither present — valid (section is optional)
    if not has_singular and not has_plural:
        return errors, warnings

    # Mutually exclusive check
    if has_singular and has_plural:
        errors.append(
            "Contract must not contain both 'artifact_declaration' (singular) and "
            "'artifact_declarations' (plural). Use one form only."
        )
        return errors, warnings

    # Singular form: must be a dict
    if has_singular:
        declaration = contract[ARTIFACT_DECLARATION_KEY]
        decl_errors, decl_warnings = validate_single_artifact_declaration(
            declaration, "artifact_declaration"
        )
        errors.extend(decl_errors)
        warnings.extend(decl_warnings)
        return errors, warnings

    # Plural form: must be a list of dicts
    declarations = contract[ARTIFACT_DECLARATIONS_KEY]
    if not isinstance(declarations, list):
        errors.append(
            f"artifact_declarations must be a list, "
            f"got {type(declarations).__name__}"
        )
        return errors, warnings

    if len(declarations) == 0:
        errors.append(
            "artifact_declarations must not be empty. "
            "Provide at least one artifact declaration or remove the section."
        )
        return errors, warnings

    for idx, decl in enumerate(declarations):
        decl_errors, decl_warnings = validate_single_artifact_declaration(
            decl, f"artifact_declarations[{idx}]"
        )
        errors.extend(decl_errors)
        warnings.extend(decl_warnings)

    return errors, warnings
