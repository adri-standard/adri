#!/usr/bin/env python3
"""Pre-commit hook for ADRI schema validation.

This hook validates ADRI schema files (YAML) for consistency issues before commit.
Uses the schema_consistency_validator to check for type conflicts, SQL reserved words,
and other design-time issues.

Exit Codes:
    0: All schemas valid
    1: Validation failures found
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple
import yaml

# Add src to path to import validator
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adri.utils.schema_consistency_validator import (
    SchemaConsistencyValidator,
    ConsistencyIssueSeverity
)


def validate_schema_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a single ADRI schema file.
    
    Args:
        file_path: Path to the YAML schema file
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    try:
        # Load YAML file
        with open(file_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        if not schema:
            errors.append("Empty or invalid YAML file")
            return False, errors
        
        # Check if it's an ADRI schema (has field_requirements)
        has_field_reqs = (
            "field_requirements" in schema or
            ("requirements" in schema and "field_requirements" in schema["requirements"])
        )
        
        if not has_field_reqs:
            # Not an ADRI schema, skip validation
            return True, []
        
        # Validate schema consistency
        validator = SchemaConsistencyValidator(strict_mode=False)
        report = validator.validate(schema)
        
        if report.has_errors():
            errors.append(f"Found {report.issues_found} consistency issue(s):")
            
            # Group by severity
            critical = report.get_issues_by_severity(ConsistencyIssueSeverity.CRITICAL)
            error_issues = report.get_issues_by_severity(ConsistencyIssueSeverity.ERROR)
            warnings = report.get_issues_by_severity(ConsistencyIssueSeverity.WARNING)
            
            if critical:
                errors.append(f"\n  CRITICAL Issues ({len(critical)}):")
                for issue in critical:
                    errors.append(f"    • {issue.field_name}: {issue.message}")
                    if issue.remediation:
                        errors.append(f"      → {issue.remediation}")
            
            if error_issues:
                errors.append(f"\n  ERROR Issues ({len(error_issues)}):")
                for issue in error_issues:
                    errors.append(f"    • {issue.field_name}: {issue.message}")
                    if issue.remediation:
                        errors.append(f"      → {issue.remediation}")
            
            if warnings:
                errors.append(f"\n  WARNING Issues ({len(warnings)}):")
                for issue in warnings:
                    errors.append(f"    • {issue.field_name}: {issue.message}")
        
        is_valid = not report.has_errors()
        return is_valid, errors
        
    except yaml.YAMLError as e:
        errors.append(f"YAML parsing error: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Validation error: {e}")
        return False, errors


def print_validation_report(results: dict) -> None:
    """
    Print formatted validation report.
    
    Args:
        results: Dictionary mapping file paths to validation results
    """
    print("\n" + "=" * 70)
    print("ADRI Schema Validation Report")
    print("=" * 70 + "\n")
    
    total_files = len(results)
    valid_files = sum(1 for is_valid, _ in results.values() if is_valid)
    invalid_files = total_files - valid_files
    
    if invalid_files == 0:
        print(f"✅ All {total_files} schema file(s) passed validation\n")
        return
    
    print(f"❌ {invalid_files} of {total_files} schema file(s) failed validation\n")
    
    for file_path, (is_valid, errors) in results.items():
        if not is_valid:
            print(f"File: {file_path}")
            print("-" * 70)
            for error in errors:
                print(error)
            print()
    
    print("=" * 70)
    print("\nFix the issues above before committing.")
    print("Run 'git diff' to see your changes and update the schemas.\n")


def main() -> int:
    """
    Pre-commit hook entry point.
    
    Returns:
        0 if all schemas valid, 1 if any failures
    """
    # Get staged files from git
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split("\n")
    except subprocess.CalledProcessError:
        # Fallback: use command line arguments
        staged_files = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not staged_files or staged_files == ['']:
        print("No files to validate")
        return 0
    
    # Filter for YAML files in relevant directories
    yaml_files = [
        f for f in staged_files
        if f.endswith(('.yaml', '.yml')) and
        ('contract' in f.lower() or 'standard' in f.lower() or 'ADRI' in f)
    ]
    
    if not yaml_files:
        # No ADRI schema files to validate
        return 0
    
    # Validate each file
    results = {}
    for file_path in yaml_files:
        if os.path.exists(file_path):
            is_valid, errors = validate_schema_file(file_path)
            results[file_path] = (is_valid, errors)
    
    if not results:
        return 0
    
    # Print report
    print_validation_report(results)
    
    # Return exit code
    all_valid = all(is_valid for is_valid, _ in results.values())
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
