"""
Pytest configuration and fixtures for end-to-end documentation tests.

Provides isolated test environments, clean ADRI workspaces, and test data
for validating that documentation, examples, and CLI commands work as advertised.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def tmpdir_adri_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """Create an isolated ADRI workspace for e2e testing.
    
    This fixture:
    - Creates a temporary directory
    - Sets up a clean ADRI environment
    - Cleans up after the test
    
    Args:
        tmp_path: pytest's built-in tmp_path fixture
        
    Yields:
        Path to temporary ADRI workspace
    """
    workspace = tmp_path / "adri_test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Change to workspace directory for test
    original_cwd = Path.cwd()
    
    try:
        import os
        os.chdir(workspace)
        yield workspace
    finally:
        # Restore original directory
        os.chdir(original_cwd)
        # Cleanup handled by tmp_path


@pytest.fixture
def clean_adri_state(tmpdir_adri_workspace: Path) -> Path:
    """Ensure ADRI state is clean before test.
    
    Removes any existing ADRI directories and files to ensure
    tests start from a known clean state.
    
    Args:
        tmpdir_adri_workspace: Temporary workspace fixture
        
    Returns:
        Path to clean workspace
    """
    # Remove ADRI directory if it exists
    adri_dir = tmpdir_adri_workspace / "ADRI"
    if adri_dir.exists():
        shutil.rmtree(adri_dir)
    
    return tmpdir_adri_workspace


@pytest.fixture
def sample_csv_data() -> str:
    """Provide sample CSV data for testing.
    
    Returns clean, well-formed CSV data that matches
    documentation examples.
    
    Returns:
        CSV data as string
    """
    return """id,name,email,age,signup_date
1,Alice,alice@example.com,25,2024-01-01
2,Bob,bob@example.com,30,2024-01-02
3,Charlie,charlie@example.com,35,2024-01-03
"""


@pytest.fixture
def bad_csv_data() -> str:
    """Provide problematic CSV data for testing validation.
    
    Returns CSV data with intentional quality issues
    to test ADRI's detection capabilities.
    
    Returns:
        CSV data with quality issues
    """
    return """id,name,email,age,signup_date
1,Alice,alice@example.com,25,2024-01-01
2,B,invalid-email,15,2020-01-02
,Charlie,charlie@example.com,35,2024-01-03
"""


@pytest.fixture
def sample_csv_file(tmpdir_adri_workspace: Path, sample_csv_data: str) -> Path:
    """Create a sample CSV file in the workspace.
    
    Args:
        tmpdir_adri_workspace: Temporary workspace
        sample_csv_data: CSV data to write
        
    Returns:
        Path to created CSV file
    """
    csv_file = tmpdir_adri_workspace / "sample_data.csv"
    csv_file.write_text(sample_csv_data, encoding="utf-8")
    return csv_file


@pytest.fixture
def bad_csv_file(tmpdir_adri_workspace: Path, bad_csv_data: str) -> Path:
    """Create a problematic CSV file in the workspace.
    
    Args:
        tmpdir_adri_workspace: Temporary workspace
        bad_csv_data: CSV data with issues
        
    Returns:
        Path to created CSV file with quality issues
    """
    csv_file = tmpdir_adri_workspace / "bad_data.csv"
    csv_file.write_text(bad_csv_data, encoding="utf-8")
    return csv_file


def run_cli_command(command: str, cwd: Path = None) -> tuple[int, str, str]:
    """Execute an ADRI CLI command and capture output.
    
    Helper function for running CLI commands in tests and
    capturing their output for validation.
    
    Args:
        command: CLI command to execute (e.g., "adri setup")
        cwd: Working directory for command execution
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    import subprocess
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd or Path.cwd()
    )
    
    return result.returncode, result.stdout, result.stderr
