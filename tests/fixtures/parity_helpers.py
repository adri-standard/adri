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
        - config: ADRI/config.yaml path
        - standards_dir: ADRI/dev/contracts
        - assessments_dir: ADRI/dev/assessments
        - logs_dir: ADRI/dev/logs
    """
    base_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    adri_dir = base_path / "ADRI"
    dev_dir = adri_dir / "dev"

    contracts_dir = dev_dir / "contracts"
    assessments_dir = dev_dir / "assessments"
    logs_dir = dev_dir / "audit-logs"

    for directory in [contracts_dir, assessments_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Create config file matching both ConfigurationLoader and DataQualityAssessor structures
    config_path = base_path / "ADRI" / "config.yaml"
    config = {
        'adri': {
            'version': '4.0.0',
            'project_name': 'test_project',
            'default_environment': 'development',
            'environments': {
                'development': {
                    'paths': {
                        'contracts': str(contracts_dir),
                        'assessments': str(assessments_dir),
                        'training_data': str(dev_dir / 'training-data'),
                        'audit_logs': str(logs_dir)
                    },
                    'protection': {
                        'default_failure_mode': 'warn',
                        'default_min_score': 75,
                        'cache_duration_hours': 0.5
                    }
                }
            },
            'protection': {
                'default_failure_mode': 'raise',
                'default_min_score': 80,
                'cache_duration_hours': 1,
                'auto_generate_contracts': True,
                'verbose_protection': False
            },
            'audit': {
                'enabled': True,
                'log_dir': str(logs_dir),
                'formats': ['jsonl'],
                'retention_days': 30
            }
        }
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return {
        'config': config_path,
        'contracts_dir': contracts_dir,
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
    with open(cli_standard_path, 'r', encoding='utf-8') as f:
        cli_std = yaml.safe_load(f)
    with open(decorator_standard_path, 'r', encoding='utf-8') as f:
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
    Compare assessment JSONL logs, excluding non-deterministic fields.

    Compares all three JSONL log files:
    - adri_assessment_logs.jsonl
    - adri_dimension_scores.jsonl
    - adri_failed_validations.jsonl

    Args:
        cli_log_dir: Directory containing CLI assessment logs
        decorator_log_dir: Directory containing Decorator assessment logs

    Raises:
        AssertionError: If logs differ in deterministic fields
    """
    import json

    # Fields to exclude from comparison (non-deterministic)
    EXCLUDE_FIELDS = [
        'assessment_id',
        'timestamp',
        'process_id',
        'hostname',
        'standard_path',  # Contains environment-specific temp directory paths
        'assessment_duration_ms',  # May vary slightly
        'rows_per_second',  # May vary slightly
        'write_seq'  # Sequence number may vary
    ]

    # Log files to compare
    log_files = [
        'adri_assessment_logs.jsonl',
        'adri_dimension_scores.jsonl',
        'adri_failed_validations.jsonl'
    ]

    for log_file in log_files:
        cli_jsonl = cli_log_dir / log_file
        dec_jsonl = decorator_log_dir / log_file

        # Check both files exist
        if not cli_jsonl.exists():
            raise AssertionError(f"CLI log file not found: {cli_jsonl}")
        if not dec_jsonl.exists():
            raise AssertionError(f"Decorator log file not found: {dec_jsonl}")

        # Load JSONL files
        cli_records = []
        with open(cli_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    cli_records.append(json.loads(line))

        dec_records = []
        with open(dec_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    dec_records.append(json.loads(line))

        # Check same number of records
        assert len(cli_records) == len(dec_records), (
            f"{log_file}: Different number of records\n"
            f"CLI: {len(cli_records)} records\n"
            f"Decorator: {len(dec_records)} records"
        )

        # Remove excluded fields from records
        for record in cli_records + dec_records:
            for field in EXCLUDE_FIELDS:
                if field in record:
                    del record[field]
                # Also check nested fields
                if 'assessment_metadata' in record:
                    for nested_field in EXCLUDE_FIELDS:
                        if nested_field in record['assessment_metadata']:
                            del record['assessment_metadata'][nested_field]

        # Compare records (order may vary, so compare as sets)
        # Convert to JSON strings for comparison
        cli_set = {json.dumps(r, sort_keys=True) for r in cli_records}
        dec_set = {json.dumps(r, sort_keys=True) for r in dec_records}

        if cli_set != dec_set:
            missing_in_dec = cli_set - dec_set
            missing_in_cli = dec_set - cli_set
            error_msg = f"{log_file}: Logs differ in deterministic fields\n"
            if missing_in_dec:
                error_msg += f"Records in CLI but not Decorator: {len(missing_in_dec)}\n"
            if missing_in_cli:
                error_msg += f"Records in Decorator but not CLI: {len(missing_in_cli)}\n"
            raise AssertionError(error_msg)


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
    Clear all JSONL log files in the specified directory.

    Args:
        log_dir: Directory containing log files
    """
    for jsonl_file in log_dir.glob("adri_*.jsonl"):
        jsonl_file.unlink()
