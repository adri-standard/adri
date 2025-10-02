import pandas as pd

from src.adri.validator.rules import (
    check_allowed_values,
    check_length_bounds,
    check_date_bounds,
    validate_field,
)


def test_check_allowed_values_basic():
    req = {"allowed_values": ["A", "B", "C"]}
    assert check_allowed_values("A", req) is True
    assert check_allowed_values("D", req) is False
    # Robustness: numeric to string comparison
    req_nums = {"allowed_values": [1, 2, 3]}
    assert check_allowed_values("2", req_nums) is True
    assert check_allowed_values("5", req_nums) is False


def test_check_length_bounds_basic():
    req = {"min_length": 2, "max_length": 5}
    assert check_length_bounds("ab", req) is True
    assert check_length_bounds("hello", req) is True
    assert check_length_bounds("a", req) is False
    assert check_length_bounds("toolong", req) is False


def test_check_date_bounds_date_only():
    req = {"after_date": "2024-01-01", "before_date": "2024-12-31"}
    assert check_date_bounds("2024-06-15", req) is True
    assert check_date_bounds("2023-12-31", req) is False
    assert check_date_bounds("2025-01-01", req) is False


def test_validate_field_with_allowed_values_and_lengths():
    field_requirements = {
        "status": {
            "type": "string",
            "nullable": False,
            "allowed_values": ["paid", "pending", "cancelled"],
            "min_length": 3,
            "max_length": 10,
        }
    }
    # Pass
    assert validate_field("status", "paid", field_requirements)["passed"] is True
    # Fail allowed_values
    res = validate_field("status", "unknown", field_requirements)
    assert res["passed"] is False
    assert any("allowed_values" in e or "allowed" in e for e in res["errors"])
    # Fail lengths
    res2 = validate_field("status", "ok", field_requirements)
    assert res2["passed"] is False
    assert any("length" in e.lower() for e in res2["errors"])


def test_validate_field_with_date_bounds():
    field_requirements = {
        "event_date": {
            "type": "date",
            "nullable": False,
            "after_date": "2024-01-01",
            "before_date": "2024-12-31",
        }
    }
    assert validate_field("event_date", "2024-06-01", field_requirements)["passed"] is True
    assert validate_field("event_date", "2023-12-31", field_requirements)["passed"] is False
    assert validate_field("event_date", "2025-01-01", field_requirements)["passed"] is False
