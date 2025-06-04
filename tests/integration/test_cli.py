"""
Integration tests for the ADRI CLI.
"""

import os
import pytest
import subprocess
import json
from pathlib import Path


def test_cli_assess_command(sample_data_path):
    """Test that the CLI assess command works correctly."""
    # Run the CLI command
    import sys
    output_path = "test_cli_output"
    result = subprocess.run(
        [sys.executable, "-m", "adri.cli", "assess", "--source", sample_data_path, "--output", output_path],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output files were created
    assert os.path.exists(f"{output_path}.adri_score_report.json")
    assert os.path.exists(f"{output_path}.html")
    
    # Check the content of the JSON file
    with open(f"{output_path}.adri_score_report.json", "r") as f:
        data = json.load(f)
    
    # Verify the report structure - it's wrapped in 'adri_score_report'
    assert "adri_score_report" in data
    report = data["adri_score_report"]
    
    assert "adri_version" in report
    assert "summary" in report
    assert "overall_score" in report["summary"]
    assert "dimensions" in report
    assert "validity" in report["dimensions"]
    assert "completeness" in report["dimensions"]
    
    # Clean up
    os.remove(f"{output_path}.adri_score_report.json")
    os.remove(f"{output_path}.html")


def test_cli_report_view_command(sample_data_path):
    """Test that the CLI report view command works correctly."""
    # First create a report
    import sys
    output_path = "test_cli_view"
    subprocess.run(
        [sys.executable, "-m", "adri.cli", "assess", "--source", sample_data_path, "--output", output_path],
        capture_output=True,
        text=True
    )
    
    # Run the view command
    result = subprocess.run(
        [sys.executable, "-m", "adri.cli", "report", "view", f"{output_path}.adri_score_report.json"],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output contains key information
    assert "ADRI Score Report" in result.stdout
    assert "Overall Score" in result.stdout
    assert "Dimension Scores" in result.stdout or "Validity" in result.stdout
    
    # Clean up
    os.remove(f"{output_path}.adri_score_report.json")
    os.remove(f"{output_path}.html")


def test_cli_with_invalid_source():
    """Test that the CLI handles invalid sources correctly."""
    # Run the CLI command with a non-existent file
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "adri.cli", "assess", "--source", "nonexistent_file.csv", "--output", "test_invalid"],
        capture_output=True,
        text=True
    )
    
    # Check that the command failed
    assert result.returncode != 0
    
    # Check that the error message is helpful
    assert "Error" in result.stderr
    assert "nonexistent_file.csv" in result.stderr


def test_cli_with_custom_dimensions():
    """Test that the CLI works with custom dimensions."""
    # Create a temporary CSV file
    import tempfile
    import pandas as pd
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        # Create a sample dataframe
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        # Write to the temp file
        df.to_csv(temp.name, index=False)
        temp_path = temp.name
    
    # Run the CLI command with specific dimensions
    import sys
    output_path = "test_cli_dimensions"
    result = subprocess.run(
        [
            sys.executable, "-m", "adri.cli", "assess",
            "--source", temp_path,
            "--output", output_path,
            "--dimensions", "validity", "completeness"
        ],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check the content of the JSON file
    with open(f"{output_path}.adri_score_report.json", "r") as f:
        data = json.load(f)
    
    # Verify the report structure - it's wrapped in 'adri_score_report'
    assert "adri_score_report" in data
    report = data["adri_score_report"]
    
    # Verify that only the specified dimensions are included
    assert "validity" in report["dimensions"]
    assert "completeness" in report["dimensions"]
    assert "freshness" not in report["dimensions"]
    
    # Clean up
    os.remove(temp_path)
    os.remove(f"{output_path}.adri_score_report.json")
    os.remove(f"{output_path}.html")


def test_cli_with_config_file():
    """Test that the CLI works with a configuration file."""
    # Create a temporary CSV file
    import tempfile
    import pandas as pd
    import yaml
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_csv:
        # Create a sample dataframe
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        # Write to the temp file
        df.to_csv(temp_csv.name, index=False)
        csv_path = temp_csv.name
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as temp_config:
        config = {
            "sources": [
                {
                    "name": "Test Source",
                    "type": "file",
                    "path": csv_path
                }
            ]
        }
        
        yaml.dump(config, temp_config, default_flow_style=False)
        config_path = temp_config.name
    
    # Run the CLI command with the config file
    import sys
    output_path = "test_cli_config"
    result = subprocess.run(
        [
            sys.executable, "-m", "adri.cli", "assess",
            "--config", config_path,
            "--output", output_path
        ],
        capture_output=True,
        text=True
    )
    
    # Check that the command succeeded
    assert result.returncode == 0
    
    # Check that the output files were created
    expected_prefix = "test_source_"
    assert os.path.exists(f"{expected_prefix}report.adri_score_report.json")
    assert os.path.exists(f"{expected_prefix}report.html")
    
    # Clean up
    os.remove(csv_path)
    os.remove(config_path)
    os.remove(f"{expected_prefix}report.adri_score_report.json")
    os.remove(f"{expected_prefix}report.html")
