import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml
from unittest.mock import patch

from adri.validator.engine import ValidationEngine
from adri.cli import scoring_explain_command


def _make_standard_dict(field_requirements: Dict[str, Any], extra: Dict[str, Any] = None) -> Dict[str, Any]:
    std: Dict[str, Any] = {
        "standards": {"id": "test_standard", "name": "Test Standard", "version": "1.0.0", "authority": "ADRI Framework"},
        "requirements": {
            "overall_minimum": 75.0,
            "field_requirements": field_requirements,
            "dimension_requirements": {
                "validity": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"type": 1.0}}},
                "completeness": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"missing_required": 1.0}}},
                "consistency": {"weight": 1.0, "minimum_score": 12.0, "scoring": {"rule_weights": {"primary_key_uniqueness": 1.0}}},
                "freshness": {"weight": 1.0, "minimum_score": 15.0, "scoring": {"rule_weights": {"recency_window": 1.0}}},
                "plausibility": {"weight": 1.0, "minimum_score": 12.0, "scoring": {"rule_weights": {}}},
            },
        },
        "record_identification": {
            "primary_key_fields": ["id"]
        },
        "metadata": {}
    }
    if extra:
        # Shallow merge for keys we care about
        for k, v in extra.items():
            if k == "metadata":
                std.setdefault("metadata", {}).update(v or {})
            elif k == "requirements":
                std["requirements"].update(v or {})
            else:
                std[k] = v
    return std


def test_engine_completeness_explain_payload():
    # Data: 3 rows, required field 'a' has 1 missing -> required_total=3, missing_required=1
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "a": ["x", None, "z"],
        "b": [None, "y", None],  # nullable by default
    })
    std = _make_standard_dict(field_requirements={
        "a": {"type": "string", "nullable": False},
        "b": {"type": "string", "nullable": True},
        "id": {"type": "string", "nullable": False},
    })
    # Ensure id has no nulls here to not affect completeness for 'id'
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)
    explain = (result.metadata or {}).get("explain", {})
    comp = explain.get("completeness", {})
    assert isinstance(comp, dict)
    assert comp.get("required_total") == len(df) * 2  # 'a' and 'id' required
    # Missing required: 1 missing in 'a', and 0 in 'id'
    assert comp.get("missing_required") == 1
    assert "per_field_missing" in comp and comp["per_field_missing"].get("a") == 1
    # Score basis should be pass_rate*20
    assert abs(float(comp.get("score_0_20", 0.0)) - float(comp.get("pass_rate", 0.0)) * 20.0) < 1e-9


def test_engine_consistency_explain_payload_with_pk_duplicates():
    # Two rows share same id -> duplicates -> failed_rows >= 2 (capped by total)
    df = pd.DataFrame({
        "id": ["dup", "dup", "ok"],
        "value": [1, 2, 3],
    })
    std = _make_standard_dict(field_requirements={
        "id": {"type": "string", "nullable": False},
        "value": {"type": "integer", "nullable": True},
    })
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)
    explain = (result.metadata or {}).get("explain", {})
    cons = explain.get("consistency", {})
    assert isinstance(cons, dict)
    assert cons.get("pk_fields") == ["id"]
    counts = cons.get("counts", {})
    assert counts.get("total") == 3
    # With one duplicate group of size 2, failed should be 2 and passed 1
    assert counts.get("failed") == 2
    assert counts.get("passed") == 1
    # Score equals pass_rate*20
    pr = float(cons.get("pass_rate", 0.0))
    assert abs(float(cons.get("score_0_20", 0.0)) - pr * 20.0) < 1e-9
    # weight applied present
    assert cons.get("rule_weights_applied", {}).get("primary_key_uniqueness", 0.0) >= 1.0


def test_engine_freshness_explain_payload_with_window():
    # as_of fixed, window_days=365; one within window, one outside
    as_of_dt = datetime(2025, 1, 31)
    df = pd.DataFrame({
        "id": ["r1", "r2", "r3"],
        "event_date": [
            (as_of_dt - timedelta(days=30)).date().isoformat(),  # pass
            (as_of_dt - timedelta(days=400)).date().isoformat(), # fail
            None,  # non-parsable is excluded from total (parsed.non-null)
        ],
    })
    std = _make_standard_dict(
        field_requirements={
            "id": {"type": "string", "nullable": False},
            "event_date": {"type": "date", "nullable": True},
        },
        extra={
            "metadata": {
                "freshness": {
                    "as_of": as_of_dt.isoformat() + "Z",
                    "window_days": 365,
                    "date_field": "event_date",
                }
            }
        }
    )
    engine = ValidationEngine()
    result = engine.assess_with_standard_dict(df, std)
    explain = (result.metadata or {}).get("explain", {})
    fresh = explain.get("freshness", {})
    assert isinstance(fresh, dict)
    assert fresh.get("date_field") == "event_date"
    counts = fresh.get("counts", {})
    # Only two parsable dates; 1 passes
    assert counts.get("total") == 2
    assert counts.get("passed") == 1
    pr = float(fresh.get("pass_rate", 0.0))
    assert abs(float(fresh.get("score_0_20", 0.0)) - pr * 20.0) < 1e-9
    assert fresh.get("rule_weights_applied", {}).get("recency_window", 0.0) >= 1.0


def test_cli_scoring_explain_json_includes_new_sections(tmp_path: Path):
    # Simulate a minimal ADRI project root
    proj = tmp_path
    # Save original directory and restore at end for test isolation
    original_cwd = os.getcwd()
    try:
        os.chdir(proj)
        (proj / "ADRI").mkdir(exist_ok=True)
        # Presence only matters for resolver
        (proj / "ADRI" / "config.yaml").write_text("adri:\n  default_environment: development\n")

        # Write data CSV under ADRI/dev/
        data_dir = proj / "ADRI" / "dev"
        data_dir.mkdir(parents=True, exist_ok=True)
        data_csv = data_dir / "sample.csv"
        data_csv.write_text("id,event_date,value\nA,2025-01-01,10\nA,2023-01-01,20\nB,2024-12-31,30\n")

        # Write a standard YAML under ADRI/dev/standards
        std_dir = proj / "ADRI" / "dev" / "standards"
        std_dir.mkdir(parents=True, exist_ok=True)
        std_yaml = std_dir / "sample_ADRI_standard.yaml"

        std_dict = _make_standard_dict(
            field_requirements={
                "id": {"type": "string", "nullable": False},
                "event_date": {"type": "date", "nullable": True},
                "value": {"type": "integer", "nullable": True},
            },
            extra={
                "metadata": {
                    "freshness": {
                        "as_of": "2025-02-01T00:00:00Z",
                        "window_days": 365,
                        "date_field": "event_date",
                    }
                }
            }
        )
        with open(std_yaml, "w") as f:
            yaml.dump(std_dict, f, sort_keys=False)

        # Capture click.echo JSON output
        captured = {}
        def _capture_echo(msg, *args, **kwargs):
            # scoring_explain_command prints only once in JSON mode
            captured["payload"] = str(msg)

        with patch("adri.cli.click.echo", side_effect=_capture_echo):
            rc = scoring_explain_command("dev/sample.csv", "dev/standards/sample_ADRI_standard.yaml", json_output=True)

        assert rc == 0
        assert "payload" in captured
        payload = json.loads(captured["payload"])
        # Must include validity always; new sections when present
        assert "validity" in payload
        assert "completeness" in payload  # computed for required fields
        assert "consistency" in payload   # pk uniqueness configured
        # Freshness explain present since metadata + weight active
        assert "freshness" in payload
        # Plausibility should be present with active rules
        assert "plausibility" in payload
        # Basic shape checks
        assert "rule_counts" in payload["validity"]
        assert "required_total" in payload["completeness"]
        assert "pk_fields" in payload["consistency"]
        assert "date_field" in payload["freshness"]
        assert "rule_counts" in payload["plausibility"]
        assert "rule_weights_applied" in payload["plausibility"]
    finally:
        # Restore original working directory for test isolation
        os.chdir(original_cwd)
