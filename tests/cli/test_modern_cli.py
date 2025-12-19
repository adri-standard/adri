"""Modern CLI tests using the command registry pattern.

This module contains modernized CLI tests that use the refactored command
registry architecture instead of direct function calls, with proper path
resolution and isolated test environments.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml
import json

import pytest

from src.adri.cli.registry import get_command
from tests.cli.fixtures import (
    ModernCLITestBase,
    create_test_workspace,
    create_sample_standard,
    create_sample_data,
    with_temp_workspace
)


class TestModernCLICommands(ModernCLITestBase):
    """Test CLI commands using the modern registry pattern."""

    def test_setup_command_success(self):
        """Test setup command execution through registry."""
        setup_command = get_command("setup")

        # Execute setup command
        result = setup_command.execute({
            "force": False,
            "project_name": "test_project",
            "guide": False
        })

        assert result == 0

        # Verify ADRI structure was created
        assert Path("ADRI").exists()
        assert Path("ADRI/config.yaml").exists()
        assert Path("ADRI/dev/contracts").exists()
        assert Path("ADRI/dev/assessments").exists()

        # Verify config content
        with open("ADRI/config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config["adri"]["project_name"] == "test_project"
        assert config["adri"]["version"] == "4.0.0"

    def test_setup_command_with_guide(self):
        """Test setup command with guide mode through registry."""
        setup_command = get_command("setup")

        result = setup_command.execute({
            "force": False,
            "project_name": "tutorial_project",
            "guide": True
        })

        assert result == 0

        # Verify tutorial files were created
        assert Path("ADRI/tutorials/invoice_processing/invoice_data.csv").exists()
        assert Path("ADRI/tutorials/invoice_processing/test_invoice_data.csv").exists()

        # Verify tutorial data content
        with open("ADRI/tutorials/invoice_processing/invoice_data.csv", 'r', encoding='utf-8') as f:
            content = f.read()
            assert "invoice_id,customer_id,amount" in content
            assert "INV-001,CUST-101,1250.00" in content

    def test_setup_command_force_overwrite(self):
        """Test setup command with force overwrite through registry."""
        setup_command = get_command("setup")

        # Create initial setup
        result1 = setup_command.execute({
            "force": False,
            "project_name": "initial_project",
            "guide": False
        })
        assert result1 == 0

        # Attempt overwrite without force should fail
        result2 = setup_command.execute({
            "force": False,
            "project_name": "new_project",
            "guide": False
        })
        assert result2 == 1

        # Overwrite with force should succeed
        result3 = setup_command.execute({
            "force": True,
            "project_name": "new_project",
            "guide": False
        })
        assert result3 == 0

        # Verify config was updated
        with open("ADRI/config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert config["adri"]["project_name"] == "new_project"

    @patch('src.adri.validator.loaders.load_data')
    def test_generate_standard_command_success(self, mock_load_data):
        """Test generate-standard command through registry."""
        mock_load_data.return_value = create_sample_data("invoice")

        # Setup workspace first
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create test data file
        test_data = "invoice_id,customer_id,amount\nINV-001,CUST-101,1250.00"
        Path("test_data.csv").write_text(test_data)

        generate_command = get_command("generate-contract")
        result = generate_command.execute({
            "data_path": "test_data.csv",
            "force": False,
            "output": None,
            "guide": False
        })

        assert result == 0

        # Verify standard was created
        expected_standard_path = Path("ADRI/dev/contracts/test_data_ADRI_standard.yaml")
        assert expected_standard_path.exists()

        # Verify standard content
        with open(expected_standard_path, 'r', encoding='utf-8') as f:
            standard = yaml.safe_load(f)

        assert "standards" in standard
        assert "requirements" in standard
        assert standard["requirements"]["overall_minimum"] == 75.0

    @patch('src.adri.validator.loaders.load_data')
    @patch('src.adri.validator.loaders.load_contract')
    @patch('src.adri.validator.engine.DataQualityAssessor')
    def test_assess_command_success(self, mock_assessor_class, mock_load_contract, mock_load_data):
        """Test assess command through registry."""
        # Setup mocks
        mock_load_data.return_value = create_sample_data("invoice")
        mock_load_contract.return_value = create_sample_standard()

        mock_result = Mock()
        mock_result.overall_score = 85.0
        mock_result.passed = True
        mock_result.to_standard_dict.return_value = {"score": 85.0, "passed": True}

        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_result
        mock_assessor.audit_logger = None
        mock_assessor_class.return_value = mock_assessor

        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create test files
        test_data = "invoice_id,customer_id,amount\nINV-001,CUST-101,1250.00"
        Path("test_data.csv").write_text(test_data)

        standard_content = create_sample_standard()
        standard_path = Path("ADRI/dev/contracts/test_standard.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        # Execute assess command
        assess_command = get_command("assess")
        result = assess_command.execute({
            "data_path": "test_data.csv",
            "standard_path": "ADRI/dev/contracts/test_standard.yaml",
            "output": None,
            "guide": False
        })

        assert result == 0

        # Verify assessment was performed
        mock_assessor.assess.assert_called_once()

    def test_show_config_command_success(self):
        """Test show-config command through registry."""
        # Setup workspace first
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        show_config_command = get_command("show-config")
        result = show_config_command.execute({
            "environment": None,
            "json_output": False
        })

        assert result == 0

    def test_show_config_command_no_config(self):
        """Test show-config command with no configuration file."""
        show_config_command = get_command("show-config")
        result = show_config_command.execute({
            "environment": None,
            "json_output": False
        })

        # Should fail gracefully
        assert result == 1

    def test_validate_standard_command_success(self):
        """Test validate-standard command through registry."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create valid standard file
        standard_content = create_sample_standard()
        standard_path = Path("ADRI/dev/contracts/valid_standard.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        validate_command = get_command("validate-contract")
        result = validate_command.execute({
            "standard_path": str(standard_path)
        })

        assert result == 0

    def test_validate_standard_command_invalid_file(self):
        """Test validate-standard command with invalid file."""
        # Create invalid standard file
        invalid_content = {"invalid": "structure"}
        invalid_path = Path("invalid_standard.yaml")
        with open(invalid_path, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_content, f)

        validate_command = get_command("validate-contract")
        result = validate_command.execute({
            "standard_path": str(invalid_path)
        })

        assert result == 1

    def test_list_standards_command_success(self):
        """Test list-standards command through registry."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create some standard files
        for i in range(3):
            standard_content = create_sample_standard(f"standard_{i}")
            standard_path = Path(f"ADRI/dev/contracts/standard_{i}.yaml")
            with open(standard_path, 'w', encoding='utf-8') as f:
                yaml.dump(standard_content, f)

        list_standards_command = get_command("list-contracts")
        result = list_standards_command.execute({
            "environment": "development",
            "json_output": False
        })

        assert result == 0

    def test_list_standards_command_no_standards(self):
        """Test list-standards command with no standards."""
        # Setup workspace without standards
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        list_standards_command = get_command("list-contracts")
        result = list_standards_command.execute({
            "environment": "development",
            "json_output": False
        })

        assert result == 0

    def test_show_standard_command_success(self):
        """Test show-standard command through registry."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create standard file
        standard_content = create_sample_standard()
        standard_path = Path("ADRI/dev/contracts/test_standard.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        show_standard_command = get_command("show-contract")
        result = show_standard_command.execute({
            "standard_path": str(standard_path)
        })

        assert result == 0

    def test_show_standard_command_file_not_found(self):
        """Test show-standard command with non-existent file."""
        show_standard_command = get_command("show-contract")
        result = show_standard_command.execute({
            "standard_path": "nonexistent_standard.yaml"
        })

        assert result == 1

    def test_list_assessments_command_success(self):
        """Test list-assessments command through registry."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create some assessment files
        for i in range(2):
            assessment_content = {
                "assessment_id": f"test_assessment_{i}",
                "overall_score": 85.0 + i,
                "passed": True,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            assessment_path = Path(f"ADRI/dev/assessments/assessment_{i}.json")
            with open(assessment_path, 'w', encoding='utf-8') as f:
                json.dump(assessment_content, f)

        list_assessments_command = get_command("list-assessments")
        result = list_assessments_command.execute({
            "environment": "development",
            "limit": 10
        })

        assert result == 0

    def test_list_assessments_command_no_assessments(self):
        """Test list-assessments command with no assessments."""
        # Setup workspace without assessments
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        list_assessments_command = get_command("list-assessments")
        result = list_assessments_command.execute({
            "environment": "development",
            "limit": 10
        })

        assert result == 0

    def test_view_logs_command_success(self):
        """Test view-logs command through registry."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create log file
        log_content = "timestamp,action,result\n2024-01-01T00:00:00Z,setup,success"
        log_path = Path("ADRI/dev/audit-logs/adri_test.log")
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)

        view_logs_command = get_command("view-logs")
        result = view_logs_command.execute({
            "environment": "development",
            "lines": 10,
            "follow": False
        })

        assert result == 0

    def test_view_logs_command_no_logs(self):
        """Test view-logs command with no log files."""
        # Setup workspace without logs
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        view_logs_command = get_command("view-logs")
        result = view_logs_command.execute({
            "environment": "development",
            "lines": 10,
            "follow": False
        })

        # Should handle gracefully
        assert result == 0


class TestCLIPathResolution(ModernCLITestBase):
    """Test CLI path resolution with modern patterns."""

    def test_commands_work_from_subdirectories(self):
        """Test that CLI commands work from various subdirectories."""
        # Setup workspace first
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": True})

        # Test from different subdirectories
        test_dirs = [
            Path("ADRI/dev"),
            Path("ADRI/tutorials"),
            Path("ADRI/tutorials/invoice_processing")
        ]

        original_cwd = os.getcwd()
        try:
            for test_dir in test_dirs:
                if test_dir.exists():
                    os.chdir(test_dir)

                    # Should be able to show config from any directory
                    show_config_command = get_command("show-config")
                    result = show_config_command.execute({
                        "environment": None,
                        "json_output": False
                    })
                    assert result == 0, f"show-config failed from {test_dir}"

                    # Return to workspace root for next iteration
                    os.chdir(self.temp_workspace)
        finally:
            os.chdir(original_cwd)

    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        # Setup workspace with guide data
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": True})

        # Test from subdirectory using relative paths
        original_cwd = os.getcwd()
        try:
            os.chdir(Path("ADRI/dev"))

            # Should be able to access tutorial data with relative path
            show_standard_command = get_command("show-contract")

            # Create a standard to show
            standard_content = create_sample_standard()
            standard_path = Path("standards/test_standard.yaml")
            with open(standard_path, 'w', encoding='utf-8') as f:
                yaml.dump(standard_content, f)

            result = show_standard_command.execute({
                "standard_path": "standards/test_standard.yaml"
            })
            assert result == 0

        finally:
            os.chdir(original_cwd)


class TestCLIErrorHandling(ModernCLITestBase):
    """Test CLI error handling scenarios."""

    def test_command_execution_with_invalid_args(self):
        """Test command execution with invalid arguments."""
        setup_command = get_command("setup")

        # Test with invalid project name type
        with pytest.raises((TypeError, ValueError, KeyError)):
            setup_command.execute({
                "force": False,
                "project_name": 123,  # Should be string
                "guide": False
            })

    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        # Create read-only directory to simulate permission errors
        readonly_dir = Path("readonly")
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        original_cwd = os.getcwd()
        try:
            os.chdir(readonly_dir)

            setup_command = get_command("setup")
            result = setup_command.execute({
                "force": False,
                "project_name": "test",
                "guide": False
            })

            # Should fail gracefully
            assert result == 1

        finally:
            os.chdir(original_cwd)
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_missing_dependencies_handling(self):
        """Test handling when dependencies are missing."""
        with patch('src.adri.validator.loaders.load_data') as mock_load_data:
            mock_load_data.side_effect = ImportError("Required package not installed")

            setup_command = get_command("setup")
            setup_command.execute({"force": False, "project_name": "test", "guide": False})

            # Create test data file
            Path("test_data.csv").write_text("test,data\n1,value")

            generate_command = get_command("generate-contract")
            result = generate_command.execute({
                "data_path": "test_data.csv",
                "force": False,
                "output": None,
                "guide": False
            })

            # Should handle dependency error gracefully
            assert result == 1


class TestCLIIntegration(ModernCLITestBase):
    """Test end-to-end CLI workflow integration."""

    @patch('src.adri.validator.loaders.load_data')
    @patch('src.adri.validator.loaders.load_contract')
    @patch('src.adri.validator.engine.DataQualityAssessor')
    def test_complete_workflow_integration(self, mock_assessor_class, mock_load_contract, mock_load_data):
        """Test complete CLI workflow from setup to assessment."""
        # Setup mocks
        mock_load_data.return_value = create_sample_data("invoice")
        mock_load_contract.return_value = create_sample_standard()

        mock_result = Mock()
        mock_result.overall_score = 85.0
        mock_result.passed = True
        mock_result.to_standard_dict.return_value = {"score": 85.0, "passed": True}

        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_result
        mock_assessor.audit_logger = None
        mock_assessor_class.return_value = mock_assessor

        # Step 1: Setup project
        setup_command = get_command("setup")
        setup_result = setup_command.execute({
            "force": False,
            "project_name": "integration_test",
            "guide": True
        })
        assert setup_result == 0

        # Step 2: Generate standard from tutorial data
        generate_command = get_command("generate-contract")
        generate_result = generate_command.execute({
            "data_path": "ADRI/tutorials/invoice_processing/invoice_data.csv",
            "force": False,
            "output": None,
            "guide": False
        })
        assert generate_result == 0

        # Step 3: Validate the generated standard
        standard_path = Path("ADRI/dev/contracts/invoice_data_ADRI_standard.yaml")
        assert standard_path.exists()

        validate_command = get_command("validate-contract")
        validate_result = validate_command.execute({
            "standard_path": str(standard_path)
        })
        assert validate_result == 0

        # Step 4: Assess test data against the standard
        assess_command = get_command("assess")
        assess_result = assess_command.execute({
            "data_path": "ADRI/tutorials/invoice_processing/test_invoice_data.csv",
            "standard_path": str(standard_path),
            "output": None,
            "guide": False
        })
        assert assess_result == 0

        # Step 5: List created assets
        list_standards_command = get_command("list-contracts")
        list_result = list_standards_command.execute({
            "environment": "development",
            "json_output": False
        })
        assert list_result == 0

    def test_error_recovery_workflow(self):
        """Test CLI error recovery and continuation."""
        # Step 1: Setup project
        setup_command = get_command("setup")
        setup_result = setup_command.execute({
            "force": False,
            "project_name": "recovery_test",
            "guide": False
        })
        assert setup_result == 0

        # Step 2: Try to generate standard with missing file
        generate_command = get_command("generate-contract")
        failed_result = generate_command.execute({
            "data_path": "nonexistent_file.csv",
            "force": False,
            "output": None,
            "guide": False
        })
        assert failed_result == 1  # Should fail

        # Step 3: Create valid data file and retry
        test_data = "invoice_id,amount\nINV-001,1250.00"
        Path("valid_data.csv").write_text(test_data)

        with patch('src.adri.validator.loaders.load_data') as mock_load_data:
            mock_load_data.return_value = create_sample_data("invoice")

            success_result = generate_command.execute({
                "data_path": "valid_data.csv",
                "force": False,
                "output": None,
                "guide": False
            })
            assert success_result == 0  # Should succeed after fix


class TestCLIPerformance(ModernCLITestBase):
    """Test CLI performance characteristics."""

    def test_command_execution_performance(self):
        """Test that commands execute within reasonable time."""
        import time

        setup_command = get_command("setup")

        start_time = time.time()
        result = setup_command.execute({
            "force": False,
            "project_name": "performance_test",
            "guide": False
        })
        end_time = time.time()

        assert result == 0
        # Setup should complete within 5 seconds
        assert (end_time - start_time) < 5.0

    def test_large_data_handling(self):
        """Test CLI with larger datasets."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "large_test", "guide": False})

        # Create larger test dataset
        large_data = ["invoice_id,customer_id,amount,status"]
        for i in range(1000):
            large_data.append(f"INV-{i:04d},CUST-{i%100:03d},{100.0 + i},{['paid', 'pending'][i%2]}")

        large_data_content = "\n".join(large_data)
        Path("large_data.csv").write_text(large_data_content)

        with patch('src.adri.validator.loaders.load_data') as mock_load_data:
            # Create mock data that represents large dataset
            mock_large_data = create_sample_data("invoice") * 250  # 1000 records
            mock_load_data.return_value = mock_large_data

            generate_command = get_command("generate-contract")
            result = generate_command.execute({
                "data_path": "large_data.csv",
                "force": False,
                "output": None,
                "guide": False
            })

            # Should handle large data successfully
            assert result == 0
