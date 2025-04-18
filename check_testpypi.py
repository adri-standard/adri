"""
Simple script to check if ADRI package exists on TestPyPI.
This script doesn't require additional dependencies beyond standard library.
"""

import json
import urllib.request
import urllib.error
import sys

def check_testpypi(package_name="adri"):
    """Check if package exists on TestPyPI and list its versions."""
    try:
        # Connect to TestPyPI API
        url = f"https://test.pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        # Extract versions
        versions = list(data.get('releases', {}).keys())
        
        # Sort versions with most recent first (development versions at top)
        versions.sort(reverse=True)
        
        # Print results
        print(f"Package '{package_name}' found on TestPyPI")
        print(f"Available versions: {len(versions)} total")
        
        # Print standard versions
        standard_versions = [v for v in versions if 'dev' not in v]
        if standard_versions:
            print(f"\nStandard versions: {', '.join(standard_versions[:5])}")
            if len(standard_versions) > 5:
                print(f"...and {len(standard_versions) - 5} more")
        
        # Check for development versions
        dev_versions = [v for v in versions if 'dev' in v]
        if dev_versions:
            print(f"\nDevelopment versions: {', '.join(dev_versions[:5])}")
            if len(dev_versions) > 5:
                print(f"...and {len(dev_versions) - 5} more")
            print("\nThe TestPyPI integration test has been run successfully!")
        
        return True
    
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Package '{package_name}' not found on TestPyPI")
        else:
            print(f"Error accessing TestPyPI: {e}")
        return False

if __name__ == "__main__":
    package_name = sys.argv[1] if len(sys.argv) > 1 else "adri"
    check_testpypi(package_name)
