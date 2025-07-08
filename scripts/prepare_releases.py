#!/usr/bin/env python3
"""
Release preparation script for ADRI Validator.

This script automatically creates and manages draft releases with pre-filled
release notes based on the current state in VERSION.json.

Features:
- Reads current version state from VERSION.json
- Calculates valid next release versions
- Creates/updates draft releases with templated notes
- Cleans up old draft releases
- Generates commit summaries since last release
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from github import Github


class ReleasePreparator:
    """Manages automated release preparation for ADRI Validator."""

    def __init__(self, github_token: str, repository: str):
        """Initialize with GitHub credentials."""
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repository)
        self.version_file = Path("VERSION.json")
        self.templates_dir = Path("templates/release-notes")

    def load_version_data(self) -> Dict:
        """Load current version data from VERSION.json."""
        if not self.version_file.exists():
            raise FileNotFoundError(f"Version file not found: {self.version_file}")

        with open(self.version_file, "r") as f:
            return json.load(f)

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string into components."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)"
        match = re.match(pattern, version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(map(int, match.groups()))

    def calculate_next_versions(self, version_data: Dict) -> Dict[str, str]:
        """Calculate all valid next version numbers."""
        current_release = version_data.get("current_release")
        current_testpypi = version_data.get("current_testpypi")

        # Use the highest current version as base
        base_version = current_release or current_testpypi or "0.0.0"
        major, minor, patch = self.parse_version(base_version)

        return {
            "patch": f"{major}.{minor}.{patch + 1}",
            "minor": f"{major}.{minor + 1}.0",
            "major": f"{major + 1}.0.0",
        }

    def get_commits_since_last_release(self, last_version: Optional[str]) -> List[Dict]:
        """Get commit messages since the last release."""
        try:
            if last_version:
                # Try to find the last release tag
                try:
                    last_tag = None
                    for tag in self.repo.get_tags():
                        if last_version in tag.name:
                            last_tag = tag.name
                            break

                    if last_tag:
                        # Get commits since last tag
                        comparison = self.repo.compare(last_tag, "main")
                        commits = []
                        for commit in comparison.commits:
                            commits.append(
                                {
                                    "sha": commit.sha[:8],
                                    "message": commit.commit.message.split("\n")[0],
                                    "author": commit.commit.author.name,
                                    "date": commit.commit.author.date.strftime(
                                        "%Y-%m-%d"
                                    ),
                                }
                            )
                        return commits
                except Exception:  # nosec B110
                    # Fallback to recent commits if tag comparison fails
                    pass

            # Fallback: get last 10 commits
            commits = []
            for commit in self.repo.get_commits()[:10]:
                commits.append(
                    {
                        "sha": commit.sha[:8],
                        "message": commit.commit.message.split("\n")[0],
                        "author": commit.commit.author.name,
                        "date": commit.commit.author.date.strftime("%Y-%m-%d"),
                    }
                )
            return commits

        except Exception as e:
            print(f"Warning: Could not fetch commits: {e}")
            return []

    def load_release_template(self, template_name: str) -> str:
        """Load release notes template from file."""
        template_path = self.templates_dir / f"{template_name}.md"
        if template_path.exists():
            with open(template_path, "r") as f:
                return f.read()

        # Fallback to default template
        return self.get_default_template()

    def get_default_template(self) -> str:
        """Get default release notes template."""
        return """## 🚀 ADRI Validator v{version} - {release_type} Release

### 📋 Release Information
- **Type**: {release_description}
- **Previous Version**: {previous_version}
- **Installation**: `pip install adri=={version}`

### ✨ What's New
<!-- Add your changes here -->
{commit_summary}

### 🐛 Bug Fixes
<!-- Add bug fixes here -->
-

### 📚 Documentation
- Updated README
- Added examples

### 🔧 Technical Details
- **Python Support**: 3.10, 3.11, 3.12
- **Dependencies**: Updated pandas to 1.5.0+
- **Testing**: 90%+ coverage maintained

### 🔗 Links
- [PyPI Package](https://pypi.org/project/adri/{version}/)
- [TestPyPI Package](https://test.pypi.org/project/adri/{version}/)
- [Documentation](https://github.com/ThinkEvolveSolve/adri-validator/blob/main/README.md)
- [Changelog](https://github.com/ThinkEvolveSolve/adri-validator/blob/main/CHANGELOG.md)

---
**Deployment Status**: 🟡 Pending (will be updated automatically during release)
"""

    def generate_release_notes(
        self,
        version: str,
        release_type: str,
        previous_version: Optional[str],
        commits: List[Dict],
    ) -> str:
        """Generate complete release notes from template."""
        # Determine release description
        release_descriptions = {
            "patch": "Production Release (Patch) - Bug fixes and minor improvements",
            "minor": "Production Release (Minor) - New features, backward compatible",
            "major": "Production Release (Major) - Breaking changes and major updates",
            "beta-patch": "Beta Release (Patch) - Testing bug fixes",
            "beta-minor": "Beta Release (Minor) - Testing new features",
            "beta-major": "Beta Release (Major) - Testing breaking changes",
        }

        release_description = release_descriptions.get(
            release_type, "Production Release"
        )

        # Generate commit summary
        if commits:
            commit_lines = []
            for commit in commits[:8]:  # Limit to recent commits
                # Clean up commit message
                msg = commit["message"]
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                commit_lines.append(f"- {msg} ({commit['sha']})")

            commit_summary = "**Recent Changes:**\n" + "\n".join(commit_lines)
            if len(commits) > 8:
                commit_summary += f"\n- ... and {len(commits) - 8} more commits"
        else:
            commit_summary = "- See commit history for detailed changes"

        # Load and format template
        template = self.load_release_template(release_type.replace("-", "_"))

        return template.format(
            version=version,
            release_type=release_type.replace("-", " ").title(),
            release_description=release_description,
            previous_version=previous_version or "None",
            commit_summary=commit_summary,
        )

    def cleanup_old_drafts(self):
        """Remove old draft releases to keep things clean."""
        try:
            for release in self.repo.get_releases():
                if release.draft and "ADRI v" in release.title:
                    print(f"🧹 Cleaning up old draft: {release.title}")
                    release.delete()
        except Exception as e:
            print(f"Warning: Could not cleanup old drafts: {e}")

    def create_or_update_draft(
        self, tag_name: str, title: str, body: str, prerelease: bool = False
    ):
        """Create or update a draft release."""
        try:
            # Check if draft already exists
            existing_draft = None
            for release in self.repo.get_releases():
                if release.draft and release.tag_name == tag_name:
                    existing_draft = release
                    break

            if existing_draft:
                print(f"📝 Updating existing draft: {title}")
                existing_draft.update_release(
                    name=title, message=body, draft=True, prerelease=prerelease
                )
            else:
                print(f"✨ Creating new draft: {title}")
                self.repo.create_git_release(
                    tag=tag_name,
                    name=title,
                    message=body,
                    draft=True,
                    prerelease=prerelease,
                )

        except Exception as e:
            print(f"Warning: Could not create/update draft {title}: {e}")

    def prepare_all_releases(self):
        """Prepare all release drafts."""
        print("🚀 Preparing ADRI Validator release drafts...")

        # Load current state
        version_data = self.load_version_data()
        next_versions = self.calculate_next_versions(version_data)

        current_version = version_data.get("current_release") or version_data.get(
            "current_testpypi"
        )
        commits = self.get_commits_since_last_release(current_version)

        print(f"📋 Current version: {current_version}")
        print(f"📝 Found {len(commits)} commits since last release")

        # Clean up old drafts first
        self.cleanup_old_drafts()

        # Create draft releases for each type
        release_types = [
            ("patch", "🔧 ADRI v{version} - Patch Release (DRAFT)", False),
            ("minor", "🚀 ADRI v{version} - Minor Release (DRAFT)", False),
            ("major", "💥 ADRI v{version} - Major Release (DRAFT)", False),
            ("beta-patch", "🧪 ADRI v{version} - Beta Patch (DRAFT)", True),
            ("beta-minor", "🧪 ADRI v{version} - Beta Minor (DRAFT)", True),
            ("beta-major", "🧪 ADRI v{version} - Beta Major (DRAFT)", True),
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
            body = self.generate_release_notes(
                version, release_type, current_version, commits
            )

            self.create_or_update_draft(tag_name, title, body, is_prerelease)

        print("✅ Release preparation completed!")
        print("📋 Check GitHub Releases for updated draft releases")
        print("🎯 Next steps:")
        print("   1. Go to GitHub Releases")
        print("   2. Select the appropriate draft release")
        print("   3. Edit release notes as needed")
        print("   4. Publish the release to trigger deployment")


def main():
    """Serve as main entry point."""
    github_token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY")

    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    if not repository:
        raise ValueError("GITHUB_REPOSITORY environment variable is required")

    preparator = ReleasePreparator(github_token, repository)
    preparator.prepare_all_releases()


if __name__ == "__main__":
    main()
