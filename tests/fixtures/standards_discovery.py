"""Auto-discovery utilities for ADRI standards testing.

This module extends the tutorial discovery concept to ALL standards in the
adri/standards/ directory. For each valid standard, it looks for or generates
test data to enable comprehensive automated testing.

File Structure Convention:
    adri/standards/<path>/<standard>.yaml
    adri/standards/test_data/<standard_id>_data.csv          # Training data (100%)
    adri/standards/test_data/test_<standard_id>_data.csv     # Test data (with errors)

Example:
    adri/standards/domains/customer_service_standard.yaml
    adri/standards/test_data/customer_service_standard_data.csv
    adri/standards/test_data/test_customer_service_standard_data.csv

Discovery Process:
    1. Scan adri/standards/ recursively for *.yaml files
    2. Validate each file is a proper ADRI standard
    3. Check for corresponding test data CSV files
    4. Return metadata for test generation
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import yaml


@dataclass
class StandardTestMetadata:
    """Metadata about a discovered standard for testing.

    Attributes:
        standard_id: Standard identifier from YAML (e.g., "customer_service_standard")
        standard_path: Path to standard YAML file
        standard_name: Human-readable name
        training_data_path: Path to training CSV (may not exist yet)
        test_data_path: Path to test CSV (may not exist yet)
        has_training_data: Whether training CSV exists
        has_test_data: Whether test CSV exists
        field_count: Number of fields in standard
        relative_path: Relative path from standards directory
    """
    standard_id: str
    standard_path: Path
    standard_name: str
    training_data_path: Path
    test_data_path: Path
    has_training_data: bool
    has_test_data: bool
    field_count: int
    relative_path: str


def find_testable_standards(
    standards_root: Optional[Path] = None,
    test_data_dir: Optional[Path] = None
) -> List[StandardTestMetadata]:
    """Find all valid standards and check for test data.

    Scans adri/standards/ recursively for YAML files that are valid ADRI standards.
    For each standard, checks if corresponding test data CSV files exist.

    Args:
        standards_root: Optional path to standards directory.
                       If None, uses adri/standards/ relative to project root.
        test_data_dir: Optional path to test data directory.
                      If None, uses adri/standards/test_data/

    Returns:
        List of StandardTestMetadata for each valid standard found.
        Includes standards even if test data doesn't exist yet.

    Example:
        standards = find_testable_standards()
        for std in standards:
            print(f"Standard: {std.standard_id}")
            print(f"  Has data: {std.has_training_data and std.has_test_data}")
    """
    # Determine standards root directory
    if standards_root is None:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        standards_root = project_root / "adri" / "standards"

    # Determine test data directory
    if test_data_dir is None:
        test_data_dir = standards_root / "test_data"

    # Create test_data directory if it doesn't exist
    test_data_dir.mkdir(exist_ok=True)

    # Return empty list if standards directory doesn't exist
    if not standards_root.exists():
        return []

    # Find all YAML files recursively
    yaml_files = list(standards_root.rglob("*.yaml"))

    # Validate each file and collect metadata
    valid_standards = []
    for yaml_file in yaml_files:
        # Skip files in test_data directory itself
        if test_data_dir in yaml_file.parents:
            continue

        is_valid, metadata = validate_standard_for_testing(
            yaml_file, standards_root, test_data_dir
        )
        if is_valid and metadata:
            valid_standards.append(metadata)

    return valid_standards


def validate_standard_for_testing(
    standard_path: Path,
    standards_root: Path,
    test_data_dir: Path
) -> Tuple[bool, Optional[StandardTestMetadata]]:
    """Validate standard file and check for test data.

    Checks:
    - File is valid YAML
    - Contains required 'standards' section with 'id' field
    - Contains 'requirements' section with 'field_requirements'
    - Looks for corresponding training and test CSV files

    Args:
        standard_path: Path to standard YAML file
        standards_root: Root directory for standards
        test_data_dir: Directory where test data CSVs are stored

    Returns:
        Tuple of (is_valid, metadata):
        - is_valid: True if file is a valid standard, False otherwise
        - metadata: StandardTestMetadata if valid, None if invalid
    """
    try:
        # Load and parse YAML
        with open(standard_path, 'r', encoding='utf-8') as f:
            standard_data = yaml.safe_load(f)

        # Validate basic structure
        if not isinstance(standard_data, dict):
            return False, None

        # Check for required sections
        if 'standards' not in standard_data:
            return False, None

        standards_section = standard_data['standards']
        if not isinstance(standards_section, dict):
            return False, None

        # Get standard ID
        standard_id = standards_section.get('id')
        if not standard_id:
            return False, None

        # Get standard name
        standard_name = standards_section.get('name', standard_id)

        # Check for requirements section
        if 'requirements' not in standard_data:
            return False, None

        requirements = standard_data['requirements']
        if not isinstance(requirements, dict):
            return False, None

        # Count fields
        field_requirements = requirements.get('field_requirements', {})
        field_count = len(field_requirements) if isinstance(field_requirements, dict) else 0

        # Build expected test data file paths
        training_data_path = test_data_dir / f"{standard_id}_data.csv"
        test_data_path = test_data_dir / f"test_{standard_id}_data.csv"

        # Check if test data files exist
        has_training_data = training_data_path.exists()
        has_test_data = test_data_path.exists()

        # Calculate relative path for reporting
        try:
            relative_path = str(standard_path.relative_to(standards_root))
        except ValueError:
            relative_path = standard_path.name

        # Build metadata
        metadata = StandardTestMetadata(
            standard_id=standard_id,
            standard_path=standard_path,
            standard_name=standard_name,
            training_data_path=training_data_path,
            test_data_path=test_data_path,
            has_training_data=has_training_data,
            has_test_data=has_test_data,
            field_count=field_count,
            relative_path=relative_path
        )

        return True, metadata

    except (yaml.YAMLError, OSError, IOError, KeyError, TypeError):
        return False, None


def get_standards_needing_data() -> List[StandardTestMetadata]:
    """Get list of standards that don't have test data yet.

    Returns:
        List of standards missing training data, test data, or both.
    """
    all_standards = find_testable_standards()
    return [
        std for std in all_standards
        if not std.has_training_data or not std.has_test_data
    ]


def get_standards_ready_for_testing() -> List[StandardTestMetadata]:
    """Get list of standards that have complete test data.

    Returns:
        List of standards with both training and test CSV files.
    """
    all_standards = find_testable_standards()
    return [
        std for std in all_standards
        if std.has_training_data and std.has_test_data
    ]
