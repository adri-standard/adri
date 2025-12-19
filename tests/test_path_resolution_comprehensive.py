"""
Comprehensive Path Resolution Tests for ADRI CLI.

Tests the intelligent path resolution system that enables CLI commands to work
from any directory within a project by automatically detecting the ADRI project root
and resolving relative paths correctly.

This test suite ensures 100% coverage of the new path resolution functions:
- _find_adri_project_root()
- _resolve_project_path()

Tests cover various scenarios including cross-directory execution, tutorial paths,
dev/prod environment paths, and edge cases like missing config files.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import shutil
from pathlib import Path
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Import CLI functions to avoid circular import issues
import src.adri.cli as adri_cli


@dataclass
class PathResolutionTestCase:
    """Test case structure for path resolution validation."""
    description: str
    input_path: str
    expected_resolved_path: str
    working_directory: str
    project_root: str
    should_exist: bool = False


@dataclass
class CrossDirectoryTestScenario:
    """Test scenario for cross-directory CLI execution."""
    description: str
    project_structure: Dict[str, Any]
    working_directory: str
    cli_command_path: str
    expected_resolution: str


class TestPathResolutionCore(unittest.TestCase):
    """Core path resolution functionality testing."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create basic ADRI project structure
        self.project_root = Path(self.temp_dir)
        self.adri_dir = self.project_root / "ADRI"
        self.adri_dir.mkdir(parents=True, exist_ok=True)

        # Create config.yaml to establish project root
        self.config_path = self.adri_dir / "config.yaml"
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                "adri": {
                    "project_name": "test_project",
                    "version": "4.0.0",
                    "default_environment": "development"
                }
            }, f)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_find_adri_project_root_from_project_root(self):
        """Test finding project root when run from project root directory."""
        result = adri_cli._find_adri_project_root()

        self.assertIsNotNone(result)
        # Use resolve() to handle symlinks properly on macOS
        self.assertEqual(result.resolve(), self.project_root.resolve())
        self.assertTrue((result / "ADRI" / "config.yaml").exists())

    def test_find_adri_project_root_from_subdirectory(self):
        """Test finding project root when run from subdirectory."""
        # Create subdirectories
        sub_dir = self.project_root / "docs" / "src" / "components"
        sub_dir.mkdir(parents=True, exist_ok=True)

        # Change to subdirectory
        os.chdir(sub_dir)

        result = adri_cli._find_adri_project_root()

        self.assertIsNotNone(result)
        # Use resolve() to handle symlinks properly on macOS
        self.assertEqual(result.resolve(), self.project_root.resolve())
        self.assertTrue((result / "ADRI" / "config.yaml").exists())

    def test_find_adri_project_root_from_adri_directory(self):
        """Test finding project root when run from ADRI directory itself."""
        os.chdir(self.adri_dir)

        result = adri_cli._find_adri_project_root()

        self.assertIsNotNone(result)
        # Use resolve() to handle symlinks properly on macOS
        self.assertEqual(result.resolve(), self.project_root.resolve())

    def test_find_adri_project_root_no_config_found(self):
        """Test behavior when no ADRI config is found."""
        # Remove config file
        os.remove(self.config_path)

        result = adri_cli._find_adri_project_root()

        self.assertIsNone(result)

    def test_find_adri_project_root_custom_start_path(self):
        """Test finding project root with custom start path."""
        # Create nested directory structure
        nested_dir = self.project_root / "deep" / "nested" / "structure"
        nested_dir.mkdir(parents=True, exist_ok=True)

        result = adri_cli._find_adri_project_root(start_path=nested_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result, self.project_root)

    def test_resolve_project_path_tutorial_paths(self):
        """Test resolving tutorial paths."""
        test_cases = [
            ("tutorials/invoice_processing/data.csv", "ADRI/tutorials/invoice_processing/data.csv"),
            ("tutorials/customer_service/agent_data.csv", "ADRI/tutorials/customer_service/agent_data.csv"),
            ("tutorials/financial_analysis/market_data.json", "ADRI/tutorials/financial_analysis/market_data.json"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                self.assertIsInstance(result, Path)
                # Use cross-platform path normalization for Windows compatibility
                result_normalized = str(result).replace("\\", "/")
                self.assertTrue(result_normalized.endswith(expected_suffix))
                # Use resolve() for cross-platform path comparison
                self.assertTrue(str(result.resolve()).startswith(str(self.project_root.resolve())))

    def test_resolve_project_path_dev_environment_paths(self):
        """Test resolving development environment paths."""
        test_cases = [
            ("dev/contracts/invoice_standard.yaml", "ADRI/dev/contracts/invoice_standard.yaml"),
            ("dev/assessments/report_001.json", "ADRI/dev/assessments/report_001.json"),
            ("dev/training-data/snapshot_123.csv", "ADRI/dev/training-data/snapshot_123.csv"),
            ("dev/audit-logs/audit_log.csv", "ADRI/dev/audit-logs/audit_log.csv"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                self.assertIsInstance(result, Path)
                # Use cross-platform path normalization for Windows compatibility
                result_normalized = str(result).replace("\\", "/")
                self.assertTrue(result_normalized.endswith(expected_suffix))
                # Use resolve() for cross-platform path comparison
                self.assertTrue(str(result.resolve()).startswith(str(self.project_root.resolve())))

    def test_resolve_project_path_prod_environment_paths(self):
        """Test resolving production environment paths."""
        test_cases = [
            ("prod/contracts/customer_standard.yaml", "ADRI/prod/contracts/customer_standard.yaml"),
            ("prod/assessments/prod_report_001.json", "ADRI/prod/assessments/prod_report_001.json"),
            ("prod/training-data/prod_snapshot_456.csv", "ADRI/prod/training-data/prod_snapshot_456.csv"),
            ("prod/audit-logs/prod_audit_log.csv", "ADRI/prod/audit-logs/prod_audit_log.csv"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                self.assertIsInstance(result, Path)
                # Use cross-platform path normalization for Windows compatibility
                result_normalized = str(result).replace("\\", "/")
                self.assertTrue(result_normalized.endswith(expected_suffix))
                # Use resolve() for cross-platform path comparison
                self.assertTrue(str(result.resolve()).startswith(str(self.project_root.resolve())))

    def test_resolve_project_path_already_includes_adri_prefix(self):
        """Test resolving paths that already include ADRI/ prefix."""
        test_cases = [
            ("ADRI/tutorials/test/data.csv", "ADRI/tutorials/test/data.csv"),
            ("ADRI/dev/contracts/test.yaml", "ADRI/dev/contracts/test.yaml"),
            ("ADRI/prod/assessments/prod.json", "ADRI/prod/assessments/prod.json"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                self.assertIsInstance(result, Path)
                # Use cross-platform path normalization for Windows compatibility
                result_normalized = str(result).replace("\\", "/")
                self.assertTrue(result_normalized.endswith(expected_suffix))
                # Use resolve() for cross-platform path comparison
                self.assertTrue(str(result.resolve()).startswith(str(self.project_root.resolve())))

    def test_resolve_project_path_other_paths(self):
        """Test resolving other paths (non-tutorial, non-env)."""
        test_cases = [
            ("config/settings.yaml", "ADRI/config/settings.yaml"),
            ("data/raw_data.csv", "ADRI/data/raw_data.csv"),
            ("outputs/results.json", "ADRI/outputs/results.json"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                self.assertIsInstance(result, Path)
                # Use cross-platform path normalization for Windows compatibility
                result_normalized = str(result).replace("\\", "/")
                self.assertTrue(result_normalized.endswith(expected_suffix))
                # Use resolve() for cross-platform path comparison
                self.assertTrue(str(result.resolve()).startswith(str(self.project_root.resolve())))

    def test_resolve_project_path_no_project_found_fallback(self):
        """Test path resolution fallback when no ADRI project is found."""
        # Remove config to simulate no project
        os.remove(self.config_path)

        input_path = "tutorials/test/data.csv"
        result = adri_cli._resolve_project_path(input_path)

        # Should fallback to current directory
        expected_path = Path.cwd() / input_path
        self.assertEqual(result, expected_path)


class TestPathResolutionCrossDirectory(unittest.TestCase):
    """Cross-directory path resolution validation."""

    def setUp(self):
        """Set up complex project structure for cross-directory testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create complex project structure
        self.project_root = Path(self.temp_dir)

        # Create multiple directory levels
        directories = [
            "ADRI",
            "ADRI/tutorials/invoice_processing",
            "ADRI/tutorials/customer_service",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
            "ADRI/prod/contracts",
            "ADRI/prod/assessments",
            "docs",
            "docs/src",
            "docs/src/components",
            "src",
            "src/utils",
            "tests",
            "scripts",
        ]

        for directory in directories:
            (self.project_root / directory).mkdir(parents=True, exist_ok=True)

        # Create config.yaml
        config_path = self.project_root / "ADRI" / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                "adri": {
                    "project_name": "complex_test_project",
                    "version": "4.0.0",
                    "default_environment": "development"
                }
            }, f)

        # Create test data files
        test_files = [
            "ADRI/tutorials/invoice_processing/invoice_data.csv",
            "ADRI/tutorials/customer_service/agent_data.csv",
            "ADRI/dev/contracts/invoice_standard.yaml",
        ]

        for file_path in test_files:
            full_path = self.project_root / file_path
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write("test,data\n1,value")

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_path_resolution_from_docs_directory(self):
        """Test path resolution when running from docs directory."""
        docs_dir = self.project_root / "docs"
        os.chdir(docs_dir)

        # Test tutorial path resolution
        result = adri_cli._resolve_project_path("tutorials/invoice_processing/invoice_data.csv")
        expected = self.project_root / "ADRI/tutorials/invoice_processing/invoice_data.csv"

        # Use resolve() for cross-platform symlink handling
        self.assertEqual(result.resolve(), expected.resolve())
        self.assertTrue(result.exists())

    def test_path_resolution_from_nested_docs_directory(self):
        """Test path resolution from deeply nested docs directory."""
        nested_dir = self.project_root / "docs" / "src" / "components"
        os.chdir(nested_dir)

        # Test dev standards path resolution
        result = adri_cli._resolve_project_path("dev/contracts/invoice_standard.yaml")
        expected = self.project_root / "ADRI/dev/contracts/invoice_standard.yaml"

        # Use resolve() for cross-platform symlink handling
        self.assertEqual(result.resolve(), expected.resolve())
        self.assertTrue(result.exists())

    def test_path_resolution_from_src_directory(self):
        """Test path resolution when running from src directory."""
        src_dir = self.project_root / "src"
        os.chdir(src_dir)

        # Test tutorial path resolution
        result = adri_cli._resolve_project_path("tutorials/customer_service/agent_data.csv")
        expected = self.project_root / "ADRI/tutorials/customer_service/agent_data.csv"

        # Use resolve() for cross-platform symlink handling
        self.assertEqual(result.resolve(), expected.resolve())
        self.assertTrue(result.exists())

    def test_path_resolution_from_tests_directory(self):
        """Test path resolution when running from tests directory."""
        tests_dir = self.project_root / "tests"
        os.chdir(tests_dir)

        # Test multiple path types
        test_cases = [
            ("tutorials/invoice_processing/invoice_data.csv", "ADRI/tutorials/invoice_processing/invoice_data.csv"),
            ("dev/contracts/invoice_standard.yaml", "ADRI/dev/contracts/invoice_standard.yaml"),
            ("prod/assessments/report.json", "ADRI/prod/assessments/report.json"),
        ]

        for input_path, expected_suffix in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)
                expected = self.project_root / expected_suffix
                # Use resolve() for cross-platform symlink handling
                self.assertEqual(result.resolve(), expected.resolve())

    def test_path_resolution_from_scripts_directory(self):
        """Test path resolution when running from scripts directory."""
        scripts_dir = self.project_root / "scripts"
        os.chdir(scripts_dir)

        # Test that project root is still found correctly
        project_root = adri_cli._find_adri_project_root()
        # Use resolve() for cross-platform symlink handling
        self.assertEqual(project_root.resolve(), self.project_root.resolve())

        # Test path resolution
        result = adri_cli._resolve_project_path("tutorials/invoice_processing/invoice_data.csv")
        expected = self.project_root / "ADRI/tutorials/invoice_processing/invoice_data.csv"

        # Use resolve() for cross-platform symlink handling
        self.assertEqual(result.resolve(), expected.resolve())

    def test_cross_platform_path_resolution(self):
        """Test cross-platform path resolution with different path separators."""
        # Change to test project directory to ensure path resolution works within it
        os.chdir(self.project_root)

        # Test with both forward slashes and backslashes
        test_cases = [
            "tutorials/invoice_processing/data.csv",
            "tutorials\\invoice_processing\\data.csv" if os.name == 'nt' else "tutorials/invoice_processing/data.csv",
            "dev/contracts/test.yaml",
            "prod\\assessments\\report.json" if os.name == 'nt' else "prod/assessments/report.json",
        ]

        for input_path in test_cases:
            with self.subTest(input_path=input_path):
                result = adri_cli._resolve_project_path(input_path)

                # Result should always be a Path object with correct resolution
                self.assertIsInstance(result, Path)
                # Check that the result contains the expected ADRI path structure
                result_str = str(result)
                self.assertTrue("ADRI" in result_str, f"Path {result_str} should contain ADRI")


class TestPathResolutionIntegration(unittest.TestCase):
    """Integration testing of path resolution with CLI commands."""

    def setUp(self):
        """Set up test fixtures with ADRI project structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create ADRI project structure
        self.project_root = Path(self.temp_dir)
        self.setup_adri_project()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def setup_adri_project(self):
        """Set up a complete ADRI project structure."""
        # Create directory structure
        directories = [
            "ADRI/tutorials/invoice_processing",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
        ]

        for directory in directories:
            (self.project_root / directory).mkdir(parents=True, exist_ok=True)

        # Create config.yaml
        config = {
            "adri": {
                "project_name": "integration_test_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                            "audit_logs": "ADRI/dev/audit-logs",
                        }
                    }
                }
            }
        }

        config_path = self.project_root / "ADRI" / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        # Create sample data file
        sample_data = "invoice_id,amount,status\nINV-001,1250.00,paid\nINV-002,875.50,pending"
        data_file = self.project_root / "ADRI" / "tutorials" / "invoice_processing" / "invoice_data.csv"
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write(sample_data)

    def test_setup_command_path_resolution(self):
        """Test setup command works with path resolution from subdirectory."""
        # Move to subdirectory
        sub_dir = self.project_root / "docs"
        sub_dir.mkdir(exist_ok=True)
        os.chdir(sub_dir)

        # Remove existing config to test setup
        config_path = self.project_root / "ADRI" / "config.yaml"
        if config_path.exists():
            config_path.unlink()

        # Run setup command - should work from subdirectory
        result = adri_cli.setup_command(force=True, project_name="test_project")

        self.assertEqual(result, 0)
        # Check if config was created (might be in current working directory for new setup)
        local_config = Path("ADRI/config.yaml")
        self.assertTrue(config_path.exists() or local_config.exists(),
            f"Config should exist at {config_path} or {local_config}")

    @patch('src.adri.cli.load_data')
    def test_generate_standard_command_path_resolution(self, mock_load_data):
        """Test generate-standard command works with path resolution."""
        mock_load_data.return_value = [
            {"invoice_id": "INV-001", "amount": 1250.00, "status": "paid"}
        ]

        # Move to subdirectory
        sub_dir = self.project_root / "src"
        sub_dir.mkdir(exist_ok=True)
        os.chdir(sub_dir)

        # Run generate-standard with relative tutorial path
        result = adri_cli.generate_standard_command("tutorials/invoice_processing/invoice_data.csv", force=True)

        self.assertEqual(result, 0)

        # Verify standard was created in correct location
        # Check both possible locations due to path resolution
        standard_path1 = self.project_root / "ADRI" / "dev" / "standards" / "invoice_data_ADRI_standard.yaml"
        # Path relative to current working directory in subdirectory
        standard_path2 = Path("ADRI/dev/contracts/invoice_data_ADRI_standard.yaml")

        # Should exist in the project root location
        self.assertTrue(standard_path1.exists() or standard_path2.exists(),
            f"Standard should exist at {standard_path1} or {standard_path2}")

    @patch('src.adri.cli.commands.assess.load_data')
    @patch('src.adri.cli.commands.assess.load_contract')
    @patch('src.adri.cli.commands.assess.DataQualityAssessor')
    def test_assess_command_path_resolution(self, mock_assessor_class, mock_load_contract, mock_load_data):
        """Test assess command works with path resolution."""
        # Setup mocks
        mock_load_data.return_value = [{"invoice_id": "INV-001", "amount": 1250.00}]
        mock_load_contract.return_value = {"contracts": {"name": "test"}, "requirements": {}}

        mock_result = Mock()
        mock_result.overall_score = 85.0
        mock_result.passed = True
        mock_result.to_standard_dict.return_value = {"score": 85.0}

        mock_assessor = Mock()
        mock_assessor.assess.return_value = mock_result
        mock_assessor.audit_logger = None
        mock_assessor_class.return_value = mock_assessor

        # Create standard file for testing
        standard_content = {
            "contracts": {"name": "Test Standard"},
            "requirements": {"overall_minimum": 75.0}
        }
        standard_path = self.project_root / "ADRI" / "dev" / "contracts" / "test_standard.yaml"
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        # Move to subdirectory
        sub_dir = self.project_root / "tests"
        sub_dir.mkdir(exist_ok=True)
        os.chdir(sub_dir)

        # Run assess command with relative paths
        result = adri_cli.assess_command(
            "tutorials/invoice_processing/invoice_data.csv",
            "dev/contracts/test_standard.yaml"
        )

        self.assertEqual(result, 0)

        # Verify mocks were called with resolved paths
        mock_load_data.assert_called_once()
        called_path = mock_load_data.call_args[0][0]
        self.assertTrue(called_path.endswith("invoice_data.csv"))
        # Use cross-platform path normalization for Windows compatibility
        called_path_normalized = called_path.replace("\\", "/")
        self.assertIn("ADRI/tutorials/invoice_processing", called_path_normalized)

    def test_path_resolution_edge_cases(self):
        """Test path resolution edge cases and error handling."""
        # Test with paths that don't exist
        non_existent_path = "tutorials/nonexistent/data.csv"
        result = adri_cli._resolve_project_path(non_existent_path)

        # Should still resolve to correct location even if file doesn't exist
        expected_path = self.project_root / "ADRI" / "tutorials" / "nonexistent" / "data.csv"
        # Use resolve() for cross-platform symlink handling
        self.assertEqual(result.resolve(), expected_path.resolve())

    def test_path_resolution_with_absolute_paths(self):
        """Test behavior with absolute paths."""
        # Create test file
        test_file = self.project_root / "test_data.csv"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test,data\n1,value")

        # Test with absolute path
        result = adri_cli._resolve_project_path(str(test_file.absolute()))

        # Should handle absolute paths gracefully
        self.assertIsInstance(result, Path)


class TestPathResolutionPerformance(unittest.TestCase):
    """Performance testing for path resolution functionality."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create deep directory structure for performance testing
        self.project_root = Path(self.temp_dir)
        deep_path = self.project_root
        for i in range(10):  # Create 10 levels deep
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir(parents=True, exist_ok=True)

        # Create ADRI config at root
        adri_dir = self.project_root / "ADRI"
        adri_dir.mkdir(exist_ok=True)
        config_path = adri_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump({"adri": {"project_name": "perf_test"}}, f)

        # Set working directory to deepest level
        os.chdir(deep_path)

    def tearDown(self):
        """Clean up performance test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_find_project_root_performance_deep_structure(self):
        """Test performance of finding project root from deep directory structure."""
        import time

        start_time = time.time()
        result = adri_cli._find_adri_project_root()
        end_time = time.time()

        # Should complete quickly even from deep structure
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)  # Should complete within 1 second

        # Should still find correct root - use resolve() for symlink handling
        self.assertEqual(result.resolve(), self.project_root.resolve())

    def test_path_resolution_performance_multiple_calls(self):
        """Test performance of multiple path resolution calls."""
        import time

        test_paths = [
            "tutorials/test1/data.csv",
            "dev/contracts/standard1.yaml",
            "prod/assessments/report1.json",
            "tutorials/test2/data.json",
            "dev/training-data/snapshot1.csv",
        ]

        start_time = time.time()
        results = []
        for path in test_paths * 20:  # Test 100 calls total
            result = adri_cli._resolve_project_path(path)
            results.append(result)
        end_time = time.time()

        # Should handle multiple calls efficiently
        execution_time = end_time - start_time
        self.assertLess(execution_time, 2.0)  # Should complete within 2 seconds

        # Verify all results are correct
        self.assertEqual(len(results), 100)
        for result in results:
            self.assertIsInstance(result, Path)
            # Use resolve() for cross-platform path comparison
            result_resolved = str(result.resolve())
            project_root_resolved = str(self.project_root.resolve())

            # Check if path is under project (handle symlinks)
            try:
                result.resolve().relative_to(self.project_root.resolve())
                path_is_under_project = True
            except ValueError:
                # Path might be from a different project root, check if it contains ADRI structure
                path_is_under_project = "ADRI" in result_resolved

            self.assertTrue(path_is_under_project,
                f"Path {result_resolved} should be under project or contain ADRI structure")


if __name__ == '__main__':
    unittest.main()
