"""Baseline regression testing utilities for ADRI tutorials.

This module provides functionality for capturing and comparing baseline artifacts
from tutorial test runs to detect framework regressions. The system automatically:

1. Captures baseline artifacts on first run (self-initializing)
2. Compares subsequent runs against baselines
3. Auto-heals missing baseline files (copies current to baseline)
4. Provides detailed diff reports for regressions

Baseline artifacts (4 files per tutorial):
- <use_case>_data_ADRI_standard.yaml: Generated standard
- adri_assessment_logs.jsonl: Assessment results (JSONL format)
- adri_dimension_scores.jsonl: Dimension breakdowns (JSONL format)
- adri_failed_validations.jsonl: Validation failures (JSONL format)

Directory Structure:
    ADRI/tutorials/<tutorial>/
    ├── <use_case>_data.csv
    ├── test_<use_case>_data.csv
    └── baseline_outcome/              # Auto-created on first run
        ├── <use_case>_data_ADRI_standard.yaml
        ├── adri_assessment_logs.jsonl
        ├── adri_dimension_scores.jsonl
        └── adri_failed_validations.jsonl

Usage:
    # In test function
    status = check_baseline_status(tutorial_metadata)

    if status.is_first_run:
        # Capture baseline and skip test
        artifacts = get_generated_artifacts(project_root, use_case_name)
        capture_baseline_artifacts(tutorial_dir, artifacts)
        pytest.skip("First run: baseline captured")
    else:
        # Compare with baseline
        artifacts = get_generated_artifacts(project_root, use_case_name)
        baseline_dir = get_baseline_directory(tutorial_metadata)
        results = compare_with_baseline(artifacts, baseline_dir)

        # Assert no differences
        failures = [r for r in results if not r.matches]
        if failures:
            diff_report = format_diff_report(failures)
            pytest.fail(diff_report)
"""

import csv
import json
import pandas as pd
import shutil
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# Type Definitions
# ============================================================================

@dataclass
class BaselineArtifact:
    """Metadata for a baseline artifact file.

    Attributes:
        artifact_type: Type of artifact (standard, assessment_log, etc.)
        filename: Name of the artifact file
        baseline_path: Path to baseline version
        current_path: Path to current generated version
        file_format: Format of file (yaml, csv)
    """
    artifact_type: str
    filename: str
    baseline_path: Path
    current_path: Path
    file_format: str


@dataclass
class ComparisonResult:
    """Result of comparing current artifact with baseline.

    Attributes:
        artifact: The artifact being compared
        matches: Whether current matches baseline
        differences: List of specific differences found
        diff_summary: Human-readable summary of differences
        auto_healed: Whether baseline was auto-regenerated
    """
    artifact: BaselineArtifact
    matches: bool
    differences: List[Dict[str, Any]]
    diff_summary: str
    auto_healed: bool = False


@dataclass
class BaselineStatus:
    """Status of baseline for a tutorial.

    Attributes:
        exists: Whether baseline_outcome/ folder exists
        artifact_count: Number of baseline artifacts found
        is_first_run: True if this is initial baseline capture
        missing_artifacts: List of expected but missing artifacts
    """
    exists: bool
    artifact_count: int
    is_first_run: bool
    missing_artifacts: List[str]


# ============================================================================
# Directory and Status Functions
# ============================================================================

def get_baseline_directory(tutorial_metadata) -> Path:
    """Returns path to baseline_outcome/ for given tutorial.

    Creates directory if it doesn't exist.

    Args:
        tutorial_metadata: TutorialMetadata from discovery

    Returns:
        Path to baseline_outcome/ directory

    Example:
        baseline_dir = get_baseline_directory(metadata)
        # Returns: ADRI/tutorials/invoice_processing/baseline_outcome/
    """
    baseline_dir = tutorial_metadata.directory / "baseline_outcome"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    return baseline_dir


def check_baseline_status(tutorial_metadata) -> BaselineStatus:
    """Checks if baseline exists for tutorial.

    Args:
        tutorial_metadata: TutorialMetadata from discovery

    Returns:
        BaselineStatus with existence and artifact counts

    Example:
        status = check_baseline_status(metadata)
        if status.is_first_run:
            # Capture baseline
        else:
            # Compare with baseline
    """
    baseline_dir = tutorial_metadata.directory / "baseline_outcome"

    if not baseline_dir.exists():
        return BaselineStatus(
            exists=False,
            artifact_count=0,
            is_first_run=True,
            missing_artifacts=[]
        )

    # Count baseline artifacts
    # Note: Standard filename can be either format depending on when baseline was captured
    # - {use_case}_data.yaml (current format from TutorialScenarios)
    # - {use_case}_data_ADRI_standard.yaml (legacy format)
    expected_artifacts = [
        f"{tutorial_metadata.use_case_name}_data.yaml",  # Current standard filename
        "adri_assessment_logs.jsonl",
        "adri_dimension_scores.jsonl",
        "adri_failed_validations.jsonl"
    ]
    # Also check for legacy standard filename
    legacy_standard_name = f"{tutorial_metadata.use_case_name}_data_ADRI_standard.yaml"

    existing_artifacts = []
    missing_artifacts = []

    for artifact_name in expected_artifacts:
        artifact_path = baseline_dir / artifact_name
        if artifact_path.exists():
            existing_artifacts.append(artifact_name)
        else:
            missing_artifacts.append(artifact_name)

    # First run if no artifacts exist
    is_first_run = len(existing_artifacts) == 0

    return BaselineStatus(
        exists=True,
        artifact_count=len(existing_artifacts),
        is_first_run=is_first_run,
        missing_artifacts=missing_artifacts
    )


# ============================================================================
# Artifact Collection Functions
# ============================================================================

def get_generated_artifacts(project_root: Path, use_case_name: str) -> Dict[str, Path]:
    """Collects all artifacts generated during tutorial test.

    Locates the 4 artifact types:
    1. Standard YAML in ADRI/dev/contracts/
    2. Assessment log JSONL in ADRI/dev/audit-logs/
    3. Dimension scores JSONL in ADRI/dev/audit-logs/
    4. Failed validations JSONL in ADRI/dev/audit-logs/

    Args:
        project_root: Test project root directory
        use_case_name: Tutorial use case name (e.g., "invoice")

    Returns:
        Dict mapping artifact type to file path

    Example:
        artifacts = get_generated_artifacts(project_root, "invoice")
        # Returns: {
        #   'standard': Path('ADRI/dev/contracts/invoice_data.yaml'),
        #   'assessment_log': Path('ADRI/dev/audit-logs/adri_assessment_logs.jsonl'),
        #   ...
        # }
    """
    artifacts = {}

    # 1. Standard YAML - check contracts/ directory with simple naming (actual location)
    # TutorialScenarios.generate_standard_from_data saves to contracts/{use_case}_data.yaml
    standard_path = project_root / "ADRI" / "dev" / "contracts" / f"{use_case_name}_data.yaml"
    if standard_path.exists():
        artifacts['standard'] = standard_path
    else:
        # Fallback: check standards/ directory with _ADRI_standard suffix (legacy location)
        standard_path_legacy = project_root / "ADRI" / "dev" / "standards" / f"{use_case_name}_data_ADRI_standard.yaml"
        if standard_path_legacy.exists():
            artifacts['standard'] = standard_path_legacy

    # 2. Assessment log JSONL
    audit_logs_dir = project_root / "ADRI" / "dev" / "audit-logs"

    assessment_log_path = audit_logs_dir / "adri_assessment_logs.jsonl"
    if assessment_log_path.exists():
        artifacts['assessment_log'] = assessment_log_path

    # 3. Dimension scores JSONL
    dimension_scores_path = audit_logs_dir / "adri_dimension_scores.jsonl"
    if dimension_scores_path.exists():
        artifacts['dimension_scores'] = dimension_scores_path

    # 4. Failed validations JSONL
    failed_validations_path = audit_logs_dir / "adri_failed_validations.jsonl"
    if failed_validations_path.exists():
        artifacts['failed_validations'] = failed_validations_path

    return artifacts


# ============================================================================
# Baseline Capture Functions
# ============================================================================

def capture_baseline_artifacts(tutorial_dir: Path, generated_files: Dict[str, Path]) -> None:
    """Copies generated artifacts to baseline_outcome/.

    Creates baseline_outcome/ if needed and copies each artifact with
    appropriate naming.

    Args:
        tutorial_dir: Tutorial directory (e.g., ADRI/tutorials/invoice_processing/)
        generated_files: Dict from get_generated_artifacts()

    Example:
        artifacts = get_generated_artifacts(project_root, "invoice")
        capture_baseline_artifacts(tutorial_dir, artifacts)
        # Creates baseline_outcome/ with 4 baseline files
    """
    baseline_dir = tutorial_dir / "baseline_outcome"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    # Copy each artifact to baseline
    for artifact_type, source_path in generated_files.items():
        if artifact_type == 'standard':
            # Keep original standard filename
            dest_path = baseline_dir / source_path.name
        else:
            # Use consistent CSV naming
            dest_path = baseline_dir / source_path.name

        shutil.copy2(source_path, dest_path)
        print(f"✓ Captured baseline: {dest_path.name}")


# ============================================================================
# Comparison Functions
# ============================================================================

def compare_yaml_files(current: Path, baseline: Path) -> Optional[Dict[str, Any]]:
    """YAML-specific comparison logic.

    Compares YAML files while ignoring volatile fields like timestamps.

    Args:
        current: Path to current YAML file
        baseline: Path to baseline YAML file

    Returns:
        Dict of differences or None if identical

    Example:
        diff = compare_yaml_files(current_path, baseline_path)
        if diff:
            print(f"Found {len(diff['changed_fields'])} differences")
    """
    with open(current, 'r', encoding='utf-8') as f:
        current_data = yaml.safe_load(f)

    with open(baseline, 'r', encoding='utf-8') as f:
        baseline_data = yaml.safe_load(f)

    # Fields to ignore in comparison (volatile)
    ignore_fields = ['timestamp', 'created_date', 'last_modified', 'generated_at']

    def remove_ignored_fields(data, path=""):
        """Recursively remove ignored fields from data structure."""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if key not in ignore_fields:
                    cleaned[key] = remove_ignored_fields(value, f"{path}.{key}")
            return cleaned
        elif isinstance(data, list):
            return [remove_ignored_fields(item, f"{path}[{i}]") for i, item in enumerate(data)]
        else:
            return data

    # Clean both datasets
    current_clean = remove_ignored_fields(current_data)
    baseline_clean = remove_ignored_fields(baseline_data)

    # Deep comparison
    def find_differences(current, baseline, path=""):
        """Find all differences between two data structures."""
        diffs = []

        if type(current) != type(baseline):
            diffs.append({
                'path': path,
                'type': 'type_mismatch',
                'current': str(type(current)),
                'baseline': str(type(baseline))
            })
            return diffs

        if isinstance(current, dict):
            # Check for added/removed keys
            current_keys = set(current.keys())
            baseline_keys = set(baseline.keys())

            for key in current_keys - baseline_keys:
                diffs.append({
                    'path': f"{path}.{key}" if path else key,
                    'type': 'added_field',
                    'current': current[key],
                    'baseline': None
                })

            for key in baseline_keys - current_keys:
                diffs.append({
                    'path': f"{path}.{key}" if path else key,
                    'type': 'removed_field',
                    'current': None,
                    'baseline': baseline[key]
                })

            # Recursively compare common keys
            for key in current_keys & baseline_keys:
                new_path = f"{path}.{key}" if path else key
                diffs.extend(find_differences(current[key], baseline[key], new_path))

        elif isinstance(current, list):
            if len(current) != len(baseline):
                diffs.append({
                    'path': path,
                    'type': 'length_mismatch',
                    'current': len(current),
                    'baseline': len(baseline)
                })
            else:
                for i, (curr_item, base_item) in enumerate(zip(current, baseline)):
                    diffs.extend(find_differences(curr_item, base_item, f"{path}[{i}]"))

        else:
            # Compare primitive values
            if current != baseline:
                diffs.append({
                    'path': path,
                    'type': 'value_changed',
                    'current': current,
                    'baseline': baseline
                })

        return diffs

    differences = find_differences(current_clean, baseline_clean)

    if differences:
        return {
            'changed_fields': differences,
            'total_changes': len(differences)
        }

    return None


def read_jsonl_as_dataframe(file_path: Path) -> pd.DataFrame:
    """Helper function to read JSONL file as pandas DataFrame.

    Args:
        file_path: Path to JSONL file

    Returns:
        DataFrame with all records from JSONL file

    Example:
        df = read_jsonl_as_dataframe(Path('audit_logs.jsonl'))
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        records = [json.loads(line) for line in f if line.strip()]
    return pd.DataFrame(records)


def compare_jsonl_files(current: Path, baseline: Path) -> Optional[Dict[str, Any]]:
    """JSONL-specific comparison logic.

    Compares JSONL files while ignoring timestamps and IDs.
    Converts JSONL to DataFrame for structured comparison.

    Args:
        current: Path to current JSONL file
        baseline: Path to baseline JSONL file

    Returns:
        Dict of differences or None if identical

    Example:
        diff = compare_jsonl_files(current_path, baseline_path)
        if diff:
            print(f"Row count changed: {diff['row_count_diff']}")
    """
    # Read both JSONL files as DataFrames
    current_df = read_jsonl_as_dataframe(current)
    baseline_df = read_jsonl_as_dataframe(baseline)

    differences = []

    # Compare column sets
    current_cols = set(current_df.columns)
    baseline_cols = set(baseline_df.columns)

    if current_cols != baseline_cols:
        differences.append({
            'type': 'column_mismatch',
            'current': sorted(current_cols),
            'baseline': sorted(baseline_cols)
        })

    # Compare row counts
    if len(current_df) != len(baseline_df):
        differences.append({
            'type': 'row_count_mismatch',
            'current': len(current_df),
            'baseline': len(baseline_df)
        })

    # Compare data structure (ignore volatile fields)
    # Performance metrics like duration and throughput vary between runs
    ignore_columns = [
        'assessment_id',
        'timestamp',
        'hostname',
        'process_id',
        'created_at',
        'standard_path',           # Environment-specific temp directory paths
        'assessment_duration_ms',  # Performance metric - varies between runs
        'rows_per_second',         # Performance metric - varies between runs
        'adri_version'             # Version changes with every commit - not a regression
    ]

    # For most recent rows (last 5), compare non-volatile values
    compare_count = min(5, len(current_df), len(baseline_df))
    if compare_count > 0:
        current_sample = current_df.tail(compare_count)
        baseline_sample = baseline_df.tail(compare_count)

        # Compare common columns only
        common_cols = current_cols & baseline_cols
        comparable_cols = [col for col in common_cols if col not in ignore_columns]

        for idx in range(compare_count):
            row_diffs = []
            for col in comparable_cols:
                curr_val = current_sample.iloc[idx][col]
                base_val = baseline_sample.iloc[idx][col]

                # Compare values, handling NaN and arrays
                try:
                    # Check if both are NaN (handles scalar and array cases)
                    curr_is_na = pd.isna(curr_val).all() if hasattr(pd.isna(curr_val), 'all') else pd.isna(curr_val)
                    base_is_na = pd.isna(base_val).all() if hasattr(pd.isna(base_val), 'all') else pd.isna(base_val)

                    if curr_is_na and base_is_na:
                        continue
                    if curr_is_na or base_is_na or curr_val != base_val:
                        row_diffs.append({
                            'column': col,
                            'current': str(curr_val),
                            'baseline': str(base_val)
                        })
                except (ValueError, TypeError):
                    # Handle complex comparisons by converting to string
                    if str(curr_val) != str(base_val):
                        row_diffs.append({
                            'column': col,
                            'current': str(curr_val),
                            'baseline': str(base_val)
                        })

            if row_diffs:
                differences.append({
                    'type': 'row_value_mismatch',
                    'row_index': idx,
                    'changes': row_diffs
                })

    if differences:
        return {
            'differences': differences,
            'total_changes': len(differences)
        }

    return None


def compare_csv_files(current: Path, baseline: Path) -> Optional[Dict[str, Any]]:
    """CSV-specific comparison logic.

    Compares CSV files while ignoring timestamps and IDs.

    Args:
        current: Path to current CSV file
        baseline: Path to baseline CSV file

    Returns:
        Dict of differences or None if identical

    Example:
        diff = compare_csv_files(current_path, baseline_path)
        if diff:
            print(f"Row count changed: {diff['row_count_diff']}")
    """
    # Read both CSVs
    with open(current, 'r', encoding='utf-8') as f:
        current_reader = csv.DictReader(f)
        current_rows = list(current_reader)
        current_headers = current_reader.fieldnames

    with open(baseline, 'r', encoding='utf-8') as f:
        baseline_reader = csv.DictReader(f)
        baseline_rows = list(baseline_reader)
        baseline_headers = baseline_reader.fieldnames

    differences = []

    # Compare headers
    if current_headers != baseline_headers:
        differences.append({
            'type': 'header_mismatch',
            'current': current_headers,
            'baseline': baseline_headers
        })

    # Compare row counts
    if len(current_rows) != len(baseline_rows):
        differences.append({
            'type': 'row_count_mismatch',
            'current': len(current_rows),
            'baseline': len(baseline_rows)
        })

    # Compare data structure (ignore volatile fields)
    # Performance metrics like duration and throughput vary between runs
    ignore_columns = [
        'assessment_id',
        'timestamp',
        'hostname',
        'process_id',
        'created_at',
        'standard_path',           # Environment-specific temp directory paths
        'assessment_duration_ms',  # Performance metric - varies between runs
        'rows_per_second',         # Performance metric - varies between runs
        'adri_version'             # Version changes with every commit - not a regression
    ]

    # For most recent rows (last 5), compare non-volatile values
    compare_count = min(5, len(current_rows), len(baseline_rows))
    if compare_count > 0:
        current_sample = current_rows[-compare_count:]
        baseline_sample = baseline_rows[-compare_count:]

        for i, (curr_row, base_row) in enumerate(zip(current_sample, baseline_sample)):
            row_diffs = []
            for key in curr_row.keys():
                if key not in ignore_columns:
                    if key in base_row:
                        if curr_row[key] != base_row[key]:
                            row_diffs.append({
                                'column': key,
                                'current': curr_row[key],
                                'baseline': base_row[key]
                            })

            if row_diffs:
                differences.append({
                    'type': 'row_value_mismatch',
                    'row_index': i,
                    'changes': row_diffs
                })

    if differences:
        return {
            'differences': differences,
            'total_changes': len(differences)
        }

    return None


def compare_with_baseline(
    current_artifacts: Dict[str, Path],
    baseline_dir: Path
) -> List[ComparisonResult]:
    """Compares each current artifact with baseline version.

    Auto-heals missing baselines by copying current file to baseline directory.

    Args:
        current_artifacts: Dict from get_generated_artifacts()
        baseline_dir: Path to baseline_outcome/ directory

    Returns:
        List of ComparisonResult objects

    Example:
        results = compare_with_baseline(artifacts, baseline_dir)
        failures = [r for r in results if not r.matches]
        if failures:
            report = format_diff_report(failures)
    """
    results = []

    for artifact_type, current_path in current_artifacts.items():
        # Determine baseline filename
        baseline_filename = current_path.name
        baseline_path = baseline_dir / baseline_filename

        # Auto-heal: If baseline missing, copy current to baseline
        if not baseline_path.exists():
            shutil.copy2(current_path, baseline_path)
            print(f"✓ Baseline auto-healed: {baseline_filename}")

            # Create result showing auto-heal
            artifact = BaselineArtifact(
                artifact_type=artifact_type,
                filename=baseline_filename,
                baseline_path=baseline_path,
                current_path=current_path,
                file_format='yaml' if baseline_filename.endswith('.yaml') else 'csv'
            )

            results.append(ComparisonResult(
                artifact=artifact,
                matches=True,
                differences=[],
                diff_summary="Auto-healed: baseline file was missing and has been regenerated",
                auto_healed=True
            ))
            continue

        # Compare based on file format
        if baseline_filename.endswith('.yaml'):
            file_format = 'yaml'
            diff = compare_yaml_files(current_path, baseline_path)
        elif baseline_filename.endswith('.jsonl'):
            file_format = 'jsonl'
            diff = compare_jsonl_files(current_path, baseline_path)
        else:
            file_format = 'csv'
            diff = compare_csv_files(current_path, baseline_path)

        # Create artifact metadata
        artifact = BaselineArtifact(
            artifact_type=artifact_type,
            filename=baseline_filename,
            baseline_path=baseline_path,
            current_path=current_path,
            file_format=file_format
        )

        # Create comparison result
        if diff is None:
            # Files match
            results.append(ComparisonResult(
                artifact=artifact,
                matches=True,
                differences=[],
                diff_summary="Files match"
            ))
        else:
            # Files differ
            summary = f"Found {diff.get('total_changes', len(diff.get('differences', [])))} differences"
            results.append(ComparisonResult(
                artifact=artifact,
                matches=False,
                differences=diff.get('differences', diff.get('changed_fields', [])),
                diff_summary=summary
            ))

    return results


# ============================================================================
# Diff Reporting Functions
# ============================================================================

def format_diff_report(comparisons: List[ComparisonResult]) -> str:
    """Formats comparison results into human-readable report.

    Args:
        comparisons: List of ComparisonResult objects with differences

    Returns:
        Formatted diff report with update instructions

    Example:
        failures = [r for r in results if not r.matches]
        if failures:
            report = format_diff_report(failures)
            pytest.fail(report)
    """
    lines = []
    lines.append("=" * 80)
    lines.append("BASELINE REGRESSION DETECTED")
    lines.append("=" * 80)
    lines.append("")

    for comparison in comparisons:
        artifact = comparison.artifact
        lines.append(f"File: {artifact.filename}")
        lines.append(f"Type: {artifact.artifact_type}")
        lines.append(f"Format: {artifact.file_format}")
        lines.append("")

        if artifact.file_format == 'yaml':
            lines.append("YAML Differences:")
            for diff in comparison.differences[:10]:  # Show first 10
                path = diff.get('path', 'unknown')
                diff_type = diff.get('type', 'unknown')

                if diff_type == 'value_changed':
                    lines.append(f"  Path: {path}")
                    lines.append(f"    - Baseline: {diff.get('baseline')}")
                    lines.append(f"    + Current:  {diff.get('current')}")
                elif diff_type == 'added_field':
                    lines.append(f"  Added: {path}")
                    lines.append(f"    + Current: {diff.get('current')}")
                elif diff_type == 'removed_field':
                    lines.append(f"  Removed: {path}")
                    lines.append(f"    - Baseline: {diff.get('baseline')}")
                else:
                    lines.append(f"  {diff_type}: {path}")
                lines.append("")

        else:  # CSV
            lines.append("CSV Differences:")
            for diff in comparison.differences[:10]:  # Show first 10
                diff_type = diff.get('type', 'unknown')

                if diff_type == 'header_mismatch':
                    lines.append(f"  Headers changed:")
                    lines.append(f"    - Baseline: {diff.get('baseline')}")
                    lines.append(f"    + Current:  {diff.get('current')}")
                elif diff_type == 'row_count_mismatch':
                    lines.append(f"  Row count changed:")
                    lines.append(f"    - Baseline: {diff.get('baseline')} rows")
                    lines.append(f"    + Current:  {diff.get('current')} rows")
                elif diff_type == 'row_value_mismatch':
                    lines.append(f"  Row {diff.get('row_index')} changed:")
                    for change in diff.get('changes', [])[:5]:  # Show first 5 per row
                        lines.append(f"    Column '{change['column']}':")
                        lines.append(f"      - Baseline: {change['baseline']}")
                        lines.append(f"      + Current:  {change['current']}")
                lines.append("")

        lines.append("-" * 80)
        lines.append("")

    lines.append("")
    lines.append("TO UPDATE BASELINE (if changes are intentional):")
    lines.append("=" * 80)
    lines.append("1. Review the changes above carefully")
    lines.append("2. If intentional, regenerate baseline:")
    lines.append("")
    lines.append("   # Get tutorial directory from the test")
    lines.append("   rm -rf <tutorial_dir>/baseline_outcome/")
    lines.append("   pytest tests/test_tutorial_auto_discovery.py::test_baseline_regression -k <tutorial>")
    lines.append("")
    lines.append("3. Commit updated baseline to git:")
    lines.append("   git add <tutorial_dir>/baseline_outcome/")
    lines.append('   git commit -m "Update baseline for <tutorial>"')
    lines.append("")
    lines.append("IF CHANGES ARE UNEXPECTED:")
    lines.append("=" * 80)
    lines.append("This indicates a framework regression. Investigate:")
    lines.append("- Recent changes to validation rules")
    lines.append("- Modifications to scoring algorithms")
    lines.append("- Updates to standard generation logic")
    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)
