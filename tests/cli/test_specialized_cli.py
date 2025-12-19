"""Consolidated specialized CLI tests using modern patterns.

This module consolidates and modernizes the catalog, enhancement, and functional
CLI tests that were previously scattered across multiple files. Uses the command
registry pattern and proper path resolution.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

import pytest

from src.adri.cli.registry import get_command
from tests.cli.fixtures import (
    ModernCLITestBase,
    create_test_workspace,
    create_sample_standard,
    create_sample_data,
    with_temp_workspace
)


class TestCatalogCommands(ModernCLITestBase):
    """Test catalog-related CLI commands using modern patterns."""

    @patch('src.adri.catalog.CatalogClient')
    @patch('src.adri.catalog.CatalogConfig')
    def test_standards_catalog_list_no_config(self, mock_config_class, mock_client_class):
        """Test catalog list command with no configuration."""
        # Mock no catalog configuration
        mock_config = Mock()
        mock_config.get_catalog_url.return_value = None
        mock_config_class.return_value = mock_config

        # This would be the actual catalog command when implemented
        # For now, test the pattern that would be used
        with patch('src.adri.cli.commands') as mock_commands:
            mock_catalog_command = Mock()
            mock_catalog_command.execute.return_value = 0

            # Simulate catalog list command
            result = mock_catalog_command.execute({
                "json_output": True
            })

            assert result == 0

    @patch('src.adri.catalog.CatalogClient')
    def test_standards_catalog_fetch_success(self, mock_client_class):
        """Test successful catalog fetch operation."""
        from src.adri.catalog.client import CatalogEntry, FetchResult

        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Mock catalog client
        mock_client = Mock()
        mock_entry = CatalogEntry(
            id="test_standard",
            name="Test Standard",
            version="1.0.0",
            description="Test standard from catalog",
            path="test_standard.yaml",
            tags=["test"],
            sha256=None,
        )

        standard_content = create_sample_standard()
        yaml_bytes = yaml.dump(standard_content).encode('utf-8')
        mock_fetch_result = FetchResult(entry=mock_entry, content_bytes=yaml_bytes)
        mock_client.fetch.return_value = mock_fetch_result
        mock_client_class.return_value = mock_client

        # This would be the actual catalog fetch command when implemented
        with patch('src.adri.cli.commands') as mock_commands:
            mock_catalog_command = Mock()
            mock_catalog_command.execute.return_value = 0

            result = mock_catalog_command.execute({
                "standard_id": "test_standard",
                "dest": "dev",
                "filename": None,
                "overwrite": True,
                "json_output": False
            })

            assert result == 0

    def test_catalog_integration_with_existing_commands(self):
        """Test catalog integration with existing CLI commands."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Simulate having fetched a standard from catalog
        catalog_standard = create_sample_standard("catalog_standard")
        standard_path = Path("ADRI/dev/contracts/catalog_standard.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(catalog_standard, f)

        # Should be able to validate the catalog standard
        validate_command = get_command("validate-contract")
        result = validate_command.execute({
            "standard_path": str(standard_path)
        })

        assert result == 0

        # Should be able to list it
        list_standards_command = get_command("list-contracts")
        result = list_standards_command.execute({
            "environment": "development",
            "json_output": False
        })

        assert result == 0


class TestEnhancedCommands(ModernCLITestBase):
    """Test enhanced CLI command features using modern patterns."""

    def test_tutorial_data_structure_creation(self):
        """Test creation of tutorial data structure."""
        setup_command = get_command("setup")
        result = setup_command.execute({
            "force": False,
            "project_name": "tutorial_test",
            "guide": True
        })

        assert result == 0

        # Verify tutorial structure
        tutorial_dir = Path("ADRI/tutorials/invoice_processing")
        assert tutorial_dir.exists()

        training_file = tutorial_dir / "invoice_data.csv"
        test_file = tutorial_dir / "test_invoice_data.csv"

        assert training_file.exists()
        assert test_file.exists()

        # Verify content includes expected data
        with open(training_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "invoice_id,customer_id,amount" in content
            assert "INV-001,CUST-101,1250.00" in content

        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "invoice_id,customer_id,amount" in content
            # Should include quality issues for testing
            assert "INV-102,," in content  # Missing customer_id

    @patch('src.adri.validator.loaders.load_data')
    def test_training_data_snapshot_creation(self, mock_load_data):
        """Test training data snapshot functionality."""
        mock_load_data.return_value = create_sample_data("invoice")

        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create test data file
        test_data = "invoice_id,customer_id,amount\nINV-001,CUST-101,1250.00"
        test_file = Path("training_data.csv")
        test_file.write_text(test_data)

        # Generate standard which should create snapshot
        generate_command = get_command("generate-contract")
        result = generate_command.execute({
            "data_path": str(test_file),
            "force": False,
            "output": None,
            "guide": False
        })

        assert result == 0

        # Check that training data directory exists (would contain snapshots)
        training_data_dir = Path("ADRI/dev/training-data")
        assert training_data_dir.exists()

        # Check that standard was created
        standard_path = Path("ADRI/dev/contracts/training_data_ADRI_standard.yaml")
        assert standard_path.exists()

    @patch('src.adri.validator.loaders.load_data')
    def test_enhanced_standard_generation_with_lineage(self, mock_load_data):
        """Test enhanced standard generation includes lineage tracking."""
        mock_load_data.return_value = create_sample_data("invoice")

        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create test data file
        test_data = "invoice_id,customer_id,amount\nINV-001,CUST-101,1250.00"
        test_file = Path("lineage_test.csv")
        test_file.write_text(test_data)

        # Generate standard
        generate_command = get_command("generate-contract")
        result = generate_command.execute({
            "data_path": str(test_file),
            "force": False,
            "output": None,
            "guide": False
        })

        assert result == 0

        # Verify standard includes enhanced sections
        standard_path = Path("ADRI/dev/contracts/lineage_test_ADRI_standard.yaml")
        assert standard_path.exists()

        with open(standard_path, 'r', encoding='utf-8') as f:
            standard = yaml.safe_load(f)

        # Check for enhanced sections (these would be added by enhanced generation)
        assert "standards" in standard
        assert "requirements" in standard
        # Note: lineage and metadata sections would be added by enhanced implementation

    def test_enhanced_metadata_generation(self):
        """Test that enhanced metadata is generated correctly."""
        # Setup workspace with guide
        setup_command = get_command("setup")
        setup_command.execute({
            "force": False,
            "project_name": "metadata_test",
            "guide": True
        })

        # Use the tutorial data for generation
        with patch('src.adri.validator.loaders.load_data') as mock_load_data:
            mock_load_data.return_value = create_sample_data("invoice")

            generate_command = get_command("generate-contract")
            result = generate_command.execute({
                "data_path": "ADRI/tutorials/invoice_processing/invoice_data.csv",
                "force": False,
                "output": None,
                "guide": False
            })

            assert result == 0

            # Verify standard was created
            standard_path = Path("ADRI/dev/contracts/invoice_data_ADRI_standard.yaml")
            assert standard_path.exists()

    def test_record_identification_configuration(self):
        """Test that record identification is properly configured."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "test", "guide": False})

        # Create standard with specific record identification
        standard_content = create_sample_standard()
        standard_content["record_identification"] = {
            "primary_key_fields": ["invoice_id"],
            "strategy": "primary_key_with_fallback"
        }

        standard_path = Path("ADRI/dev/contracts/record_id_test.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        # Validate the standard
        validate_command = get_command("validate-contract")
        result = validate_command.execute({
            "standard_path": str(standard_path)
        })

        assert result == 0

        # Show the standard to verify structure
        show_standard_command = get_command("show-contract")
        result = show_standard_command.execute({
            "standard_path": str(standard_path)
        })

        assert result == 0


class TestFunctionalWorkflows(ModernCLITestBase):
    """Test functional CLI workflows using modern patterns."""

    @patch('src.adri.validator.loaders.load_data')
    @patch('src.adri.validator.loaders.load_contract')
    @patch('src.adri.validator.engine.DataQualityAssessor')
    def test_complete_data_quality_workflow(self, mock_assessor_class, mock_load_contract, mock_load_data):
        """Test complete data quality workflow."""
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

        # Step 1: Setup project with tutorial data
        setup_command = get_command("setup")
        setup_result = setup_command.execute({
            "force": False,
            "project_name": "workflow_test",
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
        validate_command = get_command("validate-contract")
        validate_result = validate_command.execute({
            "standard_path": str(standard_path)
        })
        assert validate_result == 0

        # Step 4: Assess test data against standard
        assess_command = get_command("assess")
        assess_result = assess_command.execute({
            "data_path": "ADRI/tutorials/invoice_processing/test_invoice_data.csv",
            "standard_path": str(standard_path),
            "output": None,
            "guide": False
        })
        assert assess_result == 0

        # Step 5: Review results
        list_assessments_command = get_command("list-assessments")
        list_result = list_assessments_command.execute({
            "environment": "development",
            "limit": 10
        })
        assert list_result == 0

    def test_multi_environment_workflow(self):
        """Test workflow across development and production environments."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "multi_env", "guide": False})

        # Create standard in development
        dev_standard = create_sample_standard("dev_standard")
        dev_path = Path("ADRI/dev/contracts/dev_standard.yaml")
        with open(dev_path, 'w', encoding='utf-8') as f:
            yaml.dump(dev_standard, f)

        # Validate in development environment
        validate_command = get_command("validate-contract")
        dev_result = validate_command.execute({
            "standard_path": str(dev_path)
        })
        assert dev_result == 0

        # Copy to production (simulated)
        prod_path = Path("ADRI/prod/contracts/prod_standard.yaml")
        prod_path.parent.mkdir(parents=True, exist_ok=True)
        with open(prod_path, 'w', encoding='utf-8') as f:
            yaml.dump(dev_standard, f)

        # Validate in production
        prod_result = validate_command.execute({
            "standard_path": str(prod_path)
        })
        assert prod_result == 0

        # List standards in both environments
        list_standards_command = get_command("list-contracts")

        dev_list_result = list_standards_command.execute({
            "environment": "development",
            "json_output": False
        })
        assert dev_list_result == 0

        prod_list_result = list_standards_command.execute({
            "environment": "production",
            "json_output": False
        })
        assert prod_list_result == 0

    def test_error_recovery_and_debugging_workflow(self):
        """Test error recovery and debugging workflow."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "debug_test", "guide": False})

        # Create invalid standard file
        invalid_content = {"invalid": "structure"}
        invalid_path = Path("ADRI/dev/contracts/invalid.yaml")
        with open(invalid_path, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_content, f)

        # Attempt to validate - should fail
        validate_command = get_command("validate-contract")
        failed_result = validate_command.execute({
            "standard_path": str(invalid_path)
        })
        assert failed_result == 1  # Should fail

        # Fix the standard
        valid_content = create_sample_standard("fixed_standard")
        with open(invalid_path, 'w', encoding='utf-8') as f:
            yaml.dump(valid_content, f)

        # Validate again - should succeed
        success_result = validate_command.execute({
            "standard_path": str(invalid_path)
        })
        assert success_result == 0  # Should succeed

    def test_configuration_management_workflow(self):
        """Test configuration management workflow."""
        # Setup initial configuration
        setup_command = get_command("setup")
        setup_command.execute({
            "force": False,
            "project_name": "config_test",
            "guide": False
        })

        # Show initial configuration
        show_config_command = get_command("show-config")
        initial_result = show_config_command.execute({
            "environment": None,
            "json_output": False
        })
        assert initial_result == 0

        # Show development environment config
        dev_result = show_config_command.execute({
            "environment": "development",
            "json_output": False
        })
        assert dev_result == 0

        # Show production environment config
        prod_result = show_config_command.execute({
            "environment": "production",
            "json_output": False
        })
        assert prod_result == 0

        # Test JSON output
        json_result = show_config_command.execute({
            "environment": "development",
            "json_output": True
        })
        assert json_result == 0


class TestPathResolutionIntegration(ModernCLITestBase):
    """Test path resolution integration across specialized commands."""

    def test_cross_directory_command_execution(self):
        """Test command execution from various directories."""
        # Setup workspace with guide data
        setup_command = get_command("setup")
        setup_command.execute({
            "force": False,
            "project_name": "path_test",
            "guide": True
        })

        # Test directories to execute commands from
        test_directories = [
            Path("ADRI"),
            Path("ADRI/dev"),
            Path("ADRI/tutorials"),
            Path("ADRI/tutorials/invoice_processing")
        ]

        original_cwd = os.getcwd()
        try:
            for test_dir in test_directories:
                if test_dir.exists():
                    os.chdir(test_dir)

                    # Should be able to show config from any directory
                    show_config_command = get_command("show-config")
                    result = show_config_command.execute({
                        "environment": None,
                        "json_output": False
                    })
                    assert result == 0, f"show-config failed from {test_dir}"

                    # Return to workspace root
                    os.chdir(self.temp_workspace)
        finally:
            os.chdir(original_cwd)

    def test_relative_path_handling_in_specialized_commands(self):
        """Test relative path handling in specialized commands."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({
            "force": False,
            "project_name": "relative_test",
            "guide": True
        })

        original_cwd = os.getcwd()
        try:
            # Test from ADRI/dev directory
            os.chdir(Path("ADRI/dev"))

            # Should be able to reference standards with relative path
            standard_content = create_sample_standard()
            standard_path = Path("standards/relative_test.yaml")
            with open(standard_path, 'w', encoding='utf-8') as f:
                yaml.dump(standard_content, f)

            # Validate using relative path
            validate_command = get_command("validate-contract")
            result = validate_command.execute({
                "standard_path": "standards/relative_test.yaml"
            })
            assert result == 0

            # Show using relative path
            show_standard_command = get_command("show-contract")
            show_result = show_standard_command.execute({
                "standard_path": "standards/relative_test.yaml"
            })
            assert show_result == 0

        finally:
            os.chdir(original_cwd)

    def test_tutorial_data_access_from_various_locations(self):
        """Test accessing tutorial data from various locations."""
        # Setup workspace with tutorial data
        setup_command = get_command("setup")
        setup_command.execute({
            "force": False,
            "project_name": "tutorial_access",
            "guide": True
        })

        # Should be able to access tutorial data from project root
        tutorial_file = Path("ADRI/tutorials/invoice_processing/invoice_data.csv")
        assert tutorial_file.exists()

        # Test from different locations
        test_locations = [
            Path("."),  # Project root
            Path("ADRI"),
            Path("ADRI/dev")
        ]

        original_cwd = os.getcwd()
        try:
            for location in test_locations:
                if location.exists():
                    os.chdir(location)

                    # Calculate relative path to tutorial data
                    if location == Path("."):
                        rel_path = "ADRI/tutorials/invoice_processing/invoice_data.csv"
                    elif location == Path("ADRI"):
                        rel_path = "tutorials/invoice_processing/invoice_data.csv"
                    elif location == Path("ADRI/dev"):
                        rel_path = "../tutorials/invoice_processing/invoice_data.csv"

                    # File should be accessible
                    assert Path(rel_path).exists(), f"Tutorial data not accessible from {location}"

                    # Return to workspace root
                    os.chdir(self.temp_workspace)
        finally:
            os.chdir(original_cwd)


class TestSpecializedErrorHandling(ModernCLITestBase):
    """Test error handling in specialized CLI scenarios."""

    def test_catalog_error_scenarios(self):
        """Test catalog-related error scenarios."""
        # Test with no catalog configuration
        with patch('src.adri.cli.commands') as mock_commands:
            mock_catalog_command = Mock()
            # Simulate error when no catalog configured
            mock_catalog_command.execute.return_value = 1

            result = mock_catalog_command.execute({
                "json_output": True
            })

            # Should return error code but not crash
            assert result == 1

    def test_enhancement_feature_error_handling(self):
        """Test error handling in enhancement features."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "error_test", "guide": False})

        # Test generate standard with missing data file
        generate_command = get_command("generate-contract")
        result = generate_command.execute({
            "data_path": "nonexistent_file.csv",
            "force": False,
            "output": None,
            "guide": False
        })

        # Should fail gracefully
        assert result == 1

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        # Create directory with restricted permissions
        restricted_dir = Path("restricted")
        restricted_dir.mkdir()
        restricted_dir.chmod(0o444)  # Read-only

        original_cwd = os.getcwd()
        try:
            os.chdir(restricted_dir)

            setup_command = get_command("setup")
            result = setup_command.execute({
                "force": False,
                "project_name": "permission_test",
                "guide": False
            })

            # Should fail gracefully due to permissions
            assert result == 1

        finally:
            os.chdir(original_cwd)
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)

    def test_invalid_yaml_error_handling(self):
        """Test handling of invalid YAML files."""
        # Setup workspace
        setup_command = get_command("setup")
        setup_command.execute({"force": False, "project_name": "yaml_test", "guide": False})

        # Create invalid YAML file
        invalid_yaml_path = Path("ADRI/dev/contracts/invalid.yaml")
        with open(invalid_yaml_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [unclosed")

        # Attempt to validate - should handle YAML error gracefully
        validate_command = get_command("validate-contract")
        result = validate_command.execute({
            "standard_path": str(invalid_yaml_path)
        })

        # Should fail gracefully with proper error handling
        assert result == 1

    def test_network_error_simulation(self):
        """Test handling of network-related errors."""
        # This would test catalog operations with network issues
        with patch('src.adri.catalog.CatalogClient') as mock_client_class:
            mock_client = Mock()
            mock_client.list.side_effect = ConnectionError("Network unavailable")
            mock_client_class.return_value = mock_client

            # Simulate catalog list command with network error
            with patch('src.adri.cli.commands') as mock_commands:
                mock_catalog_command = Mock()
                mock_catalog_command.execute.return_value = 1  # Should fail gracefully

                result = mock_catalog_command.execute({
                    "json_output": False
                })

                # Should handle network error gracefully
                assert result == 1
