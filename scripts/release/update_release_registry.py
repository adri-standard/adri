#!/usr/bin/env python3
"""
ADRI Validator Release Registry Updater

Updates the ADRI-Validator-Releases.md file in the adri-standards package
as part of the publishing process.

Usage:
    python scripts/update_release_registry.py --version 1.0.0 --type stable --description "Initial release"
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReleaseRegistryUpdater:
    def __init__(self, standards_path: Optional[Path] = None):
        """Initialize the release registry updater."""
        self.validator_dir = Path(__file__).parent.parent

        # Try to find adri-standards directory
        if standards_path:
            self.standards_dir = standards_path
        else:
            # Look for adri-standards in parent directory
            self.standards_dir = self.validator_dir.parent / "adri-standards"

        self.release_file = self.standards_dir / "ADRI-Validator-Releases.md"

    def validate_setup(self) -> bool:
        """Validate that we can access the required files."""
        if not self.standards_dir.exists():
            print(f"❌ ADRI Standards directory not found: {self.standards_dir}")
            return False

        if not self.release_file.exists():
            print(f"❌ Release file not found: {self.release_file}")
            return False

        print(f"✅ Found ADRI Standards at: {self.standards_dir}")
        print(f"✅ Found release file at: {self.release_file}")
        return True

    def get_current_version(self) -> str:
        """Get current version from version.py."""
        version_file = self.validator_dir / "adri" / "version.py"
        if not version_file.exists():
            raise FileNotFoundError(f"Version file not found: {version_file}")

        version_content = version_file.read_text()
        exec(version_content)
        return locals().get("__version__", "0.0.0")

    def parse_release_table(self, content: str) -> List[Dict]:
        """Parse the existing release table."""
        releases = []

        # Find the table section
        lines = content.split("\n")
        in_table = False

        for line in lines:
            if "| Package Name |" in line:
                in_table = True
                continue
            elif in_table and line.startswith("|") and "---" not in line:
                # Parse table row
                parts = [part.strip() for part in line.split("|")[1:-1]]
                if len(parts) >= 6:
                    releases.append(
                        {
                            "package": parts[0],
                            "type": parts[1],
                            "version": parts[2],
                            "date": parts[3],
                            "latest": parts[4],
                            "description": parts[5],
                        }
                    )
            elif in_table and not line.startswith("|"):
                break

        return releases

    def format_description(self, description: str) -> str:
        """Format description with bullet points."""
        if not description.startswith("•"):
            # Split on common delimiters and add bullet points
            items = []
            for item in description.split(","):
                item = item.strip()
                if item:
                    items.append(f"• {item}")
            return "<br>".join(items)
        return description

    def update_release_file(
        self, version: str, release_type: str, description: str, dry_run: bool = False
    ) -> bool:
        """Update the release file with new version."""
        if not self.release_file.exists():
            print(f"❌ Release file not found: {self.release_file}")
            return False

        # Read current content
        content = self.release_file.read_text()

        # Parse existing releases
        releases = self.parse_release_table(content)

        # Mark all existing releases as not latest
        for release in releases:
            release["latest"] = "❌"

        # Add new release
        new_release = {
            "package": "adri-validator",
            "type": release_type.title(),
            "version": version,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "latest": "✅",
            "description": self.format_description(description),
        }

        # Insert new release at the beginning
        releases.insert(0, new_release)

        # Rebuild the table
        table_lines = [
            "| Package Name | Release Type | Version | Release Date | Latest | Description |",
            "|--------------|--------------|---------|--------------|--------|-------------|",
        ]

        for release in releases:
            line = f"| {release['package']} | {release['type']} | {release['version']} | {release['date']} | {release['latest']} | {release['description']} |"
            table_lines.append(line)

        # Replace the table in the content
        lines = content.split("\n")
        new_lines = []
        in_table = False
        table_replaced = False

        for line in lines:
            if "| Package Name |" in line and not table_replaced:
                # Start of table - replace with new table
                new_lines.extend(table_lines)
                in_table = True
                table_replaced = True
            elif in_table and (not line.startswith("|") or line.strip() == ""):
                # End of table
                in_table = False
                new_lines.append(line)
            elif not in_table:
                new_lines.append(line)

        new_content = "\n".join(new_lines)

        if dry_run:
            print("🔍 Dry run - would update release file with:")
            print(f"   Version: {version}")
            print(f"   Type: {release_type}")
            print(f"   Date: {new_release['date']}")
            print(f"   Description: {description}")
            return True
        else:
            # Write updated content
            self.release_file.write_text(new_content)
            print(f"✅ Updated release file: {self.release_file}")
            print(f"   Added version {version} as latest {release_type} release")
            return True

    def add_release_notes_section(
        self, version: str, description: str, dry_run: bool = False
    ) -> bool:
        """Add detailed release notes section."""
        if not self.release_file.exists():
            return False

        content = self.release_file.read_text()

        # Create release notes section
        version_header = f"### v{version} ({datetime.now().strftime('%Y-%m-%d')})"

        # Find where to insert (after existing release notes)
        lines = content.split("\n")
        insert_index = -1

        for i, line in enumerate(lines):
            if line.startswith("### v") and "Release Notes" not in line:
                insert_index = i
                break

        if insert_index == -1:
            # Find "## Release Notes" section
            for i, line in enumerate(lines):
                if line.startswith("## Release Notes"):
                    insert_index = i + 2  # After the header and empty line
                    break

        if insert_index != -1:
            # Insert new release notes
            new_lines = lines[:insert_index]
            new_lines.extend(
                [
                    version_header,
                    "",
                    f"**Release Type**: {description}",
                    "",
                    "**Key Features**:",
                    "- Enhanced stability and performance",
                    "- Updated documentation",
                    "- Bug fixes and improvements",
                    "",
                    "",
                ]
            )
            new_lines.extend(lines[insert_index:])

            new_content = "\n".join(new_lines)

            if not dry_run:
                self.release_file.write_text(new_content)
                print(f"✅ Added release notes section for v{version}")
            else:
                print(f"🔍 Would add release notes section for v{version}")

            return True

        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update ADRI Validator release registry"
    )
    parser.add_argument("--version", help="Version number (e.g., 1.0.0)")
    parser.add_argument(
        "--type",
        choices=["stable", "beta", "alpha", "rc"],
        default="stable",
        help="Release type",
    )
    parser.add_argument("--description", help="Release description")
    parser.add_argument(
        "--standards-path", type=Path, help="Path to adri-standards directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--auto", action="store_true", help="Auto-detect version from version.py"
    )

    args = parser.parse_args()

    # Initialize updater
    updater = ReleaseRegistryUpdater(args.standards_path)

    # Validate setup
    if not updater.validate_setup():
        sys.exit(1)

    # Get version
    if args.auto or not args.version:
        try:
            version = updater.get_current_version()
            print(f"📋 Auto-detected version: {version}")
        except Exception as e:
            print(f"❌ Could not auto-detect version: {e}")
            sys.exit(1)
    else:
        version = args.version

    # Get description
    description = (
        args.description
        or f"{args.type.title()} release with latest features and improvements"
    )

    print(f"\n🚀 Updating ADRI Validator Release Registry")
    print(f"   Version: {version}")
    print(f"   Type: {args.type}")
    print(f"   Description: {description}")
    print(f"   Dry run: {args.dry_run}")
    print()

    # Update release file
    success = updater.update_release_file(version, args.type, description, args.dry_run)

    if success and not args.dry_run:
        print(f"\n✅ Release registry updated successfully!")
        print(f"📁 File: {updater.release_file}")
        print(f"🔗 Users can now see version {version} in the release history")
    elif success and args.dry_run:
        print(f"\n🔍 Dry run completed - no changes made")
    else:
        print(f"\n❌ Failed to update release registry")
        sys.exit(1)


if __name__ == "__main__":
    main()
