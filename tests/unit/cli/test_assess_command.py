"""
Tests for the assess command implementation.

Following TDD approach: RED → GREEN → REFACTOR
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from adri.cli.commands import assess_command
from adri.core.assessor import AssessmentResult, DimensionScore


class TestAssessCommand:
    """Test suite for adri assess command."""
    
    def test_assess_command_with_csv_and_yaml_standard(self):
        """Test basic assess command with CSV data and YAML standard."""
        # This test will fail initially - we haven't implemented assess_command yet
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test CSV file
            csv_file = Path(temp_dir) / "test_data.csv"
            csv_file.write_text("name,email,age\nJohn,john@test.com,25\nJane,jane@test.com,30")
            
            # Create test YAML standard
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
    email:
      type: "string"
      nullable: false
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"
    age:
      type: "integer"
      min_value: 0
      max_value: 150
""")
            
            # Run assess command
            result = assess_command(
                data_path=str(csv_file),
                standard_path=str(yaml_file)
            )
            
            # Should return 0 for success
            assert result == 0
    
    def test_assess_command_with_json_data(self):
        """Test assess command with JSON data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test JSON file
            json_file = Path(temp_dir) / "test_data.json"
            json_data = [
                {"name": "John", "email": "john@test.com", "age": 25},
                {"name": "Jane", "email": "jane@test.com", "age": 30}
            ]
            json_file.write_text(json.dumps(json_data))
            
            # Create test YAML standard
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
""")
            
            result = assess_command(
                data_path=str(json_file),
                standard_path=str(yaml_file)
            )
            
            assert result == 0
    
    def test_assess_command_missing_data_file(self):
        """Test assess command with missing data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("standards:\n  id: test")
            
            result = assess_command(
                data_path="/nonexistent/file.csv",
                standard_path=str(yaml_file)
            )
            
            # Should return non-zero for error
            assert result != 0
    
    def test_assess_command_missing_standard_file(self):
        """Test assess command with missing standard file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = Path(temp_dir) / "test_data.csv"
            csv_file.write_text("name\nJohn")
            
            result = assess_command(
                data_path=str(csv_file),
                standard_path="/nonexistent/standard.yaml"
            )
            
            assert result != 0
    
    def test_assess_command_invalid_yaml_standard(self):
        """Test assess command with invalid YAML standard."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = Path(temp_dir) / "test_data.csv"
            csv_file.write_text("name\nJohn")
            
            yaml_file = Path(temp_dir) / "invalid_standard.yaml"
            yaml_file.write_text("invalid: yaml: content: [")
            
            result = assess_command(
                data_path=str(csv_file),
                standard_path=str(yaml_file)
            )
            
            assert result != 0
    
    def test_assess_command_with_output_file(self):
        """Test assess command with JSON output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            csv_file = Path(temp_dir) / "test_data.csv"
            csv_file.write_text("name\nJohn")
            
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
""")
            
            output_file = Path(temp_dir) / "assessment_report.json"
            
            result = assess_command(
                data_path=str(csv_file),
                standard_path=str(yaml_file),
                output_path=str(output_file)
            )
            
            assert result == 0
            assert output_file.exists()
            
            # Verify output file contains valid JSON
            with open(output_file) as f:
                report_data = json.load(f)
                assert "overall_score" in report_data
                assert "dimension_scores" in report_data
    
    def test_assess_command_with_verbose_output(self):
        """Test assess command with verbose console output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = Path(temp_dir) / "test_data.csv"
            csv_file.write_text("name\nJohn")
            
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
""")
            
            # Capture stdout to verify verbose output
            with patch('builtins.print') as mock_print:
                result = assess_command(
                    data_path=str(csv_file),
                    standard_path=str(yaml_file),
                    verbose=True
                )
                
                assert result == 0
                # Verify verbose output was printed
                assert mock_print.called
                # Check that detailed assessment info was printed
                printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
                assert "Assessment Results" in printed_output or "overall_score" in printed_output
    
    def test_assess_command_unsupported_file_format(self):
        """Test assess command with unsupported file format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create unsupported file format
            txt_file = Path(temp_dir) / "test_data.txt"
            txt_file.write_text("some random text content")
            
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("standards:\n  id: test")
            
            result = assess_command(
                data_path=str(txt_file),
                standard_path=str(yaml_file)
            )
            
            assert result != 0
    
    def test_assess_command_empty_data_file(self):
        """Test assess command with empty data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty CSV file
            csv_file = Path(temp_dir) / "empty_data.csv"
            csv_file.write_text("")
            
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
""")
            
            result = assess_command(
                data_path=str(csv_file),
                standard_path=str(yaml_file)
            )
            
            assert result != 0
    
    def test_assess_command_with_parquet_data(self):
        """Test assess command with Parquet data file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data as CSV first, then convert to Parquet
            import pandas as pd
            
            # Create test data
            test_data = [
                {"name": "John", "email": "john@test.com", "age": 25},
                {"name": "Jane", "email": "jane@test.com", "age": 30}
            ]
            df = pd.DataFrame(test_data)
            
            # Save as Parquet
            parquet_file = Path(temp_dir) / "test_data.parquet"
            df.to_parquet(parquet_file, index=False)
            
            # Create test YAML standard
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
    email:
      type: "string"
      nullable: false
    age:
      type: "integer"
      min_value: 0
      max_value: 150
""")
            
            result = assess_command(
                data_path=str(parquet_file),
                standard_path=str(yaml_file)
            )
            
            assert result == 0


class TestDataLoader:
    """Test suite for data loading functionality."""
    
    def test_load_csv_data(self):
        """Test loading CSV data."""
        # This will fail initially - we need to implement load_data function
        from adri.cli.commands import load_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = Path(temp_dir) / "test.csv"
            csv_file.write_text("name,age\nJohn,25\nJane,30")
            
            data = load_data(str(csv_file))
            
            assert len(data) == 2
            assert data[0]["name"] == "John"
            assert data[0]["age"] == "25"  # CSV loads as strings initially
    
    def test_load_json_data(self):
        """Test loading JSON data."""
        from adri.cli.commands import load_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "test.json"
            json_data = [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]
            json_file.write_text(json.dumps(json_data))
            
            data = load_data(str(json_file))
            
            assert len(data) == 2
            assert data[0]["name"] == "John"
            assert data[0]["age"] == 25
    
    def test_load_parquet_data(self):
        """Test loading Parquet data."""
        from adri.cli.commands import load_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            import pandas as pd
            
            # Create test data and save as Parquet
            test_data = [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]
            df = pd.DataFrame(test_data)
            
            parquet_file = Path(temp_dir) / "test.parquet"
            df.to_parquet(parquet_file, index=False)
            
            data = load_data(str(parquet_file))
            
            assert len(data) == 2
            assert data[0]["name"] == "John"
            assert data[0]["age"] == 25
    
    def test_load_data_file_not_found(self):
        """Test loading data from non-existent file."""
        from adri.cli.commands import load_data
        
        with pytest.raises(FileNotFoundError):
            load_data("/nonexistent/file.csv")


class TestStandardLoader:
    """Test suite for YAML standard loading functionality."""
    
    def test_load_yaml_standard(self):
        """Test loading YAML standard file."""
        from adri.cli.commands import load_standard
        
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file = Path(temp_dir) / "test_standard.yaml"
            yaml_file.write_text("""
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    name:
      type: "string"
      nullable: false
""")
            
            standard = load_standard(str(yaml_file))
            
            assert standard.standards_id == "test-standard"
            assert standard.standards_name == "Test Standard"
    
    def test_load_standard_file_not_found(self):
        """Test loading standard from non-existent file."""
        from adri.cli.commands import load_standard
        
        with pytest.raises(FileNotFoundError):
            load_standard("/nonexistent/standard.yaml")
    
    def test_load_invalid_yaml_standard(self):
        """Test loading invalid YAML standard."""
        from adri.cli.commands import load_standard
        
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_file = Path(temp_dir) / "invalid.yaml"
            yaml_file.write_text("invalid: yaml: content: [")
            
            with pytest.raises(Exception):  # Should raise YAML parsing error
                load_standard(str(yaml_file))
