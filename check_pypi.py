#!/usr/bin/env python
"""
Check PyPI Versions Script

This script checks both the live PyPI and TestPyPI repositories for the ADRI package
and displays all available versions. It helps compare what's on each repository.

Usage:
    python check_pypi.py [package_name]
    
    Default package name is "adri" if not specified.
"""

import json
import sys
import urllib.request
import urllib.error


def check_package(package_name, repository="pypi"):
    """
    Check if a package exists on PyPI/TestPyPI and list its versions.
    
    Args:
        package_name: The name of the package to check
        repository: Either "pypi" for live or "testpypi" for test
    
    Returns:
        Dictionary with package info or None if not found
    """
    # Choose the correct repository URL
    if repository == "testpypi":
        base_url = "https://test.pypi.org/pypi"
        repo_name = "TestPyPI"
    else:
        base_url = "https://pypi.org/pypi"
        repo_name = "PyPI (live)"
    
    # Construct API URL
    url = f"{base_url}/{package_name}/json"
    
    try:
        # Connect to API
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
            # Extract versions
            versions = list(data.get('releases', {}).keys())
            
            # Sort versions with most recent first
            versions.sort(reverse=True)
            
            # Print results
            print(f"\n{repo_name}:")
            print(f"Package '{package_name}' found with {len(versions)} version(s)")
            
            # Print standard versions
            standard_versions = [v for v in versions if 'dev' not in v and 'a' not in v and 'b' not in v and 'rc' not in v]
            if standard_versions:
                print("\nStandard releases:")
                for v in standard_versions[:10]:
                    print(f"  • {v}")
                if len(standard_versions) > 10:
                    print(f"  • ...and {len(standard_versions) - 10} more")
            
            # Print development versions
            dev_versions = [v for v in versions if 'dev' in v]
            if dev_versions:
                print("\nDevelopment releases:")
                for v in dev_versions[:10]:
                    print(f"  • {v}")
                if len(dev_versions) > 10:
                    print(f"  • ...and {len(dev_versions) - 10} more")
            
            # Print pre-releases
            prerelease_versions = [v for v in versions if ('a' in v or 'b' in v or 'rc' in v) and 'dev' not in v]
            if prerelease_versions:
                print("\nPre-releases (alpha/beta/rc):")
                for v in prerelease_versions[:10]:
                    print(f"  • {v}")
                if len(prerelease_versions) > 10:
                    print(f"  • ...and {len(prerelease_versions) - 10} more")
            
            # Return information
            return {
                "name": package_name,
                "repository": repository,
                "versions": versions,
                "standard_versions": standard_versions,
                "dev_versions": dev_versions,
                "prerelease_versions": prerelease_versions
            }
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"\n{repo_name}:")
            print(f"Package '{package_name}' not found (404)")
        else:
            print(f"\n{repo_name}:")
            print(f"Error accessing repository: {e}")
        return None


def main():
    """Compare package versions on live PyPI and TestPyPI."""
    # Get package name from command line or use default
    package_name = sys.argv[1] if len(sys.argv) > 1 else "adri"
    
    print("=" * 80)
    print(f"Package Version Checker - {package_name}")
    print("=" * 80)
    
    # Check live PyPI
    live_info = check_package(package_name, "pypi")
    
    # Check TestPyPI
    test_info = check_package(package_name, "testpypi")
    
    # Show summary if both repositories have the package
    if live_info and test_info:
        print("\nSummary:")
        print(f"• Live PyPI: {len(live_info['versions'])} version(s)")
        if live_info['standard_versions']:
            print(f"  Latest stable: {live_info['standard_versions'][0]}")
        
        print(f"• TestPyPI: {len(test_info['versions'])} version(s)")
        
        # Find versions in test but not in live
        unique_test_versions = [v for v in test_info['versions'] if v not in live_info['versions']]
        if unique_test_versions:
            print(f"\nVersions only on TestPyPI:")
            for v in unique_test_versions[:10]:
                print(f"  • {v}")
            if len(unique_test_versions) > 10:
                print(f"  • ...and {len(unique_test_versions) - 10} more")
    
    print("\nTo check a specific version on PyPI:")
    print(f"  https://pypi.org/project/{package_name}/VERSION/")
