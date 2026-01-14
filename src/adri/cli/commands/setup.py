"""Setup command implementation for ADRI CLI.

This module contains the SetupCommand class that handles project initialization,
directory structure creation, and sample file generation.
"""

import os
from pathlib import Path
from typing import Any

import click
import yaml

from ...core.protocols import Command


class SetupCommand(Command):
    """Command for initializing ADRI in a project.

    Handles project setup including configuration file creation, directory
    structure setup, and sample file generation for tutorials.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Initialize ADRI in a project"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the setup command.

        Args:
            args: Command arguments containing:
                - force: bool - Overwrite existing configuration
                - project_name: Optional[str] - Custom project name
                - guide: bool - Show step-by-step guidance and create sample files

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        force = args.get("force", False)
        project_name = args.get("project_name")
        guide = args.get("guide", False)

        return self._setup_project(force, project_name, guide)

    def _setup_project(
        self, force: bool = False, project_name: str | None = None, guide: bool = False
    ) -> int:
        """Initialize ADRI in a project."""
        try:
            adri_dir = Path("ADRI")
            adri_dir.mkdir(exist_ok=True)
            config_path = "ADRI/config.yaml"

            if os.path.exists(config_path) and not force:
                if guide:
                    click.echo(
                        "❌ Configuration already exists. Use --force to overwrite."
                    )
                    click.echo("💡 Or use 'adri show-config' to see current setup")
                else:
                    click.echo(
                        "❌ Configuration already exists. Use --force to overwrite."
                    )
                return 1

            project_name = project_name or Path.cwd().name

            if guide:
                click.echo("🚀 Step 1 of 4: ADRI Project Setup")
                click.echo("==================================")
                click.echo("")

            # Create configuration
            config_content = self._create_config_content(project_name)

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)

            # Create directories
            config_data = self._get_config_data(project_name)
            for path in config_data["adri"]["paths"].values():
                Path(path).mkdir(parents=True, exist_ok=True)

            if guide:
                success = self._create_sample_files()
                if not success:
                    click.echo("❌ Failed to create tutorial data files")
                    click.echo("▶ Try: adri setup --guide --force")
                    return 1

                self._display_setup_success(guide)
            else:
                click.echo("✅ ADRI project initialized successfully!")
                click.echo(f"📁 Project: {project_name}")
                click.echo(f"⚙️  Config: {config_path}")

            return 0
        except Exception as e:
            click.echo(f"❌ Setup failed: {e}")
            click.echo("▶ Try: adri setup --guide --force")
            return 1

    def _create_config_content(self, project_name: str) -> str:
        """Create the configuration file content with documentation header."""
        doc_header = """# ADRI PROJECT CONFIGURATION
# ==================================
#
# Directory Structure:
# - ADRI/contracts/      → YAML contract files (quality validation rules)
# - ADRI/assessments/    → Assessment reports (JSON quality reports)
# - ADRI/training-data/  → Training data snapshots (SHA256 integrity tracking)
# - ADRI/audit-logs/     → Audit logs (CSV activity tracking)
# - ADRI/tutorials/      → Learning examples for onboarding
#
# AUDIT CONFIGURATION
# - include_data_samples: include sample values when safe
# - max_log_size_mb: rotate logs after exceeding this size
# - log_level: INFO/DEBUG
#
# PROTECTION CONFIGURATION
# - default_failure_mode: "raise" | "warn" | "continue"
# - default_min_score: minimum quality score required (0-100)
# - auto_generate_contracts: auto-create contracts from data analysis
#
# For more information, see: https://github.com/adri-standard/adri
"""

        config_data = self._get_config_data(project_name)
        config_yaml = yaml.dump(config_data, default_flow_style=False)

        return doc_header + "\n" + config_yaml

    def _get_config_data(self, project_name: str) -> dict[str, Any]:
        """Get the configuration data structure."""
        return {
            "adri": {
                "project_name": project_name,
                "version": "4.0.0",
                "paths": {
                    "contracts": "ADRI/contracts",
                    "assessments": "ADRI/assessments",
                    "training_data": "ADRI/training-data",
                    "audit_logs": "ADRI/audit-logs",
                },
                "audit": {
                    "enabled": True,
                    "log_dir": "ADRI/audit-logs",
                    "log_prefix": "adri",
                    "log_level": "INFO",
                    "include_data_samples": True,
                    "max_log_size_mb": 100,
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                    "cache_duration_hours": 1,
                    "auto_generate_contracts": True,
                    "verbose_protection": False,
                },
            }
        }

    def _create_sample_files(self) -> bool:
        """Create sample CSV files for guided experience."""
        try:
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

            # Verify files were created
            training_file = tutorial_dir / "invoice_data.csv"
            test_file = tutorial_dir / "test_invoice_data.csv"

            return training_file.exists() and test_file.exists()

        except Exception:
            return False

    def _display_setup_success(self, guide: bool) -> None:
        """Display setup success message."""
        if guide:
            click.echo("✅ Project structure created with sample data")
            click.echo("")
            click.echo("📁 What was created:")
            click.echo(
                "   📚 tutorials/invoice_processing/ - Invoice processing tutorial"
            )
            click.echo("   📋 contracts/      - Quality rules")
            click.echo("   📊 assessments/    - Assessment reports")
            click.echo("   📄 training-data/  - Preserved data snapshots")
            click.echo("   📈 audit-logs/     - Comprehensive audit trail")
            click.echo("")
            click.echo("💡 Note: Commands use relative paths from project root")
            click.echo("")
            click.echo(
                "▶ Next Step 2 of 4: adri generate-contract tutorials/invoice_processing/invoice_data.csv --guide"
            )

    def get_name(self) -> str:
        """Get the command name."""
        return "setup"
