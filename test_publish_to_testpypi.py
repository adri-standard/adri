#!/usr/bin/env python
"""
Standalone TestPyPI Publishing Test Script

This script tests the ADRI package publishing process by:
1. Checking for required dependencies
2. Generating a unique development version
3. Temporarily modifying version files
4. Building the package
5. Publishing to TestPyPI
6. Verifying the package is accessible
7. Cleaning up

SECURITY WARNING: This script requires a PyPI API token.
Never hardcode tokens or commit them to version control.

Usage:
    # Set the token as an environment variable
    # PowerShell:
    $env:TESTPYPI_API_TOKEN="your-token"
    
    # Bash/Zsh:
    export TESTPYPI_API_TOKEN="your-token"
    
    # Run the script
    python test_publish_to_testpypi.py
"""

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


# Required external packages
REQUIRED_PACKAGES = ["build", "twine", "requests"]


def check_dependencies():
    """Check if required dependencies are installed and install if missing."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        
        try:
            print("Attempting to install missing packages...")
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            subprocess.run(cmd, check=True, capture_output=True)
            print("Packages installed successfully.")
            
            # Verify installation
            for package in missing:
                try:
                    importlib.import_module(package)
                except ImportError:
                    print(f"Failed to import {package} after installation.")
                    print(f"Please install required packages manually:")
                    print(f"pip install {' '.join(REQUIRED_PACKAGES)}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Failed to install packages: {e}")
            print(f"Please install required packages manually:")
            print(f"pip install {' '.join(REQUIRED_PACKAGES)}")
            return False
    
    return True


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
            
            # Verify changes
            with open(pyproject_path, 'r') as f:
                if version not in f.read():
                    print("Warning: Version not properly updated in pyproject.toml")
            
            with open(version_path, 'r') as f:
                if version not in f.read():
                    print("Warning: Version not properly updated in version.py")
            
            yield
            
        finally:
            # Restore original files
            print("Restoring original version files...")
            shutil.copy2(pyproject_backup, pyproject_path)
            shutil.copy2(version_backup, version_path)


def build_package():
    """Build the package distribution files."""
    repo_root = Path(__file__).parent
    build_dir = repo_root / "dist"
    
    # Clean any existing build artifacts
    if build_dir.exists():
        print(f"Cleaning existing build directory: {build_dir}")
        shutil.rmtree(build_dir)
    
    print("Building package...")
    
    try:
        # Use subprocess to run the build command
        cmd = [sys.executable, "-m", "build", str(repo_root)]
        process = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if dist directory was created and contains files
        if not build_dir.exists() or not any(build_dir.iterdir()):
            print("Error: Build completed but no distribution files were created")
            if process.stdout:
                print(f"Build output: {process.stdout}")
            return False
        
        print("Package built successfully")
        dist_files = list(build_dir.glob("*"))
        print(f"Distribution files: {[f.name for f in dist_files]}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        if e.stdout:
            print(f"Build output: {e.stdout}")
        if e.stderr:
            print(f"Build error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Build failed with exception: {str(e)}")
        return False


def upload_to_testpypi():
    """
    Upload the package to TestPyPI.
    
    Uses the TESTPYPI_API_TOKEN environment variable for authentication.
    """
    repo_root = Path(__file__).parent
    dist_dir = repo_root / "dist"
    
    # Check if dist directory exists and contains files
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print("Error: No distribution files found to upload")
        return False
    
    # Security: Get token from environment variable
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        print("Error: TESTPYPI_API_TOKEN environment variable not set")
        return False
    
    print("Uploading to TestPyPI...")
    
    # Create command for uploading to TestPyPI
    cmd = [
        sys.executable, 
        "-m", 
        "twine", 
        "upload",
        "--repository-url", 
        "https://test.pypi.org/legacy/",
        "--username", 
        "__token__",
        "--password", 
        token,  # This is securely handled by twine
        str(dist_dir / "*")
    ]
    
    try:
        # Run in a subshell to avoid exposing the token
        # Don't use shell=True for security reasons
        result = subprocess.run(
            cmd,
            check=False,  # Don't raise exception so we can handle errors
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Security: Mask token in error message
            safe_stderr = result.stderr.replace(token, "****")
            print(f"Upload failed: {safe_stderr}")
            return False
        
        print("Upload to TestPyPI successful")
        return True
        
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
        print('$env:TESTPYPI_API_TOKEN="your-token"')
        print("")
        print("Bash/Zsh:")
        print('export TESTPYPI_API_TOKEN="your-token"')
        print("")
        print("Then run this script again.")
        return False
    return True


def main():
    """Run the TestPyPI publishing test."""
    print("=" * 80)
    print("ADRI TestPyPI Publishing Test")
    print("=" * 80)
    
    try:
        # Check for TestPyPI token
        if not check_testpypi_token():
            return 1
        
        # Check dependencies
        print("\nChecking dependencies...")
        if not check_dependencies():
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
                print("\nBuilding package...")
                if not build_package():
                    print("Error: Package build failed")
                    return 1
                
                # Upload to TestPyPI
                print("\nUploading to TestPyPI...")
                if not upload_to_testpypi():
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
        
        print("\nADRI TestPyPI Publishing Test: PASSED")
        return 0
        
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        print("\nADRI TestPyPI Publishing Test: FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
