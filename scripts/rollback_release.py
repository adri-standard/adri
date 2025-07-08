#!/usr/bin/env python3
"""
ADRI Release Rollback Script

This script provides comprehensive rollback functionality for ADRI releases.
It can handle different rollback scenarios based on the publication stage.

Usage:
    python rollback_release.py <tag_name> [--reason "reason"] [--force] [--dry-run]

Examples:
    # Clean rollback (pre-PyPI)
    python rollback_release.py candidate-beta-minor-v0.3.0 --reason "Test failures"

    # Force rollback with yanking (post-PyPI)
    python rollback_release.py Pre-release.Minor.v0.3.0-beta.1 --force --reason "Critical bug"

    # Dry run to see what would be done
    python rollback_release.py candidate-minor-v0.3.0 --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


class ReleaseRollback:
    """Handles comprehensive release rollback operations."""

    def __init__(
        self,
        tag_name: str,
        reason: str = "",
        force: bool = False,
        dry_run: bool = False,
    ):
        self.tag_name = tag_name
        self.reason = reason or "Manual rollback requested"
        self.force = force
        self.dry_run = dry_run
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv(
            "GITHUB_REPOSITORY", "ThinkEvolveSolve/adri-validator"
        )

        # Convert candidate tags to proper format for analysis
        self.proper_tag, self.version = self._convert_tag_format(tag_name)

        print(f"🔄 Rollback Analysis for: {tag_name}")
        if self.proper_tag != tag_name:
            print(f"🔄 Converted to: {self.proper_tag}")
        print(f"📦 Version: {self.version}")
        print(f"🔄 Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        print()

    def _convert_tag_format(self, tag_name: str) -> Tuple[str, str]:
        """Convert candidate tags to proper release tag format."""
        if tag_name.startswith("candidate-"):
            if tag_name.startswith("candidate-beta-"):
                # candidate-beta-minor-v0.3.0 -> Pre-release.Minor.v0.3.0-beta.1
                match = re.match(r"candidate-beta-([^-]+)-v(.+)", tag_name)
                if match:
                    change_type, version_base = match.groups()
                    proper_tag = (
                        f"Pre-release.{change_type.capitalize()}.v{version_base}-beta.1"
                    )
                    version = f"{version_base}-beta.1"
                    return proper_tag, version
            else:
                # candidate-minor-v0.3.0 -> Release.Minor.v0.3.0
                match = re.match(r"candidate-([^-]+)-v(.+)", tag_name)
                if match:
                    change_type, version_base = match.groups()
                    proper_tag = f"Release.{change_type.capitalize()}.v{version_base}"
                    version = version_base
                    return proper_tag, version
        else:
            # Extract version from proper tag format
            if "-beta." in tag_name:
                match = re.search(r"\.v(.+)", tag_name)
                version = match.group(1) if match else tag_name
            else:
                match = re.search(r"\.v(.+)", tag_name)
                version = match.group(1) if match else tag_name
            return tag_name, version

        return tag_name, tag_name

    def analyze_publication_status(self) -> Dict[str, bool]:
        """Analyze where the release has been published."""
        status = {
            "git_tag_exists": False,
            "github_release_exists": False,
            "testpypi_published": False,
            "pypi_published": False,
        }

        print("🔍 Analyzing publication status...")

        # Check Git tag
        try:
            result = subprocess.run(
                ["git", "tag", "-l", self.tag_name],
                capture_output=True,
                text=True,
                check=True,
            )
            status["git_tag_exists"] = bool(result.stdout.strip())
            print(
                f"   Git tag ({self.tag_name}): {'✅ EXISTS' if status['git_tag_exists'] else '❌ NOT FOUND'}"
            )
        except subprocess.CalledProcessError:
            print(f"   Git tag ({self.tag_name}): ❌ ERROR CHECKING")

        # Check GitHub release
        if self.github_token:
            try:
                result = subprocess.run(
                    ["gh", "release", "view", self.tag_name],
                    capture_output=True,
                    text=True,
                )
                status["github_release_exists"] = result.returncode == 0
                print(
                    f"   GitHub release: {'✅ EXISTS' if status['github_release_exists'] else '❌ NOT FOUND'}"
                )
            except FileNotFoundError:
                print("   GitHub release: ⚠️ gh CLI not available")
        else:
            print("   GitHub release: ⚠️ No GITHUB_TOKEN")

        # Check TestPyPI
        try:
            response = requests.get(
                f"https://test.pypi.org/pypi/adri/{self.version}/json", timeout=10
            )
            status["testpypi_published"] = response.status_code == 200
            print(
                f"   TestPyPI: {'✅ PUBLISHED' if status['testpypi_published'] else '❌ NOT PUBLISHED'}"
            )
        except requests.RequestException:
            print("   TestPyPI: ⚠️ ERROR CHECKING")

        # Check PyPI
        try:
            response = requests.get(
                f"https://pypi.org/pypi/adri/{self.version}/json", timeout=10
            )
            status["pypi_published"] = response.status_code == 200
            print(
                f"   PyPI: {'✅ PUBLISHED' if status['pypi_published'] else '❌ NOT PUBLISHED'}"
            )
        except requests.RequestException:
            print("   PyPI: ⚠️ ERROR CHECKING")

        return status

    def determine_rollback_type(self, status: Dict[str, bool]) -> str:
        """Determine the type of rollback needed."""
        if status["pypi_published"]:
            if self.force:
                return "yank"
            else:
                print("❌ Cannot rollback: Package published to PyPI")
                print("   Use --force to yank the package (irreversible)")
                sys.exit(1)
        elif status["testpypi_published"]:
            return "partial"
        else:
            return "clean"

    def execute_rollback(self, rollback_type: str, status: Dict[str, bool]) -> None:
        """Execute the rollback based on type."""
        print(f"🚨 Executing {rollback_type.upper()} rollback...")
        print(f"📝 Reason: {self.reason}")
        print()

        actions_taken = []

        # Step 1: Handle PyPI yanking if needed
        if rollback_type == "yank":
            print("⚠️ PyPI Package Yanking Required")
            print(
                "   This action is IRREVERSIBLE and requires PyPI maintainer permissions"
            )
            print(
                f"   Command: twine yank adri {self.version} --reason '{self.reason}'"
            )

            if not self.dry_run:
                try:
                    result = subprocess.run(
                        [
                            "twine",
                            "yank",
                            "adri",
                            self.version,
                            "--reason",
                            self.reason,
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print("   ✅ Package yanked from PyPI")
                    actions_taken.append("PyPI package yanked")
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ Failed to yank package: {e}")
                    print("   Manual intervention required")
                except FileNotFoundError:
                    print("   ⚠️ twine not available - manual yanking required")
                    print(
                        f"   Run: twine yank adri {self.version} --reason '{self.reason}'"
                    )
            else:
                print("   🔍 DRY RUN: Would yank package from PyPI")
            print()

        # Step 2: Delete GitHub release
        if status["github_release_exists"]:
            print("🗑️ Deleting GitHub release...")
            if not self.dry_run and self.github_token:
                try:
                    result = subprocess.run(
                        ["gh", "release", "delete", self.tag_name, "--yes"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print("   ✅ GitHub release deleted")
                    actions_taken.append("GitHub release deleted")
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ Failed to delete GitHub release: {e}")
            else:
                print("   🔍 DRY RUN: Would delete GitHub release")
            print()

        # Step 3: Delete Git tags (only for clean rollback)
        if status["git_tag_exists"] and rollback_type in ["clean", "partial"]:
            print("🗑️ Deleting Git tags...")

            # Delete local tag
            if not self.dry_run:
                try:
                    subprocess.run(
                        ["git", "tag", "-d", self.tag_name],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print(f"   ✅ Local tag deleted: {self.tag_name}")
                except subprocess.CalledProcessError:
                    print(f"   ⚠️ Failed to delete local tag: {self.tag_name}")

                # Delete remote tag
                try:
                    subprocess.run(
                        ["git", "push", "origin", f":refs/tags/{self.tag_name}"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print(f"   ✅ Remote tag deleted: {self.tag_name}")
                    actions_taken.append("Git tags deleted")
                except subprocess.CalledProcessError:
                    print(f"   ⚠️ Failed to delete remote tag: {self.tag_name}")
            else:
                print(f"   🔍 DRY RUN: Would delete Git tag: {self.tag_name}")
            print()

        # Step 4: Clean up candidate releases
        self._cleanup_candidate_releases(actions_taken)

        # Step 5: Generate summary
        self._generate_rollback_summary(rollback_type, actions_taken)

    def _cleanup_candidate_releases(self, actions_taken: List[str]) -> None:
        """Clean up related candidate releases and tags."""
        print("🧹 Cleaning up candidate releases...")

        if self.tag_name.startswith("candidate-"):
            # Already a candidate tag, nothing to clean
            print("   ➖ No additional candidate cleanup needed")
            return

        # Generate candidate patterns to look for
        version_base = self.version.split("-")[0]  # Remove beta suffix
        candidate_patterns = [
            f"candidate-patch-v{version_base}",
            f"candidate-minor-v{version_base}",
            f"candidate-major-v{version_base}",
            f"candidate-beta-patch-v{version_base}",
            f"candidate-beta-minor-v{version_base}",
            f"candidate-beta-major-v{version_base}",
        ]

        for pattern in candidate_patterns:
            # Check and delete GitHub release
            if not self.dry_run and self.github_token:
                try:
                    result = subprocess.run(
                        ["gh", "release", "view", pattern],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        subprocess.run(
                            ["gh", "release", "delete", pattern, "--yes"],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        print(f"   ✅ Deleted candidate release: {pattern}")
                        actions_taken.append(f"Candidate release deleted: {pattern}")
                except subprocess.CalledProcessError:
                    pass

            # Check and delete Git tag
            if not self.dry_run:
                try:
                    result = subprocess.run(
                        ["git", "tag", "-l", pattern],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if result.stdout.strip():
                        subprocess.run(
                            ["git", "tag", "-d", pattern],
                            capture_output=True,
                            text=True,
                        )
                        subprocess.run(
                            ["git", "push", "origin", f":refs/tags/{pattern}"],
                            capture_output=True,
                            text=True,
                        )
                        print(f"   ✅ Deleted candidate tag: {pattern}")
                except subprocess.CalledProcessError:
                    pass

    def _generate_rollback_summary(
        self, rollback_type: str, actions_taken: List[str]
    ) -> None:
        """Generate a comprehensive rollback summary."""
        print("📋 Rollback Summary")
        print("=" * 50)
        print(f"🏷️ Tag: {self.tag_name}")
        print(f"📦 Version: {self.version}")
        print(f"🔄 Rollback Type: {rollback_type.upper()}")
        print(f"📝 Reason: {self.reason}")
        print(f"⏰ Time: {datetime.utcnow().isoformat()}Z")
        print(f"🔄 Mode: {'DRY RUN' if self.dry_run else 'EXECUTED'}")
        print()

        print("🧹 Actions Taken:")
        if actions_taken:
            for action in actions_taken:
                print(f"   ✅ {action}")
        else:
            print("   ➖ No actions required or executed")
        print()

        print("🎯 Next Steps:")
        if rollback_type == "yank":
            print("   1. Communicate to users about the yanked version")
            print("   2. Prepare hotfix release if needed")
            print("   3. Update documentation about the issue")
        else:
            print("   1. Fix the issues that caused the rollback")
            print("   2. Test fixes thoroughly in development")
            print("   3. Run prepare-releases workflow to create new drafts")
            print("   4. Retry release process")
        print()

        if self.dry_run:
            print("⚠️ This was a DRY RUN - no actual changes were made")
            print("   Remove --dry-run flag to execute the rollback")

    def run(self) -> None:
        """Execute the complete rollback process."""
        try:
            # Analyze current state
            status = self.analyze_publication_status()
            print()

            # Determine rollback strategy
            rollback_type = self.determine_rollback_type(status)
            print(f"🎯 Rollback type determined: {rollback_type.upper()}")
            print()

            # Execute rollback
            self.execute_rollback(rollback_type, status)

            print("✅ Rollback process completed!")

        except KeyboardInterrupt:
            print("\n🚫 Rollback cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Rollback failed: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ADRI Release Rollback Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean rollback (pre-PyPI)
  python rollback_release.py candidate-beta-minor-v0.3.0 --reason "Test failures"

  # Force rollback with yanking (post-PyPI)
  python rollback_release.py Pre-release.Minor.v0.3.0-beta.1 --force --reason "Critical bug"

  # Dry run to see what would be done
  python rollback_release.py candidate-minor-v0.3.0 --dry-run
        """,
    )

    parser.add_argument("tag_name", help="Release tag to rollback")
    parser.add_argument("--reason", "-r", default="", help="Reason for rollback")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force rollback even if published to PyPI (will yank)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without executing",
    )

    args = parser.parse_args()

    # Validate environment
    if not args.dry_run:
        if not os.getenv("GITHUB_TOKEN"):
            print("⚠️ Warning: GITHUB_TOKEN not set - GitHub operations may fail")

        # Check for required tools
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Error: git is required but not available")
            sys.exit(1)

    # Execute rollback
    rollback = ReleaseRollback(
        tag_name=args.tag_name,
        reason=args.reason,
        force=args.force,
        dry_run=args.dry_run,
    )

    rollback.run()


if __name__ == "__main__":
    main()
