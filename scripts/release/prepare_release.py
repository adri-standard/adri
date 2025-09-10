#!/usr/bin/env python3
"""
ADRI Validator Release Preparation Script.

This script prepares a new release by:
1. Updating the version in pyproject.toml
2. Updating the CHANGELOG.md
3. Creating a commit with the changes
4. Providing instructions for creating the GitHub Release

Usage:
    python scripts/prepare_release.py 0.1.1
    python scripts/prepare_release.py 0.2.0 --changelog "Added new features"
"""

import argparse
import re
import shlex
import subprocess  # nosec B404
import sys
from datetime import datetime
from pathlib import Path


def validate_version(version):
    """Validate semantic version format."""
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-\.]+))?(?:\+([a-zA-Z0-9\-\.]+))?$"
    if not re.match(pattern, version):
        raise ValueError(
            f"Invalid version format: {version}. Use semantic versioning (e.g., 1.0.0)"
        )
    return version


def get_current_version():
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found. Run from project root.")

    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def update_pyproject_version(new_version):
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Replace version
    updated_content = re.sub(
        r'^version = "[^"]+"', f'version = "{new_version}"', content, flags=re.MULTILINE
    )

    pyproject_path.write_text(updated_content)
    print(f"✅ Updated pyproject.toml version to {new_version}")


def update_changelog(new_version, changelog_entry=None):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        # Create new changelog
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [{new_version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- {changelog_entry or 'Initial release'}

"""
    else:
        content = changelog_path.read_text()

        # Find the position to insert new version
        lines = content.split("\n")
        insert_pos = None

        for i, line in enumerate(lines):
            if line.startswith("## [") and "Unreleased" not in line:
                insert_pos = i
                break
            elif line.startswith("## ") and insert_pos is None:
                insert_pos = i + 1
                break

        if insert_pos is None:
            # Add after the header
            for i, line in enumerate(lines):
                if line.startswith("#") and not line.startswith("##"):
                    insert_pos = i + 3  # After title and description
                    break

        # Create new version entry
        new_entry = [
            f"## [{new_version}] - {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "### Added",
            f"- {changelog_entry or 'Release version ' + new_version}",
            "",
        ]

        # Insert new entry
        lines[insert_pos:insert_pos] = new_entry
        changelog_content = "\n".join(lines)

    changelog_path.write_text(changelog_content)
    print(f"✅ Updated CHANGELOG.md with version {new_version}")


def run_git_command(command):
    """Run a git command and return the result."""
    try:
        # Split command safely to avoid shell injection
        cmd_parts = shlex.split(command)
        result = subprocess.run(
            cmd_parts, capture_output=True, text=True, check=True
        )  # nosec B603
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {command}")
        print(f"Error: {e.stderr}")
        return None


def check_git_status():
    """Check if git working directory is clean."""
    status = run_git_command("git status --porcelain")
    if status:
        print(
            "❌ Git working directory is not clean. Please commit or stash changes first."
        )
        print("Uncommitted changes:")
        print(status)
        return False
    return True


def create_commit(version):
    """Create a commit with the version changes."""
    # Add files
    run_git_command("git add pyproject.toml CHANGELOG.md")

    # Create commit
    commit_msg = f"Prepare release v{version}"
    result = run_git_command(f'git commit -m "{commit_msg}"')

    if result is not None:
        print(f"✅ Created commit: {commit_msg}")
        return True
    return False


def print_next_steps(version):
    """Print instructions for completing the release."""
    print("\n" + "=" * 60)
    print("🎉 Release preparation complete!")
    print("=" * 60)
    print(f"\nNext steps to release v{version}:")
    print("\n1. Push the changes to main:")
    print("   git push origin main")
    print("\n2. Create a GitHub Release:")
    print("   - Go to: https://github.com/ThinkEvolveSolve/adri-validator/releases/new")
    print(f"   - Tag: v{version}")
    print(f"   - Title: Release v{version}")
    print("   - Description: Copy from CHANGELOG.md or write custom notes")
    print("   - Click 'Publish release'")
    print("\n3. Monitor the workflow:")
    print("   - The release will trigger the GitHub Actions workflow")
    print("   - Check: https://github.com/ThinkEvolveSolve/adri-validator/actions")
    print("\n4. If something goes wrong:")
    print(f"   - Delete release: gh release delete v{version}")
    print(
        f"   - Delete tag: git tag -d v{version} && git push origin :refs/tags/v{version}"
    )
    print("   - Revert commit: git revert HEAD")
    print("\n" + "=" * 60)


def main():
    """Handle command line arguments and execute release preparation."""
    parser = argparse.ArgumentParser(description="Prepare ADRI Validator release")
    parser.add_argument("version", help="Version to release (e.g., 0.1.1)")
    parser.add_argument(
        "--changelog", help="Changelog entry for this version", default=None
    )
    parser.add_argument(
        "--skip-git-check",
        action="store_true",
        help="Skip git status check (use with caution)",
    )

    args = parser.parse_args()

    try:
        # Validate version
        new_version = validate_version(args.version)
        current_version = get_current_version()

        print(f"🚀 Preparing release v{new_version}")
        print(f"Current version: {current_version}")

        if new_version == current_version:
            print(f"❌ Version {new_version} is the same as current version")
            sys.exit(1)

        # Check git status
        if not args.skip_git_check and not check_git_status():
            sys.exit(1)

        # Update files
        update_pyproject_version(new_version)
        update_changelog(new_version, args.changelog)

        # Create commit
        if create_commit(new_version):
            print_next_steps(new_version)
        else:
            print("❌ Failed to create commit")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
