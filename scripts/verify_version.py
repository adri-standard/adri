#!/usr/bin/env python
"""
Version verification script for ADRI.

This script verifies that version information is consistent across all relevant
files in the codebase to ensure proper versioning.
"""

import os
import re
import sys
from pathlib import Path

def get_version_py_version():
    """Extract version directly from version.py file."""
    version_path = Path(__file__).parent.parent / "adri" / "version.py"
    
    if not version_path.exists():
        print(f"Error: version.py not found at {version_path}")
        return None
        
    with open(version_path, "r") as f:
        content = f.read()
    
    # Use regex to extract __version__
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print("Error: Could not find __version__ in version.py")
        return None
        
    return match.group(1)

# Get version from file
version_py_version = get_version_py_version()
if not version_py_version:
    sys.exit(1)


def get_pyproject_version():
    """Extract version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: pyproject.toml not found at {pyproject_path}")
        return None
        
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Use regex to extract version
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        return None
        
    return match.group(1)


def get_changelog_versions():
    """Extract versions from CHANGELOG.md."""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    
    if not changelog_path.exists():
        print(f"Error: CHANGELOG.md not found at {changelog_path}")
        return []
        
    with open(changelog_path, "r") as f:
        content = f.read()
    
    # Use regex to extract all versions
    versions = re.findall(r'## \[([0-9]+\.[0-9]+\.[0-9]+)\]', content)
    return versions


def get_versions_md_versions():
    """Extract versions from VERSIONS.md."""
    versions_path = Path(__file__).parent.parent / "VERSIONS.md"
    
    if not versions_path.exists():
        print(f"Error: VERSIONS.md not found at {versions_path}")
        return []
        
    with open(versions_path, "r") as f:
        content = f.read()
    
    # Extract detailed version sections
    versions = re.findall(r'### ([0-9]+\.[0-9]+\.[0-9]+)', content)
    return versions


def main():
    """Main function to check version consistency."""
    print("ADRI Version Consistency Checker")
    print("===============================")
    
    # Get versions from different files
    pyproject_version = get_pyproject_version()
    changelog_versions = get_changelog_versions()
    versions_md_versions = get_versions_md_versions()
    
    # Display results
    print(f"version.py:      {version_py_version}")
    print(f"pyproject.toml:  {pyproject_version}")
    print(f"CHANGELOG.md:    {', '.join(changelog_versions) if changelog_versions else 'No versions found'}")
    print(f"VERSIONS.md:     {', '.join(versions_md_versions) if versions_md_versions else 'No versions found'}")
    print()
    
    # Check consistency
    errors = []
    
    if version_py_version != pyproject_version:
        errors.append(f"Version mismatch: version.py ({version_py_version}) != pyproject.toml ({pyproject_version})")
    
    if version_py_version not in changelog_versions and version_py_version != "0.1.0":
        errors.append(f"Version {version_py_version} not found in CHANGELOG.md")
    
    if version_py_version not in versions_md_versions:
        errors.append(f"Version {version_py_version} not documented in VERSIONS.md")
    
    # Display results
    if errors:
        print("Errors detected:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Success: Version information is consistent across all files.")
        sys.exit(0)


if __name__ == "__main__":
    main()
