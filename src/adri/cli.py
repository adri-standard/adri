"""
ADRI CLI - Streamlined Command Interface

Consolidated CLI from the original 2656-line commands.py into a clean, maintainable structure.
Provides essential commands for data quality assessment and standard management.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml

# Updated imports for new structure - with fallbacks during migration
try:
    from .config.loader import ConfigurationLoader
    from .standards.parser import StandardsParser
    from .validator.engine import DataQualityAssessor
    from .validator.loaders import load_data, load_standard
    from .version import __version__
except ImportError:
    # Fallback to legacy imports during migration
    try:
        from adri.cli.commands import load_data, load_standard
        from adri.config.manager import ConfigManager as ConfigurationLoader
        from adri.core.assessor import DataQualityAssessor
        from adri.standards.loader import StandardsLoader as StandardsParser
        from adri.version import __version__
    except ImportError:
        # Handle missing components gracefully
        DataQualityAssessor = None
        load_data = None
        load_standard = None
        ConfigurationLoader = None
        StandardsParser = None
        __version__ = "unknown"


def setup_command(force: bool = False, project_name: Optional[str] = None) -> int:
    """Initialize ADRI in a project."""
    try:
        config_path = "adri-config.yaml"

        # Check existing configuration
        if os.path.exists(config_path) and not force:
            click.echo("❌ Configuration already exists. Use --force to overwrite.")
            return 1

        # Create default configuration
        if not ConfigurationLoader:
            click.echo("❌ Configuration manager not available")
            return 1

        config_loader = ConfigurationLoader()
        project_name = project_name or Path.cwd().name

        # Create basic config structure
        config = {
            "adri": {
                "project_name": project_name,
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "ADRI/dev/standards",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "ADRI/prod/standards",
                            "assessments": "ADRI/prod/assessments",
                            "training_data": "ADRI/prod/training-data",
                        }
                    },
                },
            }
        }

        # Save configuration
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Create directories
        for env_data in config["adri"]["environments"].values():
            for path in env_data["paths"].values():
                Path(path).mkdir(parents=True, exist_ok=True)

        click.echo("✅ ADRI project initialized successfully!")
        click.echo(f"📁 Project: {project_name}")
        click.echo(f"⚙️  Config: {config_path}")
        return 0

    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")
        return 1


def assess_command(
    data_path: str, standard_path: str, output_path: Optional[str] = None
) -> int:
    """Run data quality assessment."""
    try:
        # Load data
        if not load_data:
            click.echo("❌ Data loader not available")
            return 1

        data_list = load_data(data_path)
        if not data_list:
            click.echo("❌ No data loaded")
            return 1

        # Convert to DataFrame
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Create assessor and run assessment
        if not DataQualityAssessor:
            click.echo("❌ Assessment engine not available")
            return 1

        assessor = DataQualityAssessor()
        result = assessor.assess(data, standard_path)

        # Display results
        click.echo(f"📊 Assessment Score: {result.overall_score:.1f}/100")
        click.echo(f"📋 Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

        # Save report if output specified
        if output_path:
            report_data = result.to_standard_dict()
            with open(output_path, "w") as f:
                json.dump(report_data, f, indent=2)
            click.echo(f"📄 Report saved: {output_path}")

        return 0

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}")
        return 1
    except Exception as e:
        click.echo(f"❌ Assessment failed: {e}")
        return 1


def generate_standard_command(data_path: str, force: bool = False) -> int:
    """Generate ADRI standard from data analysis."""
    try:
        # Load and analyze data
        if not load_data:
            click.echo("❌ Data loader not available")
            return 1

        data_list = load_data(data_path)
        if not data_list:
            click.echo("❌ No data loaded")
            return 1

        # Generate output path
        data_name = Path(data_path).stem
        output_path = f"{data_name}_ADRI_standard.yaml"

        if os.path.exists(output_path) and not force:
            click.echo(f"❌ Standard exists: {output_path}. Use --force to overwrite.")
            return 1

        # Create basic standard structure
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Generate field requirements from data
        field_requirements = {}
        for column in data.columns:
            # Infer type and nullable from data
            non_null_data = data[column].dropna()
            if len(non_null_data) == 0:
                field_type = "string"
            elif non_null_data.dtype in ["int64", "int32"]:
                field_type = "integer"
            elif non_null_data.dtype in ["float64", "float32"]:
                field_type = "float"
            else:
                field_type = "string"

            # Convert numpy boolean to native Python bool
            nullable = bool(data[column].isnull().any())

            field_requirements[column] = {"type": field_type, "nullable": nullable}

        # Create standard dictionary
        standard = {
            "standards": {
                "id": f"{data_name}_standard",
                "name": f"{data_name} ADRI Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": f"Auto-generated standard for {data_name} data",
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": field_requirements,
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0},
                    "completeness": {"minimum_score": 15.0},
                    "consistency": {"minimum_score": 12.0},
                    "freshness": {"minimum_score": 15.0},
                    "plausibility": {"minimum_score": 12.0},
                },
            },
        }

        # Save standard
        with open(output_path, "w") as f:
            yaml.dump(standard, f, default_flow_style=False, sort_keys=False)

        click.echo("✅ Standard generated successfully!")
        click.echo(f"📄 Standard: {standard['standards']['name']}")
        click.echo(f"📁 Saved to: {output_path}")
        return 0

    except Exception as e:
        click.echo(f"❌ Generation failed: {e}")
        return 1


def validate_standard_command(standard_path: str) -> int:
    """Validate YAML standard file."""
    try:
        # Load standard
        if not load_standard:
            click.echo("❌ Standard loader not available")
            return 1

        standard = load_standard(standard_path)

        # Basic validation
        errors = []
        warnings = []

        # Check required sections
        if "standards" not in standard:
            errors.append("Missing 'standards' section")
        elif not isinstance(standard["standards"], dict):
            errors.append("'standards' section must be a dictionary")
        else:
            std_section = standard["standards"]
            required_fields = ["id", "name", "version", "authority"]
            for field in required_fields:
                if field not in std_section:
                    errors.append(f"Missing required field in standards: '{field}'")
                elif not std_section[field]:
                    errors.append(f"Empty value for required field: '{field}'")

        if "requirements" not in standard:
            errors.append("Missing 'requirements' section")
        elif not isinstance(standard["requirements"], dict):
            errors.append("'requirements' section must be a dictionary")

        # Display results
        if errors:
            click.echo("❌ Standard validation FAILED")
            for error in errors:
                click.echo(f"  • {error}")
            return 1
        else:
            click.echo("✅ Standard validation PASSED")
            std_info = standard.get("standards", {})
            click.echo(f"📄 Standard: {std_info.get('name', 'Unknown')}")
            click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
            click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")
            return 0

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        return 1


def list_standards_command() -> int:
    """List available YAML standards."""
    try:
        # Check for bundled standards first
        standards_found = False

        try:
            if StandardsParser:
                parser = StandardsParser()
                bundled_standards = parser.list_available_standards()
                if bundled_standards:
                    click.echo("📦 Bundled Standards:")
                    for i, std_name in enumerate(bundled_standards, 1):
                        click.echo(f"  {i}. {std_name}")
                    standards_found = True
        except:
            pass

        # Check for project standards
        standards_dir = Path("ADRI/dev/standards")
        if standards_dir.exists():
            yaml_files = list(standards_dir.glob("*.yaml")) + list(
                standards_dir.glob("*.yml")
            )
            if yaml_files:
                if standards_found:
                    click.echo()
                click.echo("🏗️  Project Standards:")
                for i, file_path in enumerate(yaml_files, 1):
                    click.echo(f"  {i}. {file_path.name}")
                standards_found = True

        if not standards_found:
            click.echo("📋 No standards found")
            click.echo("💡 Use 'adri generate-standard <data>' to create one")

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to list standards: {e}")
        return 1


def show_config_command(
    paths_only: bool = False, environment: Optional[str] = None
) -> int:
    """Show current ADRI configuration."""
    try:
        # Load configuration
        if not ConfigurationLoader:
            click.echo("❌ Configuration loader not available")
            return 1

        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()

        if not config:
            click.echo("❌ No ADRI configuration found")
            click.echo("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        adri_config = config["adri"]

        if not paths_only:
            click.echo("📋 ADRI Configuration")
            click.echo(f"🏗️  Project: {adri_config['project_name']}")
            click.echo(f"📦 Version: {adri_config.get('version', '4.0.0')}")
            click.echo(f"🌍 Default Environment: {adri_config['default_environment']}")
            click.echo()

        # Show environment paths
        environments_to_show = (
            [environment] if environment else list(adri_config["environments"].keys())
        )

        for env_name in environments_to_show:
            if env_name not in adri_config["environments"]:
                click.echo(f"❌ Environment '{env_name}' not found")
                continue

            env_config = adri_config["environments"][env_name]
            paths = env_config["paths"]

            click.echo(f"📁 {env_name.title()} Environment:")
            for path_type, path_value in paths.items():
                status = "✅" if os.path.exists(path_value) else "❌"
                click.echo(f"  {status} {path_type}: {path_value}")
            click.echo()

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {e}")
        return 1


def list_assessments_command(recent: int = 10, verbose: bool = False) -> int:
    """List previous assessment reports."""
    try:
        # Load configuration to find assessments directory
        config_loader = ConfigurationLoader() if ConfigurationLoader else None
        if config_loader:
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    assessments_dir = Path(env_config["paths"]["assessments"])
                except:
                    assessments_dir = Path("ADRI/dev/assessments")
            else:
                assessments_dir = Path("ADRI/dev/assessments")
        else:
            assessments_dir = Path("ADRI/dev/assessments")

        # Check if assessments directory exists
        if not assessments_dir.exists():
            click.echo("📁 No assessments directory found")
            click.echo(
                "💡 Run 'adri assess <data> --standard <standard>' to create assessments"
            )
            return 0

        # Find JSON assessment files
        assessment_files = list(assessments_dir.glob("*.json"))
        if not assessment_files:
            click.echo("📊 No assessment reports found")
            click.echo(
                "💡 Run 'adri assess <data> --standard <standard>' to create assessments"
            )
            return 0

        # Sort by modification time (newest first) and limit
        assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        if recent > 0:
            assessment_files = assessment_files[:recent]

        click.echo(f"📊 Assessment Reports ({len(assessment_files)} most recent)")
        click.echo(f"📁 Directory: {assessments_dir}")
        click.echo()

        for i, file_path in enumerate(assessment_files, 1):
            file_stats = file_path.stat()
            modified_time = file_stats.st_mtime
            from datetime import datetime

            date_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M")

            click.echo(f"{i:2d}. {file_path.name}")
            click.echo(f"    📅 {date_str}")

            if verbose:
                try:
                    with open(file_path, "r") as f:
                        assessment_data = json.load(f)

                    score = assessment_data.get("overall_score", "Unknown")
                    passed = assessment_data.get("passed", False)
                    status = "✅ PASSED" if passed else "❌ FAILED"
                    click.echo(f"    📊 Score: {score}/100 ({status})")
                except:
                    click.echo("    ⚠️  Could not read assessment details")

            click.echo()

        click.echo("💡 Use --verbose to see assessment scores")
        return 0

    except Exception as e:
        click.echo(f"❌ Failed to list assessments: {e}")
        return 1


def show_standard_command(standard_name: str, verbose: bool = False) -> int:
    """Show details of a specific ADRI standard."""
    try:
        # Try to load standard
        if not load_standard:
            click.echo("❌ Standard loader not available")
            return 1

        # Check if it's a file path or standard name
        if os.path.exists(standard_name):
            standard_path = standard_name
        else:
            # Try common locations
            standard_path = None
            for path in [
                f"ADRI/dev/standards/{standard_name}.yaml",
                f"ADRI/prod/standards/{standard_name}.yaml",
                f"{standard_name}.yaml",
            ]:
                if os.path.exists(path):
                    standard_path = path
                    break

            if not standard_path:
                click.echo(f"❌ Standard not found: {standard_name}")
                click.echo("💡 Use 'adri list-standards' to see available standards")
                return 1

        standard = load_standard(standard_path)
        std_info = standard.get("standards", {})

        click.echo("📋 ADRI Standard Details")
        click.echo(f"📄 Name: {std_info.get('name', 'Unknown')}")
        click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
        click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")
        click.echo(f"🏛️  Authority: {std_info.get('authority', 'Unknown')}")

        if "description" in std_info:
            click.echo(f"📝 Description: {std_info['description']}")

        requirements = standard.get("requirements", {})
        click.echo(
            f"\n🎯 Overall Minimum Score: {requirements.get('overall_minimum', 'Not set')}/100"
        )

        if verbose and "field_requirements" in requirements:
            field_reqs = requirements["field_requirements"]
            click.echo(f"\n📋 Field Requirements ({len(field_reqs)} fields):")
            for field_name, field_config in field_reqs.items():
                field_type = field_config.get("type", "unknown")
                nullable = (
                    "nullable" if field_config.get("nullable", True) else "required"
                )
                click.echo(f"  • {field_name}: {field_type} ({nullable})")

        if verbose and "dimension_requirements" in requirements:
            dim_reqs = requirements["dimension_requirements"]
            click.echo(f"\n📊 Dimension Requirements ({len(dim_reqs)} dimensions):")
            for dim_name, dim_config in dim_reqs.items():
                min_score = dim_config.get("minimum_score", "Not set")
                click.echo(f"  • {dim_name}: ≥{min_score}/20")

        click.echo(
            f"\n💡 Use 'adri assess <data> --standard {standard_name}' to test data"
        )
        return 0

    except Exception as e:
        click.echo(f"❌ Failed to show standard: {e}")
        return 1


# CLI Group Definition
@click.group()
@click.version_option(version=__version__, prog_name="adri")
def cli():
    """ADRI - Stop Your AI Agents Breaking on Bad Data."""
    pass


# Command Definitions
@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--project-name", help="Custom project name")
def setup(force, project_name):
    """Initialize ADRI in a project."""
    sys.exit(setup_command(force, project_name))


@cli.command()
@click.argument("data_path")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option("--output", "output_path", help="Output path for assessment report")
def assess(data_path, standard_path, output_path):
    """Run data quality assessment."""
    sys.exit(assess_command(data_path, standard_path, output_path))


@cli.command("generate-standard")
@click.argument("data_path")
@click.option("--force", is_flag=True, help="Overwrite existing standard file")
def generate_standard(data_path, force):
    """Generate ADRI standard from data file analysis."""
    sys.exit(generate_standard_command(data_path, force))


@cli.command("validate-standard")
@click.argument("standard_path")
def validate_standard(standard_path):
    """Validate YAML standard file."""
    sys.exit(validate_standard_command(standard_path))


@cli.command("list-standards")
def list_standards():
    """List available YAML standards."""
    sys.exit(list_standards_command())


@cli.command("show-config")
@click.option("--paths-only", is_flag=True, help="Show only path information")
@click.option("--environment", help="Show specific environment only")
def show_config(paths_only, environment):
    """Show current ADRI configuration."""
    sys.exit(show_config_command(paths_only, environment))


@cli.command("list-assessments")
@click.option("--recent", default=10, help="Number of recent assessments to show")
@click.option("--verbose", is_flag=True, help="Show detailed assessment information")
def list_assessments(recent, verbose):
    """List previous assessment reports."""
    sys.exit(list_assessments_command(recent, verbose))


@cli.command("show-standard")
@click.argument("standard_name")
@click.option("--verbose", is_flag=True, help="Show detailed requirements and rules")
def show_standard(standard_name, verbose):
    """Show details of a specific ADRI standard."""
    sys.exit(show_standard_command(standard_name, verbose))


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
