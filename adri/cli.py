"""
Command-line interface for the Agent Data Readiness Index.

This module provides a command-line interface for running ADRI assessments
and generating reports. It also includes an interactive mode for guided assessments.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .assessor import DataSourceAssessor
from .report import AssessmentReport
from .interactive import run_interactive_mode


def setup_logging(verbose: bool = False):
    """Set up logging with appropriate level based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def parse_args(args: Optional[List[str]] = None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Agent Data Readiness Index - Evaluate data sources for agent readiness"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", 
        help="Start interactive assessment mode with guided prompts",
        description="Start interactive assessment mode with guided prompts for data source assessment."
    )
    
    # assess command
    assess_parser = subparsers.add_parser("assess", help="Assess a data source")
    source_group = assess_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", help="Path to data source or connection string")
    source_group.add_argument("--config", help="Path to configuration file for multiple sources")
    assess_parser.add_argument("--output", required=True, help="Output path for the report")
    assess_parser.add_argument(
        "--format", 
        choices=["json", "html", "both"], 
        default="both",
        help="Output format(s) for the report"
    )
    assess_parser.add_argument(
        "--source-type", 
        choices=["file", "database", "api"],
        help="Type of the data source (auto-detected if not specified)"
    )
    assess_parser.add_argument("--table", help="Table name for database sources")
    assess_parser.add_argument("--custom-config", help="Path to custom assessment configuration")
    assess_parser.add_argument(
        "--dimensions",
        nargs="+",
        help="Specific dimensions to assess (default: all available dimensions)"
    )
    
    # report command
    report_parser = subparsers.add_parser("report", help="Work with assessment reports")
    report_subparsers = report_parser.add_subparsers(dest="report_command", help="Report command")
    
    # report view command
    view_parser = report_subparsers.add_parser("view", help="View an assessment report")
    view_parser.add_argument("report_path", help="Path to the report file")
    
    # Common arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args(args)


def run_assessment(args):
    """Run an assessment based on command-line arguments."""
    # Create assessor with specified dimensions if provided
    dimensions = args.dimensions if hasattr(args, 'dimensions') and args.dimensions else None
    assessor = DataSourceAssessor(dimensions=dimensions)
    
    if args.config:
        # Assess multiple sources from config file
        reports = assessor.assess_from_config(args.config)
        
        # Save all reports
        for source_name, report in reports.items():
            base_path = Path(args.output)
            output_dir = base_path if base_path.is_dir() else base_path.parent
            file_prefix = f"{source_name.replace(' ', '_').lower()}_"
            
            if args.format in ("json", "both"):
                report.save_json(output_dir / f"{file_prefix}report.json")
            
            if args.format in ("html", "both"):
                report.save_html(output_dir / f"{file_prefix}report.html")
                
            # Print summary to console
            report.print_summary()
            
    else:
        # Assess a single source
        source = args.source
        
        if args.source_type == "file" or (not args.source_type and Path(source).is_file()):
            report = assessor.assess_file(source)
        elif args.source_type == "database" or (not args.source_type and "://" in source):
            if not args.table:
                raise ValueError("Table name is required for database sources")
            report = assessor.assess_database(source, args.table)
        elif args.source_type == "api":
            report = assessor.assess_api(source)
        else:
            raise ValueError(f"Could not determine source type for: {source}")
            
        # Save the report
        if args.format in ("json", "both"):
            report.save_json(f"{args.output}.json" if not args.output.endswith(".json") else args.output)
        
        if args.format in ("html", "both"):
            report.save_html(f"{args.output}.html" if not args.output.endswith(".html") else args.output)
            
        # Print summary to console
        report.print_summary()


def view_report(args):
    """View a report."""
    report = AssessmentReport.load_json(args.report_path)
    report.print_summary()

def submit_benchmark(args):
    """Submit a report to the benchmark."""
    from datetime import datetime
    import uuid
    report = AssessmentReport.load_json(args.report_path)
    
    # This would typically upload to a benchmark service
    # For GitHub-based solution, we'll save to the benchmark directory
    benchmark_dir = Path(__file__).parent.parent / "benchmark" / "data"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    # Anonymize if requested
    if hasattr(args, "anonymize") and args.anonymize:
        # Keep only necessary data for benchmarking
        report.source_name = f"Anonymous {args.industry} Source"
        report.source_metadata = {
            "industry": args.industry,
            "anonymized": True,
            "submission_date": datetime.now().isoformat(),
        }
        
    # Generate a unique ID for the submission
    benchmark_id = str(uuid.uuid4())[:8]
    benchmark_file = benchmark_dir / f"{args.industry.lower().replace(' ', '_')}_{benchmark_id}.json"
    report.save_json(benchmark_file)
    
    print(f"Report submitted to benchmark as {benchmark_file.name}")
    print("The benchmark will be updated automatically within 24 hours.")
    print("You can view the updated benchmark at https://username.github.io/agent-data-readiness-index/")

def main(args=None):
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)
    setup_logging(parsed_args.verbose)
    
    try:
        if parsed_args.command == "interactive":
            return run_interactive_mode()
        elif parsed_args.command == "assess":
            run_assessment(parsed_args)
        elif parsed_args.command == "report":
            if parsed_args.report_command == "view":
                view_report(parsed_args)
        else:
            print("No command specified. Use --help for usage information.")
            return 1
    except Exception as e:
        logging.error(f"Error: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
