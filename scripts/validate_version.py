#!/usr/bin/env python3
"""
Version validation script for ADRI Validator releases.

This script validates release tags and manages version progression according to
semantic versioning rules and our custom tag format.

Tag Format: <Release Type>.<Change Type>.v<Version>
Examples:
- Release.Minor.v0.3.0
- Pre-release.Patch.v0.2.1-beta.1
- Release.Major.v1.0.0
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class VersionValidationError(Exception):
    """Custom exception for version validation errors."""

    pass


class VersionValidator:
    """Validates and manages ADRI Validator version releases."""

    def __init__(self, version_file: str = "VERSION.json"):
        """Initialize validator with version tracking file."""
        # If running from scripts directory, look in parent directory
        if not Path(version_file).exists() and Path("../VERSION.json").exists():
            version_file = "../VERSION.json"
        self.version_file = Path(version_file)
        self.version_data = self._load_version_data()

    def _load_version_data(self) -> Dict:
        """Load version data from JSON file."""
        if not self.version_file.exists():
            raise VersionValidationError(f"Version file not found: {self.version_file}")

        try:
            with open(self.version_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise VersionValidationError(f"Invalid JSON in version file: {e}")

    def _save_version_data(self) -> None:
        """Save version data back to JSON file."""
        self.version_data["metadata"]["last_updated"] = (
            datetime.utcnow().isoformat() + "Z"
        )

        with open(self.version_file, "w") as f:
            json.dump(self.version_data, f, indent=2)

    def parse_tag(self, tag: str) -> Tuple[str, str, str]:
        """
        Parse release tag into components.

        Args:
            tag: Release tag (e.g., "Release.Minor.v0.3.0")

        Returns:
            Tuple of (release_type, change_type, version)

        Raises:
            VersionValidationError: If tag format is invalid
        """
        # Expected format: <Release Type>.<Change Type>.v<Version>
        pattern = r"^(Release|Pre-release)\.(Patch|Minor|Major)\.v(.+)$"
        match = re.match(pattern, tag)

        if not match:
            raise VersionValidationError(
                f"Invalid tag format: '{tag}'\n"
                f"Expected format: <Release Type>.<Change Type>.v<Version>\n"
                f"Examples:\n"
                f"  - Release.Minor.v0.3.0\n"
                f"  - Pre-release.Patch.v0.2.1-beta.1\n"
                f"  - Release.Major.v1.0.0"
            )

        release_type, change_type, version = match.groups()

        # Validate release type
        valid_release_types = self.version_data["validation_rules"]["release_types"]
        if release_type not in valid_release_types:
            raise VersionValidationError(
                f"Invalid release type: '{release_type}'\n"
                f"Valid types: {', '.join(valid_release_types)}"
            )

        # Validate change type
        valid_change_types = self.version_data["validation_rules"]["change_types"]
        if change_type not in valid_change_types:
            raise VersionValidationError(
                f"Invalid change type: '{change_type}'\n"
                f"Valid types: {', '.join(valid_change_types)}"
            )

        return release_type, change_type, version

    def parse_version(self, version: str) -> Tuple[int, int, int, Optional[str]]:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "0.3.0" or "0.3.0-beta.1")

        Returns:
            Tuple of (major, minor, patch, prerelease)

        Raises:
            VersionValidationError: If version format is invalid
        """
        # Pattern for semantic versioning with optional pre-release
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$"
        match = re.match(pattern, version)

        if not match:
            raise VersionValidationError(
                f"Invalid version format: '{version}'\n"
                f"Expected semantic versioning: X.Y.Z or X.Y.Z-prerelease\n"
                f"Examples: 0.3.0, 1.0.0, 0.3.0-beta.1, 1.0.0-rc.1"
            )

        major, minor, patch, prerelease = match.groups()
        return int(major), int(minor), int(patch), prerelease

    def validate_version_increment(
        self, current_version: str, new_version: str, change_type: str
    ) -> None:
        """
        Validate that new version is a proper increment of current version.

        Args:
            current_version: Current version (e.g., "0.2.0")
            new_version: New version (e.g., "0.3.0")
            change_type: Type of change ("Patch", "Minor", "Major")

        Raises:
            VersionValidationError: If increment is invalid
        """
        if not current_version:
            # No current version, allow any valid version
            return

        curr_major, curr_minor, curr_patch, _ = self.parse_version(current_version)
        new_major, new_minor, new_patch, new_prerelease = self.parse_version(
            new_version
        )

        # Check increment logic based on change type
        if change_type == "Patch":
            expected_version = f"{curr_major}.{curr_minor}.{curr_patch + 1}"
            if (
                new_major != curr_major
                or new_minor != curr_minor
                or new_patch != curr_patch + 1
            ):
                raise VersionValidationError(
                    f"Invalid patch increment: {current_version} → {new_version}\n"
                    f"Expected: {expected_version} (or {expected_version}-prerelease)\n"
                    f"Patch releases should only increment the patch number"
                )

        elif change_type == "Minor":
            expected_version = f"{curr_major}.{curr_minor + 1}.0"
            if new_major != curr_major or new_minor != curr_minor + 1 or new_patch != 0:
                raise VersionValidationError(
                    f"Invalid minor increment: {current_version} → {new_version}\n"
                    f"Expected: {expected_version} (or {expected_version}-prerelease)\n"
                    f"Minor releases should increment minor number and reset patch to 0"
                )

        elif change_type == "Major":
            expected_version = f"{curr_major + 1}.0.0"
            if new_major != curr_major + 1 or new_minor != 0 or new_patch != 0:
                raise VersionValidationError(
                    f"Invalid major increment: {current_version} → {new_version}\n"
                    f"Expected: {expected_version} (or {expected_version}-prerelease)\n"
                    f"Major releases should increment major number and reset minor/patch to 0"
                )

        # Validate pre-release suffix if present
        if new_prerelease:
            valid_suffixes = self.version_data["validation_rules"][
                "prerelease_suffixes"
            ]
            suffix_base = new_prerelease.split(".")[0]  # Get "beta" from "beta.1"

            if suffix_base not in valid_suffixes:
                raise VersionValidationError(
                    f"Invalid pre-release suffix: '{new_prerelease}'\n"
                    f"Valid suffixes: {', '.join(valid_suffixes)}\n"
                    f"Examples: alpha.1, beta.1, rc.1"
                )

    def validate_release_tag(self, tag: str) -> Dict:
        """
        Validate a complete release tag.

        Args:
            tag: Release tag to validate

        Returns:
            Dict with validation results and parsed components

        Raises:
            VersionValidationError: If validation fails
        """
        # Parse tag components
        release_type, change_type, version = self.parse_tag(tag)

        # Parse version components
        major, minor, patch, prerelease = self.parse_version(version)

        # Determine current version to compare against
        current_version = None
        if release_type == "Release":
            current_version = self.version_data.get("current_release")
            if not current_version:
                current_version = self.version_data.get("current_testpypi")
        else:  # Pre-release
            current_version = self.version_data.get("current_release")
            if not current_version:
                current_version = self.version_data.get("current_testpypi")

        # Validate version increment
        self.validate_version_increment(current_version, version, change_type)

        # Check for duplicate versions
        for release in self.version_data["release_history"]:
            if release["version"] == version:
                raise VersionValidationError(
                    f"Version {version} already exists in release history\n"
                    f"Previous release: {release['tag']} on {release['date']}\n"
                    f"Each version can only be released once"
                )

        return {
            "tag": tag,
            "release_type": release_type,
            "change_type": change_type,
            "version": version,
            "major": major,
            "minor": minor,
            "patch": patch,
            "prerelease": prerelease,
            "is_prerelease": prerelease is not None,
            "current_version": current_version,
            "valid": True,
        }

    def update_version_tracking(
        self, validation_result: Dict, release_notes: str = ""
    ) -> None:
        """
        Update version tracking after successful release.

        Args:
            validation_result: Result from validate_release_tag
            release_notes: Optional release notes
        """
        version = validation_result["version"]
        release_type = validation_result["release_type"]
        tag = validation_result["tag"]

        # Add to release history
        release_entry = {
            "version": version,
            "tag": tag,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "type": "production" if release_type == "Release" else "prerelease",
            "notes": release_notes,
        }

        self.version_data["release_history"].append(release_entry)

        # Update current version tracking
        if release_type == "Release":
            self.version_data["current_release"] = version

        # Update next allowed versions
        major, minor, patch = (
            validation_result["major"],
            validation_result["minor"],
            validation_result["patch"],
        )

        if release_type == "Release":
            # Update next allowed based on the new release
            self.version_data["next_allowed"] = {
                "patch": f"{major}.{minor}.{patch + 1}",
                "minor": f"{major}.{minor + 1}.0",
                "major": f"{major + 1}.0.0",
            }

        # Save updated data
        self._save_version_data()

    def get_validation_summary(self, validation_result: Dict) -> str:
        """Generate human-readable validation summary."""
        version = validation_result["version"]
        release_type = validation_result["release_type"]
        change_type = validation_result["change_type"]
        current = validation_result["current_version"]

        summary = "✅ Version Validation Successful\n\n"
        summary += "📋 Release Details:\n"
        summary += f"  • Tag: {validation_result['tag']}\n"
        summary += f"  • Version: {version}\n"
        summary += f"  • Type: {release_type} {change_type}\n"
        summary += f"  • Pre-release: {'Yes' if validation_result['is_prerelease'] else 'No'}\n"
        summary += f"  • Current Version: {current or 'None'}\n\n"

        summary += "🚀 Deployment Plan:\n"
        if release_type == "Pre-release":
            summary += "  1. Deploy to TestPyPI (validation)\n"
            summary += "  2. Run smoke tests\n"
            summary += "  3. Deploy to Production PyPI (marked as pre-release)\n"
            summary += f"  4. Beta users: pip install adri=={version}\n"
        else:
            summary += "  1. Deploy to TestPyPI (validation)\n"
            summary += "  2. Run smoke tests\n"
            summary += "  3. Deploy to Production PyPI (marked as latest)\n"
            summary += f"  4. Users: pip install adri  # Gets {version}\n"

        return summary

    def get_error_guidance(self, error: VersionValidationError) -> str:
        """Generate helpful error guidance for Slack notifications."""
        current_release = self.version_data.get("current_release")
        current_testpypi = self.version_data.get("current_testpypi")
        next_allowed = self.version_data["next_allowed"]

        guidance = "🚨 ADRI Release FAILED: Version Validation Error\n\n"
        guidance += f"❌ Error: {str(error)}\n\n"

        guidance += "📋 Current State:\n"
        guidance += f"  • Live Version: {current_release or 'None'}\n"
        guidance += f"  • TestPyPI Version: {current_testpypi or 'None'}\n"
        guidance += f"  • Next Allowed: Patch={next_allowed['patch']}, Minor={next_allowed['minor']}, Major={next_allowed['major']}\n\n"

        guidance += "🔧 How to Fix:\n"
        guidance += "1. Delete the invalid release/tag from GitHub\n"
        guidance += "2. Create new release with valid tag format:\n"
        guidance += f"   • Release.Patch.v{next_allowed['patch']} (bug fixes)\n"
        guidance += f"   • Release.Minor.v{next_allowed['minor']} (new features)\n"
        guidance += (
            f"   • Pre-release.Minor.v{next_allowed['minor']}-beta.1 (test version)\n\n"
        )

        guidance += "📖 Tag Format: <Release Type>.<Change Type>.v<Version>\n"
        guidance += "📚 Examples:\n"
        guidance += "   • Release.Minor.v0.3.0\n"
        guidance += "   • Pre-release.Patch.v0.2.1-beta.1\n"
        guidance += "   • Release.Major.v1.0.0\n"

        return guidance


def main():
    """Provide CLI interface for version validation."""
    if len(sys.argv) != 2:
        print("Usage: python validate_version.py <release_tag>")
        print("Example: python validate_version.py Release.Minor.v0.3.0")
        sys.exit(1)

    tag = sys.argv[1]

    try:
        validator = VersionValidator()
        result = validator.validate_release_tag(tag)

        print(validator.get_validation_summary(result))

        # Output for GitHub Actions using environment files
        print(f"\nvalidation_result={json.dumps(result)}")
        print(f"version={result['version']}")
        print(f"is_prerelease={str(result['is_prerelease']).lower()}")
        print(f"release_type={result['release_type']}")

    except VersionValidationError as e:
        validator = VersionValidator()
        error_guidance = validator.get_error_guidance(e)

        print(error_guidance)
        print(f"\n::error::{str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"🚨 Unexpected error during validation: {e}")
        print(f"::error::Unexpected validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
