# @ADRI_FEATURE[cli_generate_contract, scope=OPEN_SOURCE, deps=[analysis_contract_generator]]
# Description: CLI command for auto-generating ADRI contracts from data analysis
"""Generate contract command implementation for ADRI CLI.

This module contains the GenerateContractCommand class that handles automatic
ADRI contract generation from data analysis.
"""

import sys
import time
from pathlib import Path
from typing import Any

import click
import pandas as pd
import yaml

from ...core.protocols import Command
from ...utils.path_utils import (
    get_project_root_display,
    rel_to_project_root,
    resolve_project_path,
)
from ...validator.loaders import load_data


def _progressive_echo(text: str, delay: float = 0.0) -> None:
    """Print text with optional delay for progressive output in guide mode.

    Args:
        text: Text to print
        delay: Delay in seconds after printing (only in interactive terminals)
    """
    click.echo(text)
    if delay > 0 and sys.stdout.isatty():
        time.sleep(delay)


class GenerateContractCommand(Command):
    """Command for generating ADRI standards from data analysis.

    Handles standard generation including data profiling, rule inference,
    lineage tracking, and output formatting.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Generate ADRI standard from data file analysis"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the generate-contract command.

        Args:
            args: Command arguments containing:
                - data_path: str - Path to data file to analyze
                - force: bool - Overwrite existing standard file
                - output: Optional[str] - Output path (ignored; uses config paths)
                - guide: bool - Show detailed generation explanation and next steps

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        data_path = args["data_path"]
        force = args.get("force", False)
        guide = args.get("guide", False)

        return self._generate_standard(data_path, force, guide)

    def _generate_standard(
        self, data_path: str, force: bool = False, guide: bool = False
    ) -> int:
        """Generate ADRI standard from data analysis."""
        try:
            # Validate input file
            resolved_data_path = resolve_project_path(data_path)
            if not resolved_data_path.exists():
                click.echo(f"❌ Generation failed: Data file not found: {data_path}")
                return 1

            # Load data
            data_list = load_data(str(resolved_data_path))
            if not data_list:
                click.echo("❌ No data loaded")
                return 1

            # Determine output path
            data_name = Path(data_path).stem
            standard_filename = f"{data_name}_ADRI_standard.yaml"
            output_path = self._determine_output_path(standard_filename)

            # Check for existing file
            if output_path.exists() and not force:
                click.echo(
                    f"❌ Standard exists: {output_path}. Use --force to overwrite."
                )
                return 1

            # Display guide intro if requested
            if guide:
                self._display_generation_intro(resolved_data_path)

            # Convert to DataFrame
            data = pd.DataFrame(data_list)

            # Create training snapshot
            snapshot_path = self._create_training_snapshot(str(resolved_data_path))
            if guide:
                self._display_snapshot_status(snapshot_path)

            # Generate standard
            std_dict = self._generate_standard_dict(data, data_name)

            # Add lineage metadata
            lineage_metadata = self._create_lineage_metadata(
                str(resolved_data_path), snapshot_path
            )
            std_dict["training_data_lineage"] = lineage_metadata

            # Add generation metadata
            self._add_generation_metadata(std_dict, data_name)

            # Save standard
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(std_dict, f, default_flow_style=False, sort_keys=False)

            # Display results
            if guide:
                self._display_generation_success_guide(
                    std_dict, standard_filename, output_path, data_path
                )
            else:
                self._display_generation_success_simple(standard_filename, output_path)

            return 0

        except Exception as e:
            click.echo(f"❌ Generation failed: {e}")
            return 1

    def _determine_output_path(self, standard_filename: str) -> Path:
        """Determine where to save the generated standard."""
        from ...config.loader import ConfigurationLoader

        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                standards_dir = Path(env_config["paths"]["contracts"])
                standards_dir.mkdir(parents=True, exist_ok=True)
                return standards_dir / standard_filename
        except Exception:
            pass

        # Fallback to default dev path
        default_dir = Path("ADRI/dev/contracts")
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir / standard_filename

    def _display_generation_intro(self, resolved_data_path: Path) -> None:
        """Display generation introduction for guide mode."""
        click.echo("📊 Generating ADRI Standard from Data Analysis")
        click.echo("=============================================")
        click.echo("")
        click.echo(get_project_root_display())
        click.echo(f"📄 Analyzing: {rel_to_project_root(resolved_data_path)}")
        click.echo("📋 Creating data quality rules based on your good data...")
        click.echo("🔍 Creating training data snapshot for lineage tracking...")

    def _create_training_snapshot(self, data_path: str) -> str | None:
        """Create a training data snapshot for lineage tracking."""
        try:
            source_file = Path(data_path)
            if not source_file.exists():
                return None

            file_hash = self._generate_file_hash(source_file)

            # Determine training data directory
            training_data_dir = self._get_training_data_directory()
            training_data_dir.mkdir(parents=True, exist_ok=True)

            snapshot_filename = f"{source_file.stem}_{file_hash}.csv"
            snapshot_path = training_data_dir / snapshot_filename

            import shutil

            shutil.copy2(source_file, snapshot_path)
            return str(snapshot_path)

        except Exception:
            return None

    def _get_training_data_directory(self) -> Path:
        """Get the training data directory from configuration."""
        from ...config.loader import ConfigurationLoader

        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                return Path(env_config["paths"]["training_data"])
        except Exception:
            pass

        return Path("ADRI/dev/training-data")

    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate SHA256 hash for a file."""
        import hashlib

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:8]

    def _display_snapshot_status(self, snapshot_path: str | None) -> None:
        """Display training snapshot creation status."""
        if snapshot_path:
            click.echo(f"✅ Training snapshot created: {Path(snapshot_path).name}")
        else:
            click.echo("⚠️  Training snapshot creation skipped")
        click.echo("")

    def _generate_standard_dict(
        self, data: pd.DataFrame, data_name: str
    ) -> dict[str, Any]:
        """Generate the standard dictionary using StandardGenerator."""
        from ...analysis.contract_generator import ContractGenerator

        generator = ContractGenerator()
        return generator.generate(data, data_name, generation_config=None)

    def _create_lineage_metadata(
        self, data_path: str, snapshot_path: str | None = None
    ) -> dict[str, Any]:
        """Create lineage metadata for the generated standard."""
        from datetime import datetime

        source_file = Path(data_path)
        metadata: dict[str, Any] = {
            "source_path": str(source_file.resolve()),
            "timestamp": datetime.now().isoformat(),
            "file_hash": (
                self._generate_file_hash(source_file) if source_file.exists() else None
            ),
        }

        if snapshot_path and Path(snapshot_path).exists():
            snapshot_file = Path(snapshot_path)
            metadata.update(
                {
                    "snapshot_path": str(snapshot_file.resolve()),
                    "snapshot_hash": self._generate_file_hash(snapshot_file),
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

    def _add_generation_metadata(
        self, std_dict: dict[str, Any], data_name: str
    ) -> None:
        """Add generation metadata to the standard dictionary."""
        from datetime import datetime

        current_timestamp = datetime.now().isoformat()
        base_metadata = {
            "created_by": "ADRI Framework",
            "created_date": current_timestamp,
            "last_modified": current_timestamp,
            "generation_method": "auto_generated",
            "tags": ["data_quality", "auto_generated", f"{data_name}_data"],
        }

        existing_meta = std_dict.get("metadata", {}) or {}
        std_dict["metadata"] = {**base_metadata, **existing_meta}

    def _display_generation_success_guide(
        self,
        std_dict: dict[str, Any],
        standard_filename: str,
        output_path: Path,
        data_path: str,
    ) -> None:
        """Display detailed success message for guide mode."""
        _progressive_echo("📊 Step 2 of 4: Generate ADRI Standard", 0.4)
        _progressive_echo("======================================", 0.0)
        _progressive_echo("", 0.0)

        _progressive_echo("✅ Standard created successfully!", 0.0)
        try:
            std_name = std_dict["standards"]["name"]
        except Exception:
            std_name = standard_filename

        _progressive_echo(f"📄 Name: {std_name}", 0.0)
        _progressive_echo(f"📁 Saved to: {rel_to_project_root(output_path)}", 0.0)

        # Display snapshot info if available
        lineage = std_dict.get("training_data_lineage", {})
        if lineage and lineage.get("snapshot_filename"):
            _progressive_echo(
                f"📦 Snapshot: {lineage['snapshot_filename']}  (for lineage tracking)",
                0.5,
            )
        else:
            _progressive_echo("", 0.5)

        _progressive_echo("", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("📘 What this step does", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo(
            'ADRI analyzed your good dataset and built a "standard" —', 0.0
        )
        _progressive_echo(
            "a simple contract defining what *good enough data* looks like.", 0.0
        )
        _progressive_echo("", 0.0)
        _progressive_echo("It includes:", 0.0)
        _progressive_echo("  • Required fields and allowed values", 0.0)
        _progressive_echo("  • Five quality dimensions:", 0.0)
        _progressive_echo(
            "      validity, completeness, consistency, freshness, plausibility", 0.0
        )
        _progressive_echo("And defines two checks for your agent's data supply:", 0.0)
        _progressive_echo(
            "  1️⃣  System Health → MIN_SCORE (overall dataset quality)", 0.0
        )
        _progressive_echo(
            "  2️⃣  Batch Readiness → GATE (rows that fully pass all rules)", 0.6
        )
        _progressive_echo("", 0.0)

        # Extract controls from standard
        controls = self._extract_controls_preview(std_dict)

        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("📈 Defaults learned from this dataset", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo(
            f"  • MIN_SCORE:      {controls['min_score']}/100   → Health passes if ≥ {controls['min_score']}",
            0.0,
        )
        _progressive_echo(
            f"  • READINESS.GATE: {controls['row_threshold']:.2f}     → {int(controls['row_threshold'] * 100)}% of rows must fully pass",
            0.0,
        )
        _progressive_echo(f"  • Guard mode:     {controls['guard_mode']}", 0.0)

        required_fields_str = ", ".join(controls["required_fields"])
        _progressive_echo(f"  • Required fields: [{required_fields_str}]", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("💡 Why this step", 0.0)
        _progressive_echo(
            '   You\'ve now defined what "good data" means for your agent.', 0.0
        )
        _progressive_echo(
            "   Every future dataset will be compared to this standard.", 0.6
        )
        _progressive_echo("", 0.0)

        # Display YAML controls preview
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("📄 Snapshot of the standard (key controls only)", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo(f"# Path: {rel_to_project_root(output_path)}", 0.0)
        _progressive_echo(
            f"# (preview — view full file with: less {rel_to_project_root(output_path)})",
            0.0,
        )
        _progressive_echo("", 0.0)
        _progressive_echo(self._format_yaml_controls(controls), 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)

        # Next step guidance
        _progressive_echo("▶ Next step (takes seconds)", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Run your first data quality check:", 0.0)
        _progressive_echo("", 0.0)
        if "invoice_data" in data_path:
            _progressive_echo(
                "   adri assess tutorials/invoice_processing/test_invoice_data.csv \\",
                0.0,
            )
            _progressive_echo(
                "        --standard dev/standards/invoice_data_ADRI_standard.yaml --guide",
                0.0,
            )
        else:
            _progressive_echo("   adri assess your_test_data.csv \\", 0.0)
            _progressive_echo(
                f"        --standard {rel_to_project_root(output_path)} --guide",  # noqa: E221
                0.0,
            )
        _progressive_echo("", 0.0)
        _progressive_echo("Why do this:", 0.0)
        _progressive_echo(
            "   This tests real-world data against your new standard and shows:", 0.0
        )
        _progressive_echo(
            f"     • System Health — overall dataset quality (vs MIN_SCORE {controls['min_score']})",
            0.0,
        )
        _progressive_echo(
            "     • Batch Readiness — which rows are agent-safe right now", 0.0
        )
        _progressive_echo("─" * 58, 0.0)

    def _extract_controls_preview(self, std_dict: dict[str, Any]) -> dict[str, Any]:
        """Extract control values from standard for display."""
        controls = {
            "min_score": 75,
            "row_threshold": 0.80,
            "guard_mode": "warn",
            "required_fields": [],
        }

        try:
            # Get min_score from requirements
            req = std_dict.get("requirements", {})
            controls["min_score"] = int(req.get("overall_minimum", 75))

            # Get required fields from field_requirements
            field_reqs = req.get("field_requirements", {}) or {}
            controls["required_fields"] = [
                field_name
                for field_name, config in field_reqs.items()
                if not config.get("nullable", True)
            ][
                :3
            ]  # Limit to first 3 for display

            # If no required fields found, use first 3 fields
            if not controls["required_fields"]:
                controls["required_fields"] = list(field_reqs.keys())[:3]

        except Exception:
            pass

        return controls

    def _format_yaml_controls(self, controls: dict[str, Any]) -> str:
        """Format controls as YAML preview."""
        weights_section = """weights:
  validity: 0.35
  completeness: 0.20
  consistency: 0.20
  freshness: 0.15
  plausibility: 0.10"""

        required_fields_yaml = ", ".join(controls["required_fields"])

        yaml_preview = f"""controls:
  min_score: {controls['min_score']}            # dataset-level pass/fail for health
  readiness:
    row_threshold: {controls['row_threshold']:.2f}    # % of rows that must fully pass for \"READY\"
    required_fields: [{required_fields_yaml}]
  guard:
    mode: {controls['guard_mode']}             # warn | block
{weights_section}"""

        return yaml_preview

    def _display_generation_success_simple(
        self, standard_filename: str, output_path: Path
    ) -> None:
        """Display simple success message for non-guide mode."""
        click.echo("✅ Standard generated successfully!")
        click.echo(f"📄 Standard: {standard_filename}")
        click.echo(f"📁 Saved to: {output_path}")

    def get_name(self) -> str:
        """Get the command name."""
        return "generate-contract"


# @ADRI_FEATURE_END[cli_generate_contract]
