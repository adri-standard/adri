# @ADRI_FEATURE[validator_data_loaders, scope=OPEN_SOURCE]
# Description: Data and contract loading utilities for CSV, JSON, Parquet, and YAML files
"""
ADRI Data Loaders.

Data loading utilities extracted from the CLI for use in the validator module.
Supports CSV, JSON, and Parquet file formats.
"""

import csv
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .modes import ADRIMode

# Standard pandas import for data operations
import pandas as pd
import yaml

# Import for standard validation (avoid circular import by importing here)
from ..contracts.exceptions import SchemaValidationError


def load_data(file_path: str) -> list[dict[str, Any]]:
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
        return load_csv(file_path_obj)
    elif file_path_obj.suffix.lower() == ".json":
        return load_json(file_path_obj)
    elif file_path_obj.suffix.lower() == ".parquet":
        return load_parquet(file_path_obj)
    else:
        raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")


def load_csv(file_path: Path) -> list[dict[str, Any]]:
    """
    Load data from CSV file.

    Args:
        file_path: Path to CSV file

    Returns:
        List of dictionaries, one per row

    Raises:
        ValueError: If CSV file is empty or invalid
    """
    data = []
    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(dict(row))

    # Check if no data was loaded (empty file)
    if not data:
        # Re-read to check if file is truly empty
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                raise ValueError("CSV file is empty")

    return data


def load_json(file_path: Path) -> list[dict[str, Any]]:
    """
    Load data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of dictionaries

    Raises:
        ValueError: If JSON file doesn't contain a list of objects
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Ensure data is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of objects")

    return data


def load_parquet(file_path: Path) -> list[dict[str, Any]]:
    """
    Load data from Parquet file.

    Args:
        file_path: Path to Parquet file

    Returns:
        List of dictionaries, one per row

    Raises:
        ImportError: If pandas is not installed
        ValueError: If Parquet file is empty or invalid
    """
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
        data: list[dict[str, Any]] = df.to_dict("records")

        return data

    except Exception as e:
        if "parquet" in str(e).lower():
            raise ValueError(f"Failed to read Parquet file: {e}")
        else:
            raise


def load_contract(
    file_path: str,
    validate: bool = True,
    expected_mode: "ADRIMode | None" = None,
    strict_structure: bool = False,
) -> dict[str, Any]:
    """
    Load YAML contract from file with optional validation and mode detection.

    Parses validation_rules from field_requirements and converts them to
    ValidationRule objects for use by dimension assessors. Automatically detects
    ADRI template mode (reasoning, conversation, deterministic) and validates
    structure accordingly.

    Args:
        file_path: Path to YAML contract file
        validate: Whether to validate the contract schema (default: True)
        expected_mode: Expected ADRI mode (if provided, validates detected mode matches)
        strict_structure: If True, structure warnings become errors (default: False)

    Returns:
        Contract dictionary with parsed ValidationRule objects and mode metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        Exception: If contract validation fails (when validate=True)
        ValueError: If detected mode doesn't match expected_mode
    """
    # Import validator inside function to avoid circular import at module load time
    from ..contracts.validator import get_validator
    from .modes import detect_mode, is_valid_mode_transition
    from .structure import validate_structure, format_validation_report

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Contract file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            yaml_content: dict[Any, Any] = yaml.safe_load(f)

        # Detect ADRI mode from structure
        detected_mode = detect_mode(yaml_content)

        # Validate detected mode matches expected mode (if provided)
        if expected_mode is not None:
            if not is_valid_mode_transition(detected_mode, expected_mode):
                raise ValueError(
                    f"Mode mismatch in {file_path}: detected {detected_mode.value}, "
                    f"expected {expected_mode.value}"
                )

        # Validate structure for detected mode
        structure_result = validate_structure(
            yaml_content, detected_mode, strict=strict_structure
        )

        if not structure_result.is_valid:
            # Format helpful error message
            report = format_validation_report(structure_result)
            raise ValueError(f"Structure validation failed for {file_path}:\n{report}")

        # Log structure warnings if any (but don't fail)
        if structure_result.warnings:
            import warnings

            for warning in structure_result.warnings:
                warnings.warn(f"Structure warning in {file_path}: {warning}")

        # Validate contract if requested (schema validation)
        if validate:
            validator = get_validator()
            result = validator.validate_contract(
                yaml_content, file_path, use_cache=True
            )

            if not result.is_valid:
                raise SchemaValidationError(
                    f"Contract validation failed: {file_path}",
                    validation_result=result,
                    standard_path=file_path,
                )

        # Parse validation_rules into ValidationRule objects
        yaml_content = _parse_validation_rules(yaml_content)

        # Add mode metadata to contract
        yaml_content["_adri_mode"] = detected_mode.value

        return yaml_content

    except yaml.YAMLError as e:
        raise Exception(f"Invalid YAML format: {e}")
    except SchemaValidationError:
        # Re-raise schema validation errors as-is
        raise
    except ValueError:
        # Re-raise mode/structure validation errors as-is
        raise
    except Exception as e:
        raise Exception(f"Failed to load contract: {e}")


def detect_format(file_path: str) -> str:
    """
    Detect file format based on file extension.

    Args:
        file_path: Path to file

    Returns:
        File format ('csv', 'json', 'parquet', or 'unknown')
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_path_obj = Path(file_path)
    suffix = file_path_obj.suffix.lower()

    if suffix == ".csv":
        return "csv"
    elif suffix == ".json":
        return "json"
    elif suffix == ".parquet":
        return "parquet"
    elif suffix in [".yaml", ".yml"]:
        return "yaml"
    else:
        return "unknown"


def get_data_info(file_path: str) -> dict[str, Any]:
    """
    Get basic information about a data file without fully loading it.

    Args:
        file_path: Path to data file

    Returns:
        Dictionary with file information (size, format, estimated rows, etc.)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_path_obj = Path(file_path)
    file_stats = file_path_obj.stat()

    info = {
        "path": str(file_path_obj),
        "name": file_path_obj.name,
        "size_bytes": file_stats.st_size,
        "format": detect_format(file_path),
        "modified_time": file_stats.st_mtime,
    }

    # Add format-specific information
    try:
        if info["format"] == "csv":
            info.update(_get_csv_info(file_path_obj))
        elif info["format"] == "json":
            info.update(_get_json_info(file_path_obj))
        elif info["format"] == "parquet":
            info.update(_get_parquet_info(file_path_obj))
    except Exception as e:
        info["error"] = str(e)

    return info


def _get_csv_info(file_path: Path) -> dict[str, Any]:
    """Get information about a CSV file."""
    with open(file_path, encoding="utf-8") as f:
        # Get header
        first_line = f.readline()
        if first_line:
            headers = list(csv.reader([first_line]))[0]

            # Count approximate rows
            f.seek(0)
            row_count = sum(1 for _ in f) - 1  # Subtract header

            return {
                "columns": len(headers),
                "column_names": headers,
                "estimated_rows": row_count,
            }

    return {"columns": 0, "estimated_rows": 0}


def _get_json_info(file_path: Path) -> dict[str, Any]:
    """Get information about a JSON file."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

        if isinstance(data, list):
            record_count = len(data)
            if record_count > 0 and isinstance(data[0], dict):
                columns = len(data[0].keys())
                column_names = list(data[0].keys())
            else:
                columns = 0
                column_names = []

            return {
                "records": record_count,
                "columns": columns,
                "column_names": column_names,
            }
        else:
            return {"type": type(data).__name__, "is_list": False}


def _get_parquet_info(file_path: Path) -> dict[str, Any]:
    """Get information about a Parquet file."""
    if pd is None:
        return {"error": "pandas not available"}

    try:
        df = pd.read_parquet(file_path)
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
    except Exception as e:
        return {"error": str(e)}


def _parse_validation_rules(contract: dict[str, Any]) -> dict[str, Any]:
    """
    Parse validation_rules from field_requirements into ValidationRule objects.

    Traverses the contract dictionary and converts any validation_rules lists
    into ValidationRule objects for easier use by dimension assessors.

    Args:
        contract: Contract dictionary loaded from YAML

    Returns:
        Modified contract with ValidationRule objects

    Note:
        This modifies field_requirements in place, converting:
        - Old format: field_requirements with simple constraints
        - New format: field_requirements with validation_rules lists
    """
    from ..core.validation_rule import ValidationRule

    # Check if contract has requirements section
    if "requirements" not in contract:
        return contract
    # @ADRI_FEATURE_END[validator_data_loaders]

    requirements = contract["requirements"]

    # Check if dimension_requirements exist
    if "dimension_requirements" not in requirements:
        return contract

    dimension_requirements = requirements["dimension_requirements"]

    # Process each dimension
    for dimension_name, dimension_config in dimension_requirements.items():
        if not isinstance(dimension_config, dict):
            continue

        # Check if this dimension has field_requirements
        if "field_requirements" not in dimension_config:
            continue

        field_requirements = dimension_config["field_requirements"]
        if not isinstance(field_requirements, dict):
            continue

        # Process each field
        for field_name, field_config in field_requirements.items():
            if not isinstance(field_config, dict):
                continue

            # Check if field has validation_rules (new format)
            if "validation_rules" in field_config:
                validation_rules_data = field_config["validation_rules"]

                if isinstance(validation_rules_data, list):
                    # Parse each rule into a ValidationRule object
                    parsed_rules = []
                    for rule_dict in validation_rules_data:
                        try:
                            rule = ValidationRule.from_dict(rule_dict)
                            parsed_rules.append(rule)
                        except Exception as e:
                            # Log warning but continue - validation will catch issues
                            import warnings

                            warnings.warn(
                                f"Failed to parse validation rule for field '{field_name}' "
                                f"in dimension '{dimension_name}': {e}"
                            )

                    # Replace the list of dicts with list of ValidationRule objects
                    field_config["validation_rules"] = parsed_rules

    return contract
