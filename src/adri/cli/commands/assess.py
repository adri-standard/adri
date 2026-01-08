# @ADRI_FEATURE[cli_assess_command, scope=OPEN_SOURCE]
# Description: CLI assess command for running data quality assessments
"""Assess command implementation for ADRI CLI.

This module contains the AssessCommand class that handles data quality assessment
operations using ADRI standards.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

import click
import pandas as pd

from ...core.protocols import Command
from ...utils.path_utils import (
    get_project_root_display,
    rel_to_project_root,
    resolve_project_path,
)
from ...validator.engine import DataQualityAssessor
from ...validator.loaders import load_data, load_contract


def _progressive_echo(text: str, delay: float = 0.0) -> None:
    """Print text with optional delay for progressive output in guide mode.

    Args:
        text: Text to print
        delay: Delay in seconds after printing (only in interactive terminals)
    """
    click.echo(text)
    if delay > 0 and sys.stdout.isatty():
        time.sleep(delay)


class AssessCommand(Command):
    """Command for running data quality assessments.

    Handles assessment operations including data loading, standard application,
    result reporting, and audit logging.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Run data quality assessment"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the assess command.

        Args:
            args: Command arguments containing:
                - data_path: str - Path to data file to assess
                - standard_path: str - Path to YAML standard file
                - output_path: Optional[str] - Output path for assessment report
                - guide: bool - Show detailed assessment explanation and next steps

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        data_path = args["data_path"]
        standard_path = args["standard_path"]
        output_path = args.get("output_path")
        guide = args.get("guide", False)

        return self._run_assessment(data_path, standard_path, output_path, guide)

    def _run_assessment(
        self,
        data_path: str,
        standard_path: str,
        output_path: str | None = None,
        guide: bool = False,
    ) -> int:
        """Run data quality assessment."""
        try:
            # Resolve paths
            resolved_data_path = resolve_project_path(data_path)
            resolved_standard_path = resolve_project_path(standard_path)

            # Validate file existence
            if not resolved_data_path.exists():
                self._display_file_not_found_error(
                    data_path, resolved_data_path, guide, "Data file"
                )
                return 1

            if not resolved_standard_path.exists():
                self._display_file_not_found_error(
                    standard_path, resolved_standard_path, guide, "Standard file"
                )
                return 1

            # Load and validate data
            data_list = load_data(str(resolved_data_path))
            if not data_list:
                click.echo("❌ No data loaded")
                return 1

            data = pd.DataFrame(data_list)

            # Run assessment
            assessor = DataQualityAssessor(self._load_assessor_config())
            result = assessor.assess(data, str(resolved_standard_path))

            # Process results
            self._save_assessment_report(guide, data_path, result)
            threshold = self._get_threshold_from_standard(resolved_standard_path)
            self._display_assessment_results(result, data, guide, threshold)

            # Save output if requested
            if output_path:
                report_data = result.to_standard_dict()
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
                click.echo(f"📄 Report saved: {output_path}")

            return 0

        except FileNotFoundError as e:
            click.echo(f"❌ File not found: {e}")
            return 1
        except Exception as e:
            click.echo(f"❌ Assessment failed: {e}")
            return 1

    def _display_file_not_found_error(
        self, original_path: str, resolved_path: Path, guide: bool, file_type: str
    ) -> None:
        """Display appropriate error message for missing files."""
        if guide:
            click.echo(f"❌ Assessment failed: {file_type} not found: {original_path}")
            click.echo(get_project_root_display())
            click.echo(f"📄 Path tried: {rel_to_project_root(resolved_path)}")
        else:
            click.echo(f"❌ Assessment failed: {file_type} not found: {original_path}")

    def _load_assessor_config(self) -> dict[str, Any]:
        """Load configuration for the data quality assessor."""
        from ...config.loader import ConfigurationLoader

        assessor_config: dict[str, Any] = {}

        # Try to load configuration
        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    assessor_config["audit"] = env_config.get(
                        "audit", self._get_default_audit_config()
                    )
                except (KeyError, AttributeError):
                    assessor_config["audit"] = self._get_default_audit_config()
            else:
                assessor_config["audit"] = self._get_default_audit_config()
        except Exception:
            assessor_config["audit"] = self._get_default_audit_config()

        return assessor_config

    def _get_default_audit_config(self) -> dict[str, Any]:
        """Get default audit configuration."""
        return {
            "enabled": True,
            "log_dir": "ADRI/dev/audit-logs",
            "log_prefix": "adri",
            "log_level": "INFO",
            "include_data_samples": True,
            "max_log_size_mb": 100,
        }

    def _get_threshold_from_standard(self, standard_path: Path) -> float:
        """Read requirements.overall_minimum from a standard YAML."""
        try:
            std = load_contract(str(standard_path))
            req = std.get("requirements", {}) if isinstance(std, dict) else {}
            thr = float(req.get("overall_minimum", 75.0))
            return max(0.0, min(100.0, thr))  # Clamp to [0, 100]
        except Exception:
            return 75.0

    def _save_assessment_report(self, guide: bool, data_path: str, result) -> None:
        """Save assessment report if in guide mode."""
        if not guide:
            return

        try:
            from ...config.loader import ConfigurationLoader

            assessments_dir = Path("ADRI/dev/assessments")

            # Try to get configured assessments directory
            try:
                config_loader = ConfigurationLoader()
                config = config_loader.get_active_config()
                if config:
                    env_config = config_loader.get_environment_config(config)
                    assessments_dir = Path(env_config["paths"]["assessments"])
            except Exception:
                pass

            assessments_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_name = Path(data_path).stem
            auto_output_path = (
                assessments_dir / f"{data_name}_assessment_{timestamp}.json"
            )

            report_data = result.to_standard_dict()
            with open(auto_output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

        except Exception:
            # Non-fatal error - continue without saving
            pass

    def _display_assessment_results(
        self, result, data, guide: bool, threshold: float = 75.0
    ) -> None:
        """Display assessment results with appropriate formatting."""
        status_icon = "✅" if result.passed else "❌"
        status_text = "PASSED" if result.passed else "FAILED"
        total_records = len(data)

        if guide:
            self._display_guide_results(
                result, data, status_icon, status_text, threshold, total_records
            )
        else:
            self._display_simple_results(
                result, status_icon, status_text, total_records
            )

    def _display_guide_results(
        self,
        result,
        data,
        status_icon: str,
        status_text: str,
        threshold: float,
        total_records: int,
    ) -> None:
        """Display detailed guide-mode results."""
        failed_records_list = self._analyze_failed_records(data)
        actual_failed_records = len(failed_records_list)
        actual_passed_records = total_records - actual_failed_records

        # Calculate readiness status
        readiness_pct = (
            (actual_passed_records / total_records * 100) if total_records > 0 else 0
        )
        if readiness_pct >= 80:
            readiness_status = "✅ READY"
        elif readiness_pct >= 40:
            readiness_status = "⚠️  READY WITH BLOCKERS"
        else:
            readiness_status = "❌ NOT READY"

        _progressive_echo("📊 Step 3 of 4: ADRI Assessment", 0.4)
        _progressive_echo("===============================", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo(
            f"System Health (Score): {result.overall_score:.1f}/100  {status_icon} {status_text}",
            0.0,
        )
        _progressive_echo("  • Dataset-level quality across all 5 dimensions.", 0.0)
        _progressive_echo(
            "  • Use for: monitoring, integration confidence, and trend tracking.", 0.5
        )
        _progressive_echo("", 0.0)
        _progressive_echo(
            f"Batch Readiness (Gate): {actual_passed_records}/{total_records} rows  {readiness_status}",
            0.0,
        )
        _progressive_echo(
            "  • Row-level safety: records passing every required rule.", 0.0
        )
        _progressive_echo("  • Use for: pre-flight checks before agent execution.", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("💬 Why two numbers?", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo(
            f"  • Health = average dataset quality (meets {int(threshold)}/100 threshold).",
            0.0,
        )
        _progressive_echo(
            "  • Readiness = how many records are agent-safe right now.", 0.0
        )
        if result.passed and actual_passed_records < total_records:
            _progressive_echo(
                f"  • You passed health, but {actual_failed_records} row(s) need fixes.",
                0.6,
            )
        else:
            _progressive_echo("", 0.6)
        _progressive_echo("", 0.0)

        if actual_failed_records > 0:
            _progressive_echo("🔍 Records Requiring Attention:", 0.0)
            for failure in failed_records_list[:3]:
                _progressive_echo(failure, 0.0)
            if actual_failed_records > 3:
                remaining = actual_failed_records - 3
                _progressive_echo(f"   • ... and {remaining} more record(s)", 0.5)
            else:
                _progressive_echo("", 0.5)
            _progressive_echo("", 0.0)

        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("▶ Next (Step 4): Review your audit trail", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("   adri view-logs", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "This shows your complete lineage trail and validation details.", 0.0
        )
        _progressive_echo("─" * 58, 0.0)

    def _display_simple_results(
        self, result, status_icon: str, status_text: str, total_records: int
    ) -> None:
        """Display simple results for non-guide mode."""
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

        # Display standard path for transparency (Issue #35 fix)
        if hasattr(result, "standard_path") and result.standard_path:
            click.echo(f"Standard: {result.standard_path}")

    def _analyze_failed_records(self, data) -> list:
        """Analyze data to identify failed records with specific issues."""
        failed_records_list = []

        for i, row in data.iterrows():
            issues = []

            # Check for missing values
            missing_fields = [col for col in row.index if self._is_missing(row[col])]
            if missing_fields:
                top_missing = missing_fields[:2]
                issues.append(("missing", top_missing))

            # Check for business rule violations
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

            # If there are issues, format them for display
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

    def _is_missing(self, value) -> bool:
        """Check if a value is considered missing."""
        try:
            if pd.isna(value):
                return True
        except Exception:
            pass
        return isinstance(value, str) and value.strip() == ""

    def get_name(self) -> str:
        """Get the command name."""
        return "assess"


# @ADRI_FEATURE_END[cli_assess_command]
