"""Serialization utilities for the ADRI framework.

This module contains utilities for serializing and deserializing assessment results,
standards, and other data structures to various formats like JSON, YAML, and CSV.
"""

import csv
import json
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from ..core.exceptions import SerializationError


class JSONSerializer:
    """Serializer for JSON format."""

    @staticmethod
    def serialize(data: Any, indent: int | None = 2, ensure_ascii: bool = False) -> str:
        """Convert data to JSON string format.

        Args:
            data: Data to serialize
            indent: Indentation for pretty printing (None for compact)
            ensure_ascii: Whether to escape non-ASCII characters

        Returns:
            JSON string representation

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return json.dumps(
                data,
                indent=indent,
                ensure_ascii=ensure_ascii,
                default=JSONSerializer._json_default,
                sort_keys=False,
            )
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization failed: {e}")

    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Deserialize JSON string to Python object.

        Args:
            json_str: JSON string to deserialize

        Returns:
            Deserialized Python object

        Raises:
            SerializationError: If deserialization fails
        """
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            raise SerializationError(f"JSON deserialization failed: {e}")

    @staticmethod
    def _json_default(obj: Any) -> Any:
        """Handle serialization of non-JSON-serializable objects."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)


class YAMLSerializer:
    """Serializer for YAML format."""

    @staticmethod
    def serialize(
        data: Any, default_flow_style: bool = False, sort_keys: bool = False
    ) -> str:
        """Serialize data to YAML string.

        Args:
            data: Data to serialize
            default_flow_style: Whether to use flow style formatting
            sort_keys: Whether to sort dictionary keys

        Returns:
            YAML string representation

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return yaml.dump(
                data,
                default_flow_style=default_flow_style,
                sort_keys=sort_keys,
                allow_unicode=True,
                default_style=None,
            )
        except yaml.YAMLError as e:
            raise SerializationError(f"YAML serialization failed: {e}")

    @staticmethod
    def deserialize(yaml_str: str) -> Any:
        """Deserialize YAML string to Python object.

        Args:
            yaml_str: YAML string to deserialize

        Returns:
            Deserialized Python object

        Raises:
            SerializationError: If deserialization fails
        """
        try:
            return yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise SerializationError(f"YAML deserialization failed: {e}")


class CSVSerializer:
    """Serializer for CSV format."""

    @staticmethod
    def serialize(
        data: list[dict[str, Any]],
        fieldnames: list[str] | None = None,
        delimiter: str = ",",
        quoting: int = csv.QUOTE_MINIMAL,
    ) -> str:
        """Serialize list of dictionaries to CSV string.

        Args:
            data: List of dictionaries to serialize
            fieldnames: List of field names (auto-detected if None)
            delimiter: Field delimiter character
            quoting: CSV quoting style

        Returns:
            CSV string representation

        Raises:
            SerializationError: If serialization fails
        """
        if not isinstance(data, list):
            raise SerializationError(
                "CSV serialization requires a list of dictionaries"
            )

        if not data:
            return ""

        try:
            output = StringIO()

            # Auto-detect fieldnames if not provided
            if fieldnames is None:
                fieldnames = list(data[0].keys()) if data else []

            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                delimiter=delimiter,
                quoting=quoting,
                lineterminator="\n",
            )

            writer.writeheader()
            for row in data:
                # Convert non-string values to strings
                cleaned_row = {
                    k: CSVSerializer._clean_csv_value(v) for k, v in row.items()
                }
                writer.writerow(cleaned_row)

            return output.getvalue()

        except (csv.Error, AttributeError) as e:
            raise SerializationError(f"CSV serialization failed: {e}")

    @staticmethod
    def deserialize(
        csv_str: str, delimiter: str = ",", quoting: int = csv.QUOTE_MINIMAL
    ) -> list[dict[str, Any]]:
        """Deserialize CSV string to list of dictionaries.

        Args:
            csv_str: CSV string to deserialize
            delimiter: Field delimiter character
            quoting: CSV quoting style

        Returns:
            List of dictionaries

        Raises:
            SerializationError: If deserialization fails
        """
        try:
            input_stream = StringIO(csv_str)
            reader = csv.DictReader(input_stream, delimiter=delimiter, quoting=quoting)

            return list(reader)

        except csv.Error as e:
            raise SerializationError(f"CSV deserialization failed: {e}")

    @staticmethod
    def _clean_csv_value(value: Any) -> str:
        """Clean a value for CSV serialization."""
        if value is None:
            return ""
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return json.dumps(value)
        else:
            return str(value)


class AssessmentResultSerializer:
    """Specialized serializer for ADRI assessment results."""

    @staticmethod
    def to_standard_dict(result: Any) -> dict[str, Any]:
        """Convert assessment result to standard dictionary format.

        Args:
            result: Assessment result object

        Returns:
            Standardized dictionary representation
        """
        if hasattr(result, "to_standard_dict"):
            return result.to_standard_dict()
        elif hasattr(result, "to_dict"):
            return result.to_dict()
        else:
            # Fallback: try to extract common assessment result fields
            return AssessmentResultSerializer._extract_result_fields(result)

    @staticmethod
    def to_v2_standard_dict(
        result: Any, include_explanations: bool = True
    ) -> dict[str, Any]:
        """Convert assessment result to v2 standard dictionary format.

        Args:
            result: Assessment result object
            include_explanations: Whether to include detailed explanations

        Returns:
            V2 standardized dictionary representation
        """
        if hasattr(result, "to_v2_standard_dict"):
            return result.to_v2_standard_dict(include_explanations)
        else:
            # Fallback to standard format
            return AssessmentResultSerializer.to_standard_dict(result)

    @staticmethod
    def to_json(
        result: Any, format_version: str = "standard", indent: int | None = 2
    ) -> str:
        """Serialize assessment result to JSON.

        Args:
            result: Assessment result object
            format_version: Format version ("standard" or "v2")
            indent: JSON indentation

        Returns:
            JSON string
        """
        if format_version == "v2":
            data = AssessmentResultSerializer.to_v2_standard_dict(result)
        else:
            data = AssessmentResultSerializer.to_standard_dict(result)

        return JSONSerializer.serialize(data, indent=indent)

    @staticmethod
    def to_yaml(result: Any, format_version: str = "standard") -> str:
        """Serialize assessment result to YAML.

        Args:
            result: Assessment result object
            format_version: Format version ("standard" or "v2")

        Returns:
            YAML string
        """
        if format_version == "v2":
            data = AssessmentResultSerializer.to_v2_standard_dict(result)
        else:
            data = AssessmentResultSerializer.to_standard_dict(result)

        return YAMLSerializer.serialize(data, sort_keys=False)

    @staticmethod
    def to_csv_summary(result: Any) -> str:
        """Create a CSV summary of assessment results.

        Args:
            result: Assessment result object

        Returns:
            CSV string with summary information
        """
        try:
            # Extract key metrics for CSV format
            summary_data = []

            if hasattr(result, "overall_score"):
                summary_data.append(
                    {
                        "metric": "overall_score",
                        "value": result.overall_score,
                        "unit": "percentage",
                    }
                )

            if hasattr(result, "dimension_scores"):
                for dim_name, dim_score in result.dimension_scores.items():
                    score_value = (
                        dim_score.score if hasattr(dim_score, "score") else dim_score
                    )
                    summary_data.append(
                        {
                            "metric": f"dimension_{dim_name}",
                            "value": score_value,
                            "unit": "score_20",
                        }
                    )

            if hasattr(result, "passed"):
                summary_data.append(
                    {"metric": "passed", "value": result.passed, "unit": "boolean"}
                )

            return CSVSerializer.serialize(summary_data)

        except Exception as e:
            raise SerializationError(f"CSV summary serialization failed: {e}")

    @staticmethod
    def _extract_result_fields(result: Any) -> dict[str, Any]:
        """Extract common fields from an assessment result object."""
        extracted = {}

        # Common field names to look for
        common_fields = [
            "overall_score",
            "dimension_scores",
            "passed",
            "metadata",
            "field_analysis",
            "rule_executions",
            "execution_stats",
        ]

        for field in common_fields:
            if hasattr(result, field):
                value = getattr(result, field)
                if value is not None:
                    extracted[field] = value

        return extracted


class StandardSerializer:
    """Specialized serializer for ADRI standards."""

    @staticmethod
    def serialize_standard(
        standard: dict[str, Any], format: str = "yaml", include_metadata: bool = True
    ) -> str:
        """Serialize an ADRI standard to the specified format.

        Args:
            standard: Standard dictionary to serialize
            format: Output format ("yaml", "json")
            include_metadata: Whether to include metadata section

        Returns:
            Serialized standard string

        Raises:
            SerializationError: If serialization fails
        """
        # Clean up standard for serialization
        clean_standard = StandardSerializer._clean_standard(standard, include_metadata)

        if format.lower() == "json":
            return JSONSerializer.serialize(clean_standard, indent=2)
        elif format.lower() == "yaml":
            return YAMLSerializer.serialize(clean_standard, sort_keys=False)
        else:
            raise SerializationError(f"Unsupported standard format: {format}")

    @staticmethod
    def deserialize_standard(content: str, format: str = "yaml") -> dict[str, Any]:
        """Deserialize an ADRI standard from string content.

        Args:
            content: Standard content string
            format: Input format ("yaml", "json")

        Returns:
            Standard dictionary

        Raises:
            SerializationError: If deserialization fails
        """
        if format.lower() == "json":
            return JSONSerializer.deserialize(content)
        elif format.lower() == "yaml":
            return YAMLSerializer.deserialize(content)
        else:
            raise SerializationError(f"Unsupported standard format: {format}")

    @staticmethod
    def _clean_standard(
        standard: dict[str, Any], include_metadata: bool
    ) -> dict[str, Any]:
        """Clean up standard dictionary for serialization."""
        cleaned = standard.copy()

        if not include_metadata and "metadata" in cleaned:
            del cleaned["metadata"]

        # Ensure standard has required sections
        if "standards" not in cleaned:
            cleaned["standards"] = {
                "id": "unknown",
                "name": "Unnamed Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
            }

        if "requirements" not in cleaned:
            cleaned["requirements"] = {}

        return cleaned


def serialize_assessment_result(result: Any, format: str = "json", **kwargs) -> str:
    """Serialize an assessment result to the specified format.

    Args:
        result: Assessment result to serialize
        format: Output format ("json", "yaml", "csv")
        **kwargs: Additional format-specific arguments

    Returns:
        Serialized result string

    Raises:
        SerializationError: If serialization fails
    """
    format = format.lower()

    if format == "json":
        return AssessmentResultSerializer.to_json(result, **kwargs)
    elif format == "yaml":
        return AssessmentResultSerializer.to_yaml(result, **kwargs)
    elif format == "csv":
        return AssessmentResultSerializer.to_csv_summary(result)
    else:
        raise SerializationError(f"Unsupported result format: {format}")


def save_to_file(
    data: Any, file_path: str | Path, format: str | None = None, **kwargs
) -> None:
    """Save data to a file in the specified format.

    Args:
        data: Data to save
        file_path: Output file path
        format: Output format (auto-detected from extension if None)
        **kwargs: Additional serialization arguments

    Raises:
        SerializationError: If saving fails
    """
    file_path = Path(file_path)

    # Auto-detect format from file extension
    if format is None:
        format = file_path.suffix.lower().lstrip(".")
        if not format:
            raise SerializationError("Cannot determine format from file path")

    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize data
        if format == "json":
            content = JSONSerializer.serialize(data, **kwargs)
        elif format in ["yaml", "yml"]:
            content = YAMLSerializer.serialize(data, **kwargs)
        elif format == "csv":
            if not isinstance(data, list):
                raise SerializationError("CSV format requires list data")
            content = CSVSerializer.serialize(data, **kwargs)
        else:
            raise SerializationError(f"Unsupported format: {format}")

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    except OSError as e:
        raise SerializationError(f"Failed to save file {file_path}: {e}")


def load_from_file(file_path: str | Path, format: str | None = None) -> Any:
    """Load data from a file in the specified format.

    Args:
        file_path: Input file path
        format: Input format (auto-detected from extension if None)

    Returns:
        Deserialized data

    Raises:
        SerializationError: If loading fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise SerializationError(f"File not found: {file_path}")

    # Auto-detect format from file extension
    if format is None:
        format = file_path.suffix.lower().lstrip(".")
        if not format:
            raise SerializationError("Cannot determine format from file path")

    try:
        # Read file content
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Deserialize content
        if format == "json":
            return JSONSerializer.deserialize(content)
        elif format in ["yaml", "yml"]:
            return YAMLSerializer.deserialize(content)
        elif format == "csv":
            return CSVSerializer.deserialize(content)
        else:
            raise SerializationError(f"Unsupported format: {format}")

    except OSError as e:
        raise SerializationError(f"Failed to load file {file_path}: {e}")


# Default serializers for component registry
class JSONResultSerializer:
    """JSON result serializer for component registry."""

    def serialize(self, result: Any) -> str:
        """Serialize result to JSON."""
        return AssessmentResultSerializer.to_json(result)

    def get_format_name(self) -> str:
        """Get format name."""
        return "json"


class YAMLResultSerializer:
    """YAML result serializer for component registry."""

    def serialize(self, result: Any) -> str:
        """Serialize result to YAML."""
        return AssessmentResultSerializer.to_yaml(result)

    def get_format_name(self) -> str:
        """Get format name."""
        return "yaml"


class CSVResultSerializer:
    """CSV result serializer for component registry."""

    def serialize(self, result: Any) -> str:
        """Serialize result to CSV summary."""
        return AssessmentResultSerializer.to_csv_summary(result)

    def get_format_name(self) -> str:
        """Get format name."""
        return "csv"
