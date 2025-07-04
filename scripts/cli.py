#!/usr/bin/env python3
"""
Simple CLI entry point for ADRI V2.

This provides a basic command-line interface for testing the assess command.
"""

import argparse
import sys
from pathlib import Path

# Add the adri package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adri.cli import (
    assess_command,
    clean_cache_command,
    explain_failure_command,
    export_report_command,
    generate_adri_standard_command,
    list_assessments_command,
    list_standards_command,
    list_training_data_command,
    setup_command,
    show_config_command,
    show_standard_command,
    validate_standard_command,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADRI V2 - Data Quality Assessment Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Initialize ADRI in a project")
    setup_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration"
    )
    setup_parser.add_argument("--project-name", help="Custom project name")
    setup_parser.add_argument(
        "--config-path", help="Custom config file location (default: adri-config.yaml)"
    )

    # Assess command
    assess_parser = subparsers.add_parser("assess", help="Run data quality assessment")
    assess_parser.add_argument(
        "data_path",
        help="Path to data file (CSV, JSON, Parquet) - can be relative to training_data directory",
    )
    assess_parser.add_argument(
        "--standard",
        required=True,
        help="Path to YAML standard file - can be relative to standards directory",
    )
    assess_parser.add_argument(
        "--output",
        help="Path to save assessment report (JSON) - defaults to assessments directory",
    )
    assess_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    assess_parser.add_argument(
        "--env", help="Environment to use (development/production)"
    )
    assess_parser.add_argument("--config-path", help="Specific config file path")

    # Validate-standard command
    validate_parser = subparsers.add_parser(
        "validate-standard", help="Validate YAML standard file"
    )
    validate_parser.add_argument("standard_path", help="Path to YAML standard file")
    validate_parser.add_argument(
        "--output", help="Path to save validation report (JSON)"
    )
    validate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    # Show-config command
    config_parser = subparsers.add_parser(
        "show-config", help="Show current ADRI configuration"
    )
    config_parser.add_argument("--env", help="Show specific environment only")
    config_parser.add_argument(
        "--paths-only", action="store_true", help="Show only path information"
    )
    config_parser.add_argument(
        "--validate", action="store_true", help="Validate configuration and paths"
    )
    config_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )
    config_parser.add_argument("--config-path", help="Specific config file path")

    # Generate-standard command
    generate_parser = subparsers.add_parser(
        "generate-standard", help="Generate ADRI standard from data file analysis"
    )
    generate_parser.add_argument(
        "data_path",
        help="Path to data file (CSV, JSON, Parquet) - can be relative to training_data directory",
    )
    generate_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing standard file"
    )
    generate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    generate_parser.add_argument(
        "--env", help="Environment to use (development/production)"
    )
    generate_parser.add_argument("--config-path", help="Specific config file path")

    # List-standards command
    list_standards_parser = subparsers.add_parser(
        "list-standards", help="List available YAML standards"
    )
    list_standards_parser.add_argument(
        "--env", help="Environment to list standards from (development/production)"
    )
    list_standards_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with standard details",
    )
    list_standards_parser.add_argument(
        "--config-path", help="Specific config file path"
    )

    # List-training-data command
    list_data_parser = subparsers.add_parser(
        "list-training-data", help="List available training data files"
    )
    list_data_parser.add_argument(
        "--env", help="Environment to list training data from (development/production)"
    )
    list_data_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with file details",
    )
    list_data_parser.add_argument("--config-path", help="Specific config file path")

    # List-assessments command
    list_assessments_parser = subparsers.add_parser(
        "list-assessments", help="List previous assessment reports"
    )
    list_assessments_parser.add_argument(
        "--recent",
        type=int,
        default=10,
        help="Number of recent assessments to show (default: 10)",
    )
    list_assessments_parser.add_argument(
        "--env", help="Environment to list assessments from (development/production)"
    )
    list_assessments_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with assessment details",
    )
    list_assessments_parser.add_argument(
        "--config-path", help="Specific config file path"
    )

    # Clean-cache command
    clean_cache_parser = subparsers.add_parser(
        "clean-cache", help="Clean cached assessment results and temporary files"
    )
    clean_cache_parser.add_argument(
        "--env", help="Environment to clean cache from (development/production)"
    )
    clean_cache_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    clean_cache_parser.add_argument("--config-path", help="Specific config file path")
    clean_cache_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    # Export-report command
    export_parser = subparsers.add_parser(
        "export-report", help="Export assessment report for sharing with data teams"
    )
    export_parser.add_argument(
        "--latest", action="store_true", help="Export the most recent assessment report"
    )
    export_parser.add_argument(
        "--assessment-file", help="Specific assessment file to export"
    )
    export_parser.add_argument("--output", help="Where to save the exported report")
    export_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Export format"
    )
    export_parser.add_argument("--env", help="Environment to search for assessments")
    export_parser.add_argument("--config-path", help="Specific config file path")

    # Show-standard command
    show_standard_parser = subparsers.add_parser(
        "show-standard", help="Show details of a specific ADRI standard"
    )
    show_standard_parser.add_argument(
        "standard_name",
        help="Name of the standard to show (with or without .yaml extension)",
    )
    show_standard_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed requirements and rules",
    )
    show_standard_parser.add_argument(
        "--env", help="Environment to search for standard"
    )
    show_standard_parser.add_argument("--config-path", help="Specific config file path")

    # Explain-failure command
    explain_parser = subparsers.add_parser(
        "explain-failure",
        help="Explain assessment failure in detail with actionable recommendations",
    )
    explain_parser.add_argument(
        "--assessment-file", help="Specific assessment file to explain"
    )
    explain_parser.add_argument(
        "--latest", action="store_true", help="Explain the most recent assessment"
    )
    explain_parser.add_argument("--env", help="Environment to search for assessments")
    explain_parser.add_argument("--config-path", help="Specific config file path")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute commands
    if args.command == "setup":
        return setup_command(
            force=args.force,
            project_name=args.project_name,
            config_path=args.config_path,
        )

    elif args.command == "assess":
        return assess_command(
            data_path=args.data_path,
            standard_path=args.standard,
            output_path=args.output,
            verbose=args.verbose,
            environment=args.env,
            config_path=args.config_path,
        )

    elif args.command == "validate-standard":
        return validate_standard_command(
            standard_path=args.standard_path,
            verbose=args.verbose,
            output_path=args.output,
        )

    elif args.command == "show-config":
        return show_config_command(
            environment=args.env,
            paths_only=args.paths_only,
            validate=args.validate,
            format_type=args.format,
            config_path=args.config_path,
        )

    elif args.command == "generate-standard":
        return generate_adri_standard_command(
            data_path=args.data_path,
            force=args.force,
            verbose=args.verbose,
            environment=args.env,
            config_path=args.config_path,
        )

    elif args.command == "list-standards":
        return list_standards_command(
            environment=args.env, verbose=args.verbose, config_path=args.config_path
        )

    elif args.command == "list-training-data":
        return list_training_data_command(
            environment=args.env, verbose=args.verbose, config_path=args.config_path
        )

    elif args.command == "list-assessments":
        return list_assessments_command(
            recent=args.recent,
            environment=args.env,
            verbose=args.verbose,
            config_path=args.config_path,
        )

    elif args.command == "clean-cache":
        return clean_cache_command(
            environment=args.env,
            verbose=args.verbose,
            config_path=args.config_path,
            dry_run=args.dry_run,
        )

    elif args.command == "export-report":
        return export_report_command(
            latest=args.latest,
            assessment_file=args.assessment_file,
            output_path=args.output,
            format_type=args.format,
            environment=args.env,
            config_path=args.config_path,
        )

    elif args.command == "show-standard":
        return show_standard_command(
            standard_name=args.standard_name,
            verbose=args.verbose,
            environment=args.env,
            config_path=args.config_path,
        )

    elif args.command == "explain-failure":
        return explain_failure_command(
            assessment_file=args.assessment_file,
            latest=args.latest,
            environment=args.env,
            config_path=args.config_path,
        )

    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
