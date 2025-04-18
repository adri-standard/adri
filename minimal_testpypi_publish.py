#!/usr/bin/env python
"""
Minimal TestPyPI Publishing Script

This script tests the ADRI package publishing process using only the standard library.
It doesn't install any dependencies and works with Python's built-in modules.

Steps:
1. Generate a unique development version
2. Temporarily modify version files
3. Build a simple source distribution (sdist)
4. Upload to TestPyPI using only standard library
5. Verify the package is accessible
6. Restore original version files

Usage:
    # Set token as environment variable
    # PowerShell:
    $env:TESTPYPI_API_TOKEN="your-token-here"
    
    # Run script
    python minimal_testpypi_publish.py
"""

import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import urllib.error
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def get_current_version():
    """Get the current version from version.py."""
    repo_root = Path(__file__).parent
    version_path = repo_root / "adri" / "version.py"
    
    if not version_path.exists():
        raise FileNotFoundError(f"Version file not found at {version_path}")
    
    with open(version_path, 'r') as f:
        version_content = f.read()
    
    match = re.search(r'__version__\s*=\s*"([^"]+)"', version_content)
    if not match:
        raise ValueError("Could not extract version from version.py")
    
    return match.group(1)


def generate_test_version():
    """Generate a unique development version for testing."""
    base_version = get_current_version()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{base_version}.dev{timestamp}"


@contextmanager
def temp_version_files(version):
    """
    Temporarily modify version files for testing.
    
    This context manager creates backup copies of version-related files,
    modifies them with the test version, then restores the originals afterward.
    """
    print(f"Temporarily setting version to: {version}")
    
    repo_root = Path(__file__).parent
    pyproject_path = repo_root / "pyproject.toml"
    version_path = repo_root / "adri" / "version.py"
    
    # Verify files exist
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    if not version_path.exists():
        raise FileNotFoundError(f"version.py not found at {version_path}")
    
    # Create backup copies
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        pyproject_backup = tmp_dir / "pyproject.toml.bak"
        version_backup = tmp_dir / "version.py.bak"
        
        shutil.copy2(pyproject_path, pyproject_backup)
        shutil.copy2(version_path, version_backup)
        
        try:
            # Update pyproject.toml
            print("Modifying pyproject.toml...")
            with open(pyproject_path, 'r') as f:
                pyproject_content = f.read()
            
            pyproject_content = re.sub(
                r'version\s*=\s*"[^"]+"',
                f'version = "{version}"',
                pyproject_content
            )
            
            with open(pyproject_path, 'w') as f:
                f.write(pyproject_content)
            
            # Update version.py
            print("Modifying version.py...")
            with open(version_path, 'r') as f:
                version_content = f.read()
            
            version_content = re.sub(
                r'__version__\s*=\s*"[^"]+"',
                f'__version__ = "{version}"',
                version_content
            )
            
            with open(version_path, 'w') as f:
                f.write(version_content)
            
            yield
            
        finally:
            # Restore original files
            print("Restoring original version files...")
            shutil.copy2(pyproject_backup, pyproject_path)
            shutil.copy2(version_backup, version_path)


def build_minimal_sdist(version):
    """
    Build a minimal source distribution using only the standard library.
    
    This creates a simple tarball with only the critical files needed for a
    minimal valid package that can be uploaded to TestPyPI.
    """
    print("Building minimal source distribution...")
    
    repo_root = Path(__file__).parent
    build_dir = repo_root / "dist"
    package_name = "adri"
    
    # Create build directory
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # Create the archive filename
    archive_name = f"{package_name}-{version}"
    archive_path = build_dir / f"{archive_name}.tar.gz"
    
    # Determine files to include
    include_files = [
        "pyproject.toml",
        "README.md",
        "LICENSE"
    ]
    
    # Include all Python files in the package
    for root, _, files in os.walk(package_name):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.join(root, file)
                include_files.append(rel_path)
    
    # Create the tarball
    with tarfile.open(archive_path, "w:gz") as tar:
        # Add the files
        for file_path in include_files:
            path = repo_root / file_path
            if path.exists():
                tar.add(path, arcname=os.path.join(archive_name, file_path))
            else:
                print(f"Warning: File not found: {file_path}")
    
    print(f"Built source distribution: {archive_path}")
    
    return archive_path


def upload_to_testpypi(sdist_path):
    """
    Upload the package to TestPyPI using only the standard library.
    
    This implements a basic HTTP multipart form upload to the TestPyPI API.
    """
    print("Uploading to TestPyPI...")
    
    # Get token from environment
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        print("Error: TESTPYPI_API_TOKEN environment variable not set")
        return False
    
    # TestPyPI upload URL
    url = "https://test.pypi.org/legacy/"
    
    try:
        # Read the file content
        with open(sdist_path, 'rb') as f:
            file_content = f.read()
        
        filename = os.path.basename(sdist_path)
        
        # Create boundary for multipart form
        boundary = 'X-X-X-X-TEST-PYPI-UPLOAD-X-X-X-X'
        
        # Create multipart form data
        data = []
        
        # Add metadata fields
        data.append(f'--{boundary}'.encode())
        data.append(b'Content-Disposition: form-data; name="protocol_version"')
        data.append(b'')
        data.append(b'1')
        
        # Add file
        data.append(f'--{boundary}'.encode())
        data.append(f'Content-Disposition: form-data; name="content"; filename="{filename}"'.encode())
        data.append(b'Content-Type: application/octet-stream')
        data.append(b'')
        data.append(file_content)
        
        # Add final boundary
        data.append(f'--{boundary}--'.encode())
        
        # Join with CR LF
        body = b'\r\n'.join(data)
        
        # Create request
        request = urllib.request.Request(url, data=body)
        
        # Add headers
        request.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        request.add_header('Content-Length', str(len(body)))
        
        # Add authentication
        auth_string = f"__token__:{token}"
        encoded_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        request.add_header("Authorization", f"Basic {encoded_auth}")
        
        # Make the request
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode()
            
            if response.status == 200:
                if "Upload successful" in response_body:
                    print("Upload to TestPyPI successful!")
                    return True
                else:
                    print(f"Upload succeeded but unexpected response: {response_body}")
                    return True
            else:
                print(f"Upload failed with status {response.status}")
                print(response_body)
                return False
                
    except urllib.error.HTTPError as e:
        # Security: Don't print the token if it's in the error message
        safe_error = str(e).replace(token, "****")
        print(f"HTTP Error: {safe_error}")
        
        # Try to read the response body
        try:
            error_body = e.read().decode()
            print(f"Error details: {error_body}")
        except:
            pass
            
        return False
    except Exception as e:
        print(f"Upload failed with exception: {str(e)}")
        return False


def verify_upload(version, max_attempts=5, delay=5):
    """
    Verify that the package was uploaded to TestPyPI.
    
    Args:
        version: Version to check for
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
    """
    package_name = "adri"
    print(f"Verifying package {package_name} version {version} on TestPyPI...")
    
    # Make multiple attempts with increasing delays
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"Waiting {delay} seconds before attempt {attempt}...")
            time.sleep(delay)
            delay *= 1.5  # Increase delay for each attempt
        
        # Query the TestPyPI API
        url = f"https://test.pypi.org/pypi/{package_name}/{version}/json"
        print(f"Checking URL: {url}")
        
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print(f"Success! Version {version} found on TestPyPI")
                    try:
                        # Parse the response to get more details
                        data = json.loads(response.read().decode())
                        release = data.get("info", {})
                        print(f"Package: {release.get('name')}")
                        print(f"Version: {release.get('version')}")
                        print(f"Summary: {release.get('summary')}")
                    except Exception:
                        pass  # Ignore parsing errors
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Attempt {attempt}/{max_attempts}: Version not found (404)")
            else:
                print(f"Attempt {attempt}/{max_attempts}: HTTP error {e.code}")
        except Exception as e:
            print(f"Attempt {attempt}/{max_attempts}: Error accessing TestPyPI: {e}")
    
    print(f"Version {version} not found on TestPyPI after {max_attempts} attempts")
    return False


def cleanup():
    """Clean up build artifacts."""
    repo_root = Path(__file__).parent
    build_dir = repo_root / "dist"
    
    if build_dir.exists():
        print(f"Cleaning up build directory: {build_dir}")
        shutil.rmtree(build_dir)
    else:
        print("No build directory to clean up")


def check_testpypi_token():
    """Check if TestPyPI token is available."""
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        print("Error: TESTPYPI_API_TOKEN environment variable not set")
        print("")
        print("Please set the token as an environment variable:")
        print("")
        print("PowerShell:")
        print('$env:TESTPYPI_API_TOKEN="your-token-here"')
        print("")
        print("Bash/Zsh:")
        print('export TESTPYPI_API_TOKEN="your-token-here"')
        print("")
        print("Then run this script again.")
        return False
    return True


def main():
    """Run the TestPyPI publishing test."""
    print("=" * 80)
    print("ADRI Minimal TestPyPI Publishing Test")
    print("=" * 80)
    
    try:
        # Check for TestPyPI token
        if not check_testpypi_token():
            return 1
        
        # Generate a unique version for this test run
        print("\nGenerating test version...")
        test_version = generate_test_version()
        print(f"Test version: {test_version}")
        
        try:
            # Temporarily modify version files
            with temp_version_files(test_version):
                print("\nTemporary version files created")
                
                # Build the package
                print("\nBuilding minimal package...")
                sdist_path = build_minimal_sdist(test_version)
                
                # Upload to TestPyPI
                print("\nUploading to TestPyPI...")
                if not upload_to_testpypi(sdist_path):
                    print("Error: Upload to TestPyPI failed")
                    return 1
                
                # Verify upload
                print("\nVerifying upload...")
                if not verify_upload(test_version):
                    print("Error: Upload verification failed")
                    return 1
                
                print("\nTest completed successfully!")
                print(f"Package adri-{test_version} is now available on TestPyPI")
                
        finally:
            # Clean up
            print("\nCleaning up...")
            cleanup()
        
        print("\nADRI Minimal TestPyPI Publishing Test: PASSED")
        return 0
        
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        print("\nADRI Minimal TestPyPI Publishing Test: FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
