#!/usr/bin/env python
"""Migration script to convert ADRI standards to validation_rules format.

This script converts old-style standards with field constraints to new-style
standards with explicit validation_rules and severity levels.
"""

import sys
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adri.config.severity_loader import SeverityDefaultsLoader
from src.adri.analysis.generation.field_inference import FieldInferenceEngine


def convert_standard_file(standard_path: Path) -> bool:
    """Convert a single standard file to validation_rules format.

    Args:
        standard_path: Path to the standard YAML file

    Returns:
        True if conversion successful, False otherwise
    """
    print(f"Converting: {standard_path.name}")

    try:
        # Load the standard
        with open(standard_path, 'r', encoding='utf-8') as f:
            standard = yaml.safe_load(f)

        # Check if already converted
        if has_validation_rules(standard):
            print(f"  ✓ Already uses validation_rules format - skipping")
            return True

        # Convert field_requirements
        field_reqs = standard.get('requirements', {}).get('field_requirements', {})
        if not field_reqs:
            print(f"  ✓ No field requirements - skipping")
            return True

        field_engine = FieldInferenceEngine()
        converted_count = 0

        for field_name, field_config in field_reqs.items():
            if not isinstance(field_config, dict):
                continue

            # Convert constraints to validation_rules
            validation_rules = field_engine.convert_field_constraints_to_validation_rules(
                field_config, field_name
            )

            if validation_rules:
                field_config['validation_rules'] = validation_rules
                converted_count += 1

        # Save the converted standard
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard, f, default_flow_style=False, sort_keys=False, width=120)

        print(f"  ✓ Converted {converted_count} fields")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def has_validation_rules(standard: dict) -> bool:
    """Check if standard already uses validation_rules format.

    Args:
        standard: Standard dictionary

    Returns:
        True if already converted
    """
    field_reqs = standard.get('requirements', {}).get('field_requirements', {})
    if not field_reqs:
        return False

    # Check if any field has validation_rules
    for field_config in field_reqs.values():
        if isinstance(field_config, dict) and 'validation_rules' in field_config:
            return True

    return False


def main():
    """Convert all ADRI standards to validation_rules format."""
    # Find all standard files recursively
    standards_dir = Path('adri/standards')
    standard_files = list(standards_dir.rglob('*.yaml'))

    print("=" * 60)
    print("ADRI Standards Migration to Validation Rules Format")
    print("=" * 60)
    print()

    success_count = 0
    failure_count = 0
    skipped_count = 0

    for standard_file in standard_files:
        if not standard_file.exists():
            print(f"Skipping {standard_file.name} - file not found")
            skipped_count += 1
            continue

        if convert_standard_file(standard_file):
            success_count += 1
        else:
            failure_count += 1

    print()
    print("=" * 60)
    print(f"Migration Complete:")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ✗ Failed: {failure_count}")
    print(f"  - Skipped: {skipped_count}")
    print("=" * 60)

    return 0 if failure_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
