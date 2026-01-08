"""
ADRI CLI - Streamlined Command Interface.

Refactored CLI using modular command pattern architecture.
Entry point delegates to individual command classes for maintainability.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import click
import yaml

from ..version import __version__

# Import command classes for clean modular access
from .commands.assess import AssessCommand
from .commands.config import (
    ConfigGetCommand,
    ConfigSetCommand,
    ExplainThresholdsCommand,
    ListContractsCommand,
    ShowConfigCommand,
    WhatIfCommand,
)
from .commands.generate_contract import GenerateContractCommand
from .commands.list_assessments import ListAssessmentsCommand
from .commands.setup import SetupCommand
from .commands.view_logs import ViewLogsCommand
from .registry import get_command

# Import needed components
try:
    from ..config.loader import ConfigurationLoader
except ImportError:
    ConfigurationLoader = None

try:
    from ..validator.assessor import DataQualityAssessor
except ImportError:
    DataQualityAssessor = None

try:
    from ..validator.loaders import load_contract
except ImportError:
    try:
        from ..contracts.loader import load_standard
    except ImportError:
        load_standard = None

try:
    from ..utils.data_loader import load_data
except ImportError:
    try:
        from ..utils import load_data
    except ImportError:
        load_data = None

# Ensure UTF-8 console output on Windows (avoid 'charmap' codec errors)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# --------------- Debug IO helpers -----------------
def _debug_io_enabled() -> bool:
    try:
        v = os.environ.get("ADRI_DEBUG_LOG", "0")
        return str(v).lower() in ("1", "true", "yes", "on")
    except Exception:
        return False


# ---------------- Path discovery and helpers -----------------


def _find_adri_project_root(start_path: Path | None = None) -> Path | None:
    """
    Find the ADRI project root directory by searching for ADRI/config.yaml.

    Searches upward from the current directory until it finds a directory
    containing ADRI/config.yaml or reaches the filesystem root.
    """
    try:
        current_path = start_path or Path.cwd()
    except (OSError, FileNotFoundError):
        # If we can't get current working directory, try some common locations
        current_path = Path(__file__).parent.parent.parent.parent
        if not current_path.exists():
            return None

    while current_path != current_path.parent:
        try:
            if (current_path / "ADRI" / "config.yaml").exists():
                return current_path
        except (OSError, PermissionError):
            pass
        current_path = current_path.parent

    try:
        if (current_path / "ADRI" / "config.yaml").exists():
            return current_path
    except (OSError, PermissionError):
        pass
    return None


def _resolve_project_path(relative_path: str) -> Path:
    """
    Resolve a path relative to the ADRI project root.

    If an ADRI project is found, resolves the path relative to the project root.
    Tutorial paths and dev/prod paths are automatically prefixed with ADRI/.
    """
    project_root = _find_adri_project_root()
    if project_root:
        if relative_path.startswith("ADRI/"):
            return project_root / relative_path
        if relative_path.startswith("tutorials/"):
            return project_root / "ADRI" / relative_path
        if relative_path.startswith("dev/") or relative_path.startswith("prod/"):
            return project_root / "ADRI" / relative_path
        return project_root / "ADRI" / relative_path
    return Path.cwd() / relative_path


def _shorten_home(path: Path) -> str:
    """Return a home-shortened absolute path, e.g. ~/project/file.txt."""
    try:
        abs_path = Path(os.path.abspath(str(path)))
        home_abs = Path(os.path.abspath(str(Path.home())))
        p_str = str(abs_path)
        h_str = str(home_abs)
        if p_str.startswith(h_str):
            return "~" + p_str[len(h_str) :]
        return p_str
    except Exception:
        try:
            return str(path)
        except Exception:
            return ""


def _rel_to_project_root(path: Path) -> str:
    """Return path relative to ADRI project root if under it, else home-shortened absolute path.

    Additionally, strip leading 'ADRI/' for display brevity when under the root.
    """
    try:
        root = _find_adri_project_root()
        abs_path = Path(os.path.abspath(str(path)))
        if root:
            root_abs = Path(os.path.abspath(str(root)))
            try:
                rel = abs_path.relative_to(root_abs)
                rel_str = str(rel)
                if rel_str.startswith("ADRI/"):
                    rel_str = rel_str[len("ADRI/") :]
                return rel_str
            except ValueError:
                return _shorten_home(abs_path)
        return _shorten_home(abs_path)
    except Exception:
        return _shorten_home(Path(path))


def _get_project_root_display() -> str:
    root = _find_adri_project_root()
    return (
        f"📂 Project Root: {_shorten_home(Path(root))}"
        if root
        else "📂 Project Root: (not detected)"
    )


def _get_threshold_from_standard(standard_path: Path) -> float:
    """Read requirements.overall_minimum from a standard YAML, defaulting to 75.0. Clamp to [0, 100]."""
    try:
        std = load_standard(str(standard_path)) if load_standard else None
        if std is None:
            with open(standard_path, encoding="utf-8") as f:
                std = yaml.safe_load(f) or {}
        req = std.get("requirements", {}) if isinstance(std, dict) else {}
        thr = float(req.get("overall_minimum", 75.0))
        if thr < 0.0:
            thr = 0.0
        if thr > 100.0:
            thr = 100.0
        return thr
    except Exception:
        return 75.0


# --------------- Tutorial helpers ------------------


def create_sample_files() -> None:
    """Create sample CSV files for guided experience."""
    good_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-001,CUST-101,1250.00,2024-01-15,paid,credit_card
INV-002,CUST-102,875.50,2024-01-16,paid,bank_transfer
INV-003,CUST-103,2100.75,2024-01-17,paid,credit_card
INV-004,CUST-104,450.00,2024-01-18,pending,cash
INV-005,CUST-105,1800.25,2024-01-19,paid,bank_transfer
INV-006,CUST-106,675.00,2024-01-20,paid,credit_card
INV-007,CUST-107,1425.50,2024-01-21,paid,bank_transfer
INV-008,CUST-108,950.00,2024-01-22,pending,credit_card
INV-009,CUST-109,1125.75,2024-01-23,paid,cash
INV-010,CUST-110,775.25,2024-01-24,paid,bank_transfer"""
    test_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-101,CUST-201,1350.00,2024-02-15,paid,credit_card
INV-102,,925.50,2024-02-16,paid,bank_transfer
INV-103,CUST-203,-150.75,2024-02-17,invalid,credit_card
INV-104,CUST-204,0,invalid_date,pending,cash
,CUST-205,1950.25,,paid,unknown_method
INV-106,CUST-206,850.00,2024-02-20,PAID,credit_card
INV-107,CUST-207,1625.50,2024-13-21,paid,bank_transfer
INV-108,CUST-208,,2024-02-22,pending,
INV-109,CUST-209,1225.75,2024-02-23,cancelled,cash
INV-110,DUPLICATE-ID,875.25,2024-02-24,paid,credit_card"""

    tutorial_dir = Path("ADRI/tutorials/invoice_processing")
    tutorial_dir.mkdir(parents=True, exist_ok=True)
    (tutorial_dir / "invoice_data.csv").write_text(good_data)
    (tutorial_dir / "test_invoice_data.csv").write_text(test_data)


def show_config_command(
    paths_only: bool = False, environment: str | None = None
) -> int:
    """Show current ADRI configuration (standalone function for tests)."""
    try:
        cmd = ShowConfigCommand()
        args = {"paths_only": paths_only, "environment": environment}
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}")
        return 1


def show_standard_command(standard_path: str, verbose: bool = False) -> int:
    """Show details of a specific ADRI standard (standalone function for tests)."""
    try:
        standard_file = Path(standard_path)
        if not standard_file.exists():
            click.echo(f"❌ Standard file not found: {standard_path}")
            return 1

        if load_standard:
            standard = load_standard(standard_path)
        else:
            with open(standard_file, encoding="utf-8") as f:
                standard = yaml.safe_load(f)

        if standard:
            click.echo(f"✅ Standard loaded: {standard_path}")
            return 0
        else:
            click.echo(f"❌ Failed to load standard: {standard_path}")
            return 1
    except Exception as e:
        click.echo(f"❌ Error loading standard: {e}")
        return 1


def setup_command(
    force: bool = False, project_name: str | None = None, guide: bool = False
) -> int:
    """Initialize ADRI in a project (standalone function for tests)."""
    try:
        cmd = SetupCommand()
        args = {
            "force": force,
            "project_name": project_name or "adri_project",
            "guide": guide,
        }
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")
        return 1


def assess_command(
    data_path: str,
    standard_path: str,
    output_path: str | None = None,
    guide: bool = False,
) -> int:
    """Run data quality assessment (standalone function for tests)."""
    try:
        cmd = AssessCommand()
        args = {
            "data_path": data_path,
            "standard_path": standard_path,
            "output_path": output_path,
            "guide": guide,
        }
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Assessment failed: {e}")
        return 1


def generate_standard_command(
    data_path: str, force: bool = False, output: str | None = None, guide: bool = False
) -> int:
    """Generate ADRI standard from data (standalone function for tests)."""
    try:
        cmd = GenerateContractCommand()
        args = {
            "data_path": data_path,
            "force": force,
            "output": output,
            "guide": guide,
        }
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Standard generation failed: {e}")
        return 1


def validate_standard_command(standard_path: str) -> int:
    """Validate YAML standard file (standalone function for tests)."""
    try:
        from .commands.config import ValidateContractCommand

        cmd = ValidateContractCommand()
        args = {"standard_path": standard_path}
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        return 1


def list_standards_command(include_catalog: bool = False) -> int:
    """List available YAML standards (standalone function for tests)."""
    try:
        cmd = ListContractsCommand()
        args = {"include_catalog": include_catalog}
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Failed to list standards: {e}")
        return 1


def list_assessments_command(recent: int = 10, verbose: bool = False) -> int:
    """List previous assessment reports (standalone function for tests)."""
    try:
        cmd = ListAssessmentsCommand()
        args = {"recent": recent, "verbose": verbose}
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Failed to list assessments: {e}")
        return 1


def view_logs_command(
    recent: int = 10, today: bool = False, verbose: bool = False
) -> int:
    """View audit logs (standalone function for tests)."""
    try:
        cmd = ViewLogsCommand()
        args = {"recent": recent, "today": today, "verbose": verbose}
        return cmd.execute(args)
    except Exception as e:
        click.echo(f"❌ Failed to view logs: {e}")
        return 1


# ---------------- Configuration helpers -----------------


def _get_default_audit_config() -> dict[str, Any]:
    return {
        "enabled": True,
        "log_dir": "ADRI/dev/audit-logs",
        "log_prefix": "adri",
        "log_level": "INFO",
        "include_data_samples": True,
        "max_log_size_mb": 100,
    }


def _load_assessor_config() -> dict[str, Any]:
    assessor_config: dict[str, Any] = {}
    if ConfigurationLoader:
        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()
        if config:
            try:
                env_config = config_loader.get_environment_config(config)
                assessor_config["audit"] = env_config.get(
                    "audit", _get_default_audit_config()
                )
            except (KeyError, AttributeError):
                assessor_config["audit"] = _get_default_audit_config()
        else:
            assessor_config["audit"] = _get_default_audit_config()
    return assessor_config


# ---------------- Assessment helpers -----------------


def _generate_record_id(row, row_index, primary_key_fields: list[str]) -> str:
    import pandas as pd

    if primary_key_fields:
        key_values = []
        for field in primary_key_fields:
            if field in row and pd.notna(row[field]):
                key_values.append(str(row[field]))
        if key_values:
            return f"{':'.join(key_values)} (Row {row_index + 1})"
    return f"Row {row_index + 1}"


def _check_business_rules(row, record_id, validation_id, failed_checks, data):
    import pandas as pd

    if "amount" in row and pd.notna(row["amount"]):
        try:
            amount_val = float(row["amount"])
            if amount_val < 0:
                failed_checks.append(
                    {
                        "validation_id": f"val_{validation_id:03d}",
                        "dimension": "validity",
                        "field": "amount",
                        "issue": "negative_value",
                        "affected_rows": 1,
                        "affected_percentage": (1.0 / len(data)) * 100,
                        "samples": [record_id],
                        "remediation": "Remove or correct negative amounts",
                    }
                )
                validation_id += 1
        except (ValueError, TypeError):
            failed_checks.append(
                {
                    "validation_id": f"val_{validation_id:03d}",
                    "dimension": "validity",
                    "field": "amount",
                    "issue": "invalid_format",
                    "affected_rows": 1,
                    "affected_percentage": (1.0 / len(data)) * 100,
                    "samples": [record_id],
                    "remediation": "Fix amount format to valid number",
                }
            )
            validation_id += 1
    if (
        "date" in row
        and pd.notna(row["date"])
        and "invalid" in str(row["date"]).lower()
    ):
        failed_checks.append(
            {
                "validation_id": f"val_{validation_id:03d}",
                "dimension": "validity",
                "field": "date",
                "issue": "invalid_format",
                "affected_rows": 1,
                "affected_percentage": (1.0 / len(data)) * 100,
                "samples": [record_id],
                "remediation": "Fix date format to valid date",
            }
        )
        validation_id += 1
    return validation_id


def _analyze_data_issues(data, primary_key_fields):
    import pandas as pd

    failed_checks = []
    validation_id = 1

    try:
        from ..validator.rules import check_primary_key_uniqueness

        standard_config = {
            "record_identification": {"primary_key_fields": primary_key_fields}
        }
        pk_failures = check_primary_key_uniqueness(data, standard_config)
        failed_checks.extend(pk_failures)
        validation_id += len(pk_failures)
    except Exception:
        pass

    for i, row in data.iterrows():
        record_id = _generate_record_id(row, i, primary_key_fields)
        if row.isnull().any():
            missing_fields = [col for col in row.index if pd.isna(row[col])]
            for field in missing_fields[:2]:
                failed_checks.append(
                    {
                        "validation_id": f"val_{validation_id:03d}",
                        "dimension": "completeness",
                        "field": field,
                        "issue": "missing_value",
                        "affected_rows": 1,
                        "affected_percentage": (1.0 / len(data)) * 100,
                        "samples": [record_id],
                        "remediation": f"Fill missing {field} values",
                    }
                )
                validation_id += 1
        validation_id = _check_business_rules(
            row, record_id, validation_id, failed_checks, data
        )
    return failed_checks


def _save_assessment_report(guide, data_path, result):
    if not guide:
        return
    assessments_dir = Path("ADRI/dev/assessments")
    if ConfigurationLoader:
        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()
        if config:
            try:
                env_config = config_loader.get_environment_config(config)
                assessments_dir = Path(env_config["paths"]["assessments"])
            except (KeyError, AttributeError):
                pass
    assessments_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_name = Path(data_path).stem
    auto_output_path = assessments_dir / f"{data_name}_assessment_{timestamp}.json"
    report_data = result.to_standard_dict()
    with open(auto_output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)


def _analyze_failed_records(data):
    import pandas as pd

    failed_records_list = []
    for i, row in data.iterrows():
        issues = []

        def _is_missing(v):
            try:
                if pd.isna(v):
                    return True
            except Exception:
                pass
            return isinstance(v, str) and v.strip() == ""

        missing_fields = [col for col in row.index if _is_missing(row[col])]
        if missing_fields:
            top_missing = missing_fields[:2]
            issues.append(("missing", top_missing))

        if "amount" in row and pd.notna(row["amount"]):
            try:
                amount_val = float(row["amount"])
                if amount_val < 0:
                    issues.append(("negative_amount", None))
            except (ValueError, TypeError):
                issues.append(("invalid_amount_format", None))

        if (
            "date" in row
            and pd.notna(row["date"])
            and "invalid" in str(row["date"]).lower()
        ):
            issues.append(("invalid_date_format", None))

        if issues:
            record_id = row.get("invoice_id", f"Row {i + 1}")
            try:
                if pd.isna(record_id):
                    record_id = f"Row {i + 1}"
            except Exception:
                pass

            parts = []
            for code, payload in issues:
                if code == "missing":
                    fields_str = ", ".join(payload)
                    parts.append(
                        f"missing {fields_str} (fill missing {fields_str} values)"
                    )
                elif code == "negative_amount":
                    parts.append("negative amount (should be ≥ 0)")
                elif code == "invalid_date_format":
                    parts.append("invalid date format (use YYYY-MM-DD)")
                elif code == "invalid_amount_format":
                    parts.append(
                        "invalid amount format (fix amount format to a valid number)"
                    )
                else:
                    parts.append(str(code))
            failed_records_list.append(f"   • {record_id}: {', '.join(parts)}")
    return failed_records_list


def _display_assessment_results(result, data, guide, threshold: float = 75.0):
    status_icon = "✅" if result.passed else "❌"
    status_text = "PASSED" if result.passed else "FAILED"
    total_records = len(data)

    if guide:
        failed_records_list = _analyze_failed_records(data)
        actual_failed_records = len(failed_records_list)
        actual_passed_records = total_records - actual_failed_records

        click.echo("📊 Quality Assessment Results:")
        click.echo("==============================")
        click.echo(
            f"🎯 Agent System Health: {result.overall_score:.1f}/100 {status_icon} {status_text}"
        )
        click.echo(f"Threshold = {threshold:.1f}/100 (set in your standard)")
        click.echo("   → Overall reliability for AI agent workflows")
        click.echo(
            "   → Use for: monitoring agent performance, framework integration health"
        )
        click.echo("")
        click.echo(
            f"⚙️  Execution Readiness: {actual_passed_records}/{total_records} records safe for agents"
        )
        click.echo("   → Immediate agent execution safety assessment")
        click.echo(
            "   → Use for: pre-flight checks, error handling capacity, data preprocessing needs"
        )
        if actual_failed_records > 0:
            click.echo("")
            click.echo("🔍 Records Requiring Attention:")
            for failure in failed_records_list[:3]:
                click.echo(failure)
            if actual_failed_records > 3:
                remaining = actual_failed_records - 3
                click.echo(f"   • ... and {remaining} more records with issues")
        click.echo("")
        click.echo("▶ Next: adri view-logs")
    else:
        passed_records = int((result.overall_score / 100.0) * total_records)
        failed_records = total_records - passed_records
        explanation = (
            f"{passed_records}/{total_records} records passed"
            if result.passed
            else f"{failed_records}/{total_records} records failed"
        )
        click.echo(
            f"Score: {result.overall_score:.1f}/100 {status_icon} {status_text} → {explanation}"
        )


# ---------------- Hash/snapshot helpers -----------------


def _generate_file_hash(file_path: Path) -> str:
    import hashlib

    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()[:8]


def _create_training_snapshot(data_path: str) -> str | None:
    try:
        source_file = Path(data_path)
        if not source_file.exists():
            return None
        file_hash = _generate_file_hash(source_file)
        training_data_dir = Path("ADRI/dev/training-data")
        if ConfigurationLoader:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    training_data_dir = Path(env_config["paths"]["training_data"])
                except (KeyError, AttributeError):
                    pass
        training_data_dir.mkdir(parents=True, exist_ok=True)
        snapshot_filename = f"{source_file.stem}_{file_hash}.csv"
        snapshot_path = training_data_dir / snapshot_filename
        import shutil

        shutil.copy2(source_file, snapshot_path)
        return str(snapshot_path)
    except Exception:
        return None


def _create_lineage_metadata(
    data_path: str, snapshot_path: str | None = None
) -> dict[str, Any]:
    from datetime import datetime

    source_file = Path(data_path)
    metadata: dict[str, Any] = {
        "source_path": str(source_file.resolve()),
        "timestamp": datetime.now().isoformat(),
        "file_hash": _generate_file_hash(source_file) if source_file.exists() else None,
    }
    if snapshot_path and Path(snapshot_path).exists():
        snapshot_file = Path(snapshot_path)
        metadata.update(
            {
                "snapshot_path": str(snapshot_file.resolve()),
                "snapshot_hash": _generate_file_hash(snapshot_file),
                "snapshot_filename": snapshot_file.name,
            }
        )
    if source_file.exists():
        stat_info = source_file.stat()
        metadata.update(
            {
                "source_size_bytes": stat_info.st_size,
                "source_modified": datetime.fromtimestamp(
                    stat_info.st_mtime
                ).isoformat(),
            }
        )
    return metadata


# ---------------- Core commands -----------------


def _get_assessments_directory() -> Path:
    assessments_dir = Path("ADRI/dev/assessments")
    if ConfigurationLoader:
        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()
        if config:
            try:
                env_config = config_loader.get_environment_config(config)
                assessments_dir = Path(env_config["paths"]["assessments"])
            except (KeyError, AttributeError):
                pass
    return assessments_dir


def _parse_assessment_files(assessment_files: list[Path]) -> list[dict[str, Any]]:
    table_data: list[dict[str, Any]] = []
    for file_path in assessment_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                assessment_data = json.load(f)
            adri_report = assessment_data.get("adri_assessment_report", {})
            summary = adri_report.get("summary", {})
            score = summary.get("overall_score", 0)
            passed = summary.get("overall_passed", False)

            file_stats = file_path.stat()
            modified_time = file_stats.st_mtime
            from datetime import datetime

            date_str = datetime.fromtimestamp(modified_time).strftime("%m-%d %H:%M")
            dataset_name = file_path.stem.replace("_assessment_", "_").split("_")[0]

            table_data.append(
                {
                    "dataset": dataset_name,
                    "score": f"{score:.1f}/100",
                    "status": "✅ PASSED" if passed else "❌ FAILED",
                    "date": date_str,
                    "file": file_path.name,
                }
            )
        except Exception as e:
            if _debug_io_enabled():
                click.echo(f"⚠️ Skipping invalid assessment entry {file_path}: {e}")
    return table_data


def _load_audit_entries() -> list[dict[str, Any]]:
    """Load audit entries from JSONL files using ADRILogReader."""
    from datetime import datetime

    from .logging import ADRILogReader

    audit_entries: list[dict[str, Any]] = []

    try:
        if ConfigurationLoader:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                # Create log reader with config
                log_reader = ADRILogReader({"paths": env_config.get("paths", {})})
            else:
                # Fallback to default config
                log_reader = ADRILogReader(
                    {"paths": {"audit_logs": "ADRI/dev/audit-logs"}}
                )
        else:
            # No config loader, use default
            log_reader = ADRILogReader({"paths": {"audit_logs": "ADRI/dev/audit-logs"}})

        # Read assessment logs
        assessment_logs = log_reader.read_assessment_logs()

        # Convert to audit entries format
        for log_record in assessment_logs:
            try:
                timestamp_str = log_record.get("timestamp", "")
                if "T" in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", ""))
                else:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                audit_entries.append(
                    {
                        "timestamp": timestamp,
                        "data_row_count": int(log_record.get("data_row_count", 0)),
                        "overall_score": float(log_record.get("overall_score", 0)),
                    }
                )
            except Exception as e:
                if _debug_io_enabled():
                    click.echo(f"⚠️ Skipping unreadable audit log row: {e}")

    except Exception as e:
        if _debug_io_enabled():
            click.echo(f"⚠️ Could not load audit logs: {e}")

    return audit_entries


def _enhance_with_record_counts(table_data, audit_entries):
    enhanced = []
    for entry in table_data:
        audit_entry = None
        for log_entry in audit_entries:
            if log_entry["timestamp"].strftime("%m-%d %H:%M") == entry["date"]:
                audit_entry = log_entry
                break
        if audit_entry:
            total_records = audit_entry["data_row_count"]
            score_value = float(entry["score"].split("/")[0])
            passed_records = (
                int((score_value / 100.0) * total_records) if total_records > 0 else 0
            )
            records_info = f"{passed_records}/{total_records}"
        else:
            records_info = "N/A"
        enhanced.append({**entry, "records": records_info})
    return enhanced


def _display_assessments_table(enhanced_table_data, table_data, verbose):
    click.echo(f"📊 Assessment Reports ({len(enhanced_table_data)} recent)")
    click.echo(
        "┌─────────────────┬───────────┬──────────────┬───────────┬─────────────┐"
    )
    click.echo(
        "│ Data Packet     │ Score     │ Status       │ Records   │ Date        │"
    )
    click.echo(
        "├─────────────────┼───────────┼──────────────┼───────────┼─────────────┤"
    )
    for entry in enhanced_table_data:
        data_packet = (
            entry["records"]
            if "dataset" not in entry
            else entry["dataset"][:15].ljust(15)
        )
        score = entry["score"].ljust(9)
        status = entry["status"].ljust(12)
        records = entry["records"].ljust(9)
        date = entry["date"].ljust(11)
        click.echo(f"│ {data_packet} │ {score} │ {status} │ {records} │ {date} │")
    click.echo(
        "└─────────────────┴───────────┴──────────────┴───────────┴─────────────┘"
    )
    click.echo()
    if verbose:
        click.echo("📄 Report Files:")
        for i, entry in enumerate(table_data, 1):
            click.echo(f"  {i}. {entry['file']}")
        click.echo()


def _get_audit_logs_directory() -> Path:
    audit_logs_dir = Path("ADRI/dev/audit-logs")
    if ConfigurationLoader:
        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()
        if config:
            try:
                env_config = config_loader.get_environment_config(config)
                audit_logs_dir = Path(env_config["paths"]["audit_logs"])
            except (KeyError, AttributeError):
                pass
    return audit_logs_dir


def _parse_audit_log_entries(main_log_file: Path, today: bool):
    import csv
    from datetime import date, datetime

    log_entries = []
    with open(main_log_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                timestamp_str = row.get("timestamp", "")
                if timestamp_str:
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "")
                        )
                    else:
                        timestamp = datetime.strptime(
                            timestamp_str, "%Y-%m-%d %H:%M:%S"
                        )
                else:
                    timestamp = datetime.now()
                if today and timestamp.date() != date.today():
                    continue
                log_entries.append(
                    {
                        "timestamp": timestamp,
                        "assessment_id": row.get("assessment_id", "unknown"),
                        "overall_score": float(row.get("overall_score", 0)),
                        "passed": row.get("passed", "FALSE") == "TRUE",
                        "data_row_count": int(row.get("data_row_count", 0)),
                        "function_name": row.get("function_name", ""),
                        "standard_id": row.get("standard_id", "unknown"),
                        "assessment_duration_ms": int(
                            row.get("assessment_duration_ms", 0)
                        ),
                        "execution_decision": row.get("execution_decision", "unknown"),
                    }
                )
            except Exception as e:
                if _debug_io_enabled():
                    click.echo(f"⚠️ Skipping unreadable audit log row: {e}")
    return log_entries


def _format_log_table_data(log_entries):
    table_data = []
    for entry in log_entries:
        if entry["function_name"] == "assess":
            mode = (
                "CLI Guide"
                if "guide" in entry.get("assessment_id", "")
                else "CLI Direct"
            )
            function_name = "N/A"
            module_path = "N/A"
        else:
            mode = "Decorator"
            function_name = entry["function_name"] or "Unknown"
            module_path = entry.get("module_path", "Unknown")
            if len(module_path) > 12:
                module_path = module_path[:9] + "..."
        standard_id = entry.get("standard_id", "unknown")
        data_packet = (
            standard_id.replace("_ADRI_standard", "")
            if standard_id and "_ADRI_standard" in standard_id
            else "unknown"
        )
        if len(data_packet) > 12:
            data_packet = data_packet[:9] + "..."
        if len(function_name) > 14 and function_name != "N/A":
            function_name = function_name[:11] + "..."
        date_str = entry["timestamp"].strftime("%m-%d %H:%M")
        score = f"{entry['overall_score']:.1f}/100"
        status = "✅ PASSED" if entry["passed"] else "❌ FAILED"
        table_data.append(
            {
                "data_packet": data_packet,
                "score": score,
                "status": status,
                "mode": mode,
                "function": function_name,
                "module": module_path,
                "date": date_str,
            }
        )
    return table_data


def _display_audit_logs_table(table_data, log_entries, audit_logs_dir, verbose):
    click.echo(f"📊 ADRI Audit Log Summary ({len(table_data)} recent)")
    click.echo(
        "┌─────────────┬───────────┬──────────────┬─────────────┬─────────────────┬─────────────┬─────────────┐"
    )
    click.echo(
        "│ Data Packet │ Score     │ Status       │ Mode        │ Function        │ Module      │ Date        │"
    )
    click.echo(
        "├─────────────┼───────────┼──────────────┼─────────────┼─────────────────┼─────────────┼─────────────┤"
    )
    for entry in table_data:
        data_packet = entry["data_packet"].ljust(11)
        score = entry["score"].ljust(9)
        status = entry["status"].ljust(12)
        mode = entry["mode"].ljust(11)
        function = entry["function"].ljust(15)
        module = entry["module"].ljust(11)
        date = entry["date"].ljust(11)
        click.echo(
            f"│ {data_packet} │ {score} │ {status} │ {mode} │ {function} │ {module} │ {date} │"
        )
    click.echo(
        "└─────────────┴───────────┴──────────────┴─────────────┴─────────────────┴─────────────┴─────────────┘"
    )
    if verbose:
        click.echo()
        click.echo("📄 Detailed Audit Information:")
        for i, entry in enumerate(log_entries, 1):
            click.echo(f"  {i}. Assessment ID: {entry['assessment_id']}")
            click.echo(
                f"     Records: {entry['data_row_count']} | Duration: {entry['assessment_duration_ms']}ms"
            )
            click.echo(f"     Decision: {entry['execution_decision']}")
            click.echo()
    else:
        click.echo()
        click.echo("💡 Use --verbose for detailed audit information")
    click.echo()
    click.echo("📁 Audit Log Files:")
    click.echo(f"   📄 {audit_logs_dir}/adri_assessment_logs.jsonl")
    click.echo(f"   📊 {audit_logs_dir}/adri_dimension_scores.jsonl")
    click.echo(f"   ❌ {audit_logs_dir}/adri_failed_validations.jsonl")
    click.echo()
    click.echo("🎉 ADRI onboarding complete!")
    click.echo("You now know how to:")
    click.echo("  • Generate a standard")
    click.echo("  • Assess data")
    click.echo("  • Review assessments")
    click.echo("  • Audit logs")
    click.echo("👉 Next: Integrate ADRI into your agent workflow (see docs)")


def _compute_dimension_contributions(dimension_scores, applied_dimension_weights):
    """Compute contribution (%) of each dimension to overall score given 0..20 scores and weights."""
    try:
        scores = {}
        for dim, val in (dimension_scores or {}).items():
            if hasattr(val, "score"):
                scores[dim] = float(val.score)
            elif isinstance(val, (int, float)):
                scores[dim] = float(val)
            else:
                try:
                    scores[dim] = float(val.get("score", 0.0))
                except Exception:
                    scores[dim] = 0.0

        weights = {k: float(v) for k, v in (applied_dimension_weights or {}).items()}
        sum_w = sum(weights.values()) if weights else 0.0
        contributions = {}
        for dim, s in scores.items():
            w = weights.get(dim, 1.0)
            contributions[dim] = (
                (s / 20.0) * (w / sum_w) * 100.0 if sum_w > 0.0 else 0.0
            )
        return contributions
    except Exception:
        return {}


# ---------------- Click CLI group -----------------


@click.group()
@click.version_option(version=__version__, prog_name="adri")
def cli():
    """ADRI - Stop Your AI Agents Breaking on Bad Data."""


# Initialize command registry on module load
# Note: Commands will be registered on first use to avoid duplicate registrations


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--project-name", help="Custom project name")
@click.option(
    "--guide", is_flag=True, help="Show step-by-step guidance and create sample files"
)
def setup(force, project_name, guide):
    """Initialize ADRI in a project."""
    command = get_command("setup")
    args = {"force": force, "project_name": project_name, "guide": guide}
    sys.exit(command.execute(args))


@cli.command()
@click.argument("data_path")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option("--output", "output_path", help="Output path for assessment report")
@click.option(
    "--guide", is_flag=True, help="Show detailed assessment explanation and next steps"
)
def assess(data_path, standard_path, output_path, guide):
    """Run data quality assessment."""
    command = get_command("assess")
    args = {
        "data_path": data_path,
        "standard_path": standard_path,
        "output_path": output_path,
        "guide": guide,
    }
    sys.exit(command.execute(args))


@cli.command("generate-contract")
@click.argument("data_path")
@click.option("--force", is_flag=True, help="Overwrite existing contract file")
@click.option(
    "-o",
    "--output",
    help="Output path for generated contract file (ignored; uses config paths)",
)
@click.option(
    "--guide", is_flag=True, help="Show detailed generation explanation and next steps"
)
def generate_contract(data_path, force, output, guide):
    """Generate ADRI contract from data file analysis."""
    command = get_command("generate-contract")
    args = {"data_path": data_path, "force": force, "output": output, "guide": guide}
    sys.exit(command.execute(args))


@cli.command("guide")
def guide():
    """Interactive guide for first-time users (replaces --guide flags)."""
    command = get_command("guide")
    args = {}
    sys.exit(command.execute(args))


@cli.command("validate-contract")
@click.argument("standard_path")
def validate_contract(standard_path):
    """Validate YAML contract file."""
    command = get_command("validate-contract")
    args = {"standard_path": standard_path}
    sys.exit(command.execute(args))


@cli.command("list-contracts")
@click.option(
    "--catalog",
    "include_catalog",
    is_flag=True,
    help="Also show remote catalog entries",
)
def list_contracts(include_catalog):
    """List available YAML contracts."""
    command = get_command("list-contracts")
    args = {"include_catalog": include_catalog}
    sys.exit(command.execute(args))


@cli.command("show-config")
@click.option("--paths-only", is_flag=True, help="Show only path information")
@click.option("--environment", help="Show specific environment only")
def show_config(paths_only, environment):
    """Show current ADRI configuration."""
    command = get_command("show-config")
    args = {"paths_only": paths_only, "environment": environment}
    sys.exit(command.execute(args))


@cli.command("list-assessments")
@click.option("--recent", default=10, help="Number of recent assessments to show")
@click.option("--verbose", is_flag=True, help="Show detailed assessment information")
def list_assessments(recent, verbose):
    """List previous assessment reports."""
    command = get_command("list-assessments")
    args = {"recent": recent, "verbose": verbose}
    sys.exit(command.execute(args))


@cli.command("show-standard")
@click.argument("standard_name")
@click.option("--verbose", is_flag=True, help="Show detailed requirements and rules")
def show_standard(standard_name, verbose):
    """Show details of a specific ADRI standard."""
    command = get_command("show-standard")
    args = {"standard_name": standard_name, "verbose": verbose}
    sys.exit(command.execute(args))


@cli.command("view-logs")
@click.option("--recent", default=10, help="Number of recent audit log entries to show")
@click.option("--today", is_flag=True, help="Show only today's audit logs")
@click.option("--verbose", is_flag=True, help="Show detailed audit log information")
def view_logs(recent, today, verbose):
    """View audit logs from CSV files."""
    command = get_command("view-logs")
    args = {"recent": recent, "today": today, "verbose": verbose}
    sys.exit(command.execute(args))


@cli.command("scoring-explain")
@click.argument("data_path")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable breakdown JSON"
)
def scoring_explain(data_path, standard_path, json_output):
    """Explain scoring breakdown for a dataset against a standard."""
    command = get_command("scoring-explain")
    args = {
        "data_path": data_path,
        "standard_path": standard_path,
        "json_output": json_output,
    }
    sys.exit(command.execute(args))


@cli.command("scoring-preset-apply")
@click.argument("preset", type=click.Choice(["balanced", "strict", "lenient"]))
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option(
    "-o",
    "--output",
    "output_path",
    help="Write modified standard to this path (defaults to in-place)",
)
def scoring_preset_apply(preset, standard_path, output_path):
    """Apply a scoring preset to a standard's dimension requirements."""
    command = get_command("scoring-preset-apply")
    args = {
        "preset": preset,
        "standard_path": standard_path,
        "output_path": output_path,
    }
    sys.exit(command.execute(args))


# ---------------- Remote standards catalog (group) -----------------


@click.group("standards-catalog")
def standards_catalog():
    """Remote standards catalog commands."""


@standards_catalog.command("list")
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON"
)
def standards_catalog_list(json_output):
    """List available standards from the remote catalog."""
    # Keep catalog commands as legacy for now
    sys.exit(standards_catalog_list_command(json_output))


@standards_catalog.command("fetch")
@click.argument("name_or_id")
@click.option(
    "--dest",
    type=click.Choice(["dev", "prod"]),
    default="dev",
    show_default=True,
    help="Destination environment directory",
)
@click.option("--filename", help="Override destination filename")
@click.option("--overwrite", is_flag=True, help="Overwrite existing file")
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON"
)
def standards_catalog_fetch(name_or_id, dest, filename, overwrite, json_output):
    """Fetch a standard from the remote catalog and save it locally."""
    # Keep catalog commands as legacy for now
    sys.exit(
        standards_catalog_fetch_command(
            name_or_id, dest, filename, overwrite, json_output
        )
    )


# Attach the group to the main CLI
cli.add_command(standards_catalog)


# ---------------- New Configuration Management Commands -----------------


@cli.command("config")
@click.argument("action", type=click.Choice(["set", "get"]))
@click.argument("setting")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
def config(action, setting, standard_path):
    """Get or set configuration values in YAML standard files.

    Examples:
      adri config set min_score=80 --standard dev/standards/invoice.yaml
      adri config get min_score --standard dev/standards/invoice.yaml
    """
    if action == "set":
        command = ConfigSetCommand()
        args = {"setting": setting, "standard_path": standard_path}
    else:  # get
        command = ConfigGetCommand()
        args = {"setting": setting, "standard_path": standard_path}
    sys.exit(command.execute(args))


@cli.command("explain-thresholds")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
def explain_thresholds(standard_path):
    """Explain threshold configurations and their implications."""
    command = ExplainThresholdsCommand()
    args = {"standard_path": standard_path}
    sys.exit(command.execute(args))


@cli.command("what-if")
@click.argument("changes", nargs=-1, required=True)
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option("--data", "data_path", required=True, help="Path to data file to assess")
def what_if(changes, standard_path, data_path):
    """Simulate threshold changes and show projected impact.

    Examples:
      adri what-if min_score=85 --standard dev/standards/invoice.yaml --data test.csv
      adri what-if min_score=85 readiness.row_threshold=0.9 --standard dev/standards/invoice.yaml --data test.csv
    """
    command = WhatIfCommand()
    args = {
        "changes": list(changes),
        "standard_path": standard_path,
        "data_path": data_path,
    }
    sys.exit(command.execute(args))


# Standalone functions for testing (extracted from Click commands above)
def standards_catalog_list_command(json_output: bool = False) -> int:
    """List available standards from the remote catalog (standalone function for tests)."""
    try:
        base_url = None
        try:
            # Local import to avoid hard dependency if package not available
            from ..catalog import CatalogClient as _CC  # type: ignore
            from ..catalog import CatalogConfig as _CFG

            base_url = _CC.resolve_base_url()
            CatalogClientLocal = _CC
            CatalogConfigLocal = _CFG
        except Exception:
            base_url = None
            CatalogClientLocal = None  # type: ignore
            CatalogConfigLocal = None  # type: ignore

        if not base_url or not CatalogClientLocal or not CatalogConfigLocal:
            if json_output:
                import json

                click.echo(json.dumps({"error": "no_catalog_configured"}))
            else:
                click.echo("🌐 Remote Catalog: (not configured)")
            return 0

        try:
            client = CatalogClientLocal(CatalogConfigLocal(base_url=base_url))
            resp = client.list()

            if json_output:
                import json

                entries_data = [
                    {
                        "id": e.id,
                        "name": e.name,
                        "version": e.version,
                        "description": e.description,
                        "tags": e.tags,
                    }
                    for e in resp.entries
                ]
                click.echo(json.dumps({"entries": entries_data}))
            else:
                click.echo(f"🌐 Remote Catalog ({len(resp.entries)}):")
                for i, e in enumerate(resp.entries, 1):
                    click.echo(f"  {i}. {e.id} — {e.name} v{e.version}")
            return 0
        except Exception as e:
            if json_output:
                import json

                click.echo(
                    json.dumps({"error": "catalog_fetch_failed", "details": str(e)})
                )
            else:
                click.echo(f"⚠️ Could not load remote catalog: {e}")
            return 1
    except Exception as e:
        if json_output:
            import json

            click.echo(json.dumps({"error": "unexpected_error", "details": str(e)}))
        else:
            click.echo(f"❌ Failed to list catalog: {e}")
        return 1


def standards_catalog_fetch_command(
    name_or_id: str,
    dest: str = "dev",
    filename: str | None = None,
    overwrite: bool = False,
    json_output: bool = False,
) -> int:
    """Fetch a standard from the remote catalog and save it locally (standalone function for tests)."""
    try:
        # Import catalog components
        try:
            from ..catalog import CatalogClient, CatalogConfig
        except ImportError:
            if json_output:
                import json

                click.echo(json.dumps({"error": "catalog_not_available"}))
            else:
                click.echo("❌ Catalog functionality not available")
            return 1

        try:
            base_url = CatalogClient.resolve_base_url()
            client = CatalogClient(CatalogConfig(base_url=base_url))
        except Exception as e:
            if json_output:
                import json

                click.echo(
                    json.dumps({"error": "catalog_config_failed", "details": str(e)})
                )
            else:
                click.echo(f"❌ Failed to configure catalog client: {e}")
            return 1

        # Fetch the standard
        try:
            result = client.fetch(name_or_id)
        except Exception as e:
            if json_output:
                import json

                click.echo(json.dumps({"error": "fetch_failed", "details": str(e)}))
            else:
                click.echo(f"❌ Failed to fetch standard '{name_or_id}': {e}")
            return 1

        # Determine destination directory
        if dest == "dev":
            dest_dir = Path("ADRI/dev/contracts")
        elif dest == "prod":
            dest_dir = Path("ADRI/prod/contracts")
        else:
            if json_output:
                import json

                click.echo(
                    json.dumps(
                        {
                            "error": "invalid_destination",
                            "valid_destinations": ["dev", "prod"],
                        }
                    )
                )
            else:
                click.echo(f"❌ Invalid destination '{dest}'. Use 'dev' or 'prod'")
            return 1

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename:
            output_filename = (
                filename if filename.endswith(".yaml") else f"{filename}.yaml"
            )
        else:
            output_filename = f"{result.entry.id}.yaml"

        output_path = dest_dir / output_filename

        # Check if file exists and handle overwrite
        if output_path.exists() and not overwrite:
            if json_output:
                import json

                click.echo(
                    json.dumps({"error": "file_exists", "path": str(output_path)})
                )
            else:
                click.echo(f"❌ File exists: {output_path}. Use --overwrite to replace")
            return 1

        # Save the standard
        try:
            with open(output_path, "wb") as f:
                f.write(result.content_bytes)
        except Exception as e:
            if json_output:
                import json

                click.echo(json.dumps({"error": "write_failed", "details": str(e)}))
            else:
                click.echo(f"❌ Failed to save standard: {e}")
            return 1

        if json_output:
            import json

            click.echo(
                json.dumps(
                    {
                        "success": True,
                        "saved_path": str(output_path),
                        "entry": {
                            "id": result.entry.id,
                            "name": result.entry.name,
                            "version": result.entry.version,
                        },
                    }
                )
            )
        else:
            click.echo(f"✅ Standard '{result.entry.name}' fetched successfully")
            click.echo(f"📄 Saved to: {output_path}")

        return 0
    except Exception as e:
        if json_output:
            import json

            click.echo(json.dumps({"error": "unexpected_error", "details": str(e)}))
        else:
            click.echo(f"❌ Failed to fetch standard: {e}")
        return 1


def show_help_guide() -> int:
    """Show environment information and directory structure explanation.

    Displays comprehensive ADRI environment documentation including:
    - Environment configuration details
    - Directory structure explanations
    - Configuration file locations
    - Best practices and usage guidelines

    Returns:
        0 for success, 1 for failure
    """
    try:
        # Get project root for context
        project_root = _find_adri_project_root()

        # Display Environment Information
        click.echo("🌍 Environment Information:")
        click.echo(
            f"   Current Environment: {os.environ.get('ADRI_ENV', 'development')}"
        )
        click.echo("Default: Development environment")
        click.echo("   Switch: Edit ADRI/config.yaml (set default_environment)")
        click.echo(
            f"   Project Root: {project_root if project_root else 'Not detected'}"
        )
        click.echo("")

        # Display Directory Structure
        click.echo("📁 Directory Structure:")
        click.echo("   ADRI/")
        click.echo("   ├── tutorials/           # Tutorial and example data")
        click.echo("   ├── dev/                 # Development environment")
        click.echo("   │   ├── dev/contracts/       # Draft/testing contracts")
        click.echo("   │   ├── dev/assessments/     # Development assessment reports")
        click.echo(
            "   │   ├── dev/training-data/   # Development training data snapshots"
        )
        click.echo("   │   └── dev/audit-logs/      # Development audit logs")
        click.echo("   └── prod/                # Production environment")
        click.echo("       ├── prod/contracts/       # Validated/approved contracts")
        click.echo("       ├── prod/assessments/     # Production assessment reports")
        click.echo(
            "       ├── prod/training-data/   # Production training data snapshots"
        )
        click.echo("       └── prod/audit-logs/      # Production audit logs")
        click.echo("")

        # Display Configuration Info
        click.echo("⚙️  Configuration:")
        click.echo("   File: adri-config.yaml (in project root)")
        click.echo("   Purpose: Centralized configuration for all ADRI functionality")
        click.echo("   Sections:")
        click.echo("     - environments: Development and production settings")
        click.echo("     - protection: Data protection and decorator settings")
        click.echo("     - audit: Audit logging configuration")
        click.echo("     - contracts: Contract discovery and validation")
        click.echo("")

        # Display Environment Variables
        click.echo("🔧 Environment Variables:")
        click.echo("   ADRI_ENV: Current environment (development/production)")
        click.echo("   ADRI_CONFIG_PATH: Override config file location")
        click.echo("   ADRI_CONTRACTS_DIR: Override contracts directory")
        click.echo("")

        # Display Smart Path Resolution
        click.echo("🎯 Smart Path Resolution:")
        click.echo("   Contracts resolve automatically based on environment:")
        click.echo("   - dev/ environment → ADRI/dev/contracts/")
        click.echo("   - prod/ environment → ADRI/prod/contracts/")
        click.echo("")

        click.echo(f"📦 ADRI Version: {__version__}")

        return 0
    except Exception as e:
        click.echo(f"❌ Error showing help guide: {e}")
        return 1


def main():
    """Run the main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
