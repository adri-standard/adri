"""
ADRI Data Loaders.

Data loading utilities extracted from the CLI for use in the validator module.
Supports CSV, JSON, and Parquet file formats.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Standard pandas import for data operations
import pandas as pd
import yaml


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
        return load_csv(file_path_obj)
    elif file_path_obj.suffix.lower() == ".json":
        return load_json(file_path_obj)
    elif file_path_obj.suffix.lower() == ".parquet":
        return load_parquet(file_path_obj)
    else:
        raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")


def load_csv(file_path: Path) -> List[Dict[str, Any]]:
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


def load_json(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of dictionaries

    Raises:
        ValueError: If JSON file doesn't contain a list of objects
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure data is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of objects")

    return data


def load_parquet(file_path: Path) -> List[Dict[str, Any]]:
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
        data: List[Dict[str, Any]] = df.to_dict("records")

        return data

    except Exception as e:
        if "parquet" in str(e).lower():
            raise ValueError(f"Failed to read Parquet file: {e}")
        else:
            raise


def load_standard(file_path: str, validate: bool = True) -> Dict[str, Any]:
    """
    Load YAML standard from file with optional validation.

    Args:
        file_path: Path to YAML standard file
        validate: Whether to validate the standard schema (default: True)

    Returns:
        Standard dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        Exception: If standard validation fails (when validate=True)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Standard file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            yaml_content: Dict[Any, Any] = yaml.safe_load(f)

        # Validate standard if requested
        if validate:
            from adri.standards.exceptions import SchemaValidationError
            from adri.standards.validator import get_validator

            validator = get_validator()
            result = validator.validate_standard(
                yaml_content, file_path, use_cache=True
            )

            if not result.is_valid:
                raise SchemaValidationError(
                    f"Standard validation failed: {file_path}",
                    validation_result=result,
                    standard_path=file_path,
                )

        return yaml_content

    except yaml.YAMLError as e:
        raise Exception(f"Invalid YAML format: {e}")
    except SchemaValidationError:
        # Re-raise schema validation errors as-is
        raise
    except Exception as e:
        raise Exception(f"Failed to load standard: {e}")


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


def get_data_info(file_path: str) -> Dict[str, Any]:
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


def _get_csv_info(file_path: Path) -> Dict[str, Any]:
    """Get information about a CSV file."""
    with open(file_path, "r", encoding="utf-8") as f:
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


def _get_json_info(file_path: Path) -> Dict[str, Any]:
    """Get information about a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
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
            return {
                "type": type(data).__name__,
                "is_list": False,
            }


def _get_parquet_info(file_path: Path) -> Dict[str, Any]:
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
