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
from .report import ADRIScoreReport
from .interactive import run_interactive_mode
from .templates import TemplateLoader
from .utils.metadata_generator import MetadataGenerator
from .connectors import FileConnector


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
    assess_parser.add_argument(
        "--template",
        help="Template to evaluate against (ID, file path, or URL)"
    )
    assess_parser.add_argument(
        "--template-version",
        help="Template version (if not specified in template ID)"
    )
    assess_parser.add_argument(
        "--trust-all",
        action="store_true",
        help="Trust all template sources (use with caution)"
    )
    
    # certify command
    certify_parser = subparsers.add_parser(
        "certify",
        help="Assess a data source against certification templates"
    )
    certify_parser.add_argument("--source", required=True, help="Path to data source")
    certify_parser.add_argument(
        "--templates",
        nargs="+",
        required=True,
        help="Templates to evaluate against (IDs, file paths, or URLs)"
    )
    certify_parser.add_argument("--output", required=True, help="Output path for the report")
    certify_parser.add_argument(
        "--format",
        choices=["json", "html", "both"],
        default="both",
        help="Output format(s) for the report"
    )
    certify_parser.add_argument(
        "--source-type",
        choices=["file", "database", "api"],
        help="Type of the data source (auto-detected if not specified)"
    )
    certify_parser.add_argument(
        "--trust-all",
        action="store_true",
        help="Trust all template sources (use with caution)"
    )
    certify_parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only cached templates (offline mode)"
    )
    
    # templates command
    templates_parser = subparsers.add_parser(
        "templates",
        help="Manage certification templates"
    )
    templates_subparsers = templates_parser.add_subparsers(
        dest="templates_command",
        help="Templates command"
    )
    
    # templates list command
    list_templates_parser = templates_subparsers.add_parser(
        "list",
        help="List available templates"
    )
    list_templates_parser.add_argument(
        "--cached",
        action="store_true",
        help="Show only cached templates"
    )
    
    # templates cache command
    cache_parser = templates_subparsers.add_parser(
        "cache",
        help="Manage template cache"
    )
    cache_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the template cache"
    )
    
    # templates info command
    info_parser = templates_subparsers.add_parser(
        "info",
        help="Show information about a template"
    )
    info_parser.add_argument(
        "template",
        help="Template ID, file path, or URL"
    )
    info_parser.add_argument(
        "--trust-all",
        action="store_true",
        help="Trust all template sources"
    )
    
    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Generate starter metadata files for a data source"
    )
    init_parser.add_argument(
        "source",
        help="Path to the data source file (CSV, JSON, etc.)"
    )
    init_parser.add_argument(
        "--output-dir",
        help="Output directory for metadata files (default: same as source file)"
    )
    init_parser.add_argument(
        "--dimensions",
        nargs="+",
        choices=["validity", "completeness", "freshness", "consistency", "plausibility"],
        help="Specific dimensions to generate metadata for (default: all)"
    )
    init_parser.add_argument(
        "--quick",
        action="store_true",
        help="Generate minimal metadata with more TODOs (faster)"
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
        
        # Determine connector based on source type
        if args.source_type == "file" or (not args.source_type and Path(source).is_file()):
            if hasattr(args, 'template') and args.template:
                # Assess with template
                loader_config = {'trust_all': args.trust_all} if hasattr(args, 'trust_all') else {}
                report, evaluation = assessor.assess_file_with_template(
                    source, 
                    args.template,
                    template_version=args.template_version if hasattr(args, 'template_version') else None
                )
                # Print evaluation summary
                print(f"\nTemplate Evaluation: {evaluation.get_summary()}")
                if evaluation.gaps:
                    print(f"Gaps found: {len(evaluation.gaps)}")
                    for gap in evaluation.gaps[:3]:  # Show first 3 gaps
                        print(f"  - {gap.requirement_description}: {gap.actual_value} (expected: {gap.expected_value})")
                    if len(evaluation.gaps) > 3:
                        print(f"  ... and {len(evaluation.gaps) - 3} more gaps")
            else:
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


def run_certify(args):
    """Run certification assessment against multiple templates."""
    assessor = DataSourceAssessor()
    
    # Create template loader with options
    loader_config = {
        'trust_all': args.trust_all,
        'offline_mode': args.offline if hasattr(args, 'offline') else False
    }
    
    # Get the connector for the source
    source = args.source
    if args.source_type == "file" or (not args.source_type and Path(source).is_file()):
        from .connectors import ConnectorRegistry
        connector_class = ConnectorRegistry.get_connector("file")
        connector = connector_class(source)
    else:
        raise ValueError("Only file sources are currently supported for certification")
    
    # Assess against all templates
    report, evaluations = assessor.assess_with_templates(
        connector,
        args.templates,
        loader_config
    )
    
    # Print certification results
    print(f"\nCertification Assessment Results for: {source}")
    print("=" * 60)
    
    for evaluation in evaluations:
        print(f"\n{evaluation.template_name} ({evaluation.template_id} v{evaluation.template_version})")
        print("-" * 40)
        print(f"Status: {evaluation.get_summary()}")
        print(f"Compliance Score: {evaluation.compliance_score:.1f}%")
        
        if evaluation.certification_eligible:
            print("✅ Eligible for certification")
        else:
            print("❌ Not eligible for certification")
            if evaluation.certification_blockers:
                print("Blockers:")
                for blocker in evaluation.certification_blockers:
                    print(f"  - {blocker}")
        
        if evaluation.recommendations:
            print("Recommendations:")
            for rec in evaluation.recommendations[:3]:
                print(f"  - {rec}")
    
    # Save the report
    output_path = Path(args.output)
    if args.format in ("json", "both"):
        json_path = f"{output_path}.json" if not str(output_path).endswith(".json") else output_path
        report.save_json(json_path)
        print(f"\nDetailed report saved to: {json_path}")
    
    if args.format in ("html", "both"):
        html_path = f"{output_path}.html" if not str(output_path).endswith(".html") else output_path
        report.save_html(html_path)
        print(f"HTML report saved to: {html_path}")


def handle_templates_command(args):
    """Handle templates subcommands."""
    if args.templates_command == "list":
        list_templates(args)
    elif args.templates_command == "cache":
        manage_cache(args)
    elif args.templates_command == "info":
        show_template_info(args)
    else:
        print("No templates subcommand specified. Use --help for usage information.")


def list_templates(args):
    """List available templates."""
    loader = TemplateLoader()
    
    if args.cached:
        # Show cached templates
        cached = loader.list_cached()
        if not cached:
            print("No cached templates found.")
            return
            
        print("Cached Templates:")
        print("-" * 60)
        for item in cached:
            status = "❌ Expired" if item['expired'] else "✅ Valid"
            print(f"{status} {item['url']} (cached: {item['cached_at'][:10]})")
    else:
        # Show available shortcuts
        print("Available Template Shortcuts:")
        print("-" * 60)
        for shortcut, url in TemplateLoader.REGISTRY_SHORTCUTS.items():
            print(f"{shortcut:15} -> {url}")
        
        print("\nYou can also use:")
        print("- Local file paths (e.g., ./my-template.yaml)")
        print("- URLs (e.g., https://example.com/template.yaml)")
        print("- Template IDs from the registry")


def manage_cache(args):
    """Manage template cache."""
    loader = TemplateLoader()
    
    if args.clear:
        loader.clear_cache()
        print("Template cache cleared successfully.")
    else:
        # Show cache status
        cached = loader.list_cached()
        total_size = sum(item['size'] for item in cached)
        valid_count = sum(1 for item in cached if not item['expired'])
        
        print(f"Template Cache Status:")
        print(f"  Location: {loader.cache_dir}")
        print(f"  Templates: {len(cached)} ({valid_count} valid)")
        print(f"  Total size: {total_size:,} bytes")


def show_template_info(args):
    """Show information about a template."""
    loader_config = {'trust_all': args.trust_all}
    loader = TemplateLoader(**loader_config)
    
    try:
        template = loader.load_template(args.template)
        metadata = template.get_metadata()
        
        print(f"\nTemplate Information:")
        print("=" * 60)
        print(f"ID: {metadata['id']}")
        print(f"Name: {metadata['name']}")
        print(f"Version: {metadata['version']}")
        print(f"Authority: {metadata['authority']}")
        print(f"Description: {metadata['description']}")
        
        if metadata.get('effective_date'):
            print(f"Effective Date: {metadata['effective_date']}")
        
        if metadata.get('jurisdiction'):
            print(f"Jurisdiction: {', '.join(metadata['jurisdiction'])}")
        
        # Show requirements summary
        req_summary = metadata.get('requirements_summary', {})
        print(f"\nRequirements Summary:")
        print(f"  Overall minimum score: {req_summary.get('overall_minimum_score', 'Not specified')}")
        
        dims = req_summary.get('dimensions_with_requirements', [])
        if dims:
            print(f"  Dimensions with requirements: {', '.join(dims)}")
        
        if req_summary.get('has_custom_rules'):
            print("  ✓ Has custom validation rules")
        
        if req_summary.get('has_mandatory_fields'):
            print("  ✓ Has mandatory field requirements")
        
        # Show certification info
        cert_info = template.get_certification_info()
        print(f"\nCertification Details:")
        print(f"  Authority: {cert_info['certifying_authority']}")
        print(f"  Certification: {cert_info['certification_name']}")
        print(f"  ID Prefix: {cert_info['certification_id_prefix']}")
        print(f"  Validity Period: {cert_info['validity_period_days']} days")
        
    except Exception as e:
        print(f"Error loading template: {e}")
        if args.trust_all:
            import traceback
            traceback.print_exc()


def view_report(args):
    """View a report."""
    report = ADRIScoreReport.load_json(args.report_path)
    report.print_summary()


def run_init(args):
    """Generate starter metadata files for a data source."""
    source_path = Path(args.source)
    
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        return 1
        
    print(f"Analyzing data source: {source_path}")
    print("-" * 60)
    
    try:
        # Create a file connector to load the data
        connector = FileConnector(source_path)
        
        # Create metadata generator
        generator = MetadataGenerator(connector)
        
        # Determine output directory
        output_dir = Path(args.output_dir) if args.output_dir else source_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate metadata file
        print(f"Generating metadata file in: {output_dir}")
        
        if args.dimensions:
            # Generate only specified dimensions
            print(f"Note: Generating metadata for specific dimensions: {', '.join(args.dimensions)}")
            print("(The file will still contain all dimensions, but only requested ones will have data)")
            
        # Generate the combined metadata file
        metadata_file = generator.generate_all_metadata(output_dir)
        print(f"✓ Generated metadata file: {metadata_file.name}")
        
        print("\n" + "=" * 60)
        print("✅ Metadata files generated successfully!")
        print("\nNext steps:")
        print("1. Review the generated files and fill in the TODO sections")
        print("2. Verify that auto-detected types and patterns are correct")
        print("3. Add domain-specific rules and business logic")
        print("4. Run 'adri assess' to see how your data scores with the metadata")
        
        if args.quick:
            print("\nNote: Quick mode was used - files contain minimal analysis.")
            print("Consider running without --quick for more thorough detection.")
            
    except Exception as e:
        print(f"Error generating metadata: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
        
    return 0

def submit_benchmark(args):
    """Submit a report to the benchmark."""
    from datetime import datetime
    import uuid
    report = ADRIScoreReport.load_json(args.report_path)
    
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
        elif parsed_args.command == "certify":
            run_certify(parsed_args)
        elif parsed_args.command == "templates":
            handle_templates_command(parsed_args)
        elif parsed_args.command == "init":
            return run_init(parsed_args)
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
