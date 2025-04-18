#!/usr/bin/env python
"""
Automated TestPyPI Publishing Script

This script handles the entire publishing process for testing, including:
1. Bootstrapping pip if it's not available
2. Installing required dependencies (twine and build)
3. Generating a unique development version
4. Temporarily modifying version files
5. Building the package
6. Publishing to TestPyPI
7. Verifying the published package
8. Cleaning up and restoring files

Usage:
    # Set token (PowerShell)
    $env:TESTPYPI_API_TOKEN="your-token-here"
    
    # Run script
    python auto_test_pypi_publish.py
"""

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


def bootstrap_environment():
    """
    Bootstrap the Python environment with required dependencies.
    
    This function:
    1. Ensures pip is installed
    2. Installs twine and build if needed
    """
    print("=" * 80)
    print("Environment Setup")
    print("=" * 80)
    
    # Check for pip
    print("\nChecking for pip...")
    have_pip = False
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✓ pip is installed")
        have_pip = True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("✗ pip is not installed")
    
    # Bootstrap pip if needed
    if not have_pip:
        print("\nBootstrapping pip...")
        try:
            subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                check=True
            )
            print("✓ pip bootstrapped successfully")
            have_pip = True
        except (subprocess.SubprocessError, ModuleNotFoundError):
            print("✗ Failed to bootstrap pip with ensurepip")
            
            # Try get-pip.py as a fallback
            try:
                print("\nTrying get-pip.py fallback...")
                # Download get-pip.py
                with urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py") as response:
                    get_pip_content = response.read()
                
                # Save to file
                with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    tmp_file.write(get_pip_content)
                
                # Run get-pip.py
                subprocess.run(
                    [sys.executable, tmp_path],
                    check=True
                )
                
                # Clean up
                os.unlink(tmp_path)
                
                print("✓ pip installed with get-pip.py")
                have_pip = True
            except Exception as e:
                print(f"✗ Failed to install pip: {e}")
    
    if not have_pip:
        print("\n❌ ERROR: Could not install pip. Manual intervention required.")
        print("Please install pip manually, then run this script again.")
        return False
    
    # Check for twine and build
    print("\nChecking for required packages...")
    packages_to_install = []
    
    for package in ["twine", "build"]:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"✓ {package} is installed")
        except subprocess.SubprocessError:
            print(f"✗ {package} is not installed")
            packages_to_install.append(package)
    
    # Install missing packages
    if packages_to_install:
        print(f"\nInstalling missing packages: {', '.join(packages_to_install)}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user"] + packages_to_install,
                check=True
            )
            print("✓ All packages installed successfully")
        except subprocess.SubprocessError as e:
            print(f"✗ Failed to install packages: {e}")
            print("\n❌ ERROR: Could not install required packages. Manual intervention required.")
            print(f"Please install the following packages manually: {', '.join(packages_to_install)}")
            return False
    
    print("\n✅ Environment setup completed successfully")
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
            
            yield
            
        finally:
            # Restore original files
            print("Restoring original version files...")
            shutil.copy2(pyproject_backup, pyproject_path)
            shutil.copy2(version_backup, version_path)


def build_package():
    """Build package distributions."""
    print("Building package distributions...")
    
    repo_root = Path(__file__).parent
    dist_dir = repo_root / "dist"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    try:
        # Use build module if it's installed
        subprocess.run(
            [sys.executable, "-m", "build", str(repo_root)],
            check=True
        )
        
        # Check if build succeeded
        if not dist_dir.exists() or not any(dist_dir.iterdir()):
            print("Error: No distribution files created by build")
            return False
            
        print("Package built successfully")
        return True
    except Exception as e:
        print(f"Error with build module: {e}")
        print("Falling back to setup.py...")
        
        try:
            # Fallback to setup.py sdist
            subprocess.run(
                [sys.executable, "setup.py", "sdist", "--dist-dir", str(dist_dir)],
                check=True,
                cwd=str(repo_root)
            )
            
            # Check if build succeeded
            if not dist_dir.exists() or not any(dist_dir.iterdir()):
                print("Error: No distribution files created by setup.py")
                return False
                
            print("Package built successfully (using setup.py)")
            return True
        except Exception as e:
            print(f"Error building package: {e}")
            return False


@contextmanager
def temp_pypirc_file(token):
    """
    Create a temporary .pypirc file with TestPyPI configuration.
    
    This context manager creates a .pypirc file with the token,
    yields the path, then removes the file afterward.
    """
    print("Creating temporary .pypirc file for TestPyPI...")
    
    # Get user's home directory
    home_dir = Path.home()
    pypirc_path = home_dir / ".pypirc"
    
    # Backup existing .pypirc if it exists
    had_existing = pypirc_path.exists()
    backup_path = None
    
    if had_existing:
        print("Backing up existing .pypirc file...")
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            backup_path = temp.name
            with open(pypirc_path, 'rb') as f:
                shutil.copyfileobj(f, temp)
    
    try:
        # Create .pypirc with TestPyPI configuration
        with open(pypirc_path, 'w') as f:
            f.write(f"""[distutils]
index-servers =
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = {token}
""")
        
        yield pypirc_path
        
    finally:
        # Remove the temporary .pypirc file
        if pypirc_path.exists():
            os.unlink(pypirc_path)
        
        # Restore original .pypirc if it existed
        if had_existing and backup_path:
            shutil.copy(backup_path, pypirc_path)
            os.unlink(backup_path)


def upload_to_testpypi():
    """
    Upload the package to TestPyPI.
    
    Creates a temporary .pypirc file with the TestPyPI token,
    then uses twine to upload the package.
    """
    print("Preparing to upload to TestPyPI...")
    
    # Get token from environment
    token = os.environ.get('TESTPYPI_API_TOKEN')
    if not token:
        print("Error: TESTPYPI_API_TOKEN environment variable not set")
        print("Please set the token as an environment variable and try again")
        return False
    
    repo_root = Path(__file__).parent
    dist_dir = repo_root / "dist"
    
    if not dist_dir.exists() or not any(dist_dir.iterdir()):
        print("Error: No distribution files found to upload")
        return False
    
    # Create temporary .pypirc file and upload
    with temp_pypirc_file(token):
        print("Uploading to TestPyPI...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "twine", "upload", "--repository", "testpypi", str(dist_dir / "*")],
                check=False,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Security: Mask token in error message
                safe_stderr = result.stderr.replace(token, "****")
                print(f"Upload failed: {safe_stderr}")
                return False
            
            print("Upload to TestPyPI successful!")
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
        print('$env:TESTPYPI_API_TOKEN="your-token-here"')
        print("")
        print("Bash/Zsh:")
        print('export TESTPYPI_API_TOKEN="your-token-here"')
        print("")
        print("CMD:")
        print('set TESTPYPI_API_TOKEN=your-token-here')
        print("")
        print("Then run this script again.")
        return False
    return True


def main():
    """Run the TestPyPI publishing test."""
    print("=" * 80)
    print("ADRI Automated TestPyPI Publishing Test")
    print("=" * 80)
    
    try:
        # Check for TestPyPI token
        if not check_testpypi_token():
            return 1
        
        # Bootstrap environment
        if not bootstrap_environment():
            return 1
        
        print("\n" + "=" * 80)
        print("Publishing Process")
        print("=" * 80)
        
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
                
                print("\n✅ Test completed successfully!")
                print(f"Package adri-{test_version} is now available on TestPyPI")
                
        finally:
            # Clean up
            print("\nCleaning up...")
            cleanup()
        
        print("\nADRI TestPyPI Publishing Test: PASSED")
        print("You can view your package at:")
        print(f"https://test.pypi.org/project/adri/{test_version}/")
        return 0
        
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        print("\nADRI TestPyPI Publishing Test: FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
