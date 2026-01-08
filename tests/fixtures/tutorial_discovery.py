"""Auto-discovery utilities for ADRI tutorials.

This module provides functions for discovering and validating tutorials in the
ADRI/tutorials/ directory. Tutorials follow a convention-based structure where
simply dropping two CSV files creates a fully-tested use case.

File Naming Convention:
    ADRI/tutorials/<use_case>/
    ├── <use_case>_data.csv          # Clean training data (100% quality)
    └── test_<use_case>_data.csv     # Test data with quality issues

Example:
    ADRI/tutorials/invoice_processing/
    ├── invoice_data.csv
    └── test_invoice_data.csv

Discovery Process:
    1. Scan ADRI/tutorials/ for subdirectories
    2. Validate each directory has required CSV files
    3. Extract use case name from file pattern
    4. Return metadata for test generation

Usage:
    from tests.fixtures.tutorial_discovery import find_tutorial_directories

    tutorials = find_tutorial_directories()
    for tutorial in tutorials:
        print(f"Found: {tutorial.use_case_name}")
        print(f"  Training: {tutorial.training_data_path}")
        print(f"  Test: {tutorial.test_data_path}")
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class TutorialMetadata:
    """Metadata about a discovered tutorial.

    Attributes:
        use_case_name: Extracted use case identifier (e.g., "invoice")
        directory: Tutorial directory path
        training_data_path: Path to clean training CSV
        test_data_path: Path to test CSV with issues
        directory_name: Name of tutorial directory
    """
    use_case_name: str
    directory: Path
    training_data_path: Path
    test_data_path: Path
    directory_name: str


def find_tutorial_directories(tutorials_root: Optional[Path] = None) -> List[TutorialMetadata]:
    """Find all valid tutorial directories with required CSV files.

    Scans ADRI/tutorials/ for subdirectories that contain valid tutorial data.
    Each tutorial must have exactly two CSV files matching the naming pattern.

    Args:
        tutorials_root: Optional path to tutorials directory.
                       If None, uses ADRI/tutorials/ relative to this file.

    Returns:
        List of TutorialMetadata for each valid tutorial found.
        Empty list if no tutorials found or directory doesn't exist.

    Example:
        tutorials = find_tutorial_directories()
        assert len(tutorials) > 0
        assert all(t.training_data_path.exists() for t in tutorials)
    """
    # Determine tutorials root directory
    if tutorials_root is None:
        # This file is in tests/fixtures/
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        tutorials_root = project_root / "ADRI" / "tutorials"

    # Return empty list if directory doesn't exist
    if not tutorials_root.exists():
        return []

    # Find all subdirectories
    tutorial_dirs = [d for d in tutorials_root.iterdir() if d.is_dir()]

    # Validate each directory and collect metadata
    valid_tutorials = []
    for tutorial_dir in tutorial_dirs:
        is_valid, metadata = validate_tutorial_structure(tutorial_dir)
        if is_valid and metadata:
            valid_tutorials.append(metadata)

    return valid_tutorials


def validate_tutorial_structure(tutorial_dir: Path) -> Tuple[bool, Optional[TutorialMetadata]]:
    """Validate tutorial directory has correct file structure.

    Checks:
    - Directory contains exactly 2 CSV files
    - One file matches pattern: *_data.csv (training data)
    - One file matches pattern: test_*_data.csv (test data)
    - Both files are readable
    - Use case names are consistent

    Args:
        tutorial_dir: Path to tutorial directory to validate

    Returns:
        Tuple of (is_valid, metadata):
        - is_valid: True if structure is valid, False otherwise
        - metadata: TutorialMetadata if valid, None if invalid

    Example:
        is_valid, metadata = validate_tutorial_structure(Path("ADRI/tutorials/invoice"))
        if is_valid:
            assert metadata.use_case_name == "invoice"
    """
    # Find all CSV files in directory
    csv_files = list(tutorial_dir.glob("*.csv"))

    # Must have exactly 2 CSV files
    if len(csv_files) != 2:
        return False, None

    # Try to identify training and test files
    training_file = None
    test_file = None

    for csv_file in csv_files:
        filename = csv_file.name

        # Check if this is a test file (starts with "test_")
        if filename.startswith("test_") and (filename.endswith("_data.csv") or filename.endswith("_contract_data.csv")):
            test_file = csv_file
        # Check if this is a training file (ends with "_data.csv" or "_contract_data.csv" but doesn't start with "test_")
        elif (filename.endswith("_data.csv") or filename.endswith("_contract_data.csv")) and not filename.startswith("test_"):
            training_file = csv_file

    # Both files must be identified
    if training_file is None or test_file is None:
        return False, None

    # Extract use case names and verify consistency
    training_use_case = extract_use_case_name(training_file)
    test_use_case = extract_use_case_name(test_file)

    if training_use_case != test_use_case:
        return False, None

    # Verify files are readable
    try:
        if not training_file.exists() or not test_file.exists():
            return False, None

        # Try to read first line to ensure files are accessible
        with open(training_file, 'r', encoding='utf-8') as f:
            f.readline()
        with open(test_file, 'r', encoding='utf-8') as f:
            f.readline()
    except (OSError, IOError):
        return False, None

    # Build metadata
    metadata = TutorialMetadata(
        use_case_name=training_use_case,
        directory=tutorial_dir,
        training_data_path=training_file,
        test_data_path=test_file,
        directory_name=tutorial_dir.name
    )

    return True, metadata


def extract_use_case_name(file_path: Path) -> str:
    """Extract use case name from CSV file path.

    Parses use case name from file naming pattern:
    - Training file: <use_case>_data.csv
    - Test file: test_<use_case>_data.csv

    Args:
        file_path: Path to CSV file

    Returns:
        Use case name extracted from filename

    Example:
        name = extract_use_case_name(Path("invoice_data.csv"))
        assert name == "invoice"

        name = extract_use_case_name(Path("test_invoice_data.csv"))
        assert name == "invoice"

        name = extract_use_case_name(Path("customer_support_data.csv"))
        assert name == "customer_support"
    """
    filename = file_path.name

    # Handle test files: test_<use_case>_data.csv or test_<use_case>_contract_data.csv
    if filename.startswith("test_"):
        # Remove "test_" prefix and suffix
        use_case = filename[5:]  # Remove "test_"
        if use_case.endswith("_contract_data.csv"):
            use_case = use_case[:-18]  # Remove "_contract_data.csv" (18 chars)
        elif use_case.endswith("_data.csv"):
            use_case = use_case[:-9]  # Remove "_data.csv"
        return use_case

    # Handle training files: <use_case>_data.csv or <use_case>_contract_data.csv
    if filename.endswith("_contract_data.csv"):
        use_case = filename[:-18]  # Remove "_contract_data.csv" (18 chars)
        return use_case
    elif filename.endswith("_data.csv"):
        use_case = filename[:-9]  # Remove "_data.csv"
        return use_case

    # Fallback: return filename without extension
    return file_path.stem
