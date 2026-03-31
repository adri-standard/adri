"""
Comprehensive tests for the artifact_declaration feature (v7.3.0).

Covers:
- ArtifactDeclaration dataclass (from_dict, to_dict, defaults, is_custom_type)
- Validation functions (type, render_hints, lifecycle, single declaration, section)
- Contract validation integration (ContractValidator with artifact sections)
- BundledStandardWrapper accessor methods (get_artifact_declaration, get_artifact_declarations)

Test cases derived from RFC #100 community feedback (VeroPlay reference consumer).
"""

import pytest

from src.adri.contracts.artifact import (
    ARTIFACT_DECLARATION_KEY,
    ARTIFACT_DECLARATIONS_KEY,
    CUSTOM_TYPE_PREFIX,
    DEFAULT_LIFECYCLE,
    VALID_ARTIFACT_TYPES,
    VALID_LIFECYCLES,
    VALID_RENDER_FORMATS,
    ArtifactDeclaration,
    validate_artifact_declaration_section,
    validate_artifact_type,
    validate_lifecycle,
    validate_render_hints,
    validate_single_artifact_declaration,
)
from src.adri.contracts.validator import ContractValidator
from src.adri.validator.engine import BundledStandardWrapper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_contract(**extra_sections):
    """Build a minimal valid contract dict, optionally adding extra top-level sections."""
    contract = {
        "contracts": {
            "id": "test-id",
            "name": "Test",
            "version": "1.0.0",
            "description": "Test contract",
        },
        "requirements": {
            "overall_minimum": 75.0,
            "dimension_requirements": {
                "validity": {"weight": 3},
                "completeness": {"weight": 2},
            },
        },
    }
    contract.update(extra_sections)
    return contract


# ===========================================================================
# TestArtifactDeclarationDataclass
# ===========================================================================

class TestArtifactDeclarationDataclass:
    """Tests for the ArtifactDeclaration dataclass."""

    def test_from_dict_minimal(self):
        """Only type and render_hints.format — matches community test case #1."""
        data = {"type": "report", "render_hints": {"format": "markdown"}}
        decl = ArtifactDeclaration.from_dict(data)
        assert decl.type == "report"
        assert decl.render_hints == {"format": "markdown"}
        assert decl.lifecycle == DEFAULT_LIFECYCLE
        assert decl.retention_days is None
        assert decl.channel_compatibility is None

    def test_from_dict_full(self):
        """All fields populated."""
        data = {
            "type": "ui_component",
            "render_hints": {"format": "a2ui_json", "component": "table"},
            "channel_compatibility": ["web_dashboard", "slack"],
            "lifecycle": "persistent",
            "retention_days": 90,
        }
        decl = ArtifactDeclaration.from_dict(data)
        assert decl.type == "ui_component"
        assert decl.render_hints["format"] == "a2ui_json"
        assert decl.channel_compatibility == ["web_dashboard", "slack"]
        assert decl.lifecycle == "persistent"
        assert decl.retention_days == 90

    def test_to_dict_roundtrip(self):
        """from_dict → to_dict preserves data."""
        data = {
            "type": "dataset_push",
            "render_hints": {"format": "json"},
            "channel_compatibility": ["cli"],
            "lifecycle": "persistent",
            "retention_days": 365,
        }
        decl = ArtifactDeclaration.from_dict(data)
        result = decl.to_dict()
        assert result["type"] == "dataset_push"
        assert result["render_hints"]["format"] == "json"
        assert result["channel_compatibility"] == ["cli"]
        assert result["lifecycle"] == "persistent"
        assert result["retention_days"] == 365

    def test_to_dict_omits_none_optional_fields(self):
        """to_dict omits channel_compatibility and retention_days when None."""
        decl = ArtifactDeclaration(type="report", render_hints={"format": "text"})
        result = decl.to_dict()
        assert "channel_compatibility" not in result
        assert "retention_days" not in result
        assert result["lifecycle"] == "ephemeral"

    def test_default_lifecycle(self):
        """Defaults to 'ephemeral'."""
        decl = ArtifactDeclaration(type="report")
        assert decl.lifecycle == "ephemeral"

    def test_is_custom_type_true(self):
        """True for 'x-custom-foo'."""
        decl = ArtifactDeclaration(type="x-custom-verodat-sync")
        assert decl.is_custom_type() is True

    def test_is_custom_type_false(self):
        """False for core types like 'report'."""
        decl = ArtifactDeclaration(type="report")
        assert decl.is_custom_type() is False

    def test_empty_render_hints_defaults(self):
        """Empty dict by default."""
        decl = ArtifactDeclaration(type="report")
        assert decl.render_hints == {}


# ===========================================================================
# TestArtifactDeclarationValidation
# ===========================================================================

class TestArtifactDeclarationValidation:
    """Tests for artifact validation functions."""

    # --- Type validation ---

    def test_valid_all_core_types(self):
        """All 7 core types pass validation."""
        for core_type in VALID_ARTIFACT_TYPES:
            errors = validate_artifact_type(core_type, "test")
            assert errors == [], f"Type '{core_type}' should be valid"

    def test_valid_custom_type(self):
        """x-custom-* types pass validation."""
        errors = validate_artifact_type("x-custom-my-platform", "test")
        assert errors == []

    def test_invalid_type(self):
        """Unknown type (not core, not x-custom-*) fails."""
        errors = validate_artifact_type("invalid_unknown", "test")
        assert len(errors) == 1
        assert "not a valid artifact type" in errors[0]

    def test_missing_type_empty_string(self):
        """Empty type string fails with clear error message."""
        errors = validate_artifact_type("", "test")
        assert len(errors) == 1
        assert "required" in errors[0]

    def test_type_not_string(self):
        """Non-string type fails."""
        errors = validate_artifact_type(42, "test")
        assert len(errors) == 1
        assert "must be a string" in errors[0]

    # --- Render hints validation ---

    def test_valid_render_formats(self):
        """All 5 render formats pass."""
        for fmt in VALID_RENDER_FORMATS:
            errors = validate_render_hints({"format": fmt}, "test")
            assert errors == [], f"Format '{fmt}' should be valid"

    def test_missing_render_hints_format(self):
        """Missing format inside render_hints fails."""
        errors = validate_render_hints({}, "test")
        assert len(errors) == 1
        assert "format is required" in errors[0]

    def test_invalid_render_format(self):
        """Invalid format value fails."""
        errors = validate_render_hints({"format": "xml"}, "test")
        assert len(errors) == 1
        assert "not valid" in errors[0]

    def test_render_hints_not_dict(self):
        """render_hints as string fails."""
        errors = validate_render_hints("not_a_dict", "test")
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]

    def test_render_hints_extra_keys_allowed(self):
        """Extra platform-specific keys are allowed."""
        errors = validate_render_hints(
            {"format": "json", "custom_key": "custom_value"}, "test"
        )
        assert errors == []

    # --- Lifecycle validation ---

    def test_valid_lifecycles(self):
        """Both 'ephemeral' and 'persistent' pass."""
        for lc in VALID_LIFECYCLES:
            errors, warnings = validate_lifecycle(lc, "test", has_retention_days=False)
            assert errors == [], f"Lifecycle '{lc}' should be valid"

    def test_invalid_lifecycle(self):
        """Unknown lifecycle fails."""
        errors, warnings = validate_lifecycle("unknown", "test", has_retention_days=False)
        assert len(errors) == 1
        assert "not valid" in errors[0]

    def test_persistent_without_retention_days_warns(self):
        """Persistent without retention_days produces warning (not error)."""
        errors, warnings = validate_lifecycle(
            "persistent", "test", has_retention_days=False
        )
        assert errors == []
        assert len(warnings) == 1
        assert "retention_days" in warnings[0]

    def test_persistent_with_retention_days_no_warning(self):
        """Persistent with retention_days produces no warning."""
        errors, warnings = validate_lifecycle(
            "persistent", "test", has_retention_days=True
        )
        assert errors == []
        assert warnings == []

    def test_none_lifecycle_valid(self):
        """None lifecycle (absent) is valid — defaults applied elsewhere."""
        errors, warnings = validate_lifecycle(None, "test", has_retention_days=False)
        assert errors == []
        assert warnings == []

    # --- Single artifact declaration validation ---

    def test_valid_minimal_declaration(self):
        """Minimal valid declaration: type + render_hints.format."""
        errors, warnings = validate_single_artifact_declaration(
            {"type": "report", "render_hints": {"format": "markdown"}}, "test"
        )
        assert errors == []

    def test_missing_type_in_declaration(self):
        """Missing type fails."""
        errors, warnings = validate_single_artifact_declaration(
            {"render_hints": {"format": "json"}}, "test"
        )
        assert any("type is required" in e for e in errors)

    def test_missing_render_hints_in_declaration(self):
        """Missing render_hints fails."""
        errors, warnings = validate_single_artifact_declaration(
            {"type": "report"}, "test"
        )
        assert any("render_hints is required" in e for e in errors)

    def test_declaration_not_dict(self):
        """Non-dict declaration fails."""
        errors, warnings = validate_single_artifact_declaration("not_a_dict", "test")
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]

    def test_invalid_retention_days_negative(self):
        """Negative retention_days fails."""
        errors, warnings = validate_single_artifact_declaration(
            {
                "type": "report",
                "render_hints": {"format": "text"},
                "retention_days": -1,
            },
            "test",
        )
        assert any("positive integer" in e for e in errors)

    def test_invalid_retention_days_type(self):
        """Non-integer retention_days fails."""
        errors, warnings = validate_single_artifact_declaration(
            {
                "type": "report",
                "render_hints": {"format": "text"},
                "retention_days": "thirty",
            },
            "test",
        )
        assert any("positive integer" in e for e in errors)

    def test_invalid_channel_compatibility_type(self):
        """Non-list channel_compatibility fails."""
        errors, warnings = validate_single_artifact_declaration(
            {
                "type": "report",
                "render_hints": {"format": "text"},
                "channel_compatibility": "cli",
            },
            "test",
        )
        assert any("must be a list" in e for e in errors)

    def test_retention_days_without_persistent_lifecycle_warns(self):
        """retention_days with default ephemeral lifecycle produces warning."""
        errors, warnings = validate_single_artifact_declaration(
            {
                "type": "report",
                "render_hints": {"format": "text"},
                "retention_days": 30,
            },
            "test",
        )
        assert errors == []
        assert len(warnings) >= 1
        assert any("ephemeral" in w for w in warnings)


# ===========================================================================
# TestArtifactDeclarationSection
# ===========================================================================

class TestArtifactDeclarationSection:
    """Tests for validate_artifact_declaration_section (top-level orchestration)."""

    def test_no_artifact_section_valid(self):
        """Contract without artifact section is valid (optional)."""
        contract = _minimal_contract()
        errors, warnings = validate_artifact_declaration_section(contract)
        assert errors == []
        assert warnings == []

    def test_singular_form_valid(self):
        """Singular artifact_declaration dict is valid."""
        contract = _minimal_contract(
            artifact_declaration={
                "type": "report",
                "render_hints": {"format": "markdown"},
            }
        )
        errors, warnings = validate_artifact_declaration_section(contract)
        assert errors == []

    def test_plural_form_valid(self):
        """Plural artifact_declarations list is valid."""
        contract = _minimal_contract(
            artifact_declarations=[
                {"type": "report", "render_hints": {"format": "markdown"}},
                {"type": "notification", "render_hints": {"format": "text"}},
            ]
        )
        errors, warnings = validate_artifact_declaration_section(contract)
        assert errors == []

    def test_both_forms_mutually_exclusive(self):
        """Both singular and plural present is an error."""
        contract = _minimal_contract(
            artifact_declaration={"type": "report", "render_hints": {"format": "text"}},
            artifact_declarations=[
                {"type": "notification", "render_hints": {"format": "text"}}
            ],
        )
        errors, warnings = validate_artifact_declaration_section(contract)
        assert len(errors) == 1
        assert "must not contain both" in errors[0]

    def test_empty_plural_list_error(self):
        """Empty artifact_declarations list is an error."""
        contract = _minimal_contract(artifact_declarations=[])
        errors, warnings = validate_artifact_declaration_section(contract)
        assert len(errors) == 1
        assert "must not be empty" in errors[0]

    def test_plural_not_list_error(self):
        """artifact_declarations as dict (not list) is an error."""
        contract = _minimal_contract(
            artifact_declarations={"type": "report", "render_hints": {"format": "text"}}
        )
        errors, warnings = validate_artifact_declaration_section(contract)
        assert len(errors) == 1
        assert "must be a list" in errors[0]

    def test_multiple_errors_in_plural_list(self):
        """Each invalid entry in plural list generates errors."""
        contract = _minimal_contract(
            artifact_declarations=[
                {"type": "invalid_type", "render_hints": {"format": "text"}},
                {"type": "report"},  # missing render_hints
            ]
        )
        errors, warnings = validate_artifact_declaration_section(contract)
        assert len(errors) >= 2


# ===========================================================================
# TestContractWithArtifactDeclaration
# ===========================================================================

class TestContractWithArtifactDeclaration:
    """Integration tests: ContractValidator with artifact_declaration sections."""

    def setup_method(self):
        """Create a fresh validator for each test."""
        self.validator = ContractValidator()

    def test_valid_contract_with_artifact_declaration(self):
        """Contract with valid artifact_declaration passes validation."""
        contract = _minimal_contract(
            artifact_declaration={
                "type": "report",
                "render_hints": {"format": "markdown"},
            }
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert result.is_valid, f"Errors: {result.errors}"

    def test_valid_contract_with_artifact_declarations(self):
        """Contract with valid artifact_declarations passes validation."""
        contract = _minimal_contract(
            artifact_declarations=[
                {"type": "report", "render_hints": {"format": "markdown"}},
                {"type": "ui_component", "render_hints": {"format": "a2ui_json"}},
            ]
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert result.is_valid, f"Errors: {result.errors}"

    def test_contract_without_artifacts_still_valid(self):
        """Contract without any artifact section remains valid (backward compat)."""
        contract = _minimal_contract()
        result = self.validator.validate_contract(contract, use_cache=False)
        assert result.is_valid

    def test_invalid_artifact_produces_errors(self):
        """Contract with invalid artifact type produces validation errors."""
        contract = _minimal_contract(
            artifact_declaration={
                "type": "invalid_unknown",
                "render_hints": {"format": "invalid_format"},
            }
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert not result.is_valid
        assert len(result.errors) >= 1

    def test_both_forms_produces_error(self):
        """Contract with both singular and plural produces error."""
        contract = _minimal_contract(
            artifact_declaration={"type": "report", "render_hints": {"format": "text"}},
            artifact_declarations=[
                {"type": "notification", "render_hints": {"format": "text"}}
            ],
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert not result.is_valid

    def test_persistent_without_retention_days_warning(self):
        """Persistent lifecycle without retention_days produces warning, not error."""
        contract = _minimal_contract(
            artifact_declaration={
                "type": "report",
                "render_hints": {"format": "text"},
                "lifecycle": "persistent",
            }
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert result.is_valid  # Warning, not error
        assert len(result.warnings) >= 1

    def test_custom_type_valid(self):
        """Contract with x-custom-* artifact type passes validation."""
        contract = _minimal_contract(
            artifact_declaration={
                "type": "x-custom-my-platform",
                "render_hints": {"format": "json"},
            }
        )
        result = self.validator.validate_contract(contract, use_cache=False)
        assert result.is_valid


# ===========================================================================
# TestBundledStandardWrapperArtifactAccess
# ===========================================================================

class TestBundledStandardWrapperArtifactAccess:
    """Tests for BundledStandardWrapper artifact accessor methods."""

    def test_get_artifact_declaration_singular(self):
        """get_artifact_declaration() returns first declaration from singular form."""
        standard = _minimal_contract(
            artifact_declaration={
                "type": "report",
                "render_hints": {"format": "markdown"},
            }
        )
        wrapper = BundledStandardWrapper(standard)
        decl = wrapper.get_artifact_declaration()
        assert decl is not None
        assert decl.type == "report"
        assert decl.render_hints["format"] == "markdown"

    def test_get_artifact_declaration_plural(self):
        """get_artifact_declaration() returns first from plural form."""
        standard = _minimal_contract(
            artifact_declarations=[
                {"type": "report", "render_hints": {"format": "markdown"}},
                {"type": "notification", "render_hints": {"format": "text"}},
            ]
        )
        wrapper = BundledStandardWrapper(standard)
        decl = wrapper.get_artifact_declaration()
        assert decl is not None
        assert decl.type == "report"

    def test_get_artifact_declaration_none(self):
        """get_artifact_declaration() returns None when no artifacts present."""
        standard = _minimal_contract()
        wrapper = BundledStandardWrapper(standard)
        decl = wrapper.get_artifact_declaration()
        assert decl is None

    def test_get_artifact_declarations_singular(self):
        """get_artifact_declarations() wraps singular in list."""
        standard = _minimal_contract(
            artifact_declaration={
                "type": "report",
                "render_hints": {"format": "html"},
                "lifecycle": "persistent",
                "retention_days": 30,
            }
        )
        wrapper = BundledStandardWrapper(standard)
        declarations = wrapper.get_artifact_declarations()
        assert len(declarations) == 1
        assert declarations[0].type == "report"
        assert declarations[0].lifecycle == "persistent"
        assert declarations[0].retention_days == 30

    def test_get_artifact_declarations_plural(self):
        """get_artifact_declarations() returns all from plural form."""
        standard = _minimal_contract(
            artifact_declarations=[
                {"type": "report", "render_hints": {"format": "markdown"}},
                {
                    "type": "ui_component",
                    "render_hints": {"format": "a2ui_json"},
                    "channel_compatibility": ["web_dashboard"],
                },
                {"type": "notification", "render_hints": {"format": "text"}},
            ]
        )
        wrapper = BundledStandardWrapper(standard)
        declarations = wrapper.get_artifact_declarations()
        assert len(declarations) == 3
        assert declarations[0].type == "report"
        assert declarations[1].type == "ui_component"
        assert declarations[1].channel_compatibility == ["web_dashboard"]
        assert declarations[2].type == "notification"

    def test_get_artifact_declarations_empty(self):
        """get_artifact_declarations() returns empty list when no artifacts."""
        standard = _minimal_contract()
        wrapper = BundledStandardWrapper(standard)
        declarations = wrapper.get_artifact_declarations()
        assert declarations == []

    def test_artifact_declaration_is_custom_type(self):
        """ArtifactDeclaration.is_custom_type() works through wrapper."""
        standard = _minimal_contract(
            artifact_declaration={
                "type": "x-custom-verodat-sync",
                "render_hints": {"format": "json"},
            }
        )
        wrapper = BundledStandardWrapper(standard)
        decl = wrapper.get_artifact_declaration()
        assert decl is not None
        assert decl.is_custom_type() is True

    def test_artifact_declarations_filters_non_dict_entries(self):
        """get_artifact_declarations() skips non-dict entries gracefully."""
        standard = _minimal_contract(
            artifact_declarations=[
                {"type": "report", "render_hints": {"format": "text"}},
                "not_a_dict",
                42,
                {"type": "notification", "render_hints": {"format": "text"}},
            ]
        )
        wrapper = BundledStandardWrapper(standard)
        declarations = wrapper.get_artifact_declarations()
        assert len(declarations) == 2
        assert declarations[0].type == "report"
        assert declarations[1].type == "notification"
