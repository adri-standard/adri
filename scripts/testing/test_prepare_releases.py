#!/usr/bin/env python3
"""Test script for release preparation logic without GitHub API calls."""

import json
import sys
from pathlib import Path

from prepare_releases import ReleasePreparator

# Add the scripts directory to the path so we can import from prepare_releases
sys.path.insert(0, str(Path(__file__).parent))


class MockReleasePreparator(ReleasePreparator):
    """Mock version that doesn't make GitHub API calls."""

    def __init__(self):
        """Initialize without GitHub credentials."""
        # Initialize without GitHub credentials
        self.version_file = Path("VERSION.json")
        self.templates_dir = Path("templates/release-notes")

    def get_commits_since_last_release(self, last_version):
        """Mock commit data for testing."""
        return [
            {
                "sha": "abc12345",
                "message": "Add automated release preparation system",
                "author": "Developer",
                "date": "2025-01-08",
            },
            {
                "sha": "def67890",
                "message": "Update release workflow with candidate tag support",
                "author": "Developer",
                "date": "2025-01-08",
            },
            {
                "sha": "ghi11111",
                "message": "Create release note templates",
                "author": "Developer",
                "date": "2025-01-08",
            },
        ]

    def create_or_update_draft(self, tag_name, title, body, prerelease=False):
        """Mock draft creation - just print what would be created."""
        print("\n📝 Would create/update draft release:")
        print(f"   Tag: {tag_name}")
        print(f"   Title: {title}")
        print(f"   Prerelease: {prerelease}")
        print(f"   Body length: {len(body)} characters")
        print(f"   Body preview: {body[:200]}...")

    def cleanup_old_drafts(self):
        """Mock cleanup."""
        print("🧹 Would cleanup old draft releases")


def test_release_preparation():
    """Test the release preparation logic."""
    print("🧪 Testing ADRI Release Preparation Logic")
    print("=" * 50)

    try:
        preparator = MockReleasePreparator()

        # Load version data
        version_data = preparator.load_version_data()
        print(f"📋 Current version data: {json.dumps(version_data, indent=2)}")

        # Calculate next versions
        next_versions = preparator.calculate_next_versions(version_data)
        print(f"\n🔢 Next versions: {next_versions}")

        # Get mock commits
        current_version = version_data.get("current_release") or version_data.get(
            "current_testpypi"
        )
        commits = preparator.get_commits_since_last_release(current_version)
        print(f"\n📝 Found {len(commits)} commits since {current_version}")

        # Test release note generation
        print("\n📄 Testing release note generation...")

        # Test minor release notes
        minor_notes = preparator.generate_release_notes(
            next_versions["minor"], "minor", current_version, commits
        )
        print("\n🚀 Minor release notes preview:")
        print(minor_notes[:500] + "...")

        # Test beta release notes
        beta_notes = preparator.generate_release_notes(
            next_versions["minor"] + "-beta.1", "beta-minor", current_version, commits
        )
        print("\n🧪 Beta release notes preview:")
        print(beta_notes[:500] + "...")

        # Test draft creation simulation
        print("\n📋 Simulating draft release creation...")

        release_types = [
            ("patch", "🔧 ADRI v{version} - Patch Release (DRAFT)", False),
            ("minor", "🚀 ADRI v{version} - Minor Release (DRAFT)", False),
            ("beta-minor", "🧪 ADRI v{version} - Beta Minor (DRAFT)", True),
        ]

        for release_type, title_template, is_prerelease in release_types:
            if release_type.startswith("beta-"):
                base_type = release_type.replace("beta-", "")
                base_version = next_versions[base_type]
                version = base_version + "-beta.1"
                tag_name = f"candidate-{release_type}-v{base_version}"
            else:
                version = next_versions[release_type]
                tag_name = f"candidate-{release_type}-v{version}"

            title = title_template.format(version=version)
            body = preparator.generate_release_notes(
                version, release_type, current_version, commits
            )

            preparator.create_or_update_draft(tag_name, title, body, is_prerelease)

        print("\n✅ Release preparation test completed successfully!")
        print("🎯 The system is ready to create automated draft releases")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_release_preparation()
    sys.exit(0 if success else 1)
