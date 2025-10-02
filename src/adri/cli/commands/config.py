"""Configuration command implementation for ADRI CLI.

This module contains the ShowConfigCommand class that handles configuration
display and environment management.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ...core.protocols import Command


class ShowConfigCommand(Command):
    """Command for showing current ADRI configuration.

    Handles display of project configuration including environments,
    paths, and audit settings.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Show current ADRI configuration"

    def execute(self, args: Dict[str, Any]) -> int:
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
        self, paths_only: bool = False, environment: Optional[str] = None
    ) -> int:
        """Show current ADRI configuration."""
        try:
            from ...config.loader import ConfigurationLoader

            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()

            if not config:
                click.echo("❌ No ADRI configuration found")
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


class ValidateStandardCommand(Command):
    """Command for validating YAML standard files.

    Handles structural validation of ADRI standard files to ensure
    they conform to the expected schema.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Validate YAML standard file"

    def execute(self, args: Dict[str, Any]) -> int:
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
        """Validate YAML standard file (basic structural checks)."""
        try:
            from ...validator.loaders import load_standard

            standard = load_standard(standard_path)
            errors = []

            # Check for required top-level sections
            if "standards" not in standard or not isinstance(
                standard["standards"], dict
            ):
                errors.append("'standards' section missing or invalid")
            else:
                std_section = standard["standards"]
                # Check for required fields in standards section
                for field in ["id", "name", "version", "authority"]:
                    if not std_section.get(field):
                        errors.append(f"Missing required field in standards: '{field}'")

            if "requirements" not in standard or not isinstance(
                standard["requirements"], dict
            ):
                errors.append("'requirements' section missing or invalid")

            if errors:
                click.echo("❌ Standard validation FAILED")
                for error in errors:
                    click.echo(f"  • {error}")
                return 1

            # Display success with summary
            click.echo("✅ Standard validation PASSED")
            std_info = standard.get("standards", {})
            click.echo(f"📄 Name: {std_info.get('name', 'Unknown')}")
            click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
            click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")

            return 0

        except Exception as e:
            click.echo(f"❌ Validation failed: {e}")
            return 1

    def get_name(self) -> str:
        """Get the command name."""
        return "validate-standard"


class ListStandardsCommand(Command):
    """Command for listing available YAML standards.

    Handles discovery and display of local standards with optional
    remote catalog integration.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "List available YAML standards"

    def execute(self, args: Dict[str, Any]) -> int:
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
            dev_dir = Path("ADRI/dev/standards")
            prod_dir = Path("ADRI/prod/standards")

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
                    dev_dir = Path(dev_env["paths"]["standards"])
                    prod_dir = Path(prod_env["paths"]["standards"])
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

    def _list_yaml_files(self, dir_path: Path) -> List[Path]:
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


class ShowStandardCommand(Command):
    """Command for showing details of a specific ADRI standard.

    Handles display of standard metadata, requirements, and configuration
    with optional verbose output.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Show details of a specific ADRI standard"

    def execute(self, args: Dict[str, Any]) -> int:
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
            from ...validator.loaders import load_standard

            # Find the standard file
            standard_path = self._find_standard_file(standard_name)
            if not standard_path:
                click.echo(f"❌ Standard not found: {standard_name}")
                click.echo("💡 Use 'adri list-standards' to see available standards")
                return 1

            # Load and display standard
            standard = load_standard(standard_path)
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

    def _find_standard_file(self, standard_name: str) -> Optional[str]:
        """Find the standard file by name or path."""
        if os.path.exists(standard_name):
            return standard_name

        # Search in standard locations
        search_paths = [
            f"ADRI/dev/standards/{standard_name}.yaml",
            f"ADRI/prod/standards/{standard_name}.yaml",
            f"{standard_name}.yaml",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return None

    def _display_verbose_details(self, requirements: Dict[str, Any]) -> None:
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
