"""
Integration tests for the ADRI interactive CLI.
"""

import os
import pytest
import subprocess
import tempfile
import json
from pathlib import Path


def test_cli_interactive_command_help():
    """Test that the CLI interactive command help works correctly."""
    # Run the CLI command with help
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "adri.cli", "interactive", "--help"],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output contains key information
    assert "interactive" in result.stdout
    assert "guided prompts" in result.stdout


@pytest.mark.skip("Interactive mode requires user input, can't be tested automatically")
def test_cli_interactive_command():
    """
    Test that the CLI interactive command works correctly.
    
    This test is skipped because interactive mode requires user input,
    which can't be simulated in an automated test without mocking the
    inquirer library at a lower level than subprocess allows.
    """
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        # Create a sample dataframe
        import pandas as pd
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        # Write to the temp file
        df.to_csv(temp.name, index=False)
        temp_path = temp.name
    
    try:
        # This would be the command to run interactive mode
        # But we can't automate the responses to the prompts
        # result = subprocess.run(
        #     ["python", "-m", "adri.cli", "interactive"],
        #     capture_output=True,
        #     text=True,
        #     input="file\n" + temp_path + "\n"  # This doesn't work with inquirer
        # )
        pass
    finally:
        # Clean up
        os.remove(temp_path)
