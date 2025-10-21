#!/usr/bin/env python
"""Validate all ADRI standards to ensure they pass validation rules format."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adri.standards.validator import get_validator


def validate_all_standards():
    """Validate all standard files in the standards directory."""
    standards_dir = Path('adri/standards')
    standard_files = list(standards_dir.rglob('*.yaml'))

    print("=" * 70)
    print("ADRI Standards Validation Check")
    print("=" * 70)
    print()

    validator = get_validator()

    valid_count = 0
    invalid_count = 0
    error_count = 0

    invalid_standards = []
    error_standards = []

    for standard_file in sorted(standard_files):
        try:
            result = validator.validate_standard_file(str(standard_file))

            if result.is_valid:
                print(f"✓ {standard_file.relative_to(standards_dir)}")
                valid_count += 1
            else:
                print(f"✗ {standard_file.relative_to(standards_dir)}")
                for error in result.errors:
                    print(f"  - {error}")
                invalid_count += 1
                invalid_standards.append(standard_file.relative_to(standards_dir))
        except Exception as e:
            print(f"✗ {standard_file.relative_to(standards_dir)} - ERROR: {e}")
            error_count += 1
            error_standards.append((standard_file.relative_to(standards_dir), str(e)))

    print()
    print("=" * 70)
    print(f"Validation Complete:")
    print(f"  ✓ Valid: {valid_count}")
    print(f"  ✗ Invalid: {invalid_count}")
    print(f"  ✗ Errors: {error_count}")
    print("=" * 70)

    if invalid_standards:
        print("\nInvalid Standards:")
        for std in invalid_standards:
            print(f"  - {std}")

    if error_standards:
        print("\nStandards with Errors:")
        for std, err in error_standards:
            print(f"  - {std}: {err}")

    return 0 if (invalid_count == 0 and error_count == 0) else 1


if __name__ == '__main__':
    sys.exit(validate_all_standards())
