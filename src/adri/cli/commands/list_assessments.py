"""List assessments command implementation for ADRI CLI.

This module contains the ListAssessmentsCommand class that handles listing
and displaying assessment report history.
"""

import json
from pathlib import Path
from typing import Any

import click

from ...core.protocols import Command


class ListAssessmentsCommand(Command):
    """Command for listing previous assessment reports.

    Handles retrieval and display of assessment history with optional
    detailed information and audit log integration.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "List previous assessment reports"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the list-assessments command.

        Args:
            args: Command arguments containing:
                - recent: int - Number of recent assessments to show
                - verbose: bool - Show detailed assessment information

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        recent = args.get("recent", 10)
        verbose = args.get("verbose", False)

        return self._list_assessments(recent, verbose)

    def _list_assessments(self, recent: int = 10, verbose: bool = False) -> int:
        """List previous assessment reports."""
        try:
            assessments_dir = self._get_assessments_directory()

            if not assessments_dir.exists():
                click.echo("📁 No assessments directory found")
                click.echo(
                    "▶ Create assessments: adri assess <data> --standard <standard>"
                )
                return 0

            assessment_files = list(assessments_dir.glob("*.json"))
            if not assessment_files:
                click.echo("📊 No assessment reports found")
                click.echo(
                    "▶ Create assessments: adri assess <data> --standard <standard>"
                )
                return 0

            # Sort by modification time (most recent first)
            assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            if recent > 0:
                assessment_files = assessment_files[:recent]

            # Parse assessment files
            table_data = self._parse_assessment_files(assessment_files)
            if not table_data:
                click.echo("📊 No valid assessment reports found")
                click.echo("▶ Try running: adri assess <data> --standard <standard>")
                return 0

            # Enhance with audit log data if available
            audit_entries = self._load_audit_entries()
            enhanced_table_data = self._enhance_with_record_counts(
                table_data, audit_entries
            )

            # Display results
            self._display_assessments_table(enhanced_table_data, table_data, verbose)

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to list assessments: {e}")
            click.echo("▶ Try: adri assess <data> --standard <standard>")
            return 1

    def _get_assessments_directory(self) -> Path:
        """Get the assessments directory from configuration."""
        from ...config.loader import ConfigurationLoader

        assessments_dir = Path("ADRI/dev/assessments")

        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                assessments_dir = Path(env_config["paths"]["assessments"])
        except Exception:
            pass

        return assessments_dir

    def _parse_assessment_files(
        self, assessment_files: list[Path]
    ) -> list[dict[str, Any]]:
        """Parse assessment files and extract table data."""
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

            except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError):
                # Skip invalid assessment files
                continue

        return table_data

    def _load_audit_entries(self) -> list[dict[str, Any]]:
        """Load audit entries from JSONL files using ADRILogReader."""
        from datetime import datetime

        from ...config.loader import ConfigurationLoader
        from ...logging import ADRILogReader

        audit_entries: list[dict[str, Any]] = []

        try:
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

            # Read assessment logs
            assessment_logs = log_reader.read_assessment_logs()

            # Convert to audit entries format
            for log_record in assessment_logs:
                try:
                    timestamp_str = log_record.get("timestamp", "")
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "")
                        )
                    else:
                        timestamp = datetime.strptime(
                            timestamp_str, "%Y-%m-%d %H:%M:%S"
                        )

                    audit_entries.append(
                        {
                            "timestamp": timestamp,
                            "data_row_count": int(log_record.get("data_row_count", 0)),
                            "overall_score": float(log_record.get("overall_score", 0)),
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue  # Skip unreadable entries

        except Exception:
            # If loading fails, return empty list
            pass

        return audit_entries

    def _enhance_with_record_counts(
        self, table_data: list[dict[str, Any]], audit_entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Enhance table data with record count information from audit logs."""
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
                    int((score_value / 100.0) * total_records)
                    if total_records > 0
                    else 0
                )
                records_info = f"{passed_records}/{total_records}"
            else:
                records_info = "N/A"

            enhanced.append({**entry, "records": records_info})

        return enhanced

    def _display_assessments_table(
        self,
        enhanced_table_data: list[dict[str, Any]],
        table_data: list[dict[str, Any]],
        verbose: bool,
    ) -> None:
        """Display assessments in a formatted table."""
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
            data_packet = entry.get("dataset", entry.get("records", "unknown"))[
                :15
            ].ljust(15)
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

    def get_name(self) -> str:
        """Get the command name."""
        return "list-assessments"
