"""
Tests for the interactive mode of the ADRI CLI.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from adri.interactive import run_interactive_mode


@patch("adri.interactive.inquirer.prompt")
def test_interactive_mode_file_assessment(mock_prompt, sample_data_path):
    """Test that interactive mode works correctly for file assessment."""
    # Mock the user's responses to prompts
    mock_prompt.side_effect = [
        # Step 1: Select data source type
        {"source_type": "file"},
        # Step 2: Get source path
        {"source_path": sample_data_path},
        # Step 3: Select dimensions
        {"dimensions": ["validity", "completeness"]},
        # Step 4: Ask about customization
        {"customize": False},
        # Step 5: Output format selection
        {"output_formats": ["terminal", "json"], "output_path": "test_interactive"},
        # Step 6: Additional options
        {"next_action": "exit"},
    ]
    
    # Run interactive mode
    with patch("builtins.print") as mock_print:
        result = run_interactive_mode()
    
    # Check that the function returned successfully
    assert result == 0
    
    # Check that the output file was created
    assert os.path.exists("test_interactive.json")
    
    # Clean up
    os.remove("test_interactive.json")


@patch("adri.interactive.inquirer.prompt")
def test_interactive_mode_with_customization(mock_prompt, sample_data_path):
    """Test that interactive mode works correctly with customization."""
    # Mock the user's responses to prompts
    mock_prompt.side_effect = [
        # Step 1: Select data source type
        {"source_type": "file"},
        # Step 2: Get source path
        {"source_path": sample_data_path},
        # Step 3: Select dimensions
        {"dimensions": ["validity", "completeness"]},
        # Step 4: Ask about customization
        {"customize": True},
        # Step 5: Customize validity
        {"weight": "1.5", "threshold": "0.7"},
        # Step 6: Customize completeness
        {"weight": "1.2", "threshold": "0.8"},
        # Step 7: Output format selection
        {"output_formats": ["terminal", "json"], "output_path": "test_interactive_custom"},
        # Step 8: Additional options
        {"next_action": "view_dimension"},
        # Step 9: Select dimension to view
        {"dimension": "validity"},
        # Step 10: Additional options again
        {"next_action": "recommendations"},
        # Step 11: Exit
        {"next_action": "exit"},
    ]
    
    # Run interactive mode
    with patch("builtins.print") as mock_print:
        result = run_interactive_mode()
    
    # Check that the function returned successfully
    assert result == 0
    
    # Check that the output file was created
    assert os.path.exists("test_interactive_custom.json")
    
    # Clean up
    os.remove("test_interactive_custom.json")


@patch("adri.interactive.inquirer.prompt")
def test_interactive_mode_error_handling(mock_prompt):
    """Test that interactive mode handles errors correctly."""
    # Create a mock ValidationError
    from inquirer import errors
    validation_error = errors.ValidationError("", reason="File does not exist")
    
    # Make the prompt raise the error on the second call
    def side_effect(questions):
        if mock_prompt.call_count == 1:
            return {"source_type": "file"}
        else:
            raise validation_error
    
    mock_prompt.side_effect = side_effect
    
    # Run interactive mode
    with patch("builtins.print") as mock_print:
        with pytest.raises(errors.ValidationError):
            run_interactive_mode()
