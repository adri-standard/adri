"""Generate standard command implementation for ADRI CLI.

This module contains the GenerateStandardCommand class that handles automatic
ADRI standard generation from data analysis.
"""

from pathlib import Path
from typing import Any, Dict, Optional

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


class GenerateStandardCommand(Command):
    """Command for generating ADRI standards from data analysis.

    Handles standard generation including data profiling, rule inference,
    lineage tracking, and output formatting.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Generate ADRI standard from data file analysis"

    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the generate-standard command.

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
            with open(output_path, "w") as f:
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
                standards_dir = Path(env_config["paths"]["standards"])
                standards_dir.mkdir(parents=True, exist_ok=True)
                return standards_dir / standard_filename
        except Exception:
            pass

        # Fallback to default dev path
        default_dir = Path("ADRI/dev/standards")
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

    def _create_training_snapshot(self, data_path: str) -> Optional[str]:
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

    def _display_snapshot_status(self, snapshot_path: Optional[str]) -> None:
        """Display training snapshot creation status."""
        if snapshot_path:
            click.echo(f"✅ Training snapshot created: {Path(snapshot_path).name}")
        else:
            click.echo("⚠️  Training snapshot creation skipped")
        click.echo("")

    def _generate_standard_dict(
        self, data: pd.DataFrame, data_name: str
    ) -> Dict[str, Any]:
        """Generate the standard dictionary using StandardGenerator."""
        from ...analysis.standard_generator import StandardGenerator

        generator = StandardGenerator()
        return generator.generate(data, data_name, generation_config=None)

    def _create_lineage_metadata(
        self, data_path: str, snapshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create lineage metadata for the generated standard."""
        from datetime import datetime

        source_file = Path(data_path)
        metadata: Dict[str, Any] = {
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
        self, std_dict: Dict[str, Any], data_name: str
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
        std_dict: Dict[str, Any],
        standard_filename: str,
        output_path: Path,
        data_path: str,
    ) -> None:
        """Display detailed success message for guide mode."""
        click.echo("✅ Standard Generated Successfully!")
        click.echo("==================================")

        try:
            std_name = std_dict["standards"]["name"]
        except Exception:
            std_name = standard_filename

        click.echo(f"📄 Standard: {std_name}")
        click.echo(f"📁 Saved to: {rel_to_project_root(output_path)}")
        click.echo("")

        click.echo("📋 What the standard contains:")
        try:
            field_reqs = (
                std_dict.get("requirements", {}).get("field_requirements", {}) or {}
            )
            click.echo(f"   • {len(field_reqs)} field requirements")
        except Exception:
            click.echo("   • Field requirements summary unavailable")

        click.echo(
            "   • 5 quality dimensions (validity, completeness, consistency, freshness, plausibility)"
        )
        click.echo("   • Overall minimum score: 75.0/100")
        click.echo("")

        # Generate next command suggestion
        next_cmd = (
            "adri assess tutorials/invoice_processing/test_invoice_data.csv --standard dev/standards/invoice_data_ADRI_standard.yaml --guide"
            if "invoice_data" in data_path
            else f"adri assess your_test_data.csv --standard {rel_to_project_root(output_path)} --guide"
        )
        click.echo(f"▶ Next: {next_cmd}")

    def _display_generation_success_simple(
        self, standard_filename: str, output_path: Path
    ) -> None:
        """Display simple success message for non-guide mode."""
        click.echo("✅ Standard generated successfully!")
        click.echo(f"📄 Standard: {standard_filename}")
        click.echo(f"📁 Saved to: {output_path}")

    def get_name(self) -> str:
        """Get the command name."""
        return "generate-standard"
