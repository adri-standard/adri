"""Auto-discovery utilities for ADRI standards catalog.

This module provides functions for discovering and validating standards in the
adri/contracts/ directory. Standards are organized in subdirectories by category
(domains, frameworks, templates) and follow a YAML-based v5.0.0 structure.

Directory Structure:
    adri/contracts/
    ├── domains/              # Business domain standards (5 standards)
    ├── frameworks/           # AI framework standards (4 standards)
    └── templates/            # Generic template standards (4 standards)

Discovery Process:
    1. Scan adri/contracts/{domains,frameworks,templates}/ for .yaml files
    2. Validate each file has proper v5.0.0 structure
    3. Extract standard metadata (id, name, version, etc.)
    4. Return metadata for test parametrization

Usage:
    from tests.fixtures.standards_discovery import find_catalog_standards

    standards = find_catalog_standards()
    for standard in standards:
        print(f"Found: {standard.standard_id} in {standard.category}")
        print(f"  File: {standard.file_path}")
        print(f"  Version: {standard.version}")

Benefits:
    - New standards are automatically discovered and tested
    - No manual test file updates required when catalog grows
    - Ensures complete test coverage of the standards catalog
"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict


@dataclass
class StandardMetadata:
    """Metadata about a discovered standard in the catalog.

    Attributes:
        standard_id: Unique identifier from YAML (e.g., "customer_service_standard")
        standard_name: Display name from YAML (e.g., "Customer Service Interaction Standard")
        file_path: Path to the YAML standard file
        category: Category subdirectory (domains/frameworks/templates)
        filename: Base filename without extension (used for @adri_protected references)
        version: Version string from YAML (e.g., "1.0.0")
    """
    standard_id: str
    standard_name: str
    file_path: Path
    category: str
    filename: str
    version: str


def find_catalog_standards(standards_root: Optional[Path] = None) -> List[StandardMetadata]:
    """Find all valid standards in the catalog directories.

    Scans adri/contracts/{domains,frameworks,templates}/ for .yaml files
    and extracts metadata from each standard.

    Args:
        standards_root: Optional path to standards directory.
                       If None, uses adri/contracts/ relative to project root.

    Returns:
        List of StandardMetadata for each valid standard found.
        Empty list if directories don't exist.

    Example:
        standards = find_catalog_standards()
        for std in standards:
            print(f"Found: {std.standard_id} in {std.category}")
    """
    # Determine standards root directory
    if standards_root is None:
        # This file is in tests/fixtures/
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        standards_root = project_root / "ADRI" / "contracts"

    # Return empty list if directory doesn't exist
    if not standards_root.exists():
        return []

    # Catalog subdirectories to scan
    catalog_categories = ["domains", "frameworks", "templates"]

    # Collect all valid standards
    valid_standards = []

    for category in catalog_categories:
        category_dir = standards_root / category

        # Skip if category directory doesn't exist
        if not category_dir.exists():
            continue

        # Find all YAML files in this category
        yaml_files = list(category_dir.glob("*.yaml"))

        # Validate each file and collect metadata
        for yaml_file in yaml_files:
            is_valid, metadata = validate_contract_file(yaml_file, category)
            if is_valid and metadata:
                valid_standards.append(metadata)

    return valid_standards


def validate_contract_file(file_path: Path, category: str) -> Tuple[bool, Optional[StandardMetadata]]:
    """Validate a standard YAML file and extract metadata.

    Checks:
    - File is valid YAML
    - Has required v5.0.0 structure (standards, requirements, etc.)
    - Contains standards.id and standards.name fields
    - Version field is present

    Args:
        file_path: Path to YAML standard file
        category: Category name (domains/frameworks/templates)

    Returns:
        Tuple of (is_valid, metadata):
        - is_valid: True if file is a valid standard, False otherwise
        - metadata: StandardMetadata if valid, None if invalid
    """
    try:
        # Read and parse YAML file
        with open(file_path, 'r', encoding='utf-8') as f:
            standard_data = yaml.safe_load(f)

        # Verify required v5.0.0 structure
        if not isinstance(standard_data, dict):
            return False, None

        # Check for required top-level sections
        required_sections = ['contracts', 'record_identification', 'requirements', 'metadata']
        if not all(section in standard_data for section in required_sections):
            return False, None

        # Extract standards section
        standards_section = standard_data.get('contracts', {})

        # Verify required fields in standards section
        if 'id' not in standards_section or 'name' not in standards_section:
            return False, None

        if 'version' not in standards_section:
            return False, None

        # Extract metadata
        standard_id = standards_section['id']
        standard_name = standards_section['name']
        version = standards_section['version']
        filename = extract_standard_identifier(file_path)

        # Build metadata object
        metadata = StandardMetadata(
            standard_id=standard_id,
            standard_name=standard_name,
            file_path=file_path,
            category=category,
            filename=filename,
            version=version
        )

        return True, metadata

    except (yaml.YAMLError, OSError, IOError, KeyError):
        return False, None


def get_standards_by_category() -> Dict[str, List[StandardMetadata]]:
    """Group discovered standards by category.

    Returns:
        Dictionary mapping category names to lists of standards:
        {
            'domains': [std1, std2, ...],
            'frameworks': [std3, std4, ...],
            'templates': [std5, std6, ...]
        }

    Example:
        by_category = get_standards_by_category()
        print(f"Domain standards: {len(by_category['domains'])}")
        print(f"Framework standards: {len(by_category['frameworks'])}")
        print(f"Template standards: {len(by_category['templates'])}")
    """
    standards = find_catalog_standards()

    # Initialize category dictionary
    categorized = {
        'domains': [],
        'frameworks': [],
        'templates': []
    }

    # Group standards by category
    for standard in standards:
        if standard.category in categorized:
            categorized[standard.category].append(standard)

    return categorized


def extract_standard_identifier(file_path: Path) -> str:
    """Extract the standard identifier/name used for @adri_protected.

    The identifier is the filename without extension, which should match
    how users reference standards in @adri_protected(contract="...").

    Args:
        file_path: Path to standard YAML file

    Returns:
        Standard identifier (e.g., "customer_service_standard")

    Example:
        identifier = extract_standard_identifier(Path("customer_service_standard.yaml"))
        # Returns: "customer_service_standard"

        identifier = extract_standard_identifier(Path("api_response_template.yaml"))
        # Returns: "api_response_template"
    """
    return file_path.stem
