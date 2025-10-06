"""
Helper utilities for CLI vs Decorator parity testing.

Provides functions to:
- Set up isolated test environments
- Compare standard YAML files
- Compare assessment CSV logs
- Handle non-deterministic fields
"""

import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any
import pandas as pd


def setup_isolated_environment(base_path: Path) -> Dict[str, Path]:
    """
    Create isolated ADRI environment with separate directories.

    Args:
        base_path: Base directory for the isolated environment

    Returns:
        Dictionary containing paths:
        - config: adri-config.yaml path
        - standards_dir: ADRI/dev/standards
        - assessments_dir: ADRI/dev/assessments
        - logs_dir: ADRI/dev/logs
    """
    base_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    adri_dir = base_path / "ADRI"
    dev_dir = adri_dir / "dev"

    standards_dir = dev_dir / "standards"
    assessments_dir = dev_dir / "assessments"
    logs_dir = dev_dir / "logs"

    for directory in [standards_dir, assessments_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Create config file with correct structure for ConfigurationLoader
    config_path = base_path / "adri-config.yaml"
    config = {
        'adri': {
            'environment': 'development',
            'project_root': str(base_path),
            'standards_directory': str(standards_dir),
            'assessments_directory': str(assessments_dir),
            'audit_logs_directory': str(logs_dir),
            'protection': {
                'default_min_score': 75.0,
                'auto_generate_standards': True,
                'verbose_protection': False
            },
            'audit': {
                'enabled': True,
                'log_location': str(logs_dir / 'adri_assessment_logs.csv'),
                'log_dir': str(logs_dir),
                'log_prefix': 'adri'
            }
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return {
        'config': config_path,
        'standards_dir': standards_dir,
        'assessments_dir': assessments_dir,
        'logs_dir': logs_dir,
        'base_path': base_path
    }


def compare_standards(cli_standard_path: Path, decorator_standard_path: Path) -> None:
    """
    Compare two standard YAML files, ignoring metadata timestamps.

    Args:
        cli_standard_path: Path to CLI-generated standard
        decorator_standard_path: Path to Decorator-generated standard

    Raises:
        AssertionError: If standards differ beyond allowed fields
    """
    # Load both standards
    with open(cli_standard_path, 'r') as f:
        cli_std = yaml.safe_load(f)
    with open(decorator_standard_path, 'r') as f:
        dec_std = yaml.safe_load(f)

    # Remove non-deterministic metadata fields
    for std in [cli_std, dec_std]:
        if 'metadata' in std:
            # Remove timestamps
            for timestamp_field in ['generated_at', 'timestamp', 'created_at']:
                if timestamp_field in std['metadata']:
                    del std['metadata'][timestamp_field]

            # Remove generation-specific metadata
            for gen_field in ['generation_time_ms', 'generator_version', 'standard_name', 'data_source']:
                if gen_field in std['metadata']:
                    del std['metadata'][gen_field]

            # Remove timestamp from freshness metadata
            if 'freshness' in std['metadata'] and isinstance(std['metadata']['freshness'], dict):
                if 'as_of' in std['metadata']['freshness']:
                    del std['metadata']['freshness']['as_of']

            # Remove freshness_scaffolding (contains timestamp in comment)
            if 'freshness_scaffolding' in std['metadata']:
                del std['metadata']['freshness_scaffolding']

    # Deep comparison with detailed diff
    if cli_std != dec_std:
        import json
        print("\n=== STANDARD COMPARISON DEBUG ===")
        print(f"CLI standard: {cli_standard_path}")
        print(f"Decorator standard: {decorator_standard_path}")
        print("\nCLI Standard Keys:", sorted(cli_std.keys()))
        print("Decorator Standard Keys:", sorted(dec_std.keys()))

        # Find differences
        all_keys = set(cli_std.keys()) | set(dec_std.keys())
        differences = []
        for key in sorted(all_keys):
            cli_val = cli_std.get(key)
            dec_val = dec_std.get(key)
            if cli_val != dec_val:
                diff_str = f"\nDifference in '{key}':\n"

                # For metadata, show which sub-keys differ
                if key == 'metadata' and isinstance(cli_val, dict) and isinstance(dec_val, dict):
                    meta_keys = set(cli_val.keys()) | set(dec_val.keys())
                    for mk in sorted(meta_keys):
                        cli_mv = cli_val.get(mk)
                        dec_mv = dec_val.get(mk)
                        if cli_mv != dec_mv:
                            diff_str += f"  metadata.{mk} differs:\n"
                            diff_str += f"    CLI: {str(cli_mv)[:200]}\n"
                            diff_str += f"    DEC: {str(dec_mv)[:200]}\n"
                else:
                    diff_str += f"  CLI: {json.dumps(cli_val, indent=2, default=str)[:1000]}\n"
                    diff_str += f"  DEC: {json.dumps(dec_val, indent=2, default=str)[:1000]}\n"

                differences.append(diff_str)
                print(diff_str)

        if differences:
            assert False, f"Standards differ in {len(differences)} key(s) - see debug output above"


def compare_assessment_logs(cli_log_dir: Path, decorator_log_dir: Path) -> None:
    """
    Compare assessment CSV logs, excluding non-deterministic fields.

    Compares all three CSV log files:
    - adri_assessment_logs.csv
    - adri_dimension_scores.csv
    - adri_failed_validations.csv

    Args:
        cli_log_dir: Directory containing CLI assessment logs
        decorator_log_dir: Directory containing Decorator assessment logs

    Raises:
        AssertionError: If logs differ in deterministic fields
    """
    # Fields to exclude from comparison (non-deterministic)
    EXCLUDE_FIELDS = [
        'assessment_id',
        'timestamp',
        'process_id',
        'hostname',
        'standard_path',  # Contains environment-specific temp directory paths
        'assessment_duration_ms',  # May vary slightly
        'rows_per_second'  # May vary slightly
    ]

    # Log files to compare
    log_files = [
        'adri_assessment_logs.csv',
        'adri_dimension_scores.csv',
        'adri_failed_validations.csv'
    ]

    for log_file in log_files:
        cli_csv = cli_log_dir / log_file
        dec_csv = decorator_log_dir / log_file

        # Check both files exist
        if not cli_csv.exists():
            raise AssertionError(f"CLI log file not found: {cli_csv}")
        if not dec_csv.exists():
            raise AssertionError(f"Decorator log file not found: {dec_csv}")

        # Load CSVs
        cli_df = pd.read_csv(cli_csv)
        dec_df = pd.read_csv(dec_csv)

        # Check same number of rows
        assert len(cli_df) == len(dec_df), (
            f"{log_file}: Different number of records\n"
            f"CLI: {len(cli_df)} records\n"
            f"Decorator: {len(dec_df)} records"
        )

        # Drop excluded fields
        for field in EXCLUDE_FIELDS:
            if field in cli_df.columns:
                cli_df = cli_df.drop(columns=[field])
            if field in dec_df.columns:
                dec_df = dec_df.drop(columns=[field])

        # Sort by remaining fields for consistent comparison
        # Avoid sorting by JSON/text fields that may have varying formats
        sort_cols = [
            c for c in cli_df.columns
            if c not in ['details', 'sample_failures', 'data_columns', 'remediation']
        ]

        if sort_cols:
            cli_df = cli_df.sort_values(sort_cols).reset_index(drop=True)
            dec_df = dec_df.sort_values(sort_cols).reset_index(drop=True)

        # Compare DataFrames
        try:
            pd.testing.assert_frame_equal(
                cli_df,
                dec_df,
                check_dtype=False,  # Allow dtype differences (int vs float)
                check_exact=False,  # Allow small numerical differences
                rtol=1e-3,  # Relative tolerance for floats
                atol=1e-5   # Absolute tolerance for floats
            )
        except AssertionError as e:
            raise AssertionError(
                f"{log_file}: Logs differ in deterministic fields\n"
                f"Comparison error: {str(e)}"
            )


def copy_standard(source_path: Path, dest_path: Path) -> None:
    """
    Copy a standard file from source to destination.

    Args:
        source_path: Source standard file path
        dest_path: Destination standard file path
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_path)


def clear_logs(log_dir: Path) -> None:
    """
    Clear all CSV log files in the specified directory.

    Args:
        log_dir: Directory containing log files
    """
    for csv_file in log_dir.glob("adri_*.csv"):
        csv_file.unlink()
