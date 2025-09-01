"""
Data Loading Module for ADRI Validator.

Provides unified interface for loading data from various sources:
- CSV files
- JSON files
- Pandas DataFrames
- In-memory data structures (lists, dicts)

Supports automatic format detection and consistent DataFrame output.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Unified data loader for various data sources.

    Provides methods to load data from files and in-memory structures,
    with consistent DataFrame output and error handling.
    """

    def __init__(self):
        """Initialize the DataLoader."""
        logger.debug("DataLoader initialized")

    def load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a CSV file.

        Args:
            file_path: Path to the CSV file
            **kwargs: Additional arguments passed to pd.read_csv()

        Returns:
            DataFrame containing the loaded data

        Raises:
            FileNotFoundError: If the file doesn't exist
            pd.errors.EmptyDataError: If the file is empty
            pd.errors.ParserError: If the file can't be parsed
        """
        logger.debug(f"Loading CSV file: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Set default parameters for robust CSV loading
            default_kwargs = {
                "encoding": "utf-8",
                "on_bad_lines": "warn",  # Handle malformed lines gracefully
            }
            default_kwargs.update(kwargs)

            df = pd.read_csv(file_path, **default_kwargs)
            logger.info(
                f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns"
            )
            return df

        except Exception as e:
            logger.error(f"Failed to load CSV file {file_path}: {e}")
            raise

    def load_json(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a JSON file.

        Args:
            file_path: Path to the JSON file
            **kwargs: Additional arguments passed to pd.read_json()

        Returns:
            DataFrame containing the loaded data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        logger.debug(f"Loading JSON file: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            # Try pandas read_json first (handles various JSON formats)
            df = pd.read_json(file_path, **kwargs)
            logger.info(
                f"Successfully loaded JSON with {len(df)} rows and {len(df.columns)} columns"
            )
            return df

        except ValueError:
            # If pandas fails, try manual JSON loading
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Convert to DataFrame
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Handle various dict structures
                    if all(isinstance(v, (list, tuple)) for v in data.values()):
                        # Dict of lists/arrays
                        df = pd.DataFrame(data)
                    else:
                        # Single record dict
                        df = pd.DataFrame([data])
                else:
                    raise ValueError(f"Unsupported JSON structure: {type(data)}")

                logger.info(
                    f"Successfully loaded JSON with {len(df)} rows and {len(df.columns)} columns"
                )
                return df

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in file {file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to load JSON file {file_path}: {e}")
                raise

    def load_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Load data from an existing pandas DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            Copy of the input DataFrame
        """
        logger.debug(
            f"Loading DataFrame with {len(df)} rows and {len(df.columns)} columns"
        )

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}")

        # Return a copy to avoid modifying the original
        result = df.copy()
        logger.debug("Successfully loaded DataFrame")
        return result

    def load_from_dict(self, data: Union[List[Dict], Dict, List]) -> pd.DataFrame:
        """
        Load data from in-memory data structures.

        Args:
            data: List of dictionaries, single dictionary, or list of values

        Returns:
            DataFrame containing the loaded data

        Raises:
            ValueError: If the data structure is not supported
        """
        logger.debug(f"Loading data from memory structure: {type(data)}")

        try:
            if isinstance(data, list):
                if len(data) == 0:
                    # Empty list
                    df = pd.DataFrame()
                elif isinstance(data[0], dict):
                    # List of dictionaries
                    df = pd.DataFrame(data)
                else:
                    # List of values
                    df = pd.DataFrame({"value": data})
            elif isinstance(data, dict):
                # Single dictionary - treat as one record
                df = pd.DataFrame([data])
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            logger.info(
                f"Successfully loaded data with {len(df)} rows and {len(df.columns)} columns"
            )
            return df

        except Exception as e:
            logger.error(f"Failed to load data from memory: {e}")
            raise


def detect_format(data: Any) -> str:
    """
    Detect the format of input data.

    Args:
        data: Input data of various types

    Returns:
        String indicating the detected format: 'csv', 'json', 'dataframe', 'memory'

    Raises:
        ValueError: If the format cannot be detected or is unsupported
    """
    logger.debug(f"Detecting format for data type: {type(data)}")

    if isinstance(data, pd.DataFrame):
        return "dataframe"

    if isinstance(data, (list, dict)):
        return "memory"

    if isinstance(data, (str, Path)):
        file_path = Path(data)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return "csv"
        elif suffix in [".json", ".jsonl"]:
            return "json"
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")

    raise ValueError(f"Cannot detect format for data type: {type(data)}")


def load_data(data: Any, **kwargs) -> pd.DataFrame:
    """
    High-level function to load data from any supported source.

    Automatically detects the data format and uses the appropriate loader.

    Args:
        data: Input data (file path, DataFrame, list, dict, etc.)
        **kwargs: Additional arguments passed to specific loaders

    Returns:
        DataFrame containing the loaded data

    Raises:
        ValueError: If the data format is not supported
        FileNotFoundError: If a file path is provided but the file doesn't exist
    """
    logger.debug(f"Loading data using auto-detection for type: {type(data)}")

    try:
        format_type = detect_format(data)
        loader = DataLoader()

        if format_type == "csv":
            return loader.load_csv(str(data), **kwargs)
        elif format_type == "json":
            return loader.load_json(str(data), **kwargs)
        elif format_type == "dataframe":
            return loader.load_dataframe(data)
        elif format_type == "memory":
            return loader.load_from_dict(data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
