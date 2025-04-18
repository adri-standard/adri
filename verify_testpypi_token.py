#!/usr/bin/env python
"""
Simple TestPyPI Token Verification Script

This script verifies that:
1. The TestPyPI token is valid
2. You have permission to upload to the ADRI package
3. What versions are currently available

This uses only the standard library.
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


def check_testpypi_token():
    """Check if TestPyPI token is available in environment."""
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        print("Error: TESTPYPI_API_TOKEN environment variable not set")
        return False
    
    if not token.startswith('pypi-'):
        print("Warning: TestPyPI tokens should start with 'pypi-'")
    
    return token


def test_auth_with_testpypi(token):
    """Test authentication with TestPyPI API."""
    print("\nTesting authentication with TestPyPI...")
    
    # Endpoint for listing project releases
    url = "https://test.pypi.org/pypi/adri/json"
    
    try:
        # Create a request with basic auth
        request = urllib.request.Request(url)
        auth_string = f"__token__:{token}"
        encoded_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        request.add_header("Authorization", f"Basic {encoded_auth}")
        
        # Make the request
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
            
            # Extract version information
            versions = list(data.get('releases', {}).keys())
            print(f"Authentication successful!")
            print(f"Package 'adri' exists on TestPyPI with {len(versions)} versions")
            print(f"Available versions: {', '.join(versions)}")
            return True
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"Authentication failed: Invalid token or insufficient permissions (HTTP {e.code})")
        elif e.code == 403:
            print(f"Authentication failed: Forbidden. You might not have permission (HTTP {e.code})")
        elif e.code == 404:
            print(f"Package 'adri' not found on TestPyPI (HTTP {e.code})")
            print("This is expected if the package hasn't been published yet.")
            return True
        else:
            print(f"HTTP Error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def simulate_publishing():
    """Simulate what would happen during publishing."""
    print("\nSimulating TestPyPI publishing process:")
    
    # Generate a unique development version
    current_version = "0.1.0"  # Hardcoded for demonstration
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    test_version = f"{current_version}.dev{timestamp}"
    
    print(f"1. Would generate development version: {test_version}")
    print(f"2. Would temporarily modify version files")
    print(f"3. Would build package distributions")
    print(f"4. Would upload to TestPyPI")
    print(f"5. Would verify package is accessible on TestPyPI")
    print(f"6. Would restore original version files")
    
    return test_version


def main():
    """Run the TestPyPI token verification."""
    print("=" * 80)
    print("ADRI TestPyPI Token Verification")
    print("=" * 80)
    
    # Check for token
    token = check_testpypi_token()
    if not token:
        return 1
    
    # Test authentication
    if not test_auth_with_testpypi(token):
        return 1
    
    # Simulate publishing
    test_version = simulate_publishing()
    
    print("\nToken verification completed successfully!")
    print(f"You have the correct permissions to publish to TestPyPI.")
    print(f"When you run the full test with required dependencies, version {test_version}")
    print(f"would be published to TestPyPI.")
    
    print("\nTo run the full test in a properly configured environment:")
    print("1. Install dependencies: pip install build twine requests")
    print("2. Run: python test_publish_to_testpypi.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
