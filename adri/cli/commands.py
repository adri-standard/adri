"""
CLI command implementations for ADRI V2.

This module contains the actual implementation of CLI commands.
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    import pandas as pd
except ImportError:
    pd = None

from ..analysis.data_profiler import DataProfiler
from ..analysis.standard_generator import StandardGenerator
from ..config.manager import ConfigManager
from ..core.assessor import AssessmentEngine
from ..version import __version__


def setup_command(
    force: bool = False,
    project_name: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Initialize ADRI in a project.

    Args:
        force: Overwrite existing configuration
        project_name: Custom project name (default: current directory name)
        config_path: Custom config file location (default: ADRI/adri-config.yaml)

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Determine config path - default to adri-config.yaml in current directory
        if config_path is None:
            config_path = "adri-config.yaml"

        # Check for existing configuration
        if os.path.exists(config_path) and not force:
            print(f"❌ Error: Configuration already exists at {config_path}")
            print("💡 Fix: Use --force to overwrite existing configuration")
            return 1

        # Determine project name
        if project_name is None:
            project_name = Path.cwd().name

        # Create configuration manager
        config_manager = ConfigManager()

        # Create default configuration
        config = config_manager.create_default_config(project_name)

        # Create parent directory if it doesn't exist
        config_dir = Path(config_path).parent
        if config_dir != Path("."):  # Only create if not current directory
            config_dir.mkdir(parents=True, exist_ok=True)

        # Save configuration
        config_manager.save_config(config, config_path)

        # Create directory structure
        config_manager.create_directory_structure(config)

        # Success message
        print("✅ ADRI project initialized successfully!")
        print(f"📁 Project: {project_name}")
        print(f"⚙️  Config: {config_path}")
        print("\n📂 Directory structure created:")
        print("  ADRI/")
        print("  ├── dev/")
        print("  │   ├── standards/")
        print("  │   ├── assessments/")
        print("  │   └── training-data/")
        print("  └── prod/")
        print("      ├── standards/")
        print("      ├── assessments/")
        print("      └── training-data/")
        print("\n📋 Quick Start:")
        print("1. Add @adri_protected decorator to your agent functions")
        print("2. Generate standards: adri generate-standard <your-data>")
        print("3. Run assessments: adri assess <your-data> --standard <standard>")
        print("4. See examples: check ADRI/examples/ directory")

        return 0

    except PermissionError:
        print("❌ Error: Permission denied")
        print("💡 Fix: Check file/directory permissions and try again")
        return 1
    except Exception as e:
        print(f"❌ Error: Failed to initialize ADRI project: {e}")
        return 1


def assess_command(
    data_path: str,
    standard_path: str,
    output_path: Optional[str] = None,
    verbose: bool = False,
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Run data quality assessment.

    Args:
        data_path: Path to data file (CSV, JSON) - can be relative to training_data directory
        standard_path: Path to YAML standard file - can be relative to standards directory
        output_path: Optional path to save assessment report - defaults to assessments directory
        verbose: Enable verbose output
        environment: Environment to use (development/production)
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Get environment configuration
        try:
            env_config = config_manager.get_environment_config(config, environment)
            env_name = environment or config["adri"].get(
                "default_environment", "development"
            )
        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1

        # Resolve data path - check if it's relative to training_data directory
        resolved_data_path = _resolve_data_path(data_path, env_config)

        # Resolve standard path - check if it's relative to standards directory
        resolved_standard_path = _resolve_standard_path(standard_path, env_config)

        # Resolve output path - default to assessments directory if not specified
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_name = Path(data_path).stem
            standard_name = Path(standard_path).stem
            output_filename = f"{data_name}_{standard_name}_assessment_{timestamp}.json"
            output_path = os.path.join(
                env_config["paths"]["assessments"], output_filename
            )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if verbose:
            env_name = environment or config["adri"].get(
                "default_environment", "development"
            )
            print(f"🌍 Environment: {env_name}")
            print(f"📊 Data: {resolved_data_path}")
            print(f"📋 Standard: {resolved_standard_path}")
            print(f"📄 Output: {output_path}")
            print()

        # Load data
        data_list = load_data(resolved_data_path)
        if not data_list:
            print("❌ Error: No data loaded or empty dataset")
            return 1

        # Convert to DataFrame for assessment engine
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Apply performance limits from config
        assessment_config = config["adri"].get("assessment", {})
        performance_config = assessment_config.get("performance", {})
        max_rows = performance_config.get("max_rows", 1000000)

        if len(data) > max_rows:
            print(
                f"⚠️  Warning: Dataset has {len(data):,} rows, limiting to {max_rows:,} rows per configuration"
            )
            data = data.head(max_rows)

        # Load standard (validates it exists and is valid YAML)
        load_standard(resolved_standard_path)

        # Run assessment using the loaded standard
        engine = AssessmentEngine()
        assessment = engine.assess(data, resolved_standard_path)

        # Output results
        if verbose:
            print("📊 Assessment Results:")
            print(f"Overall Score: {assessment.overall_score:.1f}/100")
            print(f"Assessment Passed: {assessment.passed}")
            print("\nDimension Scores:")
            for dim, score in assessment.dimension_scores.items():
                print(
                    f"  {dim.title()}: {score.score:.1f}/20.0 ({score.percentage():.1f}%)"
                )
        else:
            print(f"Assessment Score: {assessment.overall_score:.1f}/100")
            print(f"Status: {'✅ PASSED' if assessment.passed else '❌ FAILED'}")

        # Save to file
        report_data = assessment.to_standard_dict()
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Report saved to: {output_path}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: File not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: Assessment failed: {e}")
        return 1


def generate_adri_standard_command(
    data_path: str,
    force: bool = False,
    verbose: bool = False,
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Generate ADRI standard from data file analysis.

    Args:
        data_path: Path to data file (CSV, JSON, Parquet) - can be relative to training_data directory
        force: Overwrite existing standard file
        verbose: Enable verbose output
        environment: Environment to use (development/production)
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Get environment configuration
        try:
            env_config = config_manager.get_environment_config(config, environment)
            env_name = environment or config["adri"].get(
                "default_environment", "development"
            )
        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1

        # Resolve data path - check if it's relative to training_data directory
        resolved_data_path = _resolve_data_path(data_path, env_config)

        # Generate output path - {data_name}_ADRI_standard.yaml in standards directory
        data_name = Path(data_path).stem
        output_filename = f"{data_name}_ADRI_standard.yaml"
        output_path = os.path.join(env_config["paths"]["standards"], output_filename)

        # Check if output file exists and handle force flag
        if os.path.exists(output_path) and not force:
            print(f"❌ Error: Standard file already exists: {output_path}")
            print("💡 Fix: Use --force to overwrite existing standard")
            return 1

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"🌍 Environment: {env_name}")
            print(f"📊 Data: {resolved_data_path}")
            print(f"📄 Output: {output_path}")
            print()

        # Load data
        data_list = load_data(resolved_data_path)
        if not data_list:
            print("❌ Error: No data loaded or empty dataset")
            return 1

        # Convert to DataFrame for profiling
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Apply performance limits from config
        assessment_config = config["adri"].get("assessment", {})
        performance_config = assessment_config.get("performance", {})
        max_rows = performance_config.get("max_rows", 1000000)

        if len(data) > max_rows:
            if verbose:
                print(
                    f"⚠️  Warning: Dataset has {len(data):,} rows, analyzing first {max_rows:,} rows per configuration"
                )
            data = data.head(max_rows)

        # Profile the data
        if verbose:
            print("🔍 Analyzing data structure and content...")

        profiler = DataProfiler()
        data_profile = profiler.profile_data(data, max_rows=max_rows)

        if verbose:
            summary = data_profile["summary"]
            print("📊 Data Summary:")
            print(f"  Rows: {summary['total_rows']:,}")
            print(f"  Columns: {summary['total_columns']}")
            print(f"  Data Types: {dict(summary['data_types'])}")
            print()

        # Get generation configuration
        generation_config = config["adri"].get("generation", {})

        # Generate standard
        if verbose:
            print("📝 Generating YAML standard...")

        generator = StandardGenerator()
        standard_dict = generator.generate_standard(
            data_profile=data_profile,
            data_name=data_name,
            generation_config=generation_config,
        )

        # Save to YAML file
        with open(output_path, "w") as f:
            yaml.dump(
                standard_dict, f, default_flow_style=False, sort_keys=False, indent=2
            )

        # Success message
        print("✅ ADRI standard generated successfully!")
        print(f"📄 Standard: {standard_dict['standards']['name']}")
        print(f"🆔 ID: {standard_dict['standards']['id']}")
        print(f"📁 Saved to: {output_path}")

        if verbose:
            requirements = standard_dict["requirements"]
            print("\n📋 Generated Requirements:")
            print(f"  Overall Minimum: {requirements['overall_minimum']:.1f}/100")
            print(
                f"  Field Requirements: {len(requirements['field_requirements'])} fields"
            )
            print(
                f"  Dimension Requirements: {len(requirements['dimension_requirements'])} dimensions"
            )

        print("\n📋 Next steps:")
        print(f"1. Review the generated standard: {output_path}")
        print(
            f"2. Run assessment: adri assess {data_path} --standard {output_filename}"
        )
        print(f"3. Validate standard: adri validate-standard {output_filename}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: File not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: Standard generation failed: {e}")
        if verbose:
            import traceback

            print(f"🔍 Debug info: {traceback.format_exc()}")
        return 1


def _resolve_data_path(data_path: str, env_config: Dict[str, Any]) -> str:
    """
    Resolve data path, checking training_data directory if path is not absolute.

    Args:
        data_path: Original data path
        env_config: Environment configuration

    Returns:
        Resolved absolute path to data file
    """
    # If absolute path or exists as-is, use it
    if os.path.isabs(data_path) or os.path.exists(data_path):
        return data_path

    # Try relative to training_data directory
    training_data_dir = env_config["paths"]["training_data"]
    candidate_path = os.path.join(training_data_dir, data_path)

    if os.path.exists(candidate_path):
        return candidate_path

    # Return original path (will cause FileNotFoundError later if it doesn't exist)
    return data_path


def _resolve_standard_path(standard_path: str, env_config: Dict[str, Any]) -> str:
    """
    Resolve standard path, checking standards directory if path is not absolute.

    Args:
        standard_path: Original standard path
        env_config: Environment configuration

    Returns:
        Resolved absolute path to standard file
    """
    # If absolute path or exists as-is, use it
    if os.path.isabs(standard_path) or os.path.exists(standard_path):
        return standard_path

    # Try relative to standards directory
    standards_dir = env_config["paths"]["standards"]
    candidate_path = os.path.join(standards_dir, standard_path)

    if os.path.exists(candidate_path):
        return candidate_path

    # Try adding .yaml extension if not present
    if not standard_path.endswith((".yaml", ".yml")):
        candidate_with_ext = os.path.join(standards_dir, standard_path + ".yaml")
        if os.path.exists(candidate_with_ext):
            return candidate_with_ext

    # Return original path (will cause FileNotFoundError later if it doesn't exist)
    return standard_path


def _resolve_standard_for_validation(standard_path: str) -> str:
    """
    Resolve standard path for validation, checking bundled standards first.

    Args:
        standard_path: Original standard path or standard name

    Returns:
        Resolved absolute path to standard file
    """
    # If absolute path or exists as-is, use it
    if os.path.isabs(standard_path) or os.path.exists(standard_path):
        return standard_path

    # Try to load from bundled standards using StandardsLoader
    try:
        from ..standards.loader import StandardsLoader

        loader = StandardsLoader()

        # Check if it's a bundled standard (with or without .yaml extension)
        standard_name = standard_path
        if standard_name.endswith((".yaml", ".yml")):
            standard_name = (
                standard_name[:-5]
                if standard_name.endswith(".yaml")
                else standard_name[:-4]
            )

        if loader.standard_exists(standard_name):
            # Return the full path to the bundled standard
            return str(loader.standards_path / f"{standard_name}.yaml")

    except Exception:  # nosec B110
        # If StandardsLoader fails, continue with file-based resolution
        # This is intentional - we want to fall back to file-based resolution
        pass

    # Try adding .yaml extension if not present
    if not standard_path.endswith((".yaml", ".yml")):
        candidate_with_ext = standard_path + ".yaml"
        if os.path.exists(candidate_with_ext):
            return candidate_with_ext

    # Return original path (will cause FileNotFoundError later if it doesn't exist)
    return standard_path


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from file (CSV, JSON, or Parquet).

    Args:
        file_path: Path to data file

    Returns:
        List of dictionaries representing the data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    file_path_obj = Path(file_path)

    if file_path_obj.suffix.lower() == ".csv":
        return _load_csv_data(file_path_obj)
    elif file_path_obj.suffix.lower() == ".json":
        return _load_json_data(file_path_obj)
    elif file_path_obj.suffix.lower() == ".parquet":
        return _load_parquet_data(file_path_obj)
    else:
        raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")


def _load_csv_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from CSV file."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(dict(row))

    # Check if no data was loaded (empty file)
    if not data:
        # Re-read to check if file is truly empty
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                raise ValueError("CSV file is empty")

    return data


def _load_json_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure data is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of objects")

    return data


def _load_parquet_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from Parquet file."""
    if pd is None:
        raise ImportError(
            "pandas is required to read Parquet files. Install with: pip install pandas"
        )

    try:
        # Read Parquet file into DataFrame
        df = pd.read_parquet(file_path)

        # Check if DataFrame is empty
        if df.empty:
            raise ValueError("Parquet file is empty")

        # Convert DataFrame to list of dictionaries
        # Use .to_dict('records') to convert each row to a dictionary
        data: List[Dict[str, Any]] = df.to_dict("records")

        return data

    except Exception as e:
        if "parquet" in str(e).lower():
            raise ValueError(f"Failed to read Parquet file: {e}")
        else:
            raise


def load_standard(file_path: str) -> dict:
    """
    Load YAML standard from file.

    Args:
        file_path: Path to YAML standard file

    Returns:
        Standard dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Standard file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            yaml_content: Dict[Any, Any] = yaml.safe_load(f)
        return yaml_content

    except yaml.YAMLError as e:
        raise Exception(f"Invalid YAML format: {e}")
    except Exception as e:
        raise Exception(f"Failed to load standard: {e}")


def validate_standard_command(
    standard_path: str, verbose: bool = False, output_path: Optional[str] = None
) -> int:
    """
    Validate YAML standard file.

    Args:
        standard_path: Path to YAML standard file or standard name
        verbose: Enable verbose output
        output_path: Optional path to save validation report

    Returns:
        Exit code: 0 for valid standard, non-zero for invalid
    """
    try:
        # First try to resolve the standard path
        resolved_path = _resolve_standard_for_validation(standard_path)

        # Load and validate standard
        validation_result = validate_yaml_standard(resolved_path)

        # Output results
        if validation_result["is_valid"]:
            print("✅ Standard validation PASSED")
            print(
                f"📄 Standard: {validation_result['standard_name']} v{validation_result['standard_version']}"
            )
            print(f"🏛️  Authority: {validation_result['authority']}")

            if verbose:
                print("\n📋 Validation Details:")
                for check in validation_result["passed_checks"]:
                    print(f"  ✅ {check}")
        else:
            print("❌ Standard validation FAILED")
            print(f"📄 File: {standard_path}")
            print(f"\n🚨 Errors found ({len(validation_result['errors'])}):")
            for error in validation_result["errors"]:
                print(f"  ❌ {error}")

            if validation_result.get("warnings"):
                print(f"\n⚠️  Warnings ({len(validation_result['warnings'])}):")
                for warning in validation_result["warnings"]:
                    print(f"  ⚠️  {warning}")

        # Save to file if requested
        if output_path:
            with open(output_path, "w") as f:
                json.dump(validation_result, f, indent=2)
            print(f"📄 Validation report saved to: {output_path}")

        return 0 if validation_result["is_valid"] else 1

    except FileNotFoundError as e:
        print(f"❌ Error: File not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: Validation failed: {e}")
        return 1


def validate_yaml_standard(file_path: str) -> Dict[str, Any]:
    """
    Validate a YAML standard file and return detailed results.

    Args:
        file_path: Path to YAML standard file

    Returns:
        Dict containing validation results
    """
    from datetime import datetime

    validation_result: Dict[str, Any] = {
        "file_path": file_path,
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "passed_checks": [],
        "standard_name": None,
        "standard_version": None,
        "authority": None,
        "validation_timestamp": datetime.now().isoformat(),
    }

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            validation_result["errors"].append(f"File not found: {file_path}")
            validation_result["is_valid"] = False
            return validation_result

        # Load YAML content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                yaml_content = yaml.safe_load(f)
            validation_result["passed_checks"].append("Valid YAML syntax")
        except yaml.YAMLError as e:
            validation_result["errors"].append(f"Invalid YAML syntax: {e}")
            validation_result["is_valid"] = False
            return validation_result

        # Check root structure
        if not isinstance(yaml_content, dict):
            validation_result["errors"].append(
                "YAML must contain a dictionary at the root level"
            )
            validation_result["is_valid"] = False
            return validation_result
        validation_result["passed_checks"].append("Root dictionary structure")

        # Check required sections
        required_sections = ["standards", "requirements"]
        for section in required_sections:
            if section not in yaml_content:
                validation_result["errors"].append(
                    f"Missing required section: '{section}'"
                )
                validation_result["is_valid"] = False
            else:
                validation_result["passed_checks"].append(
                    f"Required section '{section}' present"
                )

        # Validate standards metadata
        if "standards" in yaml_content:
            _validate_standards_metadata(yaml_content["standards"], validation_result)

        # Validate requirements section
        if "requirements" in yaml_content:
            _validate_requirements_section(
                yaml_content["requirements"], validation_result
            )

        # Extract metadata directly from yaml_content
        standards_section = yaml_content.get("standards", {})
        validation_result["standard_name"] = standards_section.get("name", "Unknown")
        validation_result["standard_version"] = standards_section.get(
            "version", "Unknown"
        )
        validation_result["authority"] = standards_section.get("authority", "Unknown")
        validation_result["passed_checks"].append("Metadata extraction successful")

    except Exception as e:
        validation_result["errors"].append(f"Unexpected error during validation: {e}")
        validation_result["is_valid"] = False

    return validation_result


def _validate_standards_metadata(
    standards_section: Dict[str, Any], result: Dict[str, Any]
):
    """Validate the standards metadata section."""
    required_fields = ["id", "name", "version", "authority"]

    for field in required_fields:
        if field not in standards_section:
            result["errors"].append(
                f"Missing required field in standards section: '{field}'"
            )
            result["is_valid"] = False
        elif not standards_section[field] or not str(standards_section[field]).strip():
            result["errors"].append(f"Empty value for required field: '{field}'")
            result["is_valid"] = False
        else:
            result["passed_checks"].append(
                f"Standards field '{field}' present and non-empty"
            )

    # Validate version format (basic semver check)
    if "version" in standards_section:
        version = str(standards_section["version"])
        if not re.match(r"^\d+\.\d+\.\d+", version):
            result["warnings"].append(
                f"Version '{version}' does not follow semantic versioning (x.y.z)"
            )

    # Validate effective_date format if present
    if "effective_date" in standards_section:
        try:
            datetime.fromisoformat(standards_section["effective_date"])
            result["passed_checks"].append("Valid effective_date format")
        except ValueError:
            result["errors"].append(
                f"Invalid effective_date format: {standards_section['effective_date']} (expected ISO format)"
            )
            result["is_valid"] = False


def _validate_requirements_section(
    requirements_section: Any, result: Dict[str, Any]
) -> None:
    """Validate the requirements section."""
    if not isinstance(requirements_section, dict):
        result["errors"].append("Requirements section must be a dictionary")
        result["is_valid"] = False
        return

    result["passed_checks"].append("Requirements section is a dictionary")

    # Validate overall_minimum if present
    if "overall_minimum" in requirements_section:
        overall_min = requirements_section["overall_minimum"]
        if not isinstance(overall_min, (int, float)):
            result["errors"].append("overall_minimum must be a number")
            result["is_valid"] = False
        elif overall_min < 0 or overall_min > 100:
            result["errors"].append("overall_minimum must be between 0 and 100")
            result["is_valid"] = False
        else:
            result["passed_checks"].append(f"Valid overall_minimum: {overall_min}")

    # Validate dimension_requirements if present
    if "dimension_requirements" in requirements_section:
        _validate_dimension_requirements(
            requirements_section["dimension_requirements"], result
        )

    # Validate field_requirements if present
    if "field_requirements" in requirements_section:
        _validate_field_requirements(requirements_section["field_requirements"], result)


def _validate_dimension_requirements(
    dim_requirements: Any, result: Dict[str, Any]
) -> None:
    """Validate dimension requirements."""
    valid_dimensions = [
        "validity",
        "completeness",
        "freshness",
        "consistency",
        "plausibility",
    ]

    if not isinstance(dim_requirements, dict):
        result["errors"].append("dimension_requirements must be a dictionary")
        result["is_valid"] = False
        return

    for dimension, config in dim_requirements.items():
        if dimension not in valid_dimensions:
            result["errors"].append(
                f"Unknown dimension: '{dimension}'. Valid dimensions: {valid_dimensions}"
            )
            result["is_valid"] = False
        else:
            result["passed_checks"].append(f"Valid dimension: '{dimension}'")

        if isinstance(config, dict):
            if "minimum_score" in config:
                min_score = config["minimum_score"]
                if not isinstance(min_score, (int, float)):
                    result["errors"].append(
                        f"minimum_score for {dimension} must be a number"
                    )
                    result["is_valid"] = False
                elif min_score < 0 or min_score > 20:
                    result["errors"].append(
                        f"minimum_score for {dimension} must be between 0 and 20"
                    )
                    result["is_valid"] = False
                else:
                    result["passed_checks"].append(
                        f"Valid minimum_score for {dimension}: {min_score}"
                    )


def _validate_field_requirements(
    field_requirements: Any, result: Dict[str, Any]
) -> None:
    """Validate field requirements."""
    if not isinstance(field_requirements, dict):
        result["errors"].append("field_requirements must be a dictionary")
        result["is_valid"] = False
        return

    valid_types = ["string", "integer", "float", "boolean", "date", "datetime"]

    for field_name, field_config in field_requirements.items():
        if not isinstance(field_config, dict):
            result["errors"].append(
                f"Field '{field_name}' configuration must be a dictionary"
            )
            result["is_valid"] = False
            continue

        # Validate type
        if "type" in field_config:
            field_type = field_config["type"]
            if field_type not in valid_types:
                result["errors"].append(
                    f"Invalid type '{field_type}' for field '{field_name}'. Valid types: {valid_types}"
                )
                result["is_valid"] = False
            else:
                result["passed_checks"].append(
                    f"Valid type for field '{field_name}': {field_type}"
                )

        # Validate nullable
        if "nullable" in field_config:
            nullable = field_config["nullable"]
            if not isinstance(nullable, bool):
                result["errors"].append(
                    f"nullable for field '{field_name}' must be true or false"
                )
                result["is_valid"] = False
            else:
                result["passed_checks"].append(
                    f"Valid nullable setting for field '{field_name}': {nullable}"
                )

        # Validate min/max values
        if "min_value" in field_config and "max_value" in field_config:
            min_val = field_config["min_value"]
            max_val = field_config["max_value"]
            if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
                if min_val >= max_val:
                    result["errors"].append(
                        f"min_value must be less than max_value for field '{field_name}'"
                    )
                    result["is_valid"] = False
                else:
                    result["passed_checks"].append(
                        f"Valid min/max range for field '{field_name}': {min_val}-{max_val}"
                    )

        # Validate regex pattern
        if "pattern" in field_config:
            pattern = field_config["pattern"]
            try:
                re.compile(pattern)
                result["passed_checks"].append(
                    f"Valid regex pattern for field '{field_name}'"
                )
            except re.error as e:
                result["errors"].append(
                    f"Invalid regex pattern for field '{field_name}': {e}"
                )
                result["is_valid"] = False


def show_config_command(
    environment: Optional[str] = None,
    paths_only: bool = False,
    validate: bool = False,
    format_type: str = "human",
    config_path: Optional[str] = None,
) -> int:
    """
    Show current ADRI configuration.

    Args:
        environment: Show specific environment only
        paths_only: Show only path information
        validate: Validate configuration and paths
        format_type: Output format ('human' or 'json')
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Validate configuration structure
        if not config_manager.validate_config(config):
            print("❌ Invalid configuration structure")
            return 1

        # Validate paths if requested
        validation_results = None
        if validate:
            validation_results = config_manager.validate_paths(config)

        # Output based on format
        if format_type == "json":
            return _output_config_json(config, environment, validation_results)
        else:
            return _output_config_human(
                config,
                environment,
                paths_only,
                validate,
                validation_results,
                config_manager,
            )

    except Exception as e:
        print(f"❌ Error: Failed to show configuration: {e}")
        return 1


def _output_config_json(
    config: Dict[str, Any],
    environment: Optional[str] = None,
    validation_results: Optional[Dict[str, Any]] = None,
) -> int:
    """Output configuration in JSON format."""
    output = {
        "config": config,
        "active_environment": environment
        or config["adri"].get("default_environment", "development"),
    }

    if validation_results:
        output["validation"] = validation_results

    print(json.dumps(output, indent=2))
    return 0


def _output_config_human(
    config: Dict[str, Any],
    environment: Optional[str],
    paths_only: bool,
    validate: bool,
    validation_results: Optional[Dict[str, Any]],
    config_manager: ConfigManager,
) -> int:
    """Output configuration in human-readable format."""
    adri_config = config["adri"]

    # Header
    if not paths_only:
        print("📋 ADRI Configuration")
        print(f"🏗️  Project: {adri_config['project_name']}")
        print(f"📦 Version: {adri_config['version']}")
        print(f"🌍 Default Environment: {adri_config['default_environment']}")
        print()

    # Show specific environment or all environments
    environments_to_show = (
        [environment] if environment else list(adri_config["environments"].keys())
    )

    for env_name in environments_to_show:
        if env_name not in adri_config["environments"]:
            print(f"❌ Environment '{env_name}' not found")
            continue

        env_config = adri_config["environments"][env_name]
        paths = env_config["paths"]

        # Environment header
        env_title = f"📁 {env_name.title()} Paths"
        if env_name == adri_config["default_environment"]:
            env_title += " (default)"
        print(env_title + ":")

        # Show paths with status
        for path_type, path_value in paths.items():
            path_display = path_type.replace("_", " ").title()
            status_info = ""

            if validate and validation_results:
                path_key = f"{env_name}.{path_type}"
                if path_key in validation_results["path_status"]:
                    status = validation_results["path_status"][path_key]
                    if status["exists"]:
                        if status["file_count"] >= 0:
                            status_info = f" ({status['file_count']} files)"
                        else:
                            status_info = " (permission denied)"
                    else:
                        status_info = " (missing)"

            print(f"  {path_display:12} {path_value}{status_info}")

        print()

    # Show settings if not paths-only
    if not paths_only:
        _show_assessment_settings(adri_config)
        _show_generation_settings(adri_config)

    # Show validation results
    if validate and validation_results:
        _show_validation_results(validation_results)

    return 0


def _show_assessment_settings(adri_config: Dict[str, Any]):
    """Show assessment configuration settings."""
    assessment_config = adri_config.get("assessment", {})

    print("⚙️  Assessment Settings:")

    # Caching
    caching = assessment_config.get("caching", {})
    if caching.get("enabled", False):
        ttl = caching.get("ttl", "24h")
        print(f"  Caching: Enabled ({ttl} TTL)")
    else:
        print("  Caching: Disabled")

    # Performance
    performance = assessment_config.get("performance", {})
    max_rows = performance.get("max_rows", 1000000)
    timeout = performance.get("timeout", "5m")
    print(f"  Max Rows: {max_rows:,}")
    print(f"  Timeout: {timeout}")

    # Output
    output_config = assessment_config.get("output", {})
    output_format = output_config.get("format", "json").upper()
    print(f"  Output Format: {output_format}")

    print()


def _show_generation_settings(adri_config: Dict[str, Any]):
    """Show generation configuration settings."""
    generation_config = adri_config.get("generation", {})
    thresholds = generation_config.get("default_thresholds", {})

    print("📊 Generation Thresholds:")

    completeness = thresholds.get("completeness_min", 85)
    validity = thresholds.get("validity_min", 90)
    consistency = thresholds.get("consistency_min", 80)
    freshness = thresholds.get("freshness_max_age", "7d")
    plausibility = thresholds.get("plausibility_outlier_threshold", 3.0)

    print(f"  Completeness: ≥{completeness}%")
    print(f"  Validity: ≥{validity}%")
    print(f"  Consistency: ≥{consistency}%")
    print(f"  Freshness: ≤{freshness}")
    print(f"  Plausibility: {plausibility}σ outlier threshold")

    print()


def _show_validation_results(validation_results: Dict[str, Any]):
    """Show path validation results."""
    print("🔍 Path Validation:")

    if validation_results["valid"]:
        print("  ✅ Configuration is valid")
    else:
        print("  ❌ Configuration has errors")

    # Show errors
    if validation_results["errors"]:
        print(f"  🚨 Errors ({len(validation_results['errors'])}):")
        for error in validation_results["errors"]:
            print(f"    ❌ {error}")

    # Show warnings
    if validation_results["warnings"]:
        print(f"  ⚠️  Warnings ({len(validation_results['warnings'])}):")
        for warning in validation_results["warnings"]:
            print(f"    ⚠️  {warning}")

    # Show directory status summary
    path_status = validation_results["path_status"]
    existing_dirs = sum(1 for status in path_status.values() if status["exists"])
    total_dirs = len(path_status)

    print(f"  📁 Directories: {existing_dirs}/{total_dirs} exist")

    # Show file counts
    total_files = sum(
        status["file_count"]
        for status in path_status.values()
        if status["file_count"] > 0
    )
    if total_files > 0:
        print(f"  📄 Total files: {total_files}")

    print()


def list_standards_command(
    environment: Optional[str] = None,
    verbose: bool = False,
    config_path: Optional[str] = None,
) -> int:
    """
    List available YAML standards.

    Args:
        environment: Environment to list standards from (development/production)
        verbose: Enable verbose output with standard details
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # First, always show bundled standards
        from ..standards.loader import StandardsLoader

        loader = StandardsLoader()
        bundled_standards = loader.list_available_standards()

        print("📋 ADRI Standards")
        print()

        if bundled_standards:
            _display_bundled_standards(bundled_standards, loader, verbose)

        # Then check for project-specific standards if config exists
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is not None:
            _display_project_standards(
                config, config_manager, environment, verbose, bundled_standards
            )
        elif not bundled_standards:
            print("📁 No ADRI configuration found and no bundled standards available")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        print("📋 Usage:")
        print("  • Validate: adri validate-standard <standard-name>")
        print("  • Assess: adri assess <data-file> --standard <standard-name>")
        print("  • Generate new: adri generate-standard <data-file>")

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to list standards: {e}")
        return 1


def _display_bundled_standards(
    bundled_standards: List[str], loader: Any, verbose: bool
) -> None:
    """Display bundled standards with optional verbose details."""
    print(f"📦 Bundled Standards ({len(bundled_standards)} available)")
    print(f"📁 Location: {loader.standards_path}")
    print()

    for i, standard_name in enumerate(bundled_standards, 1):
        print(f"{i:2d}. {standard_name}")

        if verbose:
            _display_bundled_standard_details(standard_name, loader)

        print()


def _display_bundled_standard_details(standard_name: str, loader: Any) -> None:
    """Display detailed information for a bundled standard."""
    try:
        metadata = loader.get_standard_metadata(standard_name)
        print(f"    🏷️  Name: {metadata.get('name', 'Unknown')}")
        print(f"    🆔 ID: {metadata.get('id', 'Unknown')}")
        print(f"    📦 Version: {metadata.get('version', 'Unknown')}")
        print(f"    📄 Description: {metadata.get('description', 'No description')}")

        # Load full standard for requirements info
        standard_data = loader.load_standard(standard_name)
        if "requirements" in standard_data:
            req_info = standard_data["requirements"]
            overall_min = req_info.get("overall_minimum", "Not set")
            print(f"    📊 Min Score: {overall_min}")

            field_count = len(req_info.get("field_requirements", {}))
            dim_count = len(req_info.get("dimension_requirements", {}))
            print(f"    📋 Requirements: {field_count} fields, {dim_count} dimensions")

    except Exception as e:
        print(f"    ⚠️  Could not read standard details: {e}")


def _display_project_standards(
    config: Dict[str, Any],
    config_manager: ConfigManager,
    environment: Optional[str],
    verbose: bool,
    bundled_standards: List[str],
) -> None:
    """Display project-specific standards."""
    try:
        env_config = config_manager.get_environment_config(config, environment)
        standards_dir = env_config["paths"]["standards"]

        # Find YAML standard files in project directory
        project_standards = _find_project_standard_files(standards_dir)

        if project_standards:
            _display_project_standard_list(
                project_standards, environment, config, standards_dir, verbose
            )
        elif not bundled_standards:
            env_name = environment or config["adri"].get(
                "default_environment", "development"
            )
            print(f"📋 No project standards found in {env_name} environment")
            print(f"📁 Directory: {standards_dir}")

    except ValueError:
        # Environment config error - just show bundled standards
        pass


def _find_project_standard_files(standards_dir: str) -> List[Path]:
    """Find YAML standard files in project directory."""
    project_standards = []
    if os.path.exists(standards_dir):
        for file_path in Path(standards_dir).glob("*.yaml"):
            if file_path.is_file():
                project_standards.append(file_path)

        # Also check for .yml files
        for file_path in Path(standards_dir).glob("*.yml"):
            if file_path.is_file():
                project_standards.append(file_path)

    return project_standards


def _display_project_standard_list(
    project_standards: List[Path],
    environment: Optional[str],
    config: Dict[str, Any],
    standards_dir: str,
    verbose: bool,
) -> None:
    """Display list of project standards."""
    # Sort by modification time (newest first)
    project_standards.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    env_name = environment or config["adri"].get("default_environment", "development")
    print(f"🏗️  Project Standards ({env_name} environment)")
    print(f"📁 Directory: {standards_dir}")
    print(f"📄 Found {len(project_standards)} standard(s)")
    print()

    for i, file_path in enumerate(project_standards, 1):
        _display_project_standard_file(file_path, i, verbose)
        print()


def _display_project_standard_file(file_path: Path, index: int, verbose: bool) -> None:
    """Display a single project standard file."""
    file_stats = file_path.stat()
    modified_time = datetime.fromtimestamp(file_stats.st_mtime)
    file_size = file_stats.st_size

    print(f"{index:2d}. {file_path.name}")
    print(f"    📅 Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    📏 Size: {file_size:,} bytes")

    if verbose:
        _display_project_standard_details(file_path)


def _display_project_standard_details(file_path: Path) -> None:
    """Display detailed information for a project standard."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        if "standards" in yaml_content:
            std_info = yaml_content["standards"]
            print(f"    🏷️  Name: {std_info.get('name', 'Unknown')}")
            print(f"    🆔 ID: {std_info.get('id', 'Unknown')}")
            print(f"    📦 Version: {std_info.get('version', 'Unknown')}")
            print(f"    🏛️  Authority: {std_info.get('authority', 'Unknown')}")

            if "requirements" in yaml_content:
                req_info = yaml_content["requirements"]
                overall_min = req_info.get("overall_minimum", "Not set")
                print(f"    📊 Min Score: {overall_min}")

                field_count = len(req_info.get("field_requirements", {}))
                dim_count = len(req_info.get("dimension_requirements", {}))
                print(
                    f"    📋 Requirements: {field_count} fields, {dim_count} dimensions"
                )

    except Exception as e:
        print(f"    ⚠️  Could not read standard details: {e}")


def list_training_data_command(
    environment: Optional[str] = None,
    verbose: bool = False,
    config_path: Optional[str] = None,
) -> int:
    """
    List available training data files.

    Args:
        environment: Environment to list training data from (development/production)
        verbose: Enable verbose output with file details
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration and get environment
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        env_config = _get_environment_config(config_manager, config, environment)
        if env_config is None:
            return 1

        # Find and process data files
        data_files = _find_training_data_files(env_config, environment, config)
        if data_files is None:
            return 0

        # Display results
        _display_training_data_results(data_files, environment, config, verbose)
        _display_training_data_usage()

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to list training data: {e}")
        return 1


def _find_training_data_files(
    env_config: Dict[str, Any], environment: Optional[str], config: Dict[str, Any]
) -> Optional[List[Path]]:
    """Find and validate training data files."""
    training_data_dir = env_config["paths"]["training_data"]

    # Check if training data directory exists
    if not os.path.exists(training_data_dir):
        print(f"📁 Training data directory not found: {training_data_dir}")
        print("💡 Create the directory and add data files to get started")
        return None

    # Find supported data files
    data_files = []
    supported_extensions = [".csv", ".json", ".parquet"]

    for ext in supported_extensions:
        for file_path in Path(training_data_dir).glob(f"*{ext}"):
            if file_path.is_file():
                data_files.append(file_path)

    if not data_files:
        env_name = environment or config["adri"].get(
            "default_environment", "development"
        )
        print(f"📊 No training data found in {env_name} environment")
        print(f"📁 Directory: {training_data_dir}")
        print(f"💡 Supported formats: {', '.join(supported_extensions)}")
        return None

    # Sort by modification time (newest first)
    data_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return data_files


def _display_training_data_results(
    data_files: List[Path],
    environment: Optional[str],
    config: Dict[str, Any],
    verbose: bool,
):
    """Display training data files with details."""
    # Group by file type
    files_by_type: Dict[str, List[Path]] = {}
    for file_path in data_files:
        ext = file_path.suffix.lower()
        if ext not in files_by_type:
            files_by_type[ext] = []
        files_by_type[ext].append(file_path)

    # Display header
    env_name = environment or config["adri"].get("default_environment", "development")
    print(f"📊 Training Data ({env_name} environment)")
    print(f"📄 Found {len(data_files)} file(s)")
    print()

    # Display files by type
    file_counter = 1
    for ext in sorted(files_by_type.keys()):
        files = files_by_type[ext]
        print(f"📋 {ext.upper()} Files ({len(files)}):")

        for file_path in files:
            _display_file_details(file_path, file_counter, ext, verbose)
            file_counter += 1
            print()


def _display_file_details(file_path: Path, file_counter: int, ext: str, verbose: bool):
    """Display details for a single training data file."""
    file_stats = file_path.stat()
    modified_time = datetime.fromtimestamp(file_stats.st_mtime)
    file_size = file_stats.st_size

    print(f"{file_counter:2d}. {file_path.name}")
    print(f"    📅 Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    📏 Size: {_format_file_size(file_size)}")

    if verbose:
        _display_verbose_file_info(file_path, ext)


def _display_verbose_file_info(file_path: Path, ext: str):
    """Display verbose information about a file."""
    try:
        if ext == ".csv":
            row_count = _count_csv_rows(file_path)
            print(f"    📊 Rows: ~{row_count:,}")
        elif ext == ".json":
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"    📊 Records: {len(data):,}")
                else:
                    print(f"    📊 Type: {type(data).__name__}")
        elif ext == ".parquet":
            try:
                import pandas as pd

                df = pd.read_parquet(file_path)
                print(f"    📊 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
            except ImportError:
                print("    📊 Format: Parquet (pandas required for details)")

    except Exception as e:
        print(f"    ⚠️  Could not read file details: {e}")


def _display_training_data_usage():
    """Display usage instructions for training data."""
    print("📋 Usage:")
    print("  • Generate standard: adri generate-standard <data-file>")
    print("  • Run assessment: adri assess <data-file> --standard <standard>")


def list_assessments_command(
    recent: int = 10,
    environment: Optional[str] = None,
    verbose: bool = False,
    config_path: Optional[str] = None,
) -> int:
    """
    List previous assessment reports.

    Args:
        recent: Number of recent assessments to show (default: 10)
        environment: Environment to list assessments from (development/production)
        verbose: Enable verbose output with assessment details
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration and get environment
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        env_config = _get_environment_config(config_manager, config, environment)
        if env_config is None:
            return 1

        # Find and process assessment files
        assessment_files = _find_assessment_files(env_config, environment, config)
        if assessment_files is None:
            return 0

        # Limit to recent assessments
        if recent > 0:
            assessment_files = assessment_files[:recent]

        # Display results
        _display_assessment_results(assessment_files, environment, config, verbose)
        _display_assessment_pagination(assessment_files, recent, env_config)
        _display_assessment_usage()

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to list assessments: {e}")
        return 1


def _find_assessment_files(
    env_config: Dict[str, Any], environment: Optional[str], config: Dict[str, Any]
) -> Optional[List[Path]]:
    """Find and validate assessment files."""
    assessments_dir = env_config["paths"]["assessments"]

    # Check if assessments directory exists
    if not os.path.exists(assessments_dir):
        print(f"📁 Assessments directory not found: {assessments_dir}")
        print("💡 Run 'adri assess' to create assessment reports")
        return None

    # Find JSON assessment files
    assessment_files = []
    for file_path in Path(assessments_dir).glob("*.json"):
        if file_path.is_file():
            assessment_files.append(file_path)

    if not assessment_files:
        env_name = environment or config["adri"].get(
            "default_environment", "development"
        )
        print(f"📊 No assessments found in {env_name} environment")
        print(f"📁 Directory: {assessments_dir}")
        print("💡 Run 'adri assess <data> --standard <standard>' to create assessments")
        return None

    # Sort by modification time (newest first)
    assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return assessment_files


def _display_assessment_results(
    assessment_files: List[Path],
    environment: Optional[str],
    config: Dict[str, Any],
    verbose: bool,
):
    """Display assessment files with details."""
    env_name = environment or config["adri"].get("default_environment", "development")
    print(f"📊 Assessment Reports ({env_name} environment)")
    print(f"📄 Showing {len(assessment_files)} most recent assessment(s)")
    print()

    for i, file_path in enumerate(assessment_files, 1):
        _display_assessment_file_details(file_path, i, verbose)
        print()


def _display_assessment_file_details(file_path: Path, file_number: int, verbose: bool):
    """Display details for a single assessment file."""
    file_stats = file_path.stat()
    modified_time = datetime.fromtimestamp(file_stats.st_mtime)
    file_size = file_stats.st_size

    print(f"{file_number:2d}. {file_path.name}")
    print(f"    📅 Created: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    📏 Size: {_format_file_size(file_size)}")

    if verbose:
        _display_verbose_assessment_info(file_path)


def _display_verbose_assessment_info(file_path: Path):
    """Display verbose information about an assessment file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            assessment_data = json.load(f)

        # Extract key information
        overall_score = assessment_data.get("overall_score", "Unknown")
        passed = assessment_data.get("passed", False)
        status = "✅ PASSED" if passed else "❌ FAILED"

        print(f"    📊 Score: {overall_score}/100 ({status})")

        # Show dimension scores if available
        if "dimension_scores" in assessment_data:
            _display_dimension_scores(assessment_data["dimension_scores"])

        # Show data and standard info if available
        _display_assessment_metadata(assessment_data.get("metadata", {}))

    except Exception as e:
        print(f"    ⚠️  Could not read assessment details: {e}")


def _display_dimension_scores(dim_scores: Dict[str, Any]):
    """Display dimension scores for an assessment."""
    print("    📋 Dimensions:")
    for dim_name, dim_data in dim_scores.items():
        if isinstance(dim_data, dict) and "score" in dim_data:
            score = dim_data["score"]
            print(f"      {dim_name.title()}: {score:.1f}/20")


def _display_assessment_metadata(metadata: Dict[str, Any]):
    """Display assessment metadata."""
    if "data_source" in metadata:
        print(f"    📊 Data: {metadata['data_source']}")
    if "standard_name" in metadata:
        print(f"    📋 Standard: {metadata['standard_name']}")


def _display_assessment_pagination(
    assessment_files: List[Path], recent: int, env_config: Dict[str, Any]
):
    """Display pagination information if needed."""
    if len(assessment_files) == recent and recent > 0:
        assessments_dir = env_config["paths"]["assessments"]
        total_files = len(list(Path(assessments_dir).glob("*.json")))
        if total_files > recent:
            print(f"📋 Showing {recent} of {total_files} total assessments")
            print(f"💡 Use --recent {total_files} to see all assessments")
            print()


def _display_assessment_usage():
    """Display usage instructions for assessments."""
    print("📋 Usage:")
    print("  • View details: cat <assessment-file>")
    print(
        "  • Compare: adri assess <data> --standard <standard> (creates new assessment)"
    )


def clean_cache_command(
    environment: Optional[str] = None,
    verbose: bool = False,
    config_path: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """
    Clean cached assessment results and temporary files.

    Args:
        environment: Environment to clean cache from (development/production)
        verbose: Enable verbose output
        config_path: Specific config file path
        dry_run: Show what would be deleted without actually deleting

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Get environment configuration
        try:
            env_config = config_manager.get_environment_config(config, environment)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1

        # Find files to clean
        files_to_delete, dirs_to_delete, total_size = _find_cache_files(env_config)

        # Handle empty case
        if not files_to_delete and not dirs_to_delete:
            return _handle_no_cache_files(environment, config)

        # Display cleanup plan
        _display_cleanup_plan(
            files_to_delete,
            dirs_to_delete,
            total_size,
            environment,
            config,
            verbose,
            dry_run,
        )

        if dry_run:
            return _handle_dry_run()

        # Perform cleanup
        return _perform_cleanup(files_to_delete, dirs_to_delete, total_size, verbose)

    except Exception as e:
        print(f"❌ Error: Failed to clean cache: {e}")
        return 1


def _find_cache_files(env_config: Dict[str, Any]) -> tuple:
    """Find cache files and directories to delete."""
    cache_patterns = [
        "*.tmp",
        "*.temp",
        ".*.tmp",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".adri_cache",
        "*.cache",
        "*.backup",
        "*.bak",
        "*~",
    ]

    directories_to_clean = [
        env_config["paths"]["assessments"],
        env_config["paths"]["standards"],
        env_config["paths"]["training_data"],
        ".",
    ]

    files_to_delete = []
    dirs_to_delete = []
    total_size = 0

    for directory in directories_to_clean:
        if not os.path.exists(directory):
            continue

        dir_path = Path(directory)
        for pattern in cache_patterns:
            if pattern == "__pycache__":
                for pycache_dir in dir_path.rglob("__pycache__"):
                    if pycache_dir.is_dir():
                        dirs_to_delete.append(pycache_dir)
                        for file_path in pycache_dir.rglob("*"):
                            if file_path.is_file():
                                total_size += file_path.stat().st_size
            else:
                for file_path in dir_path.rglob(pattern):
                    if file_path.is_file():
                        files_to_delete.append(file_path)
                        total_size += file_path.stat().st_size

    files_to_delete = sorted(set(files_to_delete), key=lambda x: str(x))
    dirs_to_delete = sorted(set(dirs_to_delete), key=lambda x: str(x))

    return files_to_delete, dirs_to_delete, total_size


def _handle_no_cache_files(environment: Optional[str], config: Dict[str, Any]) -> int:
    """Handle case when no cache files are found."""
    env_name = environment or config["adri"].get("default_environment", "development")
    print(f"🧹 Cache Clean ({env_name} environment)")
    print("✨ No cache files found to clean")
    return 0


def _display_cleanup_plan(
    files_to_delete: List[Path],
    dirs_to_delete: List[Path],
    total_size: int,
    environment: Optional[str],
    config: Dict[str, Any],
    verbose: bool,
    dry_run: bool,
):
    """Display what will be cleaned."""
    total_items = len(files_to_delete) + len(dirs_to_delete)
    action_word = "Would delete" if dry_run else "Cleaning"
    env_name = environment or config["adri"].get("default_environment", "development")

    print(f"🧹 Cache Clean ({env_name} environment)")
    print(f"🗑️  {action_word} {total_items} item(s) ({_format_file_size(total_size)})")
    print()

    if verbose or dry_run:
        if files_to_delete:
            print(f"📄 Files to delete ({len(files_to_delete)}):")
            for file_path in files_to_delete:
                file_size = file_path.stat().st_size
                print(f"  🗑️  {file_path} ({_format_file_size(file_size)})")
            print()

        if dirs_to_delete:
            print(f"📁 Directories to delete ({len(dirs_to_delete)}):")
            for dir_path in dirs_to_delete:
                print(f"  🗑️  {dir_path}/")
            print()


def _handle_dry_run() -> int:
    """Handle dry run mode."""
    print("🔍 Dry run mode - no files were actually deleted")
    print("💡 Run without --dry-run to perform the cleanup")
    return 0


def _perform_cleanup(
    files_to_delete: List[Path],
    dirs_to_delete: List[Path],
    total_size: int,
    verbose: bool,
) -> int:
    """Perform the actual cleanup."""
    deleted_files = 0
    deleted_dirs = 0
    errors = []

    # Delete files
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_files += 1
            if verbose:
                print(f"✅ Deleted file: {file_path}")
        except Exception as e:
            errors.append(f"Failed to delete file {file_path}: {e}")

    # Delete directories
    for dir_path in dirs_to_delete:
        try:
            import shutil

            shutil.rmtree(dir_path)
            deleted_dirs += 1
            if verbose:
                print(f"✅ Deleted directory: {dir_path}")
        except Exception as e:
            errors.append(f"Failed to delete directory {dir_path}: {e}")

    # Report results
    print("✅ Cache cleanup completed!")
    print(f"🗑️  Deleted: {deleted_files} files, {deleted_dirs} directories")
    print(f"💾 Freed: {_format_file_size(total_size)}")

    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for error in errors:
            print(f"  ❌ {error}")
        return 1

    return 0


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def _count_csv_rows(file_path: Path) -> int:
    """Count rows in CSV file (approximate for large files)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Return number of data rows (total lines minus header)
            return max(0, len(lines) - 1)
    except Exception:
        return 0


def export_report_command(
    latest: bool = False,
    assessment_file: Optional[str] = None,
    output_path: Optional[str] = None,
    format_type: str = "json",
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Export assessment report for sharing with data teams.

    Args:
        latest: Export the most recent assessment report
        assessment_file: Specific assessment file to export
        output_path: Where to save the exported report
        format_type: Export format ('json', 'csv', 'pdf')
        environment: Environment to search for assessments
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Get environment configuration
        try:
            env_config = config_manager.get_environment_config(config, environment)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1

        assessments_dir = env_config["paths"]["assessments"]

        # Find the assessment file to export
        if latest:
            # Find the most recent assessment
            assessment_files = list(Path(assessments_dir).glob("*.json"))
            if not assessment_files:
                print("❌ Error: No assessment reports found")
                print(
                    "💡 Run 'adri assess <data> --standard <standard>' to create assessments"
                )
                return 1

            assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            source_file = assessment_files[0]
        elif assessment_file:
            # Use specified assessment file
            if not os.path.isabs(assessment_file):
                source_file = Path(assessments_dir) / assessment_file
            else:
                source_file = Path(assessment_file)

            if not source_file.exists():
                print(f"❌ Error: Assessment file not found: {source_file}")
                return 1
        else:
            print("❌ Error: Must specify either --latest or provide assessment file")
            print("💡 Use 'adri export-report --latest' or 'adri export-report <file>'")
            return 1

        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"adri_report_{timestamp}.{format_type}"
            output_path = output_filename

        # Load assessment data
        with open(source_file, "r") as f:
            assessment_data = json.load(f)

        # Export in requested format
        if format_type == "json":
            # Add export metadata
            export_data = {
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "source_file": str(source_file),
                    "adri_version": "2.0.0",
                },
                "assessment": assessment_data,
            }

            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

        elif format_type == "csv":
            # Create CSV summary
            rows = []

            # Overall summary
            rows.append(["Metric", "Value"])
            rows.append(
                ["Overall Score", f"{assessment_data.get('overall_score', 'N/A')}/100"]
            )
            rows.append(
                [
                    "Status",
                    "PASSED" if assessment_data.get("passed", False) else "FAILED",
                ]
            )
            rows.append(["Assessment Date", assessment_data.get("timestamp", "N/A")])
            rows.append(["", ""])  # Empty row

            # Dimension scores
            rows.append(["Dimension", "Score", "Max Score", "Percentage"])
            if "dimension_scores" in assessment_data:
                for dim_name, dim_data in assessment_data["dimension_scores"].items():
                    if isinstance(dim_data, dict) and "score" in dim_data:
                        score = dim_data["score"]
                        percentage = (score / 20) * 100 if score else 0
                        rows.append(
                            [
                                dim_name.title(),
                                f"{score:.1f}",
                                "20.0",
                                f"{percentage:.1f}%",
                            ]
                        )

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

        else:
            print(f"❌ Error: Unsupported export format: {format_type}")
            print("💡 Supported formats: json, csv")
            return 1

        # Success message
        print("📤 Assessment report exported successfully!")
        print(f"📄 Source: {source_file.name}")
        print(f"📁 Exported to: {output_path}")
        print(f"📊 Format: {format_type.upper()}")

        # Show sharing instructions
        print("\n💬 Share with your data team:")
        print(f"   'Please review the attached ADRI assessment report ({output_path})")
        print("   and address the data quality issues identified.'")

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to export report: {e}")
        return 1


def show_standard_command(
    standard_name: str,
    verbose: bool = False,
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Show details of a specific ADRI standard.

    Args:
        standard_name: Name of the standard to show (with or without .yaml extension)
        verbose: Show detailed requirements and rules
        environment: Environment to search for standard
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration and resolve paths
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        env_config = _get_environment_config(config_manager, config, environment)
        if env_config is None:
            return 1

        # Load standard data
        standard_data = _load_standard_data(standard_name, env_config)
        if standard_data is None:
            return 1

        # Display standard information
        _display_standard_header(standard_data, environment, config)
        _display_standard_info(standard_data)
        _display_requirements_summary(standard_data, verbose)
        _display_usage_instructions(standard_data)

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to show standard: {e}")
        return 1


def _get_environment_config(
    config_manager: ConfigManager, config: Dict[str, Any], environment: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Get environment configuration with error handling."""
    try:
        return config_manager.get_environment_config(config, environment)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return None


def _load_standard_data(
    standard_name: str, env_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Load and validate standard data."""
    standard_path = _resolve_standard_path(standard_name, env_config)

    if not os.path.exists(standard_path):
        print(f"❌ Error: Standard not found: {standard_name}")
        print(f"📁 Searched in: {env_config['paths']['standards']}")
        print("💡 Use 'adri list-standards' to see available standards")
        return None

    try:
        with open(standard_path, "r") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
            else:
                print("❌ Error: Standard file does not contain a valid dictionary")
                return None
    except Exception as e:
        print(f"❌ Error: Failed to load standard: {e}")
        return None


def _display_standard_header(
    standard_data: Dict[str, Any], environment: Optional[str], config: Dict[str, Any]
):
    """Display standard header information."""
    print("📋 ADRI Standard Details")
    env_name = environment or config["adri"].get("default_environment", "development")
    print(f"📁 Environment: {env_name}")

    standards_info = standard_data.get("standards", {})
    if "name" in standards_info:
        print(f"📄 File: {standards_info['name']}")
    print()


def _display_standard_info(standard_data: Dict[str, Any]):
    """Display basic standard information."""
    standards_info = standard_data.get("standards", {})

    print("📊 Standard Information:")
    print(f"  Name: {standards_info.get('name', 'Unknown')}")
    print(f"  ID: {standards_info.get('id', 'Unknown')}")
    print(f"  Version: {standards_info.get('version', 'Unknown')}")
    print(f"  Authority: {standards_info.get('authority', 'Unknown')}")

    if "effective_date" in standards_info:
        print(f"  Effective Date: {standards_info['effective_date']}")

    if "description" in standards_info:
        print(f"  Description: {standards_info['description']}")

    print()


def _display_requirements_summary(standard_data: Dict[str, Any], verbose: bool):
    """Display requirements summary with optional verbose details."""
    requirements_info = standard_data.get("requirements", {})

    print("🎯 Quality Requirements:")
    overall_min = requirements_info.get("overall_minimum", "Not set")
    print(f"  Overall Minimum Score: {overall_min}/100")

    _display_dimension_requirements(requirements_info, verbose)
    _display_field_requirements(requirements_info, verbose)
    print()


def _display_dimension_requirements(requirements_info: Dict[str, Any], verbose: bool):
    """Display dimension requirements."""
    if "dimension_requirements" not in requirements_info:
        return

    dim_reqs = requirements_info["dimension_requirements"]
    print(f"  Dimension Requirements: {len(dim_reqs)} configured")

    if verbose:
        print("    📋 Dimension Details:")
        for dim_name, dim_config in dim_reqs.items():
            if isinstance(dim_config, dict) and "minimum_score" in dim_config:
                min_score = dim_config["minimum_score"]
                print(f"      {dim_name.title()}: ≥{min_score}/20")
            else:
                print(f"      {dim_name.title()}: Default rules")


def _display_field_requirements(requirements_info: Dict[str, Any], verbose: bool):
    """Display field requirements."""
    if "field_requirements" not in requirements_info:
        return

    field_reqs = requirements_info["field_requirements"]
    print(f"  Field Requirements: {len(field_reqs)} fields")

    if verbose:
        print("    📋 Field Details:")
        for field_name, field_config in field_reqs.items():
            _display_field_details(field_name, field_config)


def _display_field_details(field_name: str, field_config: Dict[str, Any]):
    """Display details for a single field."""
    field_type = field_config.get("type", "unknown")
    nullable = field_config.get("nullable", True)
    nullable_str = "nullable" if nullable else "required"

    print(f"      {field_name}: {field_type} ({nullable_str})")

    # Show additional constraints
    _display_field_constraints(field_config)


def _display_field_constraints(field_config: Dict[str, Any]):
    """Display field constraints like ranges, patterns, etc."""
    # Range constraints
    if "min_value" in field_config or "max_value" in field_config:
        min_val = field_config.get("min_value", "")
        max_val = field_config.get("max_value", "")
        if min_val and max_val:
            print(f"        Range: {min_val} - {max_val}")
        elif min_val:
            print(f"        Minimum: {min_val}")
        elif max_val:
            print(f"        Maximum: {max_val}")

    # Pattern constraint
    if "pattern" in field_config:
        print(f"        Pattern: {field_config['pattern']}")

    # Allowed values constraint
    if "allowed_values" in field_config:
        values = field_config["allowed_values"]
        if len(values) <= 5:
            print(f"        Allowed: {', '.join(map(str, values))}")
        else:
            print(f"        Allowed: {len(values)} values")


def _display_usage_instructions(standard_data: Dict[str, Any]):
    """Display usage instructions."""
    standards_info = standard_data.get("standards", {})
    standard_name = standards_info.get("name", "standard")

    print("📋 Usage:")
    print(f"  • Test data: adri assess <data-file> --standard {standard_name}")
    print(f"  • Validate: adri validate-standard {standard_name}")
    print("  • Generate from data: adri generate-standard <data-file>")


def explain_failure_command(
    assessment_file: Optional[str] = None,
    latest: bool = False,
    environment: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
    """
    Explain assessment failure in detail with actionable recommendations.

    Args:
        assessment_file: Specific assessment file to explain
        latest: Explain the most recent assessment
        environment: Environment to search for assessments
        config_path: Specific config file path

    Returns:
        Exit code: 0 for success, non-zero for error
    """
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_active_config(config_path)

        if config is None:
            print("❌ Error: No ADRI configuration found")
            print("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        # Get environment configuration
        try:
            env_config = config_manager.get_environment_config(config, environment)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1

        assessments_dir = env_config["paths"]["assessments"]

        # Find the assessment file to explain
        if latest:
            # Find the most recent assessment
            assessment_files = list(Path(assessments_dir).glob("*.json"))
            if not assessment_files:
                print("❌ Error: No assessment reports found")
                print(
                    "💡 Run 'adri assess <data> --standard <standard>' to create assessments"
                )
                return 1

            assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            source_file = assessment_files[0]
        elif assessment_file:
            # Use specified assessment file
            if not os.path.isabs(assessment_file):
                source_file = Path(assessments_dir) / assessment_file
            else:
                source_file = Path(assessment_file)

            if not source_file.exists():
                print(f"❌ Error: Assessment file not found: {source_file}")
                return 1
        else:
            print("❌ Error: Must specify either --latest or provide assessment file")
            print(
                "💡 Use 'adri explain-failure --latest' or 'adri explain-failure <file>'"
            )
            return 1

        # Load assessment data
        with open(source_file, "r") as f:
            assessment_data = json.load(f)

        # Check if assessment actually failed
        passed = assessment_data.get("passed", False)
        overall_score = assessment_data.get("overall_score", 0)

        print("🔍 ADRI Assessment Failure Analysis")
        print(f"📄 Report: {source_file.name}")
        print(f"📊 Score: {overall_score:.1f}/100")
        print(f"📅 Date: {assessment_data.get('timestamp', 'Unknown')}")
        print()

        if passed:
            print("✅ Note: This assessment actually PASSED")
            print("💡 Use this analysis to understand what made it successful")
            print()

        # Analyze dimension failures
        dimension_scores = assessment_data.get("dimension_scores", {})
        failed_dimensions = []

        print("📊 Dimension Analysis:")
        for dim_name, dim_data in dimension_scores.items():
            if isinstance(dim_data, dict) and "score" in dim_data:
                score = dim_data["score"]
                percentage = (score / 20) * 100
                status = "✅" if score >= 15 else "❌"

                print(
                    f"  {status} {dim_name.title()}: {score:.1f}/20 ({percentage:.1f}%)"
                )

                if score < 15:
                    failed_dimensions.append((dim_name, score, dim_data))

        print()

        # Detailed failure explanations
        if failed_dimensions:
            print("🚨 Problem Areas:")

            for dim_name, score, dim_data in failed_dimensions:
                print(f"\n❌ {dim_name.title()} Failure (Score: {score:.1f}/20)")

                # Get specific issues if available
                issues = dim_data.get("issues", [])
                if issues:
                    print("   Issues found:")
                    for issue in issues[:3]:  # Show top 3 issues
                        print(f"   • {issue}")
                    if len(issues) > 3:
                        print(f"   • ... and {len(issues) - 3} more issues")

                # Provide dimension-specific recommendations
                recommendations = _get_dimension_recommendations(
                    dim_name, score, dim_data
                )
                if recommendations:
                    print("   💡 How to fix:")
                    for rec in recommendations:
                        print(f"   • {rec}")

        # Overall recommendations
        print("\n🔧 Action Plan:")
        print("1. Focus on the failed dimensions above")
        print("2. Export this report for your data team:")
        print(f"   adri export-report {source_file.name}")
        print("3. After fixes, test with:")

        # Try to extract data source and standard from metadata
        metadata = assessment_data.get("metadata", {})
        data_source = metadata.get("data_source", "<your-data>")
        standard_name = metadata.get("standard_name", "<standard>")

        print(f"   adri assess {data_source} --standard {standard_name}")

        print("\n📞 Need Help?")
        print("• Review standard requirements: adri show-standard " + standard_name)
        print("• List all assessments: adri list-assessments --verbose")
        print("• Clean and retry: adri assess <fixed-data> --standard " + standard_name)

        return 0

    except Exception as e:
        print(f"❌ Error: Failed to explain failure: {e}")
        return 1


def _get_dimension_recommendations(
    dim_name: str, score: float, dim_data: dict
) -> List[str]:
    """Get specific recommendations for a failed dimension."""
    recommendations = []

    if dim_name == "validity":
        recommendations.extend(
            [
                "Check for invalid email formats, phone numbers, or dates",
                "Validate data types match expected formats",
                "Remove or fix records with invalid characters or patterns",
                "Ensure numeric fields contain only numbers",
            ]
        )

    elif dim_name == "completeness":
        recommendations.extend(
            [
                "Fill in missing required fields",
                "Remove records with too many empty values",
                "Check for null, empty, or whitespace-only values",
                "Ensure all mandatory columns have data",
            ]
        )

    elif dim_name == "consistency":
        recommendations.extend(
            [
                "Standardize date formats across all records",
                "Use consistent naming conventions",
                "Ensure categorical values use the same spelling/case",
                "Fix inconsistent data types in the same column",
            ]
        )

    elif dim_name == "freshness":
        recommendations.extend(
            [
                "Update old records with recent data",
                "Check timestamp fields for future dates",
                "Ensure data is within acceptable age limits",
                "Verify data collection dates are reasonable",
            ]
        )

    elif dim_name == "plausibility":
        recommendations.extend(
            [
                "Review outlier values that seem unrealistic",
                "Check for negative values where they shouldn't exist",
                "Validate ranges (e.g., ages 0-120, percentages 0-100)",
                "Remove or investigate extreme values",
            ]
        )

    # Add score-specific advice
    if score < 5:
        recommendations.insert(
            0, f"CRITICAL: {dim_name} has severe issues - major data cleanup needed"
        )
    elif score < 10:
        recommendations.insert(0, f"MAJOR: {dim_name} needs significant improvement")
    else:
        recommendations.insert(
            0, f"MINOR: {dim_name} needs some cleanup to meet standards"
        )

    return recommendations[:4]  # Return top 4 recommendations


def main():
    """Provide main CLI entry point for ADRI validator commands."""
    import click

    @click.group()
    @click.version_option(version=__version__, prog_name="adri")
    def cli():
        """ADRI - Stop Your AI Agents Breaking on Bad Data."""
        pass

    @cli.command()
    @click.option("--force", is_flag=True, help="Overwrite existing configuration")
    @click.option("--project-name", help="Custom project name")
    @click.option("--config-path", help="Custom config file location")
    def setup(force, project_name, config_path):
        """Initialize ADRI in a project."""
        exit_code = setup_command(force, project_name, config_path)
        if exit_code != 0:
            raise click.ClickException("Setup failed")

    @cli.command()
    @click.argument("data_path")
    @click.option(
        "--standard", "standard_path", required=True, help="Path to YAML standard file"
    )
    @click.option("--output", "output_path", help="Output path for assessment report")
    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--environment", help="Environment to use (development/production)")
    @click.option("--config", "config_path", help="Specific config file path")
    def assess(
        data_path, standard_path, output_path, verbose, environment, config_path
    ):
        """Run data quality assessment."""
        exit_code = assess_command(
            data_path, standard_path, output_path, verbose, environment, config_path
        )
        if exit_code != 0:
            raise click.ClickException("Assessment failed")

    @cli.command("generate-standard")
    @click.argument("data_path")
    @click.option("--force", is_flag=True, help="Overwrite existing standard file")
    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--environment", help="Environment to use (development/production)")
    @click.option("--config", "config_path", help="Specific config file path")
    def generate_standard(data_path, force, verbose, environment, config_path):
        """Generate ADRI standard from data file analysis."""
        exit_code = generate_adri_standard_command(
            data_path, force, verbose, environment, config_path
        )
        if exit_code != 0:
            raise click.ClickException("Standard generation failed")

    @cli.command("validate-standard")
    @click.argument("standard_path")
    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--output", "output_path", help="Output path for validation report")
    def validate_standard(standard_path, verbose, output_path):
        """Validate YAML standard file."""
        exit_code = validate_standard_command(standard_path, verbose, output_path)
        if exit_code != 0:
            raise click.ClickException("Standard validation failed")

    @cli.command("list-standards")
    @click.option("--environment", help="Environment to list standards from")
    @click.option("--verbose", is_flag=True, help="Show detailed standard information")
    @click.option("--config", "config_path", help="Specific config file path")
    def list_standards(environment, verbose, config_path):
        """List available YAML standards."""
        return list_standards_command(environment, verbose, config_path)

    # Actually call the CLI group to execute commands
    cli()


if __name__ == "__main__":
    main()
