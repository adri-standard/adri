#!/usr/bin/env python3
"""
Documentation Link Validator.

Validates all links in markdown files to ensure:
1. Internal links point to existing files
2. Relative paths are correct
3. GitHub blob links reference actual files
4. No broken documentation references

This prevents "advertised but missing" issues and link rot.

Usage:
    python scripts/validate_documentation_links.py
    python scripts/validate_documentation_links.py --repo-root /path/to/repo
    python scripts/validate_documentation_links.py --fix-mode

Exit Codes:
    0 - All links valid
    1 - Broken links found
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse


class LinkValidator:
    """Validates links in markdown documentation."""

    def __init__(self, repo_root: Path):
        """Initialize validator."""
        self.repo_root = Path(repo_root)
        self.broken_links: List[Tuple[Path, str, str]] = []
        self.checked_links: Set[str] = set()
        self.stats = {
            "files_checked": 0,
            "total_links": 0,
            "internal_links": 0,
            "external_links": 0,
            "broken_links": 0,
        }

    def validate_all(self) -> bool:
        """
        Validate all markdown files in repository.

        Returns:
            True if all links valid, False otherwise
        """
        print("=" * 70)
        print("ADRI Documentation Link Validator")
        print("=" * 70)
        print(f"Repository: {self.repo_root}")
        print()

        # Find all markdown files
        md_files = list(self.repo_root.glob("*.md"))
        md_files.extend(self.repo_root.glob("docs/**/*.md"))

        print(f"Found {len(md_files)} markdown files to validate")
        print()

        # Validate each file
        for md_file in md_files:
            self.validate_file(md_file)

        # Report results
        self.print_report()

        return len(self.broken_links) == 0

    def validate_file(self, file_path: Path) -> None:
        """Validate all links in a single markdown file."""
        self.stats["files_checked"] += 1

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️  Warning: Could not read {file_path}: {e}")
            return

        # Extract markdown links [text](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        # Extract bare URLs
        bare_urls = re.findall(r'(?<!\()https?://[^\s)]+', content)

        # Validate markdown links
        for link_text, link_url in markdown_links:
            self.stats["total_links"] += 1
            self.validate_link(file_path, link_url, link_text)

        # Note bare URLs (don't validate external ones, just count)
        for url in bare_urls:
            if url not in [link[1] for link in markdown_links]:
                self.stats["external_links"] += 1

    def validate_link(self, source_file: Path, link_url: str, link_text: str) -> None:
        """
        Validate a single link.

        Args:
            source_file: File containing the link
            link_url: URL or path being linked to
            link_text: Display text of link
        """
        # Skip anchors and mailto links
        if link_url.startswith('#') or link_url.startswith('mailto:'):
            return

        # Check if it's an external URL
        if link_url.startswith('http://') or link_url.startswith('https://'):
            self.validate_external_link(source_file, link_url, link_text)
        else:
            self.validate_internal_link(source_file, link_url, link_text)

    def validate_internal_link(self, source_file: Path, link_path: str, link_text: str) -> None:
        """Validate internal repository links."""
        self.stats["internal_links"] += 1

        # Remove anchor fragments
        clean_path = link_path.split('#')[0]

        if not clean_path:
            return  # Just an anchor

        # Resolve relative path
        if clean_path.startswith('/'):
            # Absolute from repo root
            target_path = self.repo_root / clean_path.lstrip('/')
        else:
            # Relative to source file
            target_path = (source_file.parent / clean_path).resolve()

        # Check if target exists
        if not target_path.exists():
            self.broken_links.append((
                source_file,
                link_path,
                f"Internal link to non-existent file: {clean_path}"
            ))
            self.stats["broken_links"] += 1

    def validate_external_link(self, source_file: Path, link_url: str, link_text: str) -> None:
        """Validate external GitHub links pointing to this repository."""
        self.stats["external_links"] += 1

        # Check if it's a GitHub link to our repository
        if 'github.com/adri-standard/adri' in link_url or  'github.com/Verodat/verodat-adri' in link_url:
            # Extract the file path from GitHub blob URL
            # Pattern: https://github.com/repo/blob/branch/path/to/file
            match = re.search(r'/blob/[^/]+/(.+?)(?:\?|#|$)', link_url)

            if match:
                file_path = match.group(1)

                # Check if file exists in our repo
                target_path = self.repo_root / file_path

                if not target_path.exists():
                    self.broken_links.append((
                        source_file,
                        link_url,
                        f"GitHub link to non-existent file: {file_path}"
                    ))
                    self.stats["broken_links"] += 1

    def print_report(self) -> None:
        """Print validation report."""
        print("=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print(f"Files checked:    {self.stats['files_checked']}")
        print(f"Total links:      {self.stats['total_links']}")
        print(f"Internal links:   {self.stats['internal_links']}")
        print(f"External links:   {self.stats['external_links']}")
        print(f"Broken links:     {self.stats['broken_links']}")
        print("=" * 70)
        print()

        if self.broken_links:
            print(f"❌ Found {len(self.broken_links)} broken links:")
            print()

            for source_file, link_url, reason in self.broken_links:
                print(f"File: {source_file.relative_to(self.repo_root)}")
                print(f"  Link: {link_url}")
                print(f"  Issue: {reason}")
                print()

            return False
        else:
            print("✅ All links valid!")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate documentation links"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory (default: current directory)"
    )

    args = parser.parse_args()

    # Create validator and run
    validator = LinkValidator(args.repo_root)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
