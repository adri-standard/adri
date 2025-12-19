"""
Validator Loaders Tests - Multi-Dimensional Quality Framework
Tests data loading functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import json
import csv
import yaml
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest

from src.adri.validator.loaders import (
    load_data,
    load_csv,
    load_json,
    load_parquet,
    load_contract,
    detect_format,
    get_data_info,
    _get_csv_info,
    _get_json_info,
    _get_parquet_info
)


class TestDataLoaderIntegration(unittest.TestCase):
    """Test complete data loading workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_complete_csv_loading_workflow(self):
        """Test end-to-end CSV loading workflow with format detection."""
        # Create comprehensive CSV test data
        csv_data = [
            ["customer_id", "name", "email", "age", "balance"],
            ["CUST_001", "John Doe", "john@example.com", "25", "1000.50"],
            ["CUST_002", "Jane Smith", "jane@domain.com", "35", "2500.75"],
            ["CUST_003", "Bob Wilson", "bob@company.com", "45", "750.25"]
        ]

        csv_file = Path("test_customers.csv")
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        # Test format detection integration
        detected_format = detect_format(str(csv_file))
        self.assertEqual(detected_format, "csv")

        # Test file info integration
        file_info = get_data_info(str(csv_file))
        self.assertEqual(file_info["format"], "csv")
        self.assertEqual(file_info["columns"], 5)
        self.assertEqual(file_info["estimated_rows"], 3)
        self.assertEqual(file_info["column_names"], ["customer_id", "name", "email", "age", "balance"])

        # Test complete data loading integration
        loaded_data = load_data(str(csv_file))
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]["customer_id"], "CUST_001")
        self.assertEqual(loaded_data[0]["name"], "John Doe")
        self.assertEqual(loaded_data[1]["email"], "jane@domain.com")
        self.assertEqual(loaded_data[2]["balance"], "750.25")

    def test_complete_json_loading_workflow(self):
        """Test end-to-end JSON loading workflow with nested structures."""
        # Create comprehensive JSON test data
        json_data = [
            {
                "order_id": "ORD_001",
                "customer": {
                    "id": "CUST_001",
                    "name": "John Doe"
                },
                "items": [
                    {"product": "Widget A", "quantity": 2, "price": 15.99},
                    {"product": "Widget B", "quantity": 1, "price": 25.50}
                ],
                "total": 57.48,
                "status": "completed"
            },
            {
                "order_id": "ORD_002",
                "customer": {
                    "id": "CUST_002",
                    "name": "Jane Smith"
                },
                "items": [
                    {"product": "Widget C", "quantity": 3, "price": 12.75}
                ],
                "total": 38.25,
                "status": "pending"
            }
        ]

        json_file = Path("test_orders.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Test format detection integration
        detected_format = detect_format(str(json_file))
        self.assertEqual(detected_format, "json")

        # Test file info integration
        file_info = get_data_info(str(json_file))
        self.assertEqual(file_info["format"], "json")
        self.assertEqual(file_info["records"], 2)
        self.assertEqual(file_info["columns"], 5)
        self.assertIn("order_id", file_info["column_names"])
        self.assertIn("customer", file_info["column_names"])

        # Test complete data loading integration
        loaded_data = load_data(str(json_file))
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["order_id"], "ORD_001")
        self.assertEqual(loaded_data[0]["customer"]["name"], "John Doe")
        self.assertEqual(len(loaded_data[0]["items"]), 2)
        self.assertEqual(loaded_data[1]["status"], "pending")

    @patch('src.adri.validator.loaders.pd')
    def test_complete_parquet_loading_workflow(self, mock_pd):
        """Test end-to-end Parquet loading workflow with mocked pandas."""
        # Mock pandas DataFrame
        mock_df = Mock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"product_id": "PROD_001", "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"product_id": "PROD_002", "name": "Mouse", "price": 29.99, "category": "Accessories"},
            {"product_id": "PROD_003", "name": "Monitor", "price": 299.99, "category": "Electronics"}
        ]
        mock_df.columns = ["product_id", "name", "price", "category"]
        mock_df.__len__ = Mock(return_value=3)
        mock_df.dtypes = {
            "product_id": "object",
            "name": "object",
            "price": "float64",
            "category": "object"
        }

        mock_pd.read_parquet.return_value = mock_df

        # Create test parquet file (just touch it, pandas is mocked)
        parquet_file = Path("test_products.parquet")
        parquet_file.touch()

        # Test format detection integration
        detected_format = detect_format(str(parquet_file))
        self.assertEqual(detected_format, "parquet")

        # Test file info integration
        file_info = get_data_info(str(parquet_file))
        self.assertEqual(file_info["format"], "parquet")
        self.assertEqual(file_info["rows"], 3)
        self.assertEqual(file_info["columns"], 4)
        self.assertEqual(file_info["column_names"], ["product_id", "name", "price", "category"])

        # Test complete data loading integration
        loaded_data = load_data(str(parquet_file))
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]["product_id"], "PROD_001")
        self.assertEqual(loaded_data[1]["price"], 29.99)
        self.assertEqual(loaded_data[2]["category"], "Electronics")

    def test_yaml_standard_loading_workflow(self):
        """Test end-to-end YAML standard loading workflow."""
        # Create comprehensive YAML standard
        standard_data = {
            "contracts": {
                "id": "customer_data_standard",
                "name": "Customer Data Quality Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Comprehensive customer data quality requirements"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimensions": {
                    "validity": 85.0,
                    "completeness": 90.0,
                    "consistency": 80.0,
                    "freshness": 70.0,
                    "plausibility": 75.0
                },
                "dimension_requirements": {
                    "validity": {"weight": 0.25},
                    "completeness": {"weight": 0.25},
                    "consistency": {"weight": 0.20},
                    "freshness": {"weight": 0.15},
                    "plausibility": {"weight": 0.15}
                }
            },
            "dimensions": {
                "validity": {
                    "rules": [
                        {"field": "email", "type": "email_format"},
                        {"field": "age", "type": "numeric_range", "min": 0, "max": 150}
                    ]
                },
                "completeness": {
                    "required_fields": ["customer_id", "name", "email"],
                    "null_threshold": 5.0
                }
            }
        }

        yaml_file = Path("customer_standard.yaml")
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(standard_data, f, default_flow_style=False)

        # Test format detection integration
        detected_format = detect_format(str(yaml_file))
        self.assertEqual(detected_format, "yaml")

        # Test standard loading integration
        loaded_standard = load_contract(str(yaml_file))
        self.assertEqual(loaded_standard["contracts"]["id"], "customer_data_standard")
        self.assertEqual(loaded_standard["requirements"]["overall_minimum"], 80.0)
        self.assertEqual(len(loaded_standard["dimensions"]["validity"]["rules"]), 2)
        self.assertIn("completeness", loaded_standard["dimensions"])

    def test_multi_format_detection_workflow(self):
        """Test format detection across multiple file types."""
        test_files = {
            "data.csv": "csv",
            "data.json": "json",
            "data.parquet": "parquet",
            "standard.yaml": "yaml",
            "config.yml": "yaml",
            "unknown.txt": "unknown",
            "data.CSV": "csv",  # Test case insensitivity
            "DATA.JSON": "json"
        }

        for filename, expected_format in test_files.items():
            test_file = Path(filename)
            test_file.touch()  # Create empty file

            detected = detect_format(str(test_file))
            self.assertEqual(detected, expected_format,
                           f"Failed to detect format for {filename}")

    def test_large_dataset_integration_workflow(self):
        """Test integration with large dataset processing."""
        # Create large CSV dataset
        large_csv = Path("large_dataset.csv")
        with open(large_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "data", "value", "category", "timestamp"])

            # Write 1000 rows of test data
            for i in range(1000):
                writer.writerow([
                    f"ID_{i:04d}",
                    f"data_value_{i}",
                    i * 1.5,
                    f"category_{i % 10}",
                    f"2024-03-{(i % 28) + 1:02d}T10:30:00Z"
                ])

        # Test file info for large dataset
        file_info = get_data_info(str(large_csv))
        self.assertEqual(file_info["estimated_rows"], 1000)
        self.assertEqual(file_info["columns"], 5)
        self.assertGreater(file_info["size_bytes"], 10000)  # Should be substantial

        # Test loading large dataset
        loaded_data = load_data(str(large_csv))
        self.assertEqual(len(loaded_data), 1000)
        self.assertEqual(loaded_data[0]["id"], "ID_0000")
        self.assertEqual(loaded_data[999]["id"], "ID_0999")


class TestDataLoaderErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios (25% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_file_not_found_errors(self):
        """Test comprehensive file not found error handling."""
        # Test load_data with non-existent file
        with self.assertRaises(FileNotFoundError) as cm:
            load_data("non_existent.csv")
        self.assertIn("Data file not found", str(cm.exception))

        # Test load_contract with non-existent file
        with self.assertRaises(FileNotFoundError) as cm:
            load_contract("non_existent.yaml")
        self.assertIn("Contract file not found", str(cm.exception))

        # Test detect_format with non-existent file
        with self.assertRaises(FileNotFoundError) as cm:
            detect_format("non_existent.txt")
        self.assertIn("File not found", str(cm.exception))

        # Test get_data_info with non-existent file
        with self.assertRaises(FileNotFoundError) as cm:
            get_data_info("non_existent.csv")
        self.assertIn("File not found", str(cm.exception))

    def test_unsupported_format_errors(self):
        """Test unsupported file format error handling."""
        # Create file with unsupported extension
        unsupported_file = Path("data.txt")
        with open(unsupported_file, 'w', encoding='utf-8') as f:
            f.write("some content")

        with self.assertRaises(ValueError) as cm:
            load_data(str(unsupported_file))
        self.assertIn("Unsupported file format", str(cm.exception))

    def test_empty_file_errors(self):
        """Test empty file error handling."""
        # Test empty CSV file
        empty_csv = Path("empty.csv")
        empty_csv.touch()  # Create empty file

        with self.assertRaises(ValueError) as cm:
            load_csv(empty_csv)
        self.assertIn("CSV file is empty", str(cm.exception))

        # Test CSV with only headers
        header_only_csv = Path("header_only.csv")
        with open(header_only_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "value"])

        # CSV with only headers should either raise an error or return empty list
        try:
            loaded_data = load_csv(header_only_csv)
            # If no error, should return empty list
            self.assertEqual(len(loaded_data), 0)
        except ValueError as e:
            # If error raised, should mention empty file
            self.assertIn("CSV file is empty", str(e))

    def test_malformed_json_errors(self):
        """Test malformed JSON error handling."""
        # Test invalid JSON syntax
        invalid_json = Path("invalid.json")
        with open(invalid_json, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json syntax}')

        with self.assertRaises(json.JSONDecodeError):
            load_json(invalid_json)

        # Test JSON that's not a list
        non_list_json = Path("non_list.json")
        with open(non_list_json, 'w', encoding='utf-8') as f:
            json.dump({"not": "a list"}, f)

        with self.assertRaises(ValueError) as cm:
            load_json(non_list_json)
        self.assertIn("JSON file must contain a list", str(cm.exception))

    def test_parquet_without_pandas_error(self):
        """Test Parquet loading without pandas installed."""
        # Mock pandas as None to simulate missing dependency
        parquet_file = Path("test.parquet")
        parquet_file.touch()

        with patch('src.adri.validator.loaders.pd', None):
            with self.assertRaises(ImportError) as cm:
                load_parquet(parquet_file)
            self.assertIn("pandas is required", str(cm.exception))

    @patch('src.adri.validator.loaders.pd')
    def test_parquet_loading_errors(self, mock_pd):
        """Test Parquet loading error scenarios."""
        parquet_file = Path("test.parquet")
        parquet_file.touch()

        # Test empty DataFrame
        mock_empty_df = Mock()
        mock_empty_df.empty = True
        mock_pd.read_parquet.return_value = mock_empty_df

        with self.assertRaises(ValueError) as cm:
            load_parquet(parquet_file)
        self.assertIn("Parquet file is empty", str(cm.exception))

        # Test Parquet reading exception
        mock_pd.read_parquet.side_effect = Exception("Parquet reading error")

        with self.assertRaises(ValueError) as cm:
            load_parquet(parquet_file)
        self.assertIn("Failed to read Parquet file", str(cm.exception))

        # Test generic exception
        mock_pd.read_parquet.side_effect = RuntimeError("Generic error")

        with self.assertRaises(RuntimeError):
            load_parquet(parquet_file)

    def test_yaml_loading_errors(self):
        """Test YAML loading error scenarios."""
        # Test invalid YAML syntax
        invalid_yaml = Path("invalid.yaml")
        with open(invalid_yaml, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [\n  - unclosed list")

        with self.assertRaises(Exception) as cm:
            load_contract(str(invalid_yaml))
        self.assertIn("Invalid YAML format", str(cm.exception))

        # Test file reading error (simulate by creating and then removing file)
        missing_yaml = Path("missing.yaml")
        missing_yaml.touch()
        missing_yaml.unlink()  # Delete file

        with self.assertRaises(FileNotFoundError):
            load_contract(str(missing_yaml))

    def test_permission_denied_errors(self):
        """Test file permission error scenarios."""
        # Create a file and remove read permissions (Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            restricted_file = Path("restricted.csv")
            with open(restricted_file, 'w', encoding='utf-8') as f:
                f.write("id,name\n1,test\n")

            # Remove read permissions
            os.chmod(restricted_file, 0o000)

            try:
                with self.assertRaises(PermissionError):
                    load_data(str(restricted_file))
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_file, 0o644)

    def test_encoding_errors(self):
        """Test file encoding error handling."""
        # Create file with non-UTF-8 encoding
        encoded_file = Path("encoded.csv")
        with open(encoded_file, "w", encoding="latin-1") as f:
            f.write("id,name\n1,José\n")

        # This should handle encoding gracefully or raise appropriate error
        try:
            load_data(str(encoded_file))
        except UnicodeDecodeError:
            pass  # Expected behavior for encoding mismatch
        except Exception as e:
            # Should be a handled exception
            self.assertIsInstance(e, (UnicodeError, ValueError))

    def test_corrupted_file_errors(self):
        """Test handling of corrupted file data."""
        # Create CSV with mixed field counts
        corrupted_csv = Path("corrupted.csv")
        with open(corrupted_csv, 'w', encoding='utf-8') as f:
            f.write("id,name,email\n")
            f.write("1,John\n")  # Missing field
            f.write("2,Jane,jane@example.com,extra_field\n")  # Extra field

        # Should handle gracefully (csv.DictReader is usually tolerant)
        loaded_data = load_csv(corrupted_csv)
        self.assertEqual(len(loaded_data), 2)

        # Check that missing fields are handled
        # csv.DictReader may return None for missing fields in some cases
        self.assertIn(loaded_data[0]["email"], ["", None])  # Missing field as empty or None
        self.assertIn("id", loaded_data[1])


class TestDataLoaderPerformance(unittest.TestCase):
    """Test performance benchmarks and efficiency (15% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @pytest.mark.benchmark(group="csv_loading")
    def test_csv_loading_performance(self, benchmark=None):
        """Benchmark CSV loading performance."""
        # Create medium-sized CSV for benchmarking
        csv_file = Path("benchmark.csv")
        with open(csv_file, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "email", "age", "balance", "status"])

            for i in range(1000):
                writer.writerow([
                    f"ID_{i:04d}",
                    f"User_{i}",
                    f"user{i}@example.com",
                    25 + (i % 40),
                    round(1000 + (i * 10.5), 2),
                    "active" if i % 3 == 0 else "inactive"
                ])

        if benchmark:
            result = benchmark(load_csv, csv_file)
            self.assertEqual(len(result), 1000)
        else:
            # Fallback when benchmark fixture not available
            import time
            start_time = time.time()
            result = load_csv(csv_file)
            end_time = time.time()

            self.assertEqual(len(result), 1000)
            self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second

    @pytest.mark.benchmark(group="json_loading")
    def test_json_loading_performance(self, benchmark=None):
        """Benchmark JSON loading performance."""
        # Create medium-sized JSON for benchmarking
        json_data = []
        for i in range(500):
            json_data.append({
                "order_id": f"ORD_{i:04d}",
                "customer_id": f"CUST_{i % 100:03d}",
                "items": [
                    {"product": f"Product_{j}", "quantity": j + 1, "price": (j + 1) * 15.99}
                    for j in range(i % 5 + 1)
                ],
                "total": sum((j + 1) * 15.99 for j in range(i % 5 + 1)),
                "status": "completed" if i % 3 == 0 else "pending"
            })

        json_file = Path("benchmark.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)

        if benchmark:
            result = benchmark(load_json, json_file)
            self.assertEqual(len(result), 500)
        else:
            # Fallback when benchmark fixture not available
            import time
            start_time = time.time()
            result = load_json(json_file)
            end_time = time.time()

            self.assertEqual(len(result), 500)
            self.assertLess(end_time - start_time, 1.0)

    def test_large_file_info_performance(self):
        """Test performance of file info extraction on large files."""
        # Create large CSV
        large_csv = Path("large_info_test.csv")
        with open(large_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["col_" + str(i) for i in range(20)])  # 20 columns

            for i in range(5000):  # 5000 rows
                writer.writerow([f"data_{i}_{j}" for j in range(20)])

        import time
        start_time = time.time()
        file_info = get_data_info(str(large_csv))
        end_time = time.time()

        # Verify correct info extraction
        self.assertEqual(file_info["format"], "csv")
        self.assertEqual(file_info["columns"], 20)
        self.assertEqual(file_info["estimated_rows"], 5000)

        # Should complete quickly (file info shouldn't load all data)
        self.assertLess(end_time - start_time, 2.0)

    def test_concurrent_loading_performance(self):
        """Test concurrent file loading performance."""
        import threading
        import time

        # Create multiple test files
        test_files = []
        for i in range(3):
            csv_file = Path(f"concurrent_{i}.csv")
            with open(csv_file, 'w', encoding='utf-8', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "data", "value"])
                for j in range(100):
                    writer.writerow([f"ID_{j:03d}", f"data_{i}_{j}", j * 1.5])
            test_files.append(csv_file)

        results = []
        errors = []

        def load_file(file_path):
            """Load file in thread."""
            try:
                data = load_data(str(file_path))
                results.append((file_path.name, len(data)))
            except Exception as e:
                errors.append((file_path.name, str(e)))

        # Start concurrent loading
        start_time = time.time()
        threads = []
        for file_path in test_files:
            thread = threading.Thread(target=load_file, args=(file_path,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()
        end_time = time.time()

        # Verify results
        self.assertEqual(len(errors), 0, f"Concurrent loading errors: {errors}")
        self.assertEqual(len(results), 3)
        for filename, row_count in results:
            self.assertEqual(row_count, 100)

        # Concurrent loading should be efficient
        self.assertLess(end_time - start_time, 2.0)

    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets."""
        # Create large dataset
        large_csv = Path("memory_test.csv")
        with open(large_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "data_field", "numeric_value", "category"])

            for i in range(2000):
                writer.writerow([
                    f"ID_{i:06d}",
                    f"long_data_string_with_content_{i}_" + "x" * 50,
                    i * 2.5,
                    f"category_{i % 10}"
                ])

        import psutil
        import os

        # Measure memory usage
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # Load large dataset
        loaded_data = load_data(str(large_csv))

        memory_after = process.memory_info().rss
        memory_used = memory_after - memory_before

        # Verify data loaded correctly
        self.assertEqual(len(loaded_data), 2000)

        # Memory usage should be reasonable (less than 50MB for this dataset)
        self.assertLess(memory_used, 50 * 1024 * 1024)

    @patch('src.adri.validator.loaders.pd')
    def test_parquet_loading_performance(self, mock_pd):
        """Test Parquet loading performance benchmarks."""
        # Mock large DataFrame
        mock_df = Mock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"col_" + str(j): f"data_{i}_{j}" for j in range(10)}
            for i in range(1000)
        ]
        mock_pd.read_parquet.return_value = mock_df

        parquet_file = Path("performance.parquet")
        parquet_file.touch()

        import time
        start_time = time.time()
        result = load_parquet(parquet_file)
        end_time = time.time()

        self.assertEqual(len(result), 1000)
        self.assertLess(end_time - start_time, 1.0)


class TestDataLoaderEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for comprehensive coverage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_csv_with_special_characters(self):
        """Test CSV loading with special characters and Unicode."""
        special_csv = Path("special_chars.csv")
        with open(special_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "description"])
            writer.writerow(["1", "José María", "Description with áccénts"])
            writer.writerow(["2", "李明", "Chinese characters: 中文测试"])
            writer.writerow(["3", "Müller & Co.", "German umlauts: ä, ö, ü, ß"])
            writer.writerow(["4", "Москва", "Russian: Привет мир"])
            writer.writerow(["5", "Symbol™", "Special symbols: ®©™€£¥"])

        loaded_data = load_data(str(special_csv))
        self.assertEqual(len(loaded_data), 5)
        self.assertEqual(loaded_data[0]["name"], "José María")
        self.assertEqual(loaded_data[1]["name"], "李明")
        self.assertEqual(loaded_data[2]["name"], "Müller & Co.")
        self.assertIn("Привет", loaded_data[3]["description"])

    def test_json_with_nested_structures(self):
        """Test JSON loading with deeply nested structures."""
        nested_json = Path("nested.json")
        nested_data = [
            {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": ["deep", "nested", "array"],
                            "value": 42
                        },
                        "other": "data"
                    },
                    "array": [1, 2, 3]
                },
                "id": "nested_001"
            }
        ]

        with open(nested_json, 'w', encoding='utf-8') as f:
            json.dump(nested_data, f)

        loaded_data = load_json(nested_json)
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]["level1"]["level2"]["level3"]["value"], 42)
        self.assertEqual(len(loaded_data[0]["level1"]["level2"]["level3"]["level4"]), 3)

    def test_csv_with_quoted_fields(self):
        """Test CSV loading with quoted fields containing special characters."""
        quoted_csv = Path("quoted.csv")
        with open(quoted_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "text", "notes"])
            writer.writerow(["1", "Text with, comma", "Notes with \"quotes\""])
            writer.writerow(["2", "Text with\nnewline", "Normal notes"])
            writer.writerow(["3", "Text with;semicolon", "More \"complex\" notes"])

        loaded_data = load_csv(quoted_csv)
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]["text"], "Text with, comma")
        self.assertEqual(loaded_data[0]["notes"], 'Notes with "quotes"')
        self.assertIn("\n", loaded_data[1]["text"])

    def test_empty_and_null_values(self):
        """Test handling of empty and null values in data."""
        null_csv = Path("null_values.csv")
        with open(null_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "value", "optional"])
            writer.writerow(["1", "", "present"])
            writer.writerow(["2", "value", ""])
            writer.writerow(["3", "", ""])

        loaded_data = load_csv(null_csv)
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]["value"], "")
        self.assertEqual(loaded_data[1]["optional"], "")
        self.assertEqual(loaded_data[2]["value"], "")

    def test_single_row_files(self):
        """Test edge case of single row data files."""
        single_csv = Path("single.csv")
        with open(single_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "value"])
            writer.writerow(["1", "Single Row", "42"])

        loaded_data = load_csv(single_csv)
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]["id"], "1")

        # Test single item JSON
        single_json = Path("single.json")
        with open(single_json, 'w', encoding='utf-8') as f:
            json.dump([{"id": "1", "name": "Single Item", "value": 42}], f)

        loaded_data = load_json(single_json)
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]["value"], 42)

    def test_very_long_field_values(self):
        """Test handling of very long field values."""
        long_csv = Path("long_values.csv")
        long_text = "x" * 10000  # 10KB of text

        with open(long_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "long_field", "normal"])
            writer.writerow(["1", long_text, "normal_value"])

        loaded_data = load_csv(long_csv)
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(len(loaded_data[0]["long_field"]), 10000)
        self.assertEqual(loaded_data[0]["normal"], "normal_value")

    def test_file_info_edge_cases(self):
        """Test file info extraction edge cases."""
        # Test file info with error handling
        error_csv = Path("error_info.csv")
        with open(error_csv, 'w', encoding='utf-8') as f:
            f.write("invalid,csv,format\n")
            f.write("with\tinconsistent\tdelimiters\n")

        file_info = get_data_info(str(error_csv))
        self.assertEqual(file_info["format"], "csv")
        # Should handle gracefully even with inconsistent format

    @patch('src.adri.validator.loaders.pd')
    def test_parquet_info_edge_cases(self, mock_pd):
        """Test Parquet file info edge cases."""
        # Test when pandas not available
        with patch('src.adri.validator.loaders.pd', None):
            parquet_file = Path("no_pandas.parquet")
            parquet_file.touch()

            file_info = get_data_info(str(parquet_file))
            self.assertEqual(file_info["format"], "parquet")
            self.assertIn("error", file_info)
            self.assertEqual(file_info["error"], "pandas not available")

        # Test Parquet info with error
        mock_pd.read_parquet.side_effect = Exception("Parquet error")
        parquet_file = Path("error.parquet")
        parquet_file.touch()

        file_info = get_data_info(str(parquet_file))
        self.assertEqual(file_info["format"], "parquet")
        self.assertIn("error", file_info)

    def test_yaml_edge_cases(self):
        """Test YAML loading edge cases."""
        # Test YAML with complex structures
        complex_yaml = Path("complex.yaml")
        complex_data = {
            "contracts": {
                "id": "complex_standard",
                "name": "Complex Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Test standard with complex structures",
                "multi_line": """
                This is a multi-line
                string in YAML
                with special characters: !@#$%^&*()
                """,
                "list_of_dicts": [
                    {"name": "item1", "values": [1, 2, 3]},
                    {"name": "item2", "values": [4, 5, 6]}
                ],
                "nested": {
                    "deeply": {
                        "nested": {
                            "value": True
                        }
                    }
                }
            },
            "requirements": {
                "overall_minimum": 75.0,
                "dimensions": {
                    "validity": 80.0,
                    "completeness": 85.0
                },
                "dimension_requirements": {
                    "validity": {"weight": 0.5},
                    "completeness": {"weight": 0.5}
                }
            }
        }

        with open(complex_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(complex_data, f)

        loaded_standard = load_contract(str(complex_yaml))
        self.assertIn("contracts", loaded_standard)
        self.assertIn("multi_line", loaded_standard["contracts"])
        self.assertEqual(len(loaded_standard["contracts"]["list_of_dicts"]), 2)

    def test_file_path_edge_cases(self):
        """Test edge cases with file paths."""
        # Test with relative paths
        rel_csv = Path("./relative.csv")
        with open(rel_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "value"])
            writer.writerow(["1", "test"])

        loaded_data = load_data(str(rel_csv))
        self.assertEqual(len(loaded_data), 1)

        # Test with absolute paths
        abs_csv = Path(self.temp_dir) / "absolute.csv"
        with open(abs_csv, 'w', encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "value"])
            writer.writerow(["1", "test"])

        loaded_data = load_data(str(abs_csv))
        self.assertEqual(len(loaded_data), 1)


if __name__ == '__main__':
    unittest.main()
