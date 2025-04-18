#!/usr/bin/env python
"""
Test script for test_publish_to_testpypi.py in dry-run mode.

This simulates the TestPyPI publishing process without actually publishing,
to verify that the script logic works correctly.
"""

import os
import sys
import importlib
import test_publish_to_testpypi

# Override functions to simulate success without actual publishing
def mock_check_dependencies():
    """Mock function that bypasses dependency checking."""
    print("MOCK: All dependencies available")
    return True

def mock_build_package():
    """Mock function that simulates successful package building."""
    print("MOCK: Package built successfully")
    return True

def mock_upload_to_testpypi():
    """Mock function that simulates successful TestPyPI upload."""
    print("MOCK: Package uploaded to TestPyPI successfully")
    return True

def mock_verify_upload(version, max_attempts=1, delay=0):
    """Mock function that simulates successful verification."""
    print(f"MOCK: Verified version {version} is available on TestPyPI")
    return True

def run_dry_test():
    """Run the TestPyPI publishing test in dry-run mode."""
    # Set dummy token
    os.environ['TESTPYPI_API_TOKEN'] = 'dummy_token_for_testing'
    
    # Override actual functions with mocks
    test_publish_to_testpypi.check_dependencies = mock_check_dependencies
    test_publish_to_testpypi.build_package = mock_build_package
    test_publish_to_testpypi.upload_to_testpypi = mock_upload_to_testpypi
    test_publish_to_testpypi.verify_upload = mock_verify_upload
    
    # Run the test
    print("Running test_publish_to_testpypi.py in DRY RUN mode")
    print("(No actual publishing will take place)")
    print("=" * 80)
    
    result = test_publish_to_testpypi.main()
    
    print("=" * 80)
    if result == 0:
        print("The script logic is working correctly!")
        print("To run with actual publishing, set TESTPYPI_API_TOKEN to a real token")
        print("and run test_publish_to_testpypi.py directly.")
    else:
        print("There seems to be an issue with the script logic.")
    
    # Clean up
    del os.environ['TESTPYPI_API_TOKEN']
    return result

if __name__ == "__main__":
    sys.exit(run_dry_test())
