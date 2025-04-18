"""
TestPyPI Publishing Integration Test

This test verifies that the package can be successfully built and published to TestPyPI.

SECURITY WARNING: This test requires PyPI API credentials. Follow these guidelines:
1. NEVER hardcode the token in source code
2. NEVER commit the token to version control
3. ONLY use environment variables or secure CI/CD secrets

To run this test locally (bash/zsh):
    export TESTPYPI_API_TOKEN="your-token-here"
    pytest tests/integration/test_publishing.py -v
    unset TESTPYPI_API_TOKEN  # Important: unset when done

For CI/CD:
    Configure TESTPYPI_API_TOKEN as a repository secret in GitHub
    Set the environment variable in the workflow as shown in docs
"""

import os
import re
import sys
import time
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from adri.version import __version__


def has_testpypi_token():
    """Check if TestPyPI token is available in environment."""
    return bool(os.environ.get('TESTPYPI_API_TOKEN'))


def generate_test_version():
    """Generate a unique development version for testing."""
    base_version = __version__
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{base_version}.dev{timestamp}"


@contextmanager
def temp_version_files(version):
    """
    Temporarily modify version files for testing.
    
    This context manager creates temporary copies of version-related files,
    modifies them with the test version, then restores the originals afterward.
    """
    repo_root = Path(__file__).parent.parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    version_path = repo_root / "adri" / "version.py"
    
    # Create backup copies
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        pyproject_backup = tmp_dir / "pyproject.toml.bak"
        version_backup = tmp_dir / "version.py.bak"
        
        shutil.copy2(pyproject_path, pyproject_backup)
        shutil.copy2(version_path, version_backup)
        
        try:
            # Update pyproject.toml
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
            shutil.copy2(pyproject_backup, pyproject_path)
            shutil.copy2(version_backup, version_path)


def build_package():
    """Build the package distribution files."""
    repo_root = Path(__file__).parent.parent.parent
    
    # Clean any existing build artifacts
    build_dir = repo_root / "dist"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Build the package
    cmd = [sys.executable, "-m", "build", "--outdir", str(build_dir)]
    
    try:
        subprocess.run(
            cmd, 
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e.stderr}")
        return False


def upload_to_testpypi():
    """
    Upload the package to TestPyPI.
    
    Uses the TESTPYPI_API_TOKEN environment variable for authentication.
    """
    repo_root = Path(__file__).parent.parent.parent
    dist_dir = repo_root / "dist"
    
    # Security: Get token from environment variable
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        return False
    
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
        # Security: Don't log the command as it contains the token
        print("Uploading to TestPyPI...")
        
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            check=False,  # Don't raise exception so we can handle errors
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Security: Mask token in error message
            safe_stderr = result.stderr.replace(token, "****")
            print(f"Upload failed: {safe_stderr}")
            return False
            
        return True
    except Exception as e:
        print(f"Upload failed with exception: {str(e)}")
        return False


def verify_upload(version):
    """Verify that the package was uploaded to TestPyPI."""
    # Give TestPyPI some time to process the upload
    time.sleep(5)
    
    # Query the TestPyPI API
    url = f"https://test.pypi.org/pypi/adri/{version}/json"
    
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        print(f"Verification failed: {str(e)}")
        return False


def cleanup():
    """Clean up build artifacts."""
    repo_root = Path(__file__).parent.parent.parent
    build_dir = repo_root / "dist"
    if build_dir.exists():
        shutil.rmtree(build_dir)


@pytest.mark.skipif(
    not has_testpypi_token(),
    reason="TestPyPI token not available in environment"
)
def test_testpypi_publishing():
    """
    Integration test for publishing to TestPyPI.
    
    This test:
    1. Generates a unique development version
    2. Temporarily modifies version files
    3. Builds the package
    4. Uploads to TestPyPI
    5. Verifies the upload
    6. Cleans up
    
    The test requires TESTPYPI_API_TOKEN environment variable to be set.
    """
    try:
        # Generate a unique version for this test run
        test_version = generate_test_version()
        print(f"Testing with version: {test_version}")
        
        # Temporarily modify version files
        with temp_version_files(test_version):
            # Build the package
            assert build_package(), "Package build failed"
            
            # Upload to TestPyPI
            assert upload_to_testpypi(), "Upload to TestPyPI failed"
            
            # Verify upload
            assert verify_upload(test_version), "Upload verification failed"
            
    finally:
        # Always clean up, even if the test fails
        cleanup()


if __name__ == "__main__":
    # Allow running directly for testing
    if has_testpypi_token():
        try:
            # Check for required dependencies
            import pytest
            import build
            import twine
            import requests
            
            test_testpypi_publishing()
        except ImportError as e:
            print(f"Missing required dependency: {e}")
            print("Please install required dependencies with:")
            print("pip install pytest build twine requests")
            sys.exit(1)
    else:
        print("TestPyPI token not available in environment")
        print("Set TESTPYPI_API_TOKEN environment variable to run this test")
        sys.exit(1)
