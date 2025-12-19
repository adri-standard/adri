"""ADRI Schema Diff Service.

This module provides schema comparison and diff generation capabilities for ADRI
standards. Used by autotune to explain changes made to ADRI field specifications.

Key Features:
- Compare two ADRI schema versions
- Detect field additions, removals, and modifications
- Classify impact level (breaking vs non-breaking changes)
- Generate human-readable diff reports
- Format diffs for autotune logging

This service is consumed by the auto_tuner to provide transparency about schema changes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of schema changes."""

    FIELD_ADDED = "FIELD_ADDED"
    FIELD_REMOVED = "FIELD_REMOVED"
    FIELD_MODIFIED = "FIELD_MODIFIED"
    TYPE_CHANGED = "TYPE_CHANGED"
    CONSTRAINT_CHANGED = "CONSTRAINT_CHANGED"
    VALIDATION_RULE_ADDED = "VALIDATION_RULE_ADDED"
    VALIDATION_RULE_REMOVED = "VALIDATION_RULE_REMOVED"
    VALIDATION_RULE_MODIFIED = "VALIDATION_RULE_MODIFIED"
    DESCRIPTION_CHANGED = "DESCRIPTION_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"


class ImpactLevel(str, Enum):
    """Impact level of schema changes."""

    BREAKING = "BREAKING"  # Incompatible changes (type changes, field removals)
    NON_BREAKING = (
        "NON_BREAKING"  # Backward compatible (field additions, constraint relaxations)
    )
    CLARIFICATION = "CLARIFICATION"  # Documentation/description only


@dataclass
class SchemaChange:
    """Represents a single schema change."""

    change_type: ChangeType
    field_name: str
    impact_level: ImpactLevel
    before_value: Optional[Any]
    after_value: Optional[Any]
    description: str
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "change_type": self.change_type.value,
            "field_name": self.field_name,
            "impact_level": self.impact_level.value,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "description": self.description,
            "remediation": self.remediation,
        }


@dataclass
class SchemaDiffResult:
    """Complete diff between two schema versions."""

    source_version: str
    target_version: str
    changes: List[SchemaChange]
    breaking_changes_count: int
    non_breaking_changes_count: int
    clarification_changes_count: int
    summary: str

    def has_breaking_changes(self) -> bool:
        """Check if there are breaking changes."""
        return self.breaking_changes_count > 0

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.changes) > 0

    def get_changes_by_impact(self, impact: ImpactLevel) -> List[SchemaChange]:
        """Get changes filtered by impact level."""
        return [c for c in self.changes if c.impact_level == impact]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "total_changes": len(self.changes),
            "breaking_changes_count": self.breaking_changes_count,
            "non_breaking_changes_count": self.non_breaking_changes_count,
            "clarification_changes_count": self.clarification_changes_count,
            "summary": self.summary,
            "changes": [c.to_dict() for c in self.changes],
        }


class SchemaDiffService:
    """
    Service for comparing ADRI schema versions.

    Provides diff generation, impact analysis, and reporting.
    Used by autotune to explain schema changes.
    """

    # Properties that affect data structure
    STRUCTURAL_PROPERTIES = {"type", "items", "properties", "required", "enum"}

    # Properties that are constraints
    CONSTRAINT_PROPERTIES = {
        "min_value",
        "max_value",
        "min_length",
        "max_length",
        "min_items",
        "max_items",
        "pattern",
        "format",
    }

    # Properties that are validation rules
    VALIDATION_PROPERTIES = {"validation_rules", "custom_validators"}

    # Properties that are metadata/documentation
    METADATA_PROPERTIES = {"description", "examples", "default", "title"}

    def __init__(self):
        """Initialize the schema diff service."""
        pass

    def diff_files(
        self,
        source_path: str,
        target_path: str,
        source_version: str = "v1",
        target_version: str = "v2",
    ) -> SchemaDiffResult:
        """
        Compare two ADRI schema files.

        Args:
            source_path: Path to original schema file
            target_path: Path to updated schema file
            source_version: Version identifier for source
            target_version: Version identifier for target

        Returns:
            SchemaDiffResult with all detected changes
        """
        import yaml

        with open(source_path, "r") as f:
            source_schema = yaml.safe_load(f)

        with open(target_path, "r") as f:
            target_schema = yaml.safe_load(f)

        return self.diff_dicts(
            source_schema, target_schema, source_version, target_version
        )

    def diff_dicts(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        source_version: str = "v1",
        target_version: str = "v2",
    ) -> SchemaDiffResult:
        """
        Compare two schema dictionaries.

        Args:
            source: Original schema dictionary
            target: Updated schema dictionary
            source_version: Version identifier for source
            target_version: Version identifier for target

        Returns:
            SchemaDiffResult with all detected changes
        """
        changes = []

        # Extract field requirements from schemas
        source_fields = self._extract_field_requirements(source)
        target_fields = self._extract_field_requirements(target)

        # Detect field-level changes
        changes.extend(self._detect_field_changes(source_fields, target_fields))

        # Count changes by impact level
        breaking_count = sum(
            1 for c in changes if c.impact_level == ImpactLevel.BREAKING
        )
        non_breaking_count = sum(
            1 for c in changes if c.impact_level == ImpactLevel.NON_BREAKING
        )
        clarification_count = sum(
            1 for c in changes if c.impact_level == ImpactLevel.CLARIFICATION
        )

        # Generate summary
        summary = self._generate_summary(
            changes, breaking_count, non_breaking_count, clarification_count
        )

        return SchemaDiffResult(
            source_version=source_version,
            target_version=target_version,
            changes=changes,
            breaking_changes_count=breaking_count,
            non_breaking_changes_count=non_breaking_count,
            clarification_changes_count=clarification_count,
            summary=summary,
        )

    def _extract_field_requirements(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract field_requirements from ADRI schema."""
        if not schema:
            return {}

        # Support multiple schema formats
        if "requirements" in schema and "field_requirements" in schema["requirements"]:
            return schema["requirements"]["field_requirements"]
        elif "field_requirements" in schema:
            return schema["field_requirements"]
        else:
            return {}

    def _detect_field_changes(
        self, source_fields: Dict[str, Any], target_fields: Dict[str, Any]
    ) -> List[SchemaChange]:
        """
        Detect changes to field definitions.

        Args:
            source_fields: Original field requirements
            target_fields: Updated field requirements

        Returns:
            List of detected changes
        """
        changes = []

        source_field_names = set(source_fields.keys())
        target_field_names = set(target_fields.keys())

        # Detect added fields
        added_fields = target_field_names - source_field_names
        for field_name in added_fields:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_ADDED,
                    field_name=field_name,
                    impact_level=ImpactLevel.NON_BREAKING,
                    before_value=None,
                    after_value=target_fields[field_name],
                    description=f"Field '{field_name}' was added to the schema",
                    remediation="Existing data will not have this field; consider backfilling or making it optional",
                )
            )

        # Detect removed fields
        removed_fields = source_field_names - target_field_names
        for field_name in removed_fields:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_REMOVED,
                    field_name=field_name,
                    impact_level=ImpactLevel.BREAKING,
                    before_value=source_fields[field_name],
                    after_value=None,
                    description=f"Field '{field_name}' was removed from the schema",
                    remediation="Consumers expecting this field will break; migration required",
                )
            )

        # Detect modified fields
        common_fields = source_field_names & target_field_names
        for field_name in common_fields:
            source_field = source_fields[field_name]
            target_field = target_fields[field_name]

            field_changes = self._detect_field_property_changes(
                field_name, source_field, target_field
            )
            changes.extend(field_changes)

        return changes

    def _detect_field_property_changes(
        self,
        field_name: str,
        source_field: Dict[str, Any],
        target_field: Dict[str, Any],
    ) -> List[SchemaChange]:
        """
        Detect changes to individual field properties.

        Args:
            field_name: Name of the field
            source_field: Original field specification
            target_field: Updated field specification

        Returns:
            List of detected changes for this field
        """
        changes = []

        # Handle None or malformed field specs
        if not isinstance(source_field, dict):
            source_field = {}
        if not isinstance(target_field, dict):
            target_field = {}

        # Check for type changes
        if source_field.get("type") != target_field.get("type"):
            changes.append(
                SchemaChange(
                    change_type=ChangeType.TYPE_CHANGED,
                    field_name=field_name,
                    impact_level=ImpactLevel.BREAKING,
                    before_value=source_field.get("type"),
                    after_value=target_field.get("type"),
                    description=f"Field '{field_name}' type changed from '{source_field.get('type')}' to '{target_field.get('type')}'",
                    remediation="Data migration required to convert existing values to new type",
                )
            )

        # Check for constraint changes
        changes.extend(
            self._detect_constraint_changes(field_name, source_field, target_field)
        )

        # Check for validation rule changes
        changes.extend(
            self._detect_validation_rule_changes(field_name, source_field, target_field)
        )

        # Check for description changes
        if source_field.get("description") != target_field.get("description"):
            changes.append(
                SchemaChange(
                    change_type=ChangeType.DESCRIPTION_CHANGED,
                    field_name=field_name,
                    impact_level=ImpactLevel.CLARIFICATION,
                    before_value=source_field.get("description"),
                    after_value=target_field.get("description"),
                    description=f"Field '{field_name}' description was updated",
                    remediation=None,
                )
            )

        # Check for other metadata changes
        metadata_changed = False
        for prop in self.METADATA_PROPERTIES:
            if prop == "description":
                continue  # Already handled
            if source_field.get(prop) != target_field.get(prop):
                metadata_changed = True
                break

        if metadata_changed:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.METADATA_CHANGED,
                    field_name=field_name,
                    impact_level=ImpactLevel.CLARIFICATION,
                    before_value={
                        k: source_field.get(k)
                        for k in self.METADATA_PROPERTIES
                        if k in source_field
                    },
                    after_value={
                        k: target_field.get(k)
                        for k in self.METADATA_PROPERTIES
                        if k in target_field
                    },
                    description=f"Field '{field_name}' metadata was updated",
                    remediation=None,
                )
            )

        return changes

    def _detect_constraint_changes(
        self,
        field_name: str,
        source_field: Dict[str, Any],
        target_field: Dict[str, Any],
    ) -> List[SchemaChange]:
        """
        Detect changes to field constraints.

        Args:
            field_name: Name of the field
            source_field: Original field specification
            target_field: Updated field specification

        Returns:
            List of constraint changes
        """
        changes = []

        for constraint in self.CONSTRAINT_PROPERTIES:
            source_value = source_field.get(constraint)
            target_value = target_field.get(constraint)

            if source_value != target_value:
                # Determine if this is a breaking change
                impact = self._classify_constraint_change_impact(
                    constraint, source_value, target_value
                )

                changes.append(
                    SchemaChange(
                        change_type=ChangeType.CONSTRAINT_CHANGED,
                        field_name=field_name,
                        impact_level=impact,
                        before_value=source_value,
                        after_value=target_value,
                        description=f"Field '{field_name}' constraint '{constraint}' changed from {source_value} to {target_value}",
                        remediation=self._get_constraint_remediation(
                            constraint, source_value, target_value, impact
                        ),
                    )
                )

        return changes

    def _classify_constraint_change_impact(
        self, constraint: str, source_value: Optional[Any], target_value: Optional[Any]
    ) -> ImpactLevel:
        """
        Classify the impact of a constraint change.

        Args:
            constraint: Name of the constraint
            source_value: Original constraint value
            target_value: New constraint value

        Returns:
            Impact level of the change
        """
        # If constraint was removed, it's non-breaking (relaxation)
        if source_value is not None and target_value is None:
            return ImpactLevel.NON_BREAKING

        # If constraint was added, it's breaking (tightening)
        if source_value is None and target_value is not None:
            return ImpactLevel.BREAKING

        # For min constraints, increasing is breaking
        if constraint.startswith("min"):
            return (
                ImpactLevel.BREAKING
                if target_value > source_value
                else ImpactLevel.NON_BREAKING
            )

        # For max constraints, decreasing is breaking
        if constraint.startswith("max"):
            return (
                ImpactLevel.BREAKING
                if target_value < source_value
                else ImpactLevel.NON_BREAKING
            )

        # For pattern/format changes, always breaking
        if constraint in ["pattern", "format"]:
            return ImpactLevel.BREAKING

        # Default to breaking for safety
        return ImpactLevel.BREAKING

    def _get_constraint_remediation(
        self,
        constraint: str,
        source_value: Optional[Any],
        target_value: Optional[Any],
        impact: ImpactLevel,
    ) -> Optional[str]:
        """Get remediation advice for constraint change."""
        if impact == ImpactLevel.NON_BREAKING:
            return "Constraint was relaxed; no migration needed"
        elif source_value is None and target_value is not None:
            return f"New constraint added; validate existing data meets {constraint}={target_value}"
        else:
            return f"Constraint tightened; migrate existing data to meet {constraint}={target_value}"

    def _detect_validation_rule_changes(
        self,
        field_name: str,
        source_field: Dict[str, Any],
        target_field: Dict[str, Any],
    ) -> List[SchemaChange]:
        """
        Detect changes to validation rules.

        Args:
            field_name: Name of the field
            source_field: Original field specification
            target_field: Updated field specification

        Returns:
            List of validation rule changes
        """
        changes = []

        source_rules = source_field.get("validation_rules", [])
        target_rules = target_field.get("validation_rules", [])

        # Convert to sets for comparison (using rule names as keys)
        source_rule_names = {
            self._get_rule_identifier(r) for r in source_rules if isinstance(r, dict)
        }
        target_rule_names = {
            self._get_rule_identifier(r) for r in target_rules if isinstance(r, dict)
        }

        # Detect added rules
        added_rules = target_rule_names - source_rule_names
        if added_rules:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.VALIDATION_RULE_ADDED,
                    field_name=field_name,
                    impact_level=ImpactLevel.BREAKING,
                    before_value=None,
                    after_value=list(added_rules),
                    description=f"Field '{field_name}' has new validation rules: {', '.join(added_rules)}",
                    remediation="Validate existing data meets new rules; may require data cleanup",
                )
            )

        # Detect removed rules
        removed_rules = source_rule_names - target_rule_names
        if removed_rules:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.VALIDATION_RULE_REMOVED,
                    field_name=field_name,
                    impact_level=ImpactLevel.NON_BREAKING,
                    before_value=list(removed_rules),
                    after_value=None,
                    description=f"Field '{field_name}' validation rules removed: {', '.join(removed_rules)}",
                    remediation="Validation relaxed; no migration needed",
                )
            )

        # Detect modified rules (simplified - just check if rules changed)
        if source_rules and target_rules and source_rules != target_rules:
            common_rules = source_rule_names & target_rule_names
            if common_rules:
                changes.append(
                    SchemaChange(
                        change_type=ChangeType.VALIDATION_RULE_MODIFIED,
                        field_name=field_name,
                        impact_level=ImpactLevel.BREAKING,
                        before_value=source_rules,
                        after_value=target_rules,
                        description=f"Field '{field_name}' validation rules were modified",
                        remediation="Review rule changes and validate existing data",
                    )
                )

        return changes

    def _get_rule_identifier(self, rule: Dict[str, Any]) -> str:
        """Get identifier for a validation rule."""
        if "name" in rule:
            return rule["name"]
        elif "code" in rule:
            return rule["code"][:50]  # First 50 chars of code
        else:
            return str(hash(str(rule)))

    def _generate_summary(
        self,
        changes: List[SchemaChange],
        breaking_count: int,
        non_breaking_count: int,
        clarification_count: int,
    ) -> str:
        """Generate human-readable summary of changes."""
        if not changes:
            return "No changes detected between schema versions"

        total = len(changes)
        parts = [f"Total changes: {total}"]

        if breaking_count > 0:
            parts.append(f"⚠️  Breaking changes: {breaking_count}")
        if non_breaking_count > 0:
            parts.append(f"✅ Non-breaking changes: {non_breaking_count}")
        if clarification_count > 0:
            parts.append(f"📝 Documentation updates: {clarification_count}")

        return " | ".join(parts)

    def generate_report(
        self, diff_result: SchemaDiffResult, format: str = "text"
    ) -> str:
        """
        Generate formatted diff report.

        Args:
            diff_result: SchemaDiffResult to format
            format: Output format ('text', 'markdown', or 'autotune')

        Returns:
            Formatted report string
        """
        if format == "text":
            return format_diff_report(diff_result)
        elif format == "markdown":
            return format_diff_markdown(diff_result)
        elif format == "autotune":
            return format_diff_for_autotune(diff_result)
        else:
            raise ValueError(f"Unsupported format: {format}")


def format_diff_report(diff_result: SchemaDiffResult) -> str:
    """Format diff result as human-readable text report."""
    lines = []
    lines.append("=" * 70)
    lines.append(
        f"ADRI Schema Diff: {diff_result.source_version} → {diff_result.target_version}"
    )
    lines.append("=" * 70)
    lines.append("")
    lines.append(diff_result.summary)
    lines.append("")

    if not diff_result.changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    # Group changes by impact level
    breaking = diff_result.get_changes_by_impact(ImpactLevel.BREAKING)
    non_breaking = diff_result.get_changes_by_impact(ImpactLevel.NON_BREAKING)
    clarifications = diff_result.get_changes_by_impact(ImpactLevel.CLARIFICATION)

    if breaking:
        lines.append("⚠️  BREAKING CHANGES")
        lines.append("-" * 70)
        for change in breaking:
            lines.append(f"  • {change.description}")
            if change.remediation:
                lines.append(f"    → {change.remediation}")
        lines.append("")

    if non_breaking:
        lines.append("✅ NON-BREAKING CHANGES")
        lines.append("-" * 70)
        for change in non_breaking:
            lines.append(f"  • {change.description}")
            if change.remediation:
                lines.append(f"    → {change.remediation}")
        lines.append("")

    if clarifications:
        lines.append("📝 DOCUMENTATION UPDATES")
        lines.append("-" * 70)
        for change in clarifications:
            lines.append(f"  • {change.description}")
        lines.append("")

    return "\n".join(lines)


def format_diff_markdown(diff_result: SchemaDiffResult) -> str:
    """Format diff result as Markdown report."""
    lines = []
    lines.append(
        f"# ADRI Schema Diff: {diff_result.source_version} → {diff_result.target_version}"
    )
    lines.append("")
    lines.append(diff_result.summary)
    lines.append("")

    if not diff_result.changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    # Group changes by impact level
    breaking = diff_result.get_changes_by_impact(ImpactLevel.BREAKING)
    non_breaking = diff_result.get_changes_by_impact(ImpactLevel.NON_BREAKING)
    clarifications = diff_result.get_changes_by_impact(ImpactLevel.CLARIFICATION)

    if breaking:
        lines.append("## ⚠️  Breaking Changes")
        lines.append("")
        for change in breaking:
            lines.append(f"- **{change.field_name}**: {change.description}")
            if change.remediation:
                lines.append(f"  - *Remediation*: {change.remediation}")
        lines.append("")

    if non_breaking:
        lines.append("## ✅ Non-Breaking Changes")
        lines.append("")
        for change in non_breaking:
            lines.append(f"- **{change.field_name}**: {change.description}")
            if change.remediation:
                lines.append(f"  - *Remediation*: {change.remediation}")
        lines.append("")

    if clarifications:
        lines.append("## 📝 Documentation Updates")
        lines.append("")
        for change in clarifications:
            lines.append(f"- **{change.field_name}**: {change.description}")
        lines.append("")

    return "\n".join(lines)


def format_diff_for_autotune(diff_result: SchemaDiffResult) -> str:
    """Format diff specifically for autotune logging (concise format)."""
    if not diff_result.changes:
        return "No schema changes"

    lines = []
    lines.append(
        f"Schema Changes ({diff_result.source_version} → {diff_result.target_version}):"
    )

    # Breaking changes first (most important)
    breaking = diff_result.get_changes_by_impact(ImpactLevel.BREAKING)
    if breaking:
        lines.append("  ⚠️  Breaking:")
        for change in breaking:
            lines.append(f"     - {change.field_name}: {change.change_type.value}")

    # Non-breaking changes
    non_breaking = diff_result.get_changes_by_impact(ImpactLevel.NON_BREAKING)
    if non_breaking:
        lines.append("  ✅ Non-breaking:")
        for change in non_breaking:
            lines.append(f"     - {change.field_name}: {change.change_type.value}")

    # Clarifications (least important)
    clarifications = diff_result.get_changes_by_impact(ImpactLevel.CLARIFICATION)
    if clarifications:
        lines.append(f"  📝 Documentation: {len(clarifications)} update(s)")

    return "\n".join(lines)


def compare_schemas(
    source_schema: Dict[str, Any],
    target_schema: Dict[str, Any],
    source_version: str = "v1",
    target_version: str = "v2",
) -> SchemaDiffResult:
    """
    Compare two ADRI schema versions and generate diff.

    Convenience function for one-off comparisons.

    Args:
        source_schema: Original schema (before changes)
        target_schema: Updated schema (after changes)
        source_version: Version identifier for source
        target_version: Version identifier for target

    Returns:
        SchemaDiffResult with all detected changes
    """
    service = SchemaDiffService()
    return service.diff_dicts(
        source_schema, target_schema, source_version, target_version
    )
