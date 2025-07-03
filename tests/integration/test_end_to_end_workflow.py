"""
End-to-end integration tests for ADRI V2 CLI workflow.

Tests the complete workflow: generate-standard → validate-standard → assess
"""

import json
import os
import tempfile
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


class TestEndToEndWorkflow:
    """Test complete ADRI workflow from data to assessment."""
    
    def test_complete_workflow_with_cli(self):
        """
        Test the complete workflow using CLI commands:
        1. Setup project
        2. Generate standard from data
        3. Validate generated standard
        4. Run assessment with generated standard
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create sample data file
                sample_data = [
                    {"customer_id": 1001, "name": "John Doe", "email": "john@example.com", "age": 35, "registration_date": "2023-01-15", "account_balance": 1250.50},
                    {"customer_id": 1002, "name": "Jane Smith", "email": "jane@example.com", "age": 28, "registration_date": "2023-02-20", "account_balance": 2100.75},
                    {"customer_id": 1003, "name": "Bob Johnson", "email": "bob@example.com", "age": 42, "registration_date": "2023-03-10", "account_balance": 850.25},
                    {"customer_id": 1004, "name": "Alice Brown", "email": "alice@example.com", "age": 31, "registration_date": "2023-04-05", "account_balance": 3200.00},
                    {"customer_id": 1005, "name": "Charlie Wilson", "email": "charlie@example.com", "age": 29, "registration_date": "2023-05-12", "account_balance": 1750.80}
                ]
                
                # Save as CSV
                import csv
                csv_file = Path("sample_data.csv")
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                    writer.writeheader()
                    writer.writerows(sample_data)
                
                # Get path to CLI script
                cli_script = Path(original_cwd) / "scripts" / "cli.py"
                
                # Step 1: Setup ADRI project
                result = subprocess.run([
                    sys.executable, str(cli_script), "setup", "--project-name", "test-project"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Setup failed: {result.stderr}"
                assert Path("adri-config.yaml").exists(), "Config file should be created"
                assert Path("ADRI/dev/training-data").exists(), "Training data directory should be created"
                assert Path("ADRI/dev/standards").exists(), "Standards directory should be created"
                assert Path("ADRI/dev/assessments").exists(), "Assessments directory should be created"
                
                # Move sample data to training data directory
                import shutil
                shutil.move(str(csv_file), "ADRI/dev/training-data/sample_data.csv")
                
                # Step 2: Generate standard from data
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "sample_data.csv", "--verbose"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Generate standard failed: {result.stderr}"
                
                # Check that standard file was created
                standard_file = Path("ADRI/dev/standards/sample_data_ADRI_standard.yaml")
                assert standard_file.exists(), "Standard file should be created"
                
                # Verify standard file content
                with open(standard_file, 'r') as f:
                    standard_content = yaml.safe_load(f)
                
                assert "standards" in standard_content
                assert "requirements" in standard_content
                assert standard_content["standards"]["name"] == "Sample Data Quality Standard"
                assert "field_requirements" in standard_content["requirements"]
                assert "customer_id" in standard_content["requirements"]["field_requirements"]
                assert "email" in standard_content["requirements"]["field_requirements"]
                
                # Step 3: Validate generated standard
                result = subprocess.run([
                    sys.executable, str(cli_script), "validate-standard", str(standard_file), "--verbose"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Validate standard failed: {result.stderr}"
                assert "✅ Standard validation PASSED" in result.stdout
                assert "Valid YAML syntax" in result.stdout
                assert "YAMLStandards instantiation successful" in result.stdout
                
                # Step 4: Run assessment with generated standard
                result = subprocess.run([
                    sys.executable, str(cli_script), "assess", "sample_data.csv", 
                    "--standard", "sample_data_ADRI_standard.yaml", "--verbose"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Assessment failed: {result.stderr}"
                assert "Assessment Results:" in result.stdout
                assert "Overall Score:" in result.stdout
                assert "Dimension Scores:" in result.stdout
                
                # Check that assessment report was created
                assessment_files = list(Path("ADRI/dev/assessments").glob("sample_data_sample_data_ADRI_standard_assessment_*.json"))
                assert len(assessment_files) > 0, "Assessment report should be created"
                
                # Verify assessment report content
                with open(assessment_files[0], 'r') as f:
                    assessment_data = json.load(f)
                
                assert "overall_score" in assessment_data
                assert "dimension_scores" in assessment_data
                assert "passed" in assessment_data
                assert isinstance(assessment_data["overall_score"], (int, float))
                assert assessment_data["overall_score"] >= 0
                assert assessment_data["overall_score"] <= 100
                
                # Verify all dimensions are present
                expected_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]
                for dimension in expected_dimensions:
                    assert dimension in assessment_data["dimension_scores"]
                    dim_score = assessment_data["dimension_scores"][dimension]
                    assert "score" in dim_score
                    assert "percentage" in dim_score
                    assert isinstance(dim_score["score"], (int, float))
                    assert isinstance(dim_score["percentage"], (int, float))
                
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
    
    def test_workflow_with_force_overwrite(self):
        """Test workflow with force overwrite of existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create sample data
                csv_content = "id,name,value\n1,test,100\n2,test2,200"
                Path("test_data.csv").write_text(csv_content)
                
                cli_script = Path(original_cwd) / "scripts" / "cli.py"
                
                # Setup project
                result = subprocess.run([
                    sys.executable, str(cli_script), "setup"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
                # Move data to training directory
                import shutil
                shutil.move("test_data.csv", "ADRI/dev/training-data/test_data.csv")
                
                # Generate standard first time
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "test_data.csv"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
                # Try to generate again without force (should fail)
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "test_data.csv"
                ], capture_output=True, text=True)
                assert result.returncode != 0
                assert "already exists" in result.stdout
                
                # Generate again with force (should succeed)
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "test_data.csv", "--force"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
            finally:
                os.chdir(original_cwd)
    
    def test_workflow_with_invalid_data(self):
        """Test workflow error handling with invalid data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                cli_script = Path(original_cwd) / "scripts" / "cli.py"
                
                # Setup project
                result = subprocess.run([
                    sys.executable, str(cli_script), "setup"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
                # Try to generate standard from non-existent file
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "nonexistent.csv"
                ], capture_output=True, text=True)
                assert result.returncode != 0
                assert "File not found" in result.stdout
                
                # Create empty CSV file
                Path("ADRI/dev/training-data/empty.csv").write_text("")
                
                # Try to generate standard from empty file
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "empty.csv"
                ], capture_output=True, text=True)
                assert result.returncode != 0
                
            finally:
                os.chdir(original_cwd)
    
    def test_yaml_standard_structure_validation(self):
        """Test that generated YAML standard follows correct structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create comprehensive sample data
                sample_data = [
                    {"id": 1, "name": "John", "email": "john@test.com", "age": 25, "active": True, "created": "2023-01-01"},
                    {"id": 2, "name": "Jane", "email": "jane@test.com", "age": 30, "active": False, "created": "2023-01-02"},
                    {"id": 3, "name": "Bob", "email": "bob@test.com", "age": 35, "active": True, "created": "2023-01-03"}
                ]
                
                import csv
                csv_file = Path("comprehensive_data.csv")
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                    writer.writeheader()
                    writer.writerows(sample_data)
                
                cli_script = Path(original_cwd) / "scripts" / "cli.py"
                
                # Setup and generate
                subprocess.run([sys.executable, str(cli_script), "setup"], capture_output=True)
                import shutil
                shutil.move(str(csv_file), "ADRI/dev/training-data/comprehensive_data.csv")
                
                result = subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "comprehensive_data.csv"
                ], capture_output=True, text=True)
                assert result.returncode == 0
                
                # Load and validate structure
                standard_file = Path("ADRI/dev/standards/comprehensive_data_ADRI_standard.yaml")
                with open(standard_file, 'r') as f:
                    standard = yaml.safe_load(f)
                
                # Validate top-level structure
                assert "standards" in standard
                assert "requirements" in standard
                
                # Validate standards section
                standards_section = standard["standards"]
                required_fields = ["id", "name", "version", "authority", "effective_date"]
                for field in required_fields:
                    assert field in standards_section, f"Missing required field: {field}"
                
                # Validate requirements section
                requirements = standard["requirements"]
                assert "overall_minimum" in requirements
                assert "dimension_requirements" in requirements
                assert "field_requirements" in requirements
                
                # Validate dimension requirements
                dim_reqs = requirements["dimension_requirements"]
                expected_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]
                for dimension in expected_dimensions:
                    assert dimension in dim_reqs
                    assert "minimum_score" in dim_reqs[dimension]
                    assert isinstance(dim_reqs[dimension]["minimum_score"], (int, float))
                
                # Validate field requirements
                field_reqs = requirements["field_requirements"]
                expected_fields = ["id", "name", "email", "age", "active", "created"]
                for field in expected_fields:
                    assert field in field_reqs
                    field_config = field_reqs[field]
                    assert "type" in field_config
                    assert "nullable" in field_config
                    assert isinstance(field_config["nullable"], bool)
                
                # Validate specific field types
                assert field_reqs["id"]["type"] == "integer"
                assert field_reqs["name"]["type"] == "string"
                assert field_reqs["email"]["type"] == "string"
                assert field_reqs["age"]["type"] == "integer"
                assert field_reqs["active"]["type"] == "boolean"
                assert field_reqs["created"]["type"] == "date"
                
                # Validate email pattern
                assert "pattern" in field_reqs["email"]
                assert field_reqs["email"]["pattern"] == "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                
                # Validate integer constraints
                assert "min_value" in field_reqs["id"]
                assert "max_value" in field_reqs["id"]
                assert "min_value" in field_reqs["age"]
                assert "max_value" in field_reqs["age"]
                
            finally:
                os.chdir(original_cwd)
    
    def test_assessment_score_validation(self):
        """Test that assessment produces realistic and valid scores."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create high-quality data
                high_quality_data = [
                    {"customer_id": i, "name": f"Customer {i}", "email": f"customer{i}@example.com", 
                     "age": 25 + (i % 40), "registration_date": f"2023-{1 + (i % 12):02d}-{1 + (i % 28):02d}", 
                     "account_balance": 1000.0 + (i * 100)}
                    for i in range(1, 21)  # 20 high-quality records
                ]
                
                import csv
                csv_file = Path("high_quality_data.csv")
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=high_quality_data[0].keys())
                    writer.writeheader()
                    writer.writerows(high_quality_data)
                
                cli_script = Path(original_cwd) / "scripts" / "cli.py"
                
                # Setup, generate, and assess
                subprocess.run([sys.executable, str(cli_script), "setup"], capture_output=True)
                import shutil
                shutil.move(str(csv_file), "ADRI/dev/training-data/high_quality_data.csv")
                
                subprocess.run([
                    sys.executable, str(cli_script), "generate-standard", "high_quality_data.csv"
                ], capture_output=True)
                
                result = subprocess.run([
                    sys.executable, str(cli_script), "assess", "high_quality_data.csv",
                    "--standard", "high_quality_data_ADRI_standard.yaml", "--verbose"
                ], capture_output=True, text=True)
                
                assert result.returncode == 0
                
                # Extract score from output
                lines = result.stdout.split('\n')
                overall_score = None
                for line in lines:
                    if "Overall Score:" in line:
                        score_part = line.split("Overall Score:")[1].split("/")[0].strip()
                        overall_score = float(score_part)
                        break
                
                assert overall_score is not None, "Could not extract overall score"
                assert overall_score >= 80.0, f"High-quality data should score well, got {overall_score}"
                assert overall_score <= 100.0, f"Score should not exceed 100, got {overall_score}"
                
                # Check individual dimension scores
                dimension_scores = {}
                for line in lines:
                    for dimension in ["Validity", "Completeness", "Consistency", "Freshness", "Plausibility"]:
                        if f"{dimension}:" in line:
                            score_part = line.split(f"{dimension}:")[1].split("/")[0].strip()
                            dimension_scores[dimension.lower()] = float(score_part)
                
                # All dimensions should have reasonable scores for high-quality data
                for dimension, score in dimension_scores.items():
                    assert score >= 15.0, f"{dimension} score too low: {score}"
                    assert score <= 20.0, f"{dimension} score too high: {score}"
                
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
