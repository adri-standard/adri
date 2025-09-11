#!/usr/bin/env python3
"""
ADRI Validator Version Tracking Updater.

This script automatically updates the version tracking files when a new release is made.
It updates both JSON and Markdown formats for cross-repository coordination.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class VersionTracker:
    """Manages version tracking for ADRI Validator releases."""

    def __init__(self, validator_repo_path: str, output_dir: str = None):
        """Initialize the version tracker with repository path and output directory."""
        self.validator_repo = Path(validator_repo_path)
        self.output_dir = Path(output_dir) if output_dir else self.validator_repo / "release-tracking"

        # File paths
        self.json_file = self.output_dir / "ADRI_VALIDATOR_RELEASES.json"
        self.md_file = self.output_dir / "ADRI-Validator-Releases.md"
        self.pyproject_file = self.validator_repo / "pyproject.toml"

        # Validate and create directories if needed
        self._validate_and_setup()

    def _validate_and_setup(self) -> None:
        """Validate repository path and create necessary directories."""
        # Check validator repo exists
        if not self.validator_repo.exists():
            raise FileNotFoundError(
                f"Validator repository not found: {self.validator_repo}"
            )

        # Create output directory if missing
        if not self.output_dir.exists():
            print(f"🔧 Creating output directory: {self.output_dir}")
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check pyproject.toml exists
        if not self.pyproject_file.exists():
            raise FileNotFoundError(f"pyproject.toml not found: {self.pyproject_file}")

        print(f"✅ Validator repo: {self.validator_repo}")
        print(f"✅ Output directory: {self.output_dir}")

    def get_current_version(self) -> str:
        """Extract current version from pyproject.toml."""
        if not self.pyproject_file.exists():
            raise FileNotFoundError(
                f"pyproject.toml not found at {self.pyproject_file}"
            )

        content = self.pyproject_file.read_text()
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if not version_match:
            raise ValueError("Version not found in pyproject.toml")

        return version_match.group(1)

    def load_release_data(self) -> Dict[str, Any]:
        """Load existing release data from JSON file."""
        if self.json_file.exists():
            return json.loads(self.json_file.read_text())
        else:
            # Create initial structure
            return {
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                    "format_version": "1.0.0",
                    "description": "ADRI Validator release tracking for self-contained deployment",
                },
                "current_release": {},
                "releases": [],
                "installation_guide": {
                    "latest_stable": "pip install adri",
                    "specific_version": "pip install adri==VERSION",
                    "with_standards": "pip install adri-standards adri",
                    "development": "pip install adri[dev]",
                },
            }

    def add_new_release(
        self,
        version: str,
        release_type: str,
        description: List[str],
        breaking_changes: List[str] = None,
    ) -> None:
        """Add a new release to the tracking system."""
        # Load existing data
        data = self.load_release_data()

        # Mark all existing releases as not latest
        for release in data["releases"]:
            release["is_latest"] = False

        # Create new release entry
        new_release = {
            "package_name": "adri-validator",
            "version": version,
            "release_type": release_type,
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "is_latest": True,
            "description": description,
            "breaking_changes": breaking_changes or [],
            "dependencies": {
                "pandas": ">=1.5.0",
                "pyyaml": ">=6.0",
                "click": ">=8.0",
                "python": ">=3.8",
            },
            "compatibility": {
                "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"],
                "platforms": ["linux", "macos", "windows"],
            },
        }

        # Add to releases list (newest first)
        data["releases"].insert(0, new_release)

        # Update current release
        data["current_release"] = {
            "package_name": "adri-validator",
            "version": version,
            "release_type": release_type,
            "release_date": new_release["release_date"],
            "is_latest": True,
            "pypi_url": "https://pypi.org/project/adri/",
            "github_url": "https://github.com/adri-standard/adri",
            "installation": f"pip install adri=={version}",
        }

        # Update metadata
        data["metadata"]["last_updated"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        # Update installation guide
        data["installation_guide"]["specific_version"] = f"pip install adri=={version}"
        data["installation_guide"]["with_standards"] = "pip install adri"  # Self-contained now

        # Save JSON file
        self.json_file.write_text(json.dumps(data, indent=2))

        # Update markdown file
        self._update_markdown_file(data)

    def _update_markdown_file(self, data: Dict[str, Any]) -> None:
        """Update the markdown release file."""
        # Generate table rows
        table_rows = []
        for release in data["releases"]:
            latest_mark = "✅" if release["is_latest"] else ""
            description_bullets = "<br>".join(
                [f"• {desc}" for desc in release["description"]]
            )

            row = f"| {release['package_name']} | {release['release_type']} | {release['version']} | {release['release_date']} | {latest_mark} | {description_bullets} |"
            table_rows.append(row)

        # Read current markdown file
        if self.md_file.exists():
            content = self.md_file.read_text()
        else:
            content = self._get_markdown_template()

        # Update the table
        table_header = "| Package Name | Release Type | Version | Release Date | Latest | Description |\n|--------------|--------------|---------|--------------|--------|-------------|"
        table_content = "\n".join(table_rows)

        # Replace the table in the markdown
        table_pattern = r"(\| Package Name \| Release Type \| Version \| Release Date \| Latest \| Description \|\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|)(.*?)(\n\n## Installation)"

        new_table = f"{table_header}\n{table_content}"

        if re.search(table_pattern, content, re.DOTALL):
            content = re.sub(
                table_pattern, f"\\1\n{table_content}\\3", content, flags=re.DOTALL
            )
        else:
            # If pattern not found, replace the whole table section
            content = re.sub(
                r"## Release History\n\n.*?\n\n## Installation",
                f"## Release History\n\n{new_table}\n\n## Installation",
                content,
                flags=re.DOTALL,
            )

        # Update installation commands
        current_version = data["current_release"]["version"]
        content = re.sub(
            r"pip install adri==[\d.]+", f"pip install adri=={current_version}", content
        )

        self.md_file.write_text(content)

    def _get_markdown_template(self) -> str:
        """Get the markdown template for new files."""
        return """# ADRI Validator Releases

This document tracks all releases of the ADRI Validator package. The ADRI Validator provides the implementation layer for ADRI Standards, including decorators, CLI tools, and validation engines.

## Release History

| Package Name | Release Type | Version | Release Date | Latest | Description |
|--------------|--------------|---------|--------------|--------|-------------|

## Installation

### Latest Release
```bash
pip install adri==VERSION
```

### Latest (Auto-detect version)
```bash
pip install adri
```

### With Bundled Standards (Self-contained)
```bash
pip install adri
```

### Development Version
```bash
pip install adri[dev]
```

## Quick Start

```python
from adri.decorators.guard import adri_protected

@adri_protected(data_param="customer_data")
def process_customers(customer_data):
    # Your processing logic here
    return processed_data
```

## Documentation

- **[ADRI README](https://github.com/adri-standard/adri/blob/main/README.md)** - Complete package documentation
- **[Bundled Standards](https://github.com/adri-standard/adri/tree/main/adri/standards/bundled)** - Self-contained standards library
- **[Getting Started Guide](https://github.com/adri-standard/adri/blob/main/QUICK_START.md)** - Quick setup tutorial

---

*This file is automatically maintained by the ADRI Validator publishing process.*
"""


def main():
    """Run the main function for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update ADRI Validator version tracking"
    )
    parser.add_argument(
        "--validator-repo", default=".", help="Path to ADRI Validator repository"
    )
    parser.add_argument(
        "--output-dir", help="Output directory for tracking files (default: ./release-tracking)"
    )
    parser.add_argument(
        "--release-type", default="Beta", help="Release type (Beta, Stable, RC, etc.)"
    )
    parser.add_argument("--description", nargs="+", help="Release description points")
    parser.add_argument(
        "--breaking-changes", nargs="*", help="Breaking changes (if any)"
    )

    args = parser.parse_args()

    tracker = VersionTracker(args.validator_repo, args.output_dir)

    # Get current version from pyproject.toml
    try:
        current_version = tracker.get_current_version()
        print(f"Detected version: {current_version}")

        # Default description if none provided
        if not args.description:
            description = [
                "Production-ready CI/CD pipeline",
                "91% test coverage with comprehensive test suite",
                "@adri_protected decorator with variants",
                "Complete CLI workflow (setup, assess, generate)",
                "Data quality assessment engine",
                "Configuration management system",
                "Analysis tools (profiler, generator)",
                "Full integration with adri-standards",
            ]
        else:
            description = args.description

        # Add new release
        tracker.add_new_release(
            version=current_version,
            release_type=args.release_type,
            description=description,
            breaking_changes=args.breaking_changes,
        )

        print(f"✅ Updated version tracking files for v{current_version}")
        print(f"📄 JSON: {tracker.json_file}")
        print(f"📄 Markdown: {tracker.md_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
