"""View logs command implementation for ADRI CLI.

This module contains the ViewLogsCommand class that handles audit log
viewing and analysis operations.
"""

import csv
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

            main_log_file = audit_logs_dir / "adri_assessment_logs.csv"
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
            table_data = self._format_log_table_data(log_entries)
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

    def _parse_audit_log_entries(
        self, main_log_file: Path, today: bool
    ) -> List[Dict[str, Any]]:
        """Parse audit log entries from CSV file."""
        from datetime import date, datetime

        log_entries = []

        with open(main_log_file, "r") as f:
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

                    # Filter by today if requested
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
                            "execution_decision": row.get(
                                "execution_decision", "unknown"
                            ),
                        }
                    )

                except (ValueError, TypeError, OSError):
                    continue  # Skip unreadable entries

        return log_entries

    def _format_log_table_data(
        self, log_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format log entries for table display."""
        table_data = []

        for entry in log_entries:
            # Determine mode and function info
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

            # Format standard ID for display
            standard_id = entry.get("standard_id", "unknown")
            data_packet = (
                standard_id.replace("_ADRI_standard", "")
                if standard_id and "_ADRI_standard" in standard_id
                else "unknown"
            )
            if len(data_packet) > 12:
                data_packet = data_packet[:9] + "..."

            # Format function name
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
        click.echo(f"   📄 {audit_logs_dir}/adri_assessment_logs.csv")
        click.echo(f"   📊 {audit_logs_dir}/adri_dimension_scores.csv")
        click.echo(f"   ❌ {audit_logs_dir}/adri_failed_validations.csv")
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
