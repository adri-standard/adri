"""View logs command implementation for ADRI CLI.

This module contains the ViewLogsCommand class that handles audit log
viewing and analysis operations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import click

from ...core.protocols import Command


class ViewLogsCommand(Command):
    """Command for viewing audit logs from CSV files.

    Handles retrieval and display of audit log entries with filtering
    and detailed breakdown options.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "View audit logs from CSV files"

    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the view-logs command.

        Args:
            args: Command arguments containing:
                - recent: int - Number of recent audit log entries to show
                - today: bool - Show only today's audit logs
                - verbose: bool - Show detailed audit log information

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        recent = args.get("recent", 10)
        today = args.get("today", False)
        verbose = args.get("verbose", False)

        return self._view_logs(recent, today, verbose)

    def _view_logs(
        self, recent: int = 10, today: bool = False, verbose: bool = False
    ) -> int:
        """View audit logs from CSV files."""
        try:
            audit_logs_dir = self._get_audit_logs_directory()

            if not audit_logs_dir.exists():
                click.echo("📁 No audit logs directory found")
                click.echo(
                    "💡 Run 'adri assess <data> --standard <standard>' to create audit logs"
                )
                return 0

            main_log_file = audit_logs_dir / "adri_assessment_logs.jsonl"
            if not main_log_file.exists():
                click.echo("📊 No audit logs found")
                click.echo(
                    "💡 Run 'adri assess <data> --standard <standard>' to create audit logs"
                )
                return 0

            # Parse log entries
            log_entries = self._parse_audit_log_entries(main_log_file, today)
            if not log_entries:
                click.echo("📊 No audit log entries found")
                return 0

            # Sort by timestamp (most recent first)
            log_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            if recent > 0:
                log_entries = log_entries[:recent]

            # Format and display
            table_data = self._format_log_table_data(log_entries, audit_logs_dir)
            self._display_audit_logs_table(
                table_data, log_entries, audit_logs_dir, verbose
            )

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to view logs: {e}")
            return 1

    def _get_audit_logs_directory(self) -> Path:
        """Get the audit logs directory from configuration."""
        from ...config.loader import ConfigurationLoader

        audit_logs_dir = Path("ADRI/dev/audit-logs")

        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                audit_logs_dir = Path(env_config["paths"]["audit_logs"])
        except Exception:
            pass

        return audit_logs_dir

    def _count_failed_rows(
        self, assessment_id: str, total_rows: int, audit_logs_dir: Path
    ) -> tuple[int, float]:
        """Count total failed rows for an assessment.

        Args:
            assessment_id: Assessment ID to look up failures for
            total_rows: Total rows in the dataset
            audit_logs_dir: Directory containing audit log files

        Returns:
            Tuple of (total_failed_rows, error_percentage)

        Algorithm:
            1. Open adri_failed_validations.jsonl
            2. Parse each line as JSON
            3. Filter where assessment_id matches
            4. Sum affected_rows across all matching entries
            5. Calculate percentage: (failed / total) * 100
            6. Return (total_failed, percentage)

        Edge cases:
            - No failures file: return (0, 0.0)
            - No matching failures: return (0, 0.0)
            - Cannot read file: return (0, 0.0)
            - Invalid JSON: skip that line, continue
        """
        failed_val_path = audit_logs_dir / "adri_failed_validations.jsonl"

        # If no failures file exists, no errors
        if not failed_val_path.exists():
            return (0, 0.0)

        total_failed = 0

        try:
            with open(failed_val_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        failure = json.loads(line)
                        # Check if this failure belongs to our assessment
                        if failure.get("assessment_id") == assessment_id:
                            affected = int(failure.get("affected_rows", 0))
                            total_failed += affected
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # Skip malformed lines
                        continue
        except Exception:
            # If we can't read the file, return 0 errors
            return (0, 0.0)

        # Calculate percentage
        if total_rows > 0:
            percentage = (total_failed / total_rows) * 100.0
        else:
            percentage = 0.0

        return (total_failed, percentage)

    def _parse_audit_log_entries(
        self, main_log_file: Path, today: bool
    ) -> List[Dict[str, Any]]:
        """Parse audit log entries from JSONL file."""
        from datetime import date, datetime

        log_entries = []

        with open(main_log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)

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

                    # Filter by today if requested
                    if today and timestamp.date() != date.today():
                        continue

                    log_entries.append(
                        {
                            "timestamp": timestamp,
                            "assessment_id": row.get("assessment_id", "unknown"),
                            "overall_score": float(row.get("overall_score", 0)),
                            "passed": bool(row.get("passed", False)),
                            "data_row_count": int(row.get("data_row_count", 0)),
                            "function_name": row.get("function_name", ""),
                            "standard_id": row.get("standard_id", "unknown"),
                            "assessment_duration_ms": int(
                                row.get("assessment_duration_ms", 0)
                            ),
                            "execution_decision": row.get(
                                "execution_decision", "unknown"
                            ),
                        }
                    )

                except (ValueError, TypeError, OSError, json.JSONDecodeError):
                    continue  # Skip unreadable entries

        return log_entries

    def _format_log_table_data(
        self, log_entries: List[Dict[str, Any]], audit_logs_dir: Path
    ) -> List[Dict[str, Any]]:
        """Format log entries for table display."""
        table_data = []

        for entry in log_entries:
            # Determine mode
            if entry["function_name"] == "assess":
                mode = (
                    "CLI Guide"
                    if "guide" in entry.get("assessment_id", "")
                    else "CLI Direct"
                )
            else:
                mode = "Decorator"

            # Format standard ID for display
            standard_id = entry.get("standard_id", "unknown")
            data_packet = (
                standard_id.replace("_ADRI_standard", "")
                if standard_id and "_ADRI_standard" in standard_id
                else "unknown"
            )
            if len(data_packet) > 12:
                data_packet = data_packet[:9] + "..."

            # Get row count and error count
            total_rows = entry.get("data_row_count", 0)
            assessment_id = entry.get("assessment_id", "")

            # Count errors for this assessment
            failed_count, failed_pct = self._count_failed_rows(
                assessment_id, total_rows, audit_logs_dir
            )

            # Format row count with commas for thousands
            if total_rows >= 1000:
                rows_str = f"{total_rows:,}"
            else:
                rows_str = str(total_rows)

            # Format error count as "N (X%)"
            if failed_pct >= 10.0:
                errors_str = f"{failed_count} ({failed_pct:.0f}%)"
            elif failed_pct > 0:
                errors_str = f"{failed_count} ({failed_pct:.1f}%)"
            else:
                errors_str = "0 (0%)"

            date_str = entry["timestamp"].strftime("%m-%d %H:%M")
            score = f"{entry['overall_score']:.1f}/100"
            status = "✅ PASSED" if entry["passed"] else "❌ FAILED"

            table_data.append(
                {
                    "data_packet": data_packet,
                    "score": score,
                    "status": status,
                    "rows": rows_str,
                    "errors": errors_str,
                    "mode": mode,
                    "date": date_str,
                }
            )

        return table_data

    def _display_audit_logs_table(
        self,
        table_data: List[Dict[str, Any]],
        log_entries: List[Dict[str, Any]],
        audit_logs_dir: Path,
        verbose: bool,
    ) -> None:
        """Display audit logs in a formatted table."""
        click.echo(f"📊 ADRI Audit Log Summary ({len(table_data)} recent)")
        click.echo(
            "┌─────────────┬──────────┬──────────┬───────┬──────────┬───────────┬──────────────┐"
        )
        click.echo(
            "│ Data Packet │ Score    │ Status   │ Rows  │ Errors   │ Mode      │ Date         │"
        )
        click.echo(
            "├─────────────┼──────────┼──────────┼───────┼──────────┼───────────┼──────────────┤"
        )

        for entry in table_data:
            data_packet = entry["data_packet"].ljust(11)
            score = entry["score"].ljust(8)
            status = entry["status"].ljust(8)
            rows = entry["rows"].rjust(5)
            errors = entry["errors"].ljust(8)
            mode = entry["mode"].ljust(9)
            date = entry["date"].ljust(12)
            click.echo(
                f"│ {data_packet} │ {score} │ {status} │ {rows} │ {errors} │ {mode} │ {date} │"
            )

        click.echo(
            "└─────────────┴──────────┴──────────┴───────┴──────────┴───────────┴──────────────┘"
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

        # Check if failed validations file has content
        failed_val_path = Path(audit_logs_dir) / "adri_failed_validations.jsonl"
        failed_val_count = 0
        if failed_val_path.exists():
            try:
                with open(failed_val_path, "r", encoding="utf-8") as f:
                    failed_val_count = sum(1 for _ in f)
            except Exception:
                pass

        if failed_val_count > 0:
            click.echo(
                f"   ✅ {audit_logs_dir}/adri_failed_validations.jsonl ({failed_val_count} validation failures)"
            )
        else:
            click.echo(
                f"   ⚪ {audit_logs_dir}/adri_failed_validations.jsonl (no failures - data passed all checks)"
            )

        # Show sample failures if verbose mode and failures exist
        if verbose and failed_val_count > 0:
            click.echo()
            click.echo("🔍 Recent Validation Failures:")
            try:
                with open(failed_val_path, "r") as f:
                    lines = f.readlines()
                    # Show last 5 failures
                    for line in lines[-5:]:
                        try:
                            failure = json.loads(line)
                            field = failure.get("field_name", "unknown")
                            issue = failure.get("issue_type", "unknown").replace(
                                "_", " "
                            )
                            rows = failure.get("affected_rows", 0)
                            pct = failure.get("affected_percentage", 0)
                            samples = failure.get("sample_failures", [])[:2]
                            remediation = failure.get("remediation", "")

                            click.echo(f"   • {field}: {issue}")
                            click.echo(f"     Affected: {rows} rows ({pct:.1f}%)")
                            if samples:
                                click.echo(
                                    f"     Samples: {', '.join(str(s) for s in samples)}"
                                )
                            if remediation:
                                click.echo(f"     Fix: {remediation}")
                            click.echo()
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass
        click.echo()

        # Display completion message
        click.echo("🎉 ADRI onboarding complete!")
        click.echo("You now know how to:")
        click.echo("  • Generate a standard")
        click.echo("  • Assess data")
        click.echo("  • Review assessments")
        click.echo("  • Audit logs")
        click.echo("👉 Next: Integrate ADRI into your agent workflow (see docs)")

    def get_name(self) -> str:
        """Get the command name."""
        return "view-logs"
