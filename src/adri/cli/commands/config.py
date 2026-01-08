"""Configuration command implementation for ADRI CLI.

This module contains the ShowConfigCommand class that handles configuration
display and environment management.
"""

import os
from pathlib import Path
from typing import Any

import click
import pandas as pd

from ...core.protocols import Command


class ShowConfigCommand(Command):
    """Command for showing current ADRI configuration.

    Handles display of project configuration including environments,
    paths, and audit settings.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Show current ADRI configuration"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the show-config command.

        Args:
            args: Command arguments containing:
                - paths_only: bool - Show only path information
                - environment: Optional[str] - Show specific environment only

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        paths_only = args.get("paths_only", False)
        environment = args.get("environment")

        return self._show_config(paths_only, environment)

    def _show_config(
        self, paths_only: bool = False, environment: str | None = None
    ) -> int:
        """Show current ADRI configuration."""
        try:
            from ...config.loader import ConfigurationLoader

            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()

            if not config:
                click.echo("❌ Configuration must be located at ADRI/config.yaml")
                click.echo("💡 Run 'adri setup' to initialize ADRI in this project")
                return 1

            adri_config = config["adri"]

            # Display general information unless paths-only
            if not paths_only:
                click.echo("📋 ADRI Configuration")
                click.echo(f"🏗️  Project: {adri_config['project_name']}")
                click.echo(f"📦 Version: {adri_config.get('version', '4.0.0')}")
                click.echo(
                    f"🌍 Default Environment: {adri_config['default_environment']}"
                )
                click.echo()

            # Determine which environments to show
            environments_to_show = (
                [environment]
                if environment
                else list(adri_config["environments"].keys())
            )

            for env_name in environments_to_show:
                if env_name not in adri_config["environments"]:
                    click.echo(f"❌ Environment '{env_name}' not found")
                    continue

                env_config = adri_config["environments"][env_name]
                paths = env_config["paths"]

                click.echo(f"📁 {env_name.title()} Environment:")
                for path_type, path_value in paths.items():
                    status = "✅" if os.path.exists(path_value) else "❌"
                    click.echo(f"  {status} {path_type}: {path_value}")
                click.echo()

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to show configuration: {e}")
            return 1

    def get_name(self) -> str:
        """Get the command name."""
        return "show-config"


class ValidateContractCommand(Command):
    """Command for validating YAML standard files.

    Handles structural validation of ADRI standard files to ensure
    they conform to the expected schema.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Validate YAML standard file"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the validate-standard command.

        Args:
            args: Command arguments containing:
                - standard_path: str - Path to standard file to validate

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        standard_path = args["standard_path"]
        return self._validate_standard(standard_path)

    def _validate_standard(self, standard_path: str) -> int:
        """Validate YAML standard file using comprehensive StandardValidator."""
        try:
            from ...contracts.exceptions import SchemaValidationError
            from ...contracts.validator import get_validator

            # Use the comprehensive validator
            validator = get_validator()
            result = validator.validate_contract_file(standard_path, use_cache=False)

            if result.is_valid:
                # Display success with summary
                click.echo("✅ Standard validation PASSED")

                # Load and display standard info
                from ...validator.loaders import load_contract

                standard = load_contract(
                    standard_path, validate=False
                )  # Already validated
                std_info = standard.get("standards", {})

                click.echo(f"📄 Name: {std_info.get('name', 'Unknown')}")
                click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
                click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")

                # Show warnings if any
                if result.has_warnings:
                    click.echo(f"\n⚠️  {result.warning_count} warning(s):")
                    for warning in result.warnings:
                        click.echo(f"  • {warning.path}: {warning.message}")

                return 0
            else:
                # Display validation errors
                click.echo("❌ Standard validation FAILED")
                click.echo(f"\n{result.format_errors()}")

                # Show warnings if any
                if result.has_warnings:
                    click.echo(f"\n⚠️  {result.warning_count} warning(s):")
                    for warning in result.warnings:
                        click.echo(f"  • {warning.path}: {warning.message}")

                return 1

        except SchemaValidationError as e:
            click.echo("❌ Standard validation FAILED")
            click.echo(f"\n{str(e)}")
            return 1
        except Exception as e:
            click.echo(f"❌ Validation failed: {e}")
            return 1

    def get_name(self) -> str:
        """Get the command name."""
        return "validate-standard"


class ListContractsCommand(Command):
    """Command for listing available YAML standards.

    Handles discovery and display of local standards with optional
    remote catalog integration.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "List available YAML standards"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the list-standards command.

        Args:
            args: Command arguments containing:
                - include_catalog: bool - Also show remote catalog entries

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        include_catalog = args.get("include_catalog", False)
        return self._list_standards(include_catalog)

    def _list_standards(self, include_catalog: bool = False) -> int:
        """List available YAML standards (local). Optionally include remote catalog."""
        try:
            from ...config.loader import ConfigurationLoader

            standards_found = False

            # Local project standards (development and production)
            dev_dir = Path("ADRI/dev/contracts")
            prod_dir = Path("ADRI/prod/contracts")

            # Try to resolve from config if available
            try:
                config_loader = ConfigurationLoader()
                config = config_loader.get_active_config()
                if config:
                    dev_env = config_loader.get_environment_config(
                        config, "development"
                    )
                    prod_env = config_loader.get_environment_config(
                        config, "production"
                    )
                    dev_dir = Path(dev_env["paths"]["contracts"])
                    prod_dir = Path(prod_env["paths"]["contracts"])
            except Exception:
                pass

            # List YAML files in directories
            dev_files = self._list_yaml_files(dev_dir)
            prod_files = self._list_yaml_files(prod_dir)

            if dev_files:
                click.echo("🏗️  Project Standards (dev):")
                for i, p in enumerate(dev_files, 1):
                    click.echo(f"  {i}. {p.name}")
                standards_found = True

            if prod_files:
                if standards_found:
                    click.echo()
                click.echo("🏛️  Project Standards (prod):")
                for i, p in enumerate(prod_files, 1):
                    click.echo(f"  {i}. {p.name}")
                standards_found = True

            # Optionally include remote catalog
            if include_catalog:
                self._display_remote_catalog(standards_found)

            if not standards_found and not include_catalog:
                click.echo("📋 No standards found")
                click.echo("💡 Use 'adri generate-standard <data>' to create one")

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to list standards: {e}")
            return 1

    def _list_yaml_files(self, dir_path: Path) -> list[Path]:
        """List YAML files in a directory."""
        if not dir_path.exists():
            return []
        return list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml"))

    def _display_remote_catalog(self, standards_found: bool) -> None:
        """Display remote catalog entries if available."""
        if standards_found:
            click.echo()

        try:
            from ...catalog import CatalogClient, CatalogConfig

            base_url = CatalogClient.resolve_base_url()
            if not base_url:
                click.echo("🌐 Remote Catalog: (not configured)")
                return

            client = CatalogClient(CatalogConfig(base_url=base_url))
            resp = client.list()

            click.echo(f"🌐 Remote Catalog ({len(resp.entries)}):")
            for i, e in enumerate(resp.entries, 1):
                click.echo(f"  {i}. {e.id} — {e.name} v{e.version}")

        except Exception as e:
            click.echo(f"⚠️ Could not load remote catalog: {e}")

    def get_name(self) -> str:
        """Get the command name."""
        return "list-standards"


class ShowContractCommand(Command):
    """Command for showing details of a specific ADRI standard.

    Handles display of standard metadata, requirements, and configuration
    with optional verbose output.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Show details of a specific ADRI standard"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the show-standard command.

        Args:
            args: Command arguments containing:
                - standard_name: str - Name or path of the standard to show
                - verbose: bool - Show detailed requirements and rules

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        standard_name = args["standard_name"]
        verbose = args.get("verbose", False)

        return self._show_standard(standard_name, verbose)

    def _show_standard(self, standard_name: str, verbose: bool = False) -> int:
        """Show details of a specific ADRI standard."""
        try:
            from ...validator.loaders import load_contract

            # Find the standard file
            standard_path = self._find_standard_file(standard_name)
            if not standard_path:
                click.echo(f"❌ Standard not found: {standard_name}")
                click.echo("💡 Use 'adri list-standards' to see available standards")
                return 1

            # Load and display standard
            standard = load_contract(standard_path)
            std_info = standard.get("standards", {})

            click.echo("📋 ADRI Standard Details")
            click.echo(f"📄 Name: {std_info.get('name', 'Unknown')}")
            click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
            click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")
            click.echo(f"🏛️  Authority: {std_info.get('authority', 'Unknown')}")

            if "description" in std_info:
                click.echo(f"📝 Description: {std_info['description']}")

            requirements = standard.get("requirements", {})
            click.echo(
                f"\n🎯 Overall Minimum Score: {requirements.get('overall_minimum', 'Not set')}/100"
            )

            if verbose:
                self._display_verbose_details(requirements)

            click.echo(
                f"\n💡 Use 'adri assess <data> --standard {standard_name}' to test data"
            )
            return 0

        except Exception as e:
            click.echo(f"❌ Failed to show standard: {e}")
            return 1

    def _find_standard_file(self, standard_name: str) -> str | None:
        """Find the standard file by name or path."""
        if os.path.exists(standard_name):
            return standard_name

        # Search in standard locations
        search_paths = [
            f"ADRI/dev/contracts/{standard_name}.yaml",
            f"ADRI/prod/contracts/{standard_name}.yaml",
            f"{standard_name}.yaml",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return None

    def _display_verbose_details(self, requirements: dict[str, Any]) -> None:
        """Display verbose standard details."""
        if "field_requirements" in requirements:
            field_reqs = requirements["field_requirements"]
            click.echo(f"\n📋 Field Requirements ({len(field_reqs)} fields):")
            for field_name, field_config in field_reqs.items():
                field_type = field_config.get("type", "unknown")
                nullable = (
                    "nullable" if field_config.get("nullable", True) else "required"
                )
                click.echo(f"  • {field_name}: {field_type} ({nullable})")

        if "dimension_requirements" in requirements:
            dim_reqs = requirements["dimension_requirements"]
            click.echo(f"\n📊 Dimension Requirements ({len(dim_reqs)} dimensions):")
            for dim_name, dim_config in dim_reqs.items():
                min_score = dim_config.get("minimum_score", "Not set")
                click.echo(f"  • {dim_name}: ≥{min_score}/20")

    def get_name(self) -> str:
        """Get the command name."""
        return "show-standard"


class ConfigSetCommand(Command):
    """Command for setting configuration values in YAML standard files.

    Handles editing YAML standard files with dot notation for nested paths,
    validates values before saving, and creates backups.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Set configuration values in YAML standard files"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the config set command.

        Args:
            args: Command arguments containing:
                - setting: str - Setting to modify (e.g., 'min_score=80')
                - standard_path: str - Path to standard file to modify

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        setting = args["setting"]
        standard_path = args["standard_path"]

        return self._set_config(setting, standard_path)

    def _set_config(self, setting: str, standard_path: str) -> int:
        """Set a configuration value in a YAML standard file."""
        try:
            import shutil

            import yaml

            # Parse setting
            if "=" not in setting:
                click.echo("❌ Invalid setting format. Use: key=value")
                click.echo("   Examples: min_score=80, readiness.row_threshold=0.9")
                return 1

            key_path, value_str = setting.split("=", 1)
            key_parts = key_path.split(".")

            # Validate and convert value
            value = self._parse_value(value_str)
            if value is None:
                click.echo(f"❌ Invalid value: {value_str}")
                return 1

            # Load standard
            standard_file = Path(standard_path)
            if not standard_file.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                return 1

            with open(standard_file, encoding="utf-8") as f:
                standard = yaml.safe_load(f)

            # Create backup
            backup_path = standard_file.with_suffix(".yaml.backup")
            shutil.copy2(standard_file, backup_path)

            # Set value using dot notation
            self._set_nested_value(standard, key_parts, value)

            # Save standard
            with open(standard_file, "w", encoding="utf-8") as f:
                yaml.dump(standard, f, default_flow_style=False, sort_keys=False)

            click.echo(f"✅ Configuration updated: {key_path} = {value}")
            click.echo(f"📄 Standard: {standard_path}")
            click.echo(f"💾 Backup saved: {backup_path}")

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to set configuration: {e}")
            return 1

    def _parse_value(self, value_str: str) -> Any:
        """Parse and validate a configuration value."""
        # Try boolean
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"

        # Try integer
        try:
            return int(value_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str

    def _set_nested_value(
        self, data: dict[str, Any], key_parts: list[str], value: Any
    ) -> None:
        """Set a value in nested dictionary using dot notation."""
        current = data
        for i, key in enumerate(key_parts[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]
        current[key_parts[-1]] = value

    def get_name(self) -> str:
        """Get the command name."""
        return "config-set"


class ConfigGetCommand(Command):
    """Command for getting configuration values from YAML standard files.

    Handles reading configuration values using dot notation for nested paths.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Get configuration values from YAML standard files"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the config get command.

        Args:
            args: Command arguments containing:
                - setting: str - Setting to retrieve (e.g., 'min_score')
                - standard_path: str - Path to standard file

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        setting = args["setting"]
        standard_path = args["standard_path"]

        return self._get_config(setting, standard_path)

    def _get_config(self, setting: str, standard_path: str) -> int:
        """Get a configuration value from a YAML standard file."""
        try:
            import yaml

            key_parts = setting.split(".")

            # Load standard
            standard_file = Path(standard_path)
            if not standard_file.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                return 1

            with open(standard_file, encoding="utf-8") as f:
                standard = yaml.safe_load(f)

            # Get value using dot notation
            value = self._get_nested_value(standard, key_parts)

            if value is None:
                click.echo(f"❌ Configuration key not found: {setting}")
                return 1

            click.echo(f"{setting}: {value}")
            return 0

        except Exception as e:
            click.echo(f"❌ Failed to get configuration: {e}")
            return 1

    def _get_nested_value(
        self, data: dict[str, Any], key_parts: list[str]
    ) -> Any | None:
        """Get a value from nested dictionary using dot notation."""
        current = data
        for key in key_parts:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def get_name(self) -> str:
        """Get the command name."""
        return "config-get"


class ExplainThresholdsCommand(Command):
    """Command for explaining threshold configurations and their implications.

    Educational tool that helps users understand current thresholds,
    their meanings, and potential what-if scenarios.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Explain threshold configurations and their implications"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the explain-thresholds command.

        Args:
            args: Command arguments containing:
                - standard_path: str - Path to standard file

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        standard_path = args["standard_path"]
        return self._explain_thresholds(standard_path)

    def _explain_thresholds(self, standard_path: str) -> int:
        """Explain thresholds in a standard file."""
        try:
            import yaml

            # Load standard
            standard_file = Path(standard_path)
            if not standard_file.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                return 1

            with open(standard_file, encoding="utf-8") as f:
                standard = yaml.safe_load(f)

            click.echo("📊 Threshold Explanation")
            click.echo("=======================")
            click.echo(f"Standard: {standard_path}")
            click.echo("")

            # Health threshold
            requirements = standard.get("requirements", {})
            min_score = int(requirements.get("overall_minimum", 75))

            click.echo("Health Threshold (MIN_SCORE):")
            click.echo(f"  • Current: {min_score}/100")
            click.echo(
                f"  • Meaning: Dataset must average ≥{min_score}% quality across all dimensions"
            )
            click.echo(
                f"  • What passes: Weighted average of dimension scores ≥ {min_score}"
            )
            click.echo(f"  • What fails: Weighted average < {min_score}")
            click.echo("")

            # Readiness gate
            click.echo("Readiness Gate:")
            click.echo("  • Current: 80% of rows must fully pass")

            # Get required fields
            field_reqs = requirements.get("field_requirements", {}) or {}
            required_fields = [
                field_name
                for field_name, config in field_reqs.items()
                if not config.get("nullable", True)
            ]

            if required_fields:
                required_fields_str = ", ".join(required_fields[:5])
                if len(required_fields) > 5:
                    required_fields_str += f", ... ({len(required_fields)} total)"
                click.echo(f"  • Required fields: [{required_fields_str}]")
            else:
                click.echo(
                    "  • Required fields: (none specified - all fields optional)"
                )

            click.echo(
                "  • Meaning: At least 80% of rows must have ALL required fields valid"
            )
            click.echo("  • What's READY: ≥80% of rows pass all required checks")
            click.echo("  • What's READY WITH BLOCKERS: 40-79% of rows pass")
            click.echo("  • What's NOT READY: <40% of rows pass")
            click.echo("")

            # Guard mode
            click.echo("Guard Mode:")
            click.echo("  • Current: warn")
            click.echo("  • Meaning: Log issues but don't block execution")
            click.echo("  • Options: warn | block")
            click.echo("")

            # What-if scenarios
            click.echo("What-if scenarios:")
            click.echo("  • If min_score = 85: Would require higher average quality")
            click.echo(
                "  • If row_threshold = 0.9: Would require 90% of rows instead of 80%"
            )
            click.echo("  • If guard.mode = block: Would halt execution on failures")
            click.echo("")

            click.echo(
                "💡 Use 'adri what-if' to simulate changes without modifying the standard"
            )

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to explain thresholds: {e}")
            return 1

    def get_name(self) -> str:
        """Get the command name."""
        return "explain-thresholds"


class WhatIfCommand(Command):
    """Command for simulating threshold changes and their impact.

    Allows users to explore how changing thresholds would affect
    pass/fail status without modifying the actual standard.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Simulate threshold changes and show projected impact"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the what-if command.

        Args:
            args: Command arguments containing:
                - changes: List[str] - Threshold changes to simulate
                - standard_path: str - Path to standard file
                - data_path: str - Path to data file to assess

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        changes = args["changes"]
        standard_path = args["standard_path"]
        data_path = args["data_path"]

        return self._what_if(changes, standard_path, data_path)

    def _what_if(self, changes: list[str], standard_path: str, data_path: str) -> int:
        """Simulate threshold changes and show impact."""
        try:
            import yaml

            from ...validator.engine import DataQualityAssessor
            from ...validator.loaders import load_data

            # Load standard and data
            standard_file = Path(standard_path)
            if not standard_file.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                return 1

            data_file = Path(data_path)
            if not data_file.exists():
                click.echo(f"❌ Data file not found: {data_path}")
                return 1

            with open(standard_file, encoding="utf-8") as f:
                standard = yaml.safe_load(f)

            data_list = load_data(data_path)
            data = pd.DataFrame(data_list)

            # Run current assessment
            assessor = DataQualityAssessor({})
            current_result = assessor.assess(data, standard_path)

            # Get current configuration
            requirements = standard.get("requirements", {})
            current_min_score = int(requirements.get("overall_minimum", 75))
            current_row_threshold = 0.80
            total_rows = len(data)

            # Calculate current readiness
            current_passed_rows = self._calculate_passed_rows(data)
            current_readiness_pct = (
                (current_passed_rows / total_rows * 100) if total_rows > 0 else 0
            )

            click.echo("🔮 What-If Analysis")
            click.echo("==================")
            click.echo(f"Standard: {standard_path}")
            click.echo(f"Data: {data_path} ({total_rows} rows)")
            click.echo("")

            click.echo("Current Configuration:")
            click.echo(f"  • MIN_SCORE: {current_min_score}/100")
            click.echo(
                f"  • Row Threshold: {int(current_row_threshold * 100)}% ({int(total_rows * current_row_threshold)}/{total_rows} rows)"
            )

            current_health_status = (
                "✅ PASSED" if current_result.passed else "❌ FAILED"
            )
            current_readiness_status = self._get_readiness_status(current_readiness_pct)

            click.echo(
                f"  • Status: Health {current_health_status} ({current_result.overall_score:.1f}/100), Readiness {current_readiness_status} ({current_passed_rows}/{total_rows})"
            )
            click.echo("")

            # Parse proposed changes
            proposed_changes = {}
            for change in changes:
                if "=" not in change:
                    click.echo(f"⚠️  Skipping invalid change: {change}")
                    continue
                key, value = change.split("=", 1)
                proposed_changes[key] = self._parse_value(value)

            if not proposed_changes:
                click.echo("❌ No valid changes provided")
                return 1

            click.echo("Proposed Changes:")
            for key, value in proposed_changes.items():
                if key == "min_score":
                    click.echo(f"  • MIN_SCORE: {current_min_score} → {value}")
                elif key == "readiness.row_threshold":
                    new_threshold = float(value)
                    click.echo(
                        f"  • Row Threshold: {current_row_threshold} → {new_threshold} ({int(total_rows * new_threshold)}/{total_rows} rows required)"
                    )
            click.echo("")

            # Project results
            new_min_score = proposed_changes.get("min_score", current_min_score)
            new_row_threshold = float(
                proposed_changes.get("readiness.row_threshold", current_row_threshold)
            )

            new_health_passed = current_result.overall_score >= new_min_score
            new_health_status = "✅ PASSED" if new_health_passed else "❌ FAILED"

            new_readiness_pct = (
                current_readiness_pct  # Same data, percentage doesn't change
            )
            new_readiness_status = self._get_readiness_status(
                new_readiness_pct, new_row_threshold
            )

            click.echo("Projected Results:")
            click.echo(
                f"  • Health: {current_health_status} → {new_health_status} ({current_result.overall_score:.1f}/100 vs threshold {new_min_score})"
            )
            click.echo(
                f"  • Readiness: {current_readiness_status} → {new_readiness_status} ({current_passed_rows}/{total_rows}, need {int(total_rows * new_row_threshold)}/{total_rows})"
            )
            click.echo("")

            # Impact summary
            click.echo("Impact Summary:")

            if new_health_passed != current_result.passed:
                health_impact = (
                    "Would change from PASSED to FAILED"
                    if current_result.passed
                    else "Would change from FAILED to PASSED"
                )
                click.echo(f"  • Health threshold: {health_impact}")
            else:
                click.echo("  • Health threshold: No change in pass/fail")

            rows_needed = int(total_rows * new_row_threshold)
            if current_passed_rows < rows_needed:
                rows_to_fix = rows_needed - current_passed_rows
                click.echo(
                    f"  • Readiness: Would require {rows_to_fix} more row(s) to pass"
                )
            elif current_passed_rows >= rows_needed:
                click.echo("  • Readiness: Currently meets new threshold")

            click.echo(
                f"  • Recommendation: Fix {max(0, rows_needed - current_passed_rows)} more row(s) to meet new readiness gate"
            )
            click.echo("")

            click.echo("💡 Use 'adri config set' to apply these changes permanently")

            return 0

        except Exception as e:
            click.echo(f"❌ What-if analysis failed: {e}")
            return 1

    def _parse_value(self, value_str: str) -> Any:
        """Parse a configuration value."""
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"
        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str

    def _calculate_passed_rows(self, data: pd.DataFrame) -> int:
        """Calculate how many rows pass all checks."""
        # Simple heuristic: count rows with no missing required fields
        passed = 0
        for _, row in data.iterrows():
            has_issues = False

            # Check for missing values
            if row.isnull().any():
                has_issues = True

            # Check for negative amounts
            if "amount" in row and pd.notna(row["amount"]):
                try:
                    if float(row["amount"]) < 0:
                        has_issues = True
                except (ValueError, TypeError):
                    has_issues = True

            if not has_issues:
                passed += 1

        return passed

    def _get_readiness_status(
        self, readiness_pct: float, threshold: float = 0.80
    ) -> str:
        """Get readiness status string based on percentage."""
        required_pct = threshold * 100
        if readiness_pct >= required_pct:
            return "✅ READY"
        elif readiness_pct >= 40:
            return "⚠️  READY WITH BLOCKERS"
        else:
            return "❌ NOT READY"

    def get_name(self) -> str:
        """Get the command name."""
        return "what-if"
