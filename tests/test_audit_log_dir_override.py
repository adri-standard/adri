"""Tests for per-call audit log output directory override.

These tests cover the run-scoped audit logging feature added to the
`@adri_protected` decorator via the `audit_log_dir` parameter.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


def test_audit_log_dir_overrides_output_dir(tmp_path: Path):
    from adri.decorator import adri_protected

    # Ensure ADRI uses a local/test environment so it can create contracts.
    os.environ["ADRI_ENV"] = "development"

    log_dir = tmp_path / "runs" / "RUN_001" / "adri" / "audit-logs"

    @adri_protected(
        contract="audit_log_dir_test",
        data_param="data",
        auto_generate=True,
        on_failure="warn",
        audit_log_dir=str(log_dir),
    )
    def f(data):
        return data

    f({"x": 1})

    # LocalLogger prefixes default to "adri".
    assert (log_dir / "adri_assessment_logs.jsonl").exists()
    assert (log_dir / "adri_dimension_scores.jsonl").exists()
    assert (log_dir / "adri_failed_validations.jsonl").exists()
    assert (log_dir / "adri_write_seq.txt").exists()


def test_audit_log_dir_does_not_leak_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from adri.decorator import adri_protected

    os.environ["ADRI_ENV"] = "development"

    # Simulate a pre-existing env value and ensure we restore it.
    monkeypatch.setenv("ADRI_LOG_DIR", str(tmp_path / "preexisting"))
    before = os.environ.get("ADRI_LOG_DIR")

    log_dir = tmp_path / "runs" / "RUN_002" / "adri" / "audit-logs"

    @adri_protected(
        contract="audit_log_dir_test_2",
        data_param="data",
        auto_generate=True,
        on_failure="warn",
        audit_log_dir=str(log_dir),
    )
    def f(data):
        return data

    f({"x": 1})

    after = os.environ.get("ADRI_LOG_DIR")
    assert after == before
