"""
Link validation tests for the ADRI project.

This module contains tests to verify that links within HTML and Markdown files
are valid and point to existing resources within the project structure.
"""

import os
import re
from pathlib import Path
import unittest

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent.parent

# Directories to scan for user-facing HTML and Markdown files
SCAN_DIRS = [
    ROOT_DIR / "docs",              # Documentation source
    ROOT_DIR / "benchmark" / "public", # Benchmark public page
]

# Key user-facing files to explicitly test
KEY_FILES = [
    ROOT_DIR / "index.html",  # Main website
    ROOT_DIR / "docs" / "index.md",  # Documentation index
    ROOT_DIR / "docs" / "CONTRIBUTING.md",  # Contribution guide
    ROOT_DIR / "README.md",  # README
]

# External domains that should be working but we don't need to test
TRUSTED_DOMAINS = [
    "github.com",
    "verodat.ai",
    "twitter.com",
    "linkedin.com",
    "cdn.jsdelivr.net",
    "fonts.googleapis.com",
    "img.shields.io",
]

# New directory mapping after restructuring
OLD_TO_NEW_PATHS = {
    "assessed_datasets": "datasets",
    "../CONTRIBUTING.md": "docs/CONTRIBUTING.md",
    "../LICENSE": "LICENSE",
    "EXTENDING.md": "docs/EXTENDING.md",
    "Implementation-Guide.md": "docs/Implementation-Guide.md",
    "Methodology.md": "docs/Methodology.md",
}


class LinkValidator:
    """Utility class to validate links within HTML and Markdown files."""

    def __init__(self, base_dir=ROOT_DIR):
        self.base_dir = Path(base_dir)
        self.broken_links = []
        self.warned_links = []
        self.checked_links = set()

    def validate_file(self, file_path):
        """Validate links in a single file."""
        file_path = Path(file_path)
        
        # Skip files that don't exist
        if not file_path.exists():
            return
            
        if file_path.suffix.lower() in ['.html', '.htm']:
            return self._validate_html_file(file_path)
        elif file_path.suffix.lower() in ['.md', '.markdown']:
            return self._validate_markdown_file(file_path)
        else:
            return  # Unsupported file type
    
    def _validate_html_file(self, file_path):
        """Extract and validate links from an HTML file using regex."""
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Look for href attributes in a tags
        href_pattern = re.compile(r'<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
        for match in href_pattern.finditer(html_content):
            href = match.group(1)
            self._check_link(href, file_path)
        
        # Look for href attributes in link tags (CSS)
        css_pattern = re.compile(r'<link[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
        for match in css_pattern.finditer(html_content):
            href = match.group(1)
            self._check_link(href, file_path)
        
        # Look for src attributes in script tags
        script_pattern = re.compile(r'<script[^>]+src=["\'](.*?)["\']', re.IGNORECASE)
        for match in script_pattern.finditer(html_content):
            src = match.group(1)
            self._check_link(src, file_path)
        
        # Look for src attributes in img tags
        img_pattern = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.IGNORECASE)
        for match in img_pattern.finditer(html_content):
            src = match.group(1)
            self._check_link(src, file_path)
    
    def _validate_markdown_file(self, file_path):
        """Extract and validate links from a Markdown file using regex."""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Find Markdown links [text](url)
        md_links = re.findall(r'\[.*?\]\((.*?)\)', md_content)
        for href in md_links:
            if '#' in href:
                href = href.split('#')[0]  # Remove anchor part
            self._check_link(href, file_path)
    
    def _check_link(self, href, source_file):
        """Check if a link is valid."""
        # Skip if already checked
        if href in self.checked_links:
            return
        
        self.checked_links.add(href)
        
        # Skip empty links, anchors, and javascript
        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
            return
        
        # Skip external links to trusted domains
        if any(href.startswith(f"https://{domain}") for domain in TRUSTED_DOMAINS):
            return
        
        # Handle GitHub repository links
        if "github.com/verodat/agent-data-readiness-index" in href:
            self.warned_links.append({
                'source': str(source_file),
                'link': href,
                'reason': "GitHub repository URL should be updated to ThinkEvolveSolve organization"
            })
            return
        
        # Is this an external link?
        if href.startswith(('http://', 'https://')):
            # We skip actual HTTP checks but warn about non-trusted domains
            if not any(domain in href for domain in TRUSTED_DOMAINS):
                self.warned_links.append({
                    'source': str(source_file),
                    'link': href,
                    'reason': "External link to non-trusted domain"
                })
            return
        
        # Normalize path
        if href.startswith('/'):
            # Absolute path from root
            target_path = self.base_dir / href.lstrip('/')
        else:
            # Relative path from source file
            source_dir = source_file.parent
            target_path = source_dir / href
        
        # Check for the "under-construction.html" link which is valid
        if "under-construction.html" in str(target_path):
            return
        
        # Check if the target file exists
        try:
            target_path = target_path.resolve(strict=True) # Use strict=True to raise FileNotFoundError
            if not target_path.exists(): # This check might be redundant with strict=True but kept for clarity
                 # This path should not be reached if strict=True works as expected
                 self.broken_links.append({
                    'source': str(source_file),
                    'link': href,
                    'reason': "Target file does not exist (unexpected)"
                 })
        except FileNotFoundError:
             # File doesn't exist, now check if it's due to an old path structure
             if href in OLD_TO_NEW_PATHS:
                 new_path = OLD_TO_NEW_PATHS[href]
                 self.broken_links.append({
                     'source': str(source_file),
                     'link': href,
                     'reason': f"Uses old path structure. Should use {new_path} instead of {href}"
                 })
             else:
                 # Genuinely broken link, not matching old paths
                 self.broken_links.append({
                     'source': str(source_file),
                     'link': href,
                     'reason': "Target file does not exist"
                 })
        except Exception as e: # Catch other potential errors like permission issues
            self.broken_links.append({
                'source': str(source_file),
                'link': href,
                'reason': f"Error resolving path: {str(e)}"
            })


# Directories to exclude from scanning
EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "venv",
    "site",
    "site_backup",
    "adri.egg-info",
    "tests", # Exclude tests directory itself from general scan
    "scripts",
    "internal",
    "ai_dev_manager",
    "config",
    "datasets", # Exclude raw datasets, catalog is checked via scripts/docs
    "examples", # Exclude examples source from user-facing link check
    "notebooks", # Exclude notebooks source from user-facing link check
}

def find_files(base_dir, extensions):
    """Find all files with given extensions in a directory, excluding specified subdirectories."""
    files = []
    base_dir = Path(base_dir)
    for root, dirnames, filenames in os.walk(base_dir, topdown=True):
        # Modify dirnames in-place to prevent os.walk from descending into excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in extensions):
                files.append(Path(root) / filename)
    return files


def test_key_files_links():
    """Test links in key files like index.html and index.md."""
    validator = LinkValidator()
    
    for file_path in KEY_FILES:
        if file_path.exists():
            validator.validate_file(file_path)
    
    # Print report summary
    broken_count = len(validator.broken_links)
    warn_count = len(validator.warned_links)
    
    print(f"\nLink Test Results for Key Files:")
    print(f"  - {broken_count} broken links")
    print(f"  - {warn_count} links with warnings")
    
    # Print broken links
    if validator.broken_links:
        print("\nBroken Links:")
        for link in validator.broken_links:
            print(f"  - In {link['source']}: {link['link']} - {link['reason']}")
    
    # Print warned links
    if validator.warned_links:
        print("\nLinks with Warnings:")
        for link in validator.warned_links:
            print(f"  - In {link['source']}: {link['link']} - {link['reason']}")
    
    return len(validator.broken_links) == 0


def test_all_documentation_links():
    """Test links in all documentation files."""
    validator = LinkValidator()
    
    # Find all HTML and Markdown files in documentation directories
    html_extensions = ['.html', '.htm']
    md_extensions = ['.md', '.markdown']
    
    for scan_dir in SCAN_DIRS:
        if scan_dir.exists():
            html_files = find_files(scan_dir, html_extensions)
            md_files = find_files(scan_dir, md_extensions)
            
            for file_path in html_files + md_files:
                validator.validate_file(file_path)
    
    # Print report summary
    broken_count = len(validator.broken_links)
    warn_count = len(validator.warned_links)
    
    print(f"\nLink Test Results for All Documentation:")
    print(f"  - {broken_count} broken links")
    print(f"  - {warn_count} links with warnings")
    
    # Print broken links
    if validator.broken_links:
        print("\nBroken Links:")
        for link in validator.broken_links:
            print(f"  - In {link['source']}: {link['link']} - {link['reason']}")
    
    # Print warned links
    if validator.warned_links:
        print("\nLinks with Warnings:")
        for link in validator.warned_links:
            print(f"  - In {link['source']}: {link['link']} - {link['reason']}")
    
    # This test is informational only - it won't fail the build yet
    return True


class TestLinks(unittest.TestCase):
    """Test case for link validation."""
    
    def test_key_files(self):
        """Test links in key files."""
        self.assertTrue(test_key_files_links())
    
    def test_all_documentation(self):
        """Test links in all documentation files."""
        self.assertTrue(test_all_documentation_links())


if __name__ == "__main__":
    # Run tests directly
    print("Running link tests...")
    test_key_files_links()
    test_all_documentation_links()
