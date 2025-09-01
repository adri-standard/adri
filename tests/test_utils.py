"""
Test utilities for ADRI Validator test suite.

This module provides utilities to prevent token explosion and manage test output.
"""

import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class OutputLimiter:
    """Limits test output to prevent token explosion in CI/CD."""

    MAX_OUTPUT_CHARS = int(os.environ.get("ADRI_TEST_MAX_OUTPUT", "1000"))
    MAX_DATAFRAME_ROWS = int(os.environ.get("ADRI_TEST_MAX_DF_ROWS", "10"))
    MAX_LIST_ITEMS = int(os.environ.get("ADRI_TEST_MAX_LIST_ITEMS", "10"))

    @classmethod
    def truncate(cls, output: Any, context: str = "") -> str:
        """
        Truncate any output to prevent token explosion.

        Args:
            output: The output to truncate
            context: Optional context string for the output

        Returns:
            Truncated string representation
        """
        if output is None:
            return "None"

        # Handle DataFrames specially
        if isinstance(output, pd.DataFrame):
            return cls._truncate_dataframe(output, context)

        # Handle numpy arrays
        if isinstance(output, np.ndarray):
            return cls._truncate_array(output, context)

        # Handle lists
        if isinstance(output, (list, tuple)):
            return cls._truncate_list(output, context)

        # Handle dictionaries
        if isinstance(output, dict):
            return cls._truncate_dict(output, context)

        # Default string truncation
        str_output = str(output)
        if len(str_output) > cls.MAX_OUTPUT_CHARS:
            return f"{str_output[:cls.MAX_OUTPUT_CHARS]}... [TRUNCATED - {context}]"
        return str_output

    @classmethod
    def _truncate_dataframe(cls, df: pd.DataFrame, context: str) -> str:
        """Truncate DataFrame output."""
        shape_info = f"DataFrame[{df.shape[0]}x{df.shape[1]}]"
        if df.shape[0] <= cls.MAX_DATAFRAME_ROWS:
            return f"{shape_info}\n{df}"

        head = df.head(cls.MAX_DATAFRAME_ROWS // 2)
        tail = df.tail(cls.MAX_DATAFRAME_ROWS // 2)
        return (
            f"{shape_info} - showing first and last {cls.MAX_DATAFRAME_ROWS // 2} rows\n"
            f"{head}\n...\n{tail}"
        )

    @classmethod
    def _truncate_array(cls, arr: np.ndarray, context: str) -> str:
        """Truncate numpy array output."""
        shape_info = f"Array{arr.shape}"
        if arr.size <= cls.MAX_LIST_ITEMS:
            return f"{shape_info}: {arr}"

        flat = arr.flatten()
        truncated = flat[: cls.MAX_LIST_ITEMS]
        return f"{shape_info}: [{', '.join(map(str, truncated))}... ({arr.size} total items)]"

    @classmethod
    def _truncate_list(cls, lst: List, context: str) -> str:
        """Truncate list output."""
        if len(lst) <= cls.MAX_LIST_ITEMS:
            return str(lst)

        truncated = lst[: cls.MAX_LIST_ITEMS]
        return f"[{', '.join(map(str, truncated))}... ({len(lst)} total items)]"

    @classmethod
    def _truncate_dict(cls, d: Dict, context: str) -> str:
        """Truncate dictionary output."""
        if len(d) <= cls.MAX_LIST_ITEMS:
            return json.dumps(d, indent=2, default=str)[: cls.MAX_OUTPUT_CHARS]

        items = list(d.items())[: cls.MAX_LIST_ITEMS]
        truncated = dict(items)
        result = json.dumps(truncated, indent=2, default=str)[: cls.MAX_OUTPUT_CHARS]
        return f"{result}... ({len(d)} total keys)"


class TestDataGenerator:
    """Generates test data with size controls."""

    @staticmethod
    def get_safe_row_count(requested: int, test_type: str = "normal") -> int:
        """
        Get safe row count based on environment and test type.

        Args:
            requested: The requested number of rows
            test_type: Type of test ('quick', 'normal', 'performance', 'stress')

        Returns:
            Safe row count to use
        """
        # Check for environment override
        max_rows = int(os.environ.get("ADRI_TEST_MAX_ROWS", "0"))

        if max_rows > 0:
            return min(requested, max_rows)

        # Apply sensible defaults based on test type
        limits = {"quick": 100, "normal": 1000, "performance": 10000, "stress": 100000}

        limit = limits.get(test_type, 1000)
        return min(requested, limit)

    @staticmethod
    def generate_dataset(
        rows: int, cols: int = 10, test_type: str = "normal"
    ) -> pd.DataFrame:
        """
        Generate a test dataset with size controls.

        Args:
            rows: Requested number of rows
            cols: Number of columns
            test_type: Type of test

        Returns:
            Generated DataFrame
        """
        safe_rows = TestDataGenerator.get_safe_row_count(rows, test_type)

        # Warn if rows were reduced
        if safe_rows < rows:
            print(
                f"⚠️  Dataset reduced from {rows} to {safe_rows} rows for {test_type} test"
            )

        data = {f"col_{i}": np.random.randn(safe_rows) for i in range(cols)}
        return pd.DataFrame(data)


def safe_assert_equal(actual: Any, expected: Any, message: str = ""):
    """
    Assert equality with truncated output on failure.

    Args:
        actual: Actual value
        expected: Expected value
        message: Optional assertion message
    """
    try:
        if isinstance(actual, pd.DataFrame) and isinstance(expected, pd.DataFrame):
            pd.testing.assert_frame_equal(actual, expected)
        elif isinstance(actual, np.ndarray) and isinstance(expected, np.ndarray):
            np.testing.assert_array_equal(actual, expected)
        else:
            assert actual == expected, message
    except AssertionError:
        # Truncate the error message
        actual_str = OutputLimiter.truncate(actual, "actual")
        expected_str = OutputLimiter.truncate(expected, "expected")

        raise AssertionError(
            f"{message}\n" f"Actual: {actual_str}\n" f"Expected: {expected_str}"
        ) from None


def skip_if_ci():
    """Skip test if running in CI environment."""
    import pytest

    if os.environ.get("CI"):
        pytest.skip("Skipping resource-intensive test in CI")


def skip_if_slow():
    """Skip test if ADRI_SKIP_SLOW_TESTS is set."""
    import pytest

    if os.environ.get("ADRI_SKIP_SLOW_TESTS"):
        pytest.skip("Skipping slow test (ADRI_SKIP_SLOW_TESTS is set)")
