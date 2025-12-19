"""
Standards Parser Tests - Multi-Dimensional Quality Framework
Tests YAML parsing and validation functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import yaml
import threading
import time
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest

from src.adri.contracts.parser import (
    ContractsParser,
    load_bundled_contract,
    list_bundled_contracts,
    StandardsDirectoryNotFoundError,
    StandardNotFoundError,
    InvalidStandardError
)


class TestContractsParserIntegration(unittest.TestCase):
    """Test complete standards parsing workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = Path(self.temp_dir) / "standards"
        self.standards_dir.mkdir()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Set environment variable for standards path
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

        # Clean up environment variable
        if "ADRI_CONTRACTS_DIR" in os.environ:
            del os.environ["ADRI_CONTRACTS_DIR"]

    def test_complete_standard_parsing_workflow(self):
        """Test end-to-end standard parsing workflow with validation."""
        # Create comprehensive ADRI standard
        standard_content = {
            "contracts": {
                "id": "customer_data_standard",
                "name": "Customer Data Quality Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Comprehensive customer data quality requirements"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 85.0
                    },
                    "completeness": {
                        "weight": 3,
                        "minimum_score": 90.0
                    },
                    "consistency": {
                        "weight": 3,
                        "minimum_score": 80.0
                    },
                    "freshness": {
                        "weight": 3,
                        "minimum_score": 70.0
                    },
                    "plausibility": {
                        "weight": 3,
                        "minimum_score": 75.0
                    }
                }
            },
            "dimensions": {
                "validity": {
                    "rules": [
                        {"field": "email", "type": "email_format"},
                        {"field": "age", "type": "numeric_range", "min": 0, "max": 150}
                    ],
                    "weight": 0.3
                },
                "completeness": {
                    "required_fields": ["customer_id", "name", "email"],
                    "null_threshold": 5.0,
                    "weight": 0.25
                },
                "consistency": {
                    "cross_field_rules": [
                        {"fields": ["first_name", "last_name", "full_name"], "type": "name_consistency"}
                    ],
                    "weight": 0.2
                }
            }
        }

        # Write standard to file
        standard_file = self.standards_dir / "customer_data_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f, default_flow_style=False)

        # Test complete parsing workflow
        parser = ContractsParser()

        # Test standard existence check
        self.assertTrue(parser.contract_exists("customer_data_standard"))

        # Test parsing integration
        parsed_standard = parser.parse_contract("customer_data_standard")
        self.assertEqual(parsed_standard["contracts"]["id"], "customer_data_standard")
        self.assertEqual(parsed_standard["requirements"]["overall_minimum"], 80.0)
        self.assertEqual(len(parsed_standard["dimensions"]["validity"]["rules"]), 2)

        # Test metadata extraction integration
        metadata = parser.get_contract_metadata("customer_data_standard")
        self.assertEqual(metadata["name"], "Customer Data Quality Standard")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["id"], "customer_data_standard")
        self.assertIn("customer_data_standard.yaml", metadata["file_path"])

        # Test standards listing integration
        available_standards = parser.list_available_contracts()
        self.assertIn("customer_data_standard", available_standards)

        # Test validation integration
        validation_result = parser.validate_contract_file(str(standard_file))
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
        self.assertIn("Valid YAML syntax", validation_result["passed_checks"])
        self.assertIn("Valid ADRI contract structure", validation_result["passed_checks"])

    def test_multiple_standards_workflow(self):
        """Test workflow with multiple standards in directory."""
        # Create multiple standards
        standards_data = {
            "financial_standard": {
                "contracts": {
                    "id": "financial_data_standard",
                    "name": "Financial Data Standard",
                    "version": "2.1.0",
                    "authority": "ADRI Framework",
                    "description": "Financial Data Standard"
                },
                "requirements": {
                    "overall_minimum": 90.0,
                    "dimension_requirements": {
                        "validity": {
                            "weight": 3,
                            "minimum_score": 95.0
                        },
                        "completeness": {
                            "weight": 3,
                            "minimum_score": 85.0
                        }
                    }
                },
                "dimensions": {
                    "validity": {
                        "currency_validation": True,
                        "amount_precision": 2
                    }
                }
            },
            "product_standard": {
                "contracts": {
                    "id": "product_catalog_standard",
                    "name": "Product Catalog Standard",
                    "version": "1.5.0",
                    "authority": "ADRI Framework",
                    "description": "Product Catalog Standard"
                },
                "requirements": {
                    "overall_minimum": 75.0,
                    "dimension_requirements": {
                        "validity": {
                            "weight": 3,
                            "minimum_score": 75.0
                        }
                    }
                },
                "dimensions": {
                    "validity": {
                        "sku_format": "alphanumeric",
                        "price_validation": True
                    }
                }
            },
            "order_standard": {
                "contracts": {
                    "id": "order_processing_standard",
                    "name": "Order Processing Standard",
                    "version": "3.0.0",
                    "authority": "ADRI Framework",
                    "description": "Order Processing Standard"
                },
                "requirements": {
                    "overall_minimum": 85.0,
                    "dimension_requirements": {
                        "completeness": {
                            "weight": 3,
                            "minimum_score": 85.0
                        }
                    }
                },
                "dimensions": {
                    "completeness": {
                        "required_fields": ["order_id", "customer_id", "total"]
                    }
                }
            }
        }

        # Write all standards to files
        for standard_name, content in standards_data.items():
            standard_file = self.standards_dir / f"{standard_name}.yaml"
            with open(standard_file, 'w', encoding='utf-8') as f:
                yaml.dump(content, f)

        parser = ContractsParser()

        # Test listing all standards
        available_standards = parser.list_available_contracts()
        self.assertEqual(len(available_standards), 3)
        self.assertIn("financial_standard", available_standards)
        self.assertIn("product_standard", available_standards)
        self.assertIn("order_standard", available_standards)

        # Test parsing each standard
        for standard_name in available_standards:
            parsed = parser.parse_contract(standard_name)
            self.assertIn("contracts", parsed)
            self.assertIn("requirements", parsed)

        # Test metadata for each standard
        financial_metadata = parser.get_contract_metadata("financial_standard")
        self.assertEqual(financial_metadata["version"], "2.1.0")

        product_metadata = parser.get_contract_metadata("product_standard")
        self.assertEqual(product_metadata["name"], "Product Catalog Standard")

    def test_caching_integration_workflow(self):
        """Test standards caching and cache management integration."""
        # Create test standard
        standard_content = {
            "contracts": {
                "id": "cache_test_standard",
                "name": "Cache Test Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Cache Test Standard"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "cache_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        parser = ContractsParser()

        # Clear any cache activity from parser initialization
        parser.clear_cache()

        # Test initial cache state
        initial_cache_info = parser.get_cache_info()
        self.assertEqual(initial_cache_info.hits, 0)
        self.assertEqual(initial_cache_info.misses, 0)

        # Parse standard - should miss cache
        parsed_first = parser.parse_contract("cache_test")
        cache_after_first = parser.get_cache_info()
        self.assertEqual(cache_after_first.misses, 1)
        self.assertEqual(cache_after_first.hits, 0)

        # Parse same standard again - should hit cache
        parsed_second = parser.parse_contract("cache_test")
        cache_after_second = parser.get_cache_info()
        self.assertEqual(cache_after_second.hits, 1)
        self.assertEqual(cache_after_second.misses, 1)

        # Verify same object returned
        self.assertEqual(parsed_first, parsed_second)

        # Test cache clearing
        parser.clear_cache()
        cache_after_clear = parser.get_cache_info()
        self.assertEqual(cache_after_clear.hits, 0)
        self.assertEqual(cache_after_clear.misses, 0)

    def test_convenience_functions_integration(self):
        """Test convenience function integration."""
        # Create test standard
        standard_content = {
            "contracts": {
                "id": "convenience_test",
                "name": "Convenience Test Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Convenience Test Standard"
            },
            "requirements": {
                "overall_minimum": 70.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 70.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "convenience_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        # Test load_bundled_contract function
        loaded_standard = load_bundled_contract("convenience_test")
        self.assertEqual(loaded_standard["contracts"]["id"], "convenience_test")

        # Test list_bundled_contracts function
        bundled_standards = list_bundled_contracts()
        self.assertIn("convenience_test", bundled_standards)

    def test_complex_standard_structures_integration(self):
        """Test integration with complex nested standard structures."""
        complex_standard = {
            "contracts": {
                "id": "complex_data_standard",
                "name": "Complex Data Standard",
                "version": "2.0.0",
                "authority": "ADRI Framework",
                "description": "Complex nested validation standard",
                "tags": ["enterprise", "comprehensive", "multi-domain"]
            },
            "requirements": {
                "overall_minimum": 85.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 90.0
                    },
                    "completeness": {
                        "weight": 3,
                        "minimum_score": 80.0
                    },
                    "consistency": {
                        "weight": 3,
                        "minimum_score": 85.0
                    },
                    "freshness": {
                        "weight": 3,
                        "minimum_score": 75.0
                    },
                    "plausibility": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                },
                "domain_specific": {
                    "financial": {"minimum": 95.0},
                    "personal": {"minimum": 90.0},
                    "operational": {"minimum": 80.0}
                }
            },
            "dimensions": {
                "validity": {
                    "field_validation": {
                        "email": {
                            "type": "email_format",
                            "required": True,
                            "domain_whitelist": ["company.com", "partner.org"]
                        },
                        "phone": {
                            "type": "phone_format",
                            "international": True,
                            "required": False
                        },
                        "date_of_birth": {
                            "type": "date",
                            "format": "YYYY-MM-DD",
                            "min_age": 18,
                            "max_age": 120
                        }
                    },
                    "business_rules": [
                        {
                            "name": "age_consistency",
                            "condition": "age >= 18 if account_type == 'adult'",
                            "severity": "critical"
                        },
                        {
                            "name": "email_domain_check",
                            "condition": "email.domain in approved_domains",
                            "severity": "warning"
                        }
                    ]
                },
                "completeness": {
                    "required_fields": {
                        "tier_1": ["id", "name", "email"],
                        "tier_2": ["phone", "address", "registration_date"],
                        "tier_3": ["preferences", "last_activity", "segment"]
                    },
                    "conditional_requirements": [
                        {
                            "condition": "account_type == 'premium'",
                            "required_fields": ["billing_address", "payment_method"]
                        }
                    ]
                }
            },
            "metadata": {
                "created_by": "Data Quality Team",
                "created_date": "2024-01-15",
                "last_modified": "2024-03-20",
                "review_cycle": "quarterly",
                "stakeholders": ["data-team@company.com", "compliance@company.com"]
            }
        }

        standard_file = self.standards_dir / "complex_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(complex_standard, f, default_flow_style=False)

        parser = ContractsParser()

        # Test parsing complex structure
        parsed = parser.parse_contract("complex_standard")
        self.assertEqual(parsed["contracts"]["id"], "complex_data_standard")
        self.assertIn("tags", parsed["contracts"])
        self.assertEqual(len(parsed["contracts"]["tags"]), 3)
        self.assertIn("domain_specific", parsed["requirements"])
        self.assertIn("business_rules", parsed["dimensions"]["validity"])
        self.assertIn("metadata", parsed)

        # Test metadata extraction from complex standard
        metadata = parser.get_contract_metadata("complex_standard")
        self.assertEqual(metadata["name"], "Complex Data Standard")
        self.assertEqual(metadata["version"], "2.0.0")


class TestContractsParserErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios (25% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = Path(self.temp_dir) / "standards"
        self.standards_dir.mkdir()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

        # Clean up environment variable
        if "ADRI_CONTRACTS_DIR" in os.environ:
            del os.environ["ADRI_CONTRACTS_DIR"]

    def test_missing_environment_variable_error(self):
        """Test error handling when ADRI_CONTRACTS_DIR is not set."""
        # Ensure environment variable is not set
        if "ADRI_CONTRACTS_DIR" in os.environ:
            del os.environ["ADRI_CONTRACTS_DIR"]

        with self.assertRaises(StandardsDirectoryNotFoundError) as cm:
            ContractsParser()
        self.assertIn("ADRI_CONTRACTS_DIR environment variable must be set", str(cm.exception))

    def test_nonexistent_contracts_directory_error(self):
        """Test error handling when standards directory doesn't exist."""
        nonexistent_path = "/nonexistent/contracts/path"
        os.environ["ADRI_CONTRACTS_DIR"] = nonexistent_path

        with self.assertRaises(StandardsDirectoryNotFoundError) as cm:
            ContractsParser()
        self.assertIn(f"Contracts directory does not exist: {nonexistent_path}", str(cm.exception))

    def test_standards_path_not_directory_error(self):
        """Test error handling when standards path points to a file."""
        # Create a file instead of directory
        file_path = Path(self.temp_dir) / "not_a_directory.txt"
        file_path.touch()

        os.environ["ADRI_CONTRACTS_DIR"] = str(file_path)

        with self.assertRaises(StandardsDirectoryNotFoundError) as cm:
            ContractsParser()
        self.assertIn("Contracts path is not a directory", str(cm.exception))

    def test_standard_not_found_errors(self):
        """Test comprehensive standard not found error handling."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)
        parser = ContractsParser()

        # Test parsing non-existent standard
        with self.assertRaises(StandardNotFoundError) as cm:
            parser.parse_contract("nonexistent_standard")
        self.assertIn("nonexistent_standard", str(cm.exception))

        # Test metadata for non-existent standard
        with self.assertRaises(StandardNotFoundError):
            parser.get_contract_metadata("nonexistent_standard")

        # Test standard existence check
        self.assertFalse(parser.contract_exists("nonexistent_standard"))

    def test_invalid_yaml_syntax_errors(self):
        """Test error handling for invalid YAML syntax."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

        # Create file with invalid YAML
        invalid_yaml_file = self.standards_dir / "invalid_syntax.yaml"
        with open(invalid_yaml_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [\n  - unclosed list\n  - another: item")

        parser = ContractsParser()

        with self.assertRaises(InvalidStandardError) as cm:
            parser.parse_contract("invalid_syntax")
        self.assertIn("YAML parsing error", str(cm.exception))

    def test_invalid_standard_structure_errors(self):
        """Test error handling for invalid standard structures."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)
        parser = ContractsParser()

        # Test missing required sections
        test_cases = [
            ("missing_standards_section", {"requirements": {"overall_minimum": 80.0}}),
            ("missing_requirements_section", {"contracts": {"id": "test", "name": "test", "version": "1.0"}}),
            ("missing_standards_fields", {
                "contracts": {"name": "test"},  # Missing id and version
                "requirements": {"overall_minimum": 80.0}
            }),
            ("missing_overall_minimum", {
                "contracts": {"id": "test", "name": "test", "version": "1.0"},
                "requirements": {"dimensions": {"validity": 80.0}}
            }),
            ("invalid_standards_type", {
                "contracts": "not_a_dict",  # Should be dict
                "requirements": {"overall_minimum": 80.0}
            }),
            ("invalid_requirements_type", {
                "contracts": {"id": "test", "name": "test", "version": "1.0"},
                "requirements": "not_a_dict"  # Should be dict
            })
        ]

        for standard_name, invalid_content in test_cases:
            standard_file = self.standards_dir / f"{standard_name}.yaml"
            with open(standard_file, 'w', encoding='utf-8') as f:
                yaml.dump(invalid_content, f)

            with self.assertRaises(InvalidStandardError):
                parser.parse_contract(standard_name)

    def test_non_dict_yaml_content_error(self):
        """Test error handling when YAML content is not a dictionary."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

        # Create YAML file with list instead of dict
        list_yaml_file = self.standards_dir / "list_content.yaml"
        with open(list_yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(["item1", "item2", "item3"], f)

        parser = ContractsParser()

        with self.assertRaises(InvalidStandardError) as cm:
            parser.parse_contract("list_content")
        # The error message may be wrapped, so check for the key part
        self.assertIn("Contract must be a dictionary", str(cm.exception))

    def test_file_permission_errors(self):
        """Test file permission error scenarios."""
        if os.name == 'nt':  # Skip on Windows
            self.skipTest("File permission tests not applicable on Windows")

        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

        # Create standard file and remove read permissions
        restricted_file = self.standards_dir / "restricted.yaml"
        standard_content = {
            "contracts": {"id": "test", "name": "test", "version": "1.0"},
            "requirements": {"overall_minimum": 80.0}
        }

        with open(restricted_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        # Remove read permissions
        os.chmod(restricted_file, 0o000)

        parser = ContractsParser()

        try:
            with self.assertRaises(InvalidStandardError):
                parser.parse_contract("restricted")
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_file, 0o644)

    def test_validation_file_errors(self):
        """Test validation errors for file operations."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)
        parser = ContractsParser()

        # Test validation of non-existent file
        validation_result = parser.validate_contract_file("/nonexistent/file.yaml")
        self.assertFalse(validation_result["is_valid"])
        self.assertIn("File not found", validation_result["errors"][0])

        # Test validation of file with invalid YAML
        invalid_file = self.standards_dir / "invalid_for_validation.yaml"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: [unclosed")

        validation_result = parser.validate_contract_file(str(invalid_file))
        self.assertFalse(validation_result["is_valid"])
        self.assertTrue(any("Invalid YAML syntax" in error for error in validation_result["errors"]))

    def test_concurrent_access_errors(self):
        """Test error handling in concurrent access scenarios."""
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

        # Create test standard
        standard_content = {
            "contracts": {"id": "concurrent_test", "name": "test", "version": "1.0", "description": "Concurrent test standard"},
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "concurrent_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        parser = ContractsParser()
        errors = []
        results = []

        def parse_in_thread(thread_id):
            """Parse standard in separate thread."""
            try:
                result = parser.parse_contract("concurrent_test")
                results.append((thread_id, result["contracts"]["id"]))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Start multiple concurrent parsing operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=parse_in_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        self.assertEqual(len(results), 5)


class TestContractsParserPerformance(unittest.TestCase):
    """Test performance benchmarks and efficiency (15% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = Path(self.temp_dir) / "standards"
        self.standards_dir.mkdir()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        if "ADRI_CONTRACTS_DIR" in os.environ:
            del os.environ["ADRI_CONTRACTS_DIR"]

    @pytest.mark.benchmark(group="standards_parsing")
    def test_standard_parsing_performance(self, benchmark=None):
        """Benchmark standard parsing performance."""
        # Create medium complexity standard
        standard_content = {
            "contracts": {
                "id": "performance_test_standard",
                "name": "Performance Test Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Standard designed for performance testing"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {"minimum_score": 80.0, "weight": 3}
                }
            },
            "dimensions": {
                f"dimension_{i}": {
                    "rules": [
                        {"field": f"field_{j}", "type": "validation_type", "value": j}
                        for j in range(20)
                    ],
                    "thresholds": {f"threshold_{k}": k * 0.5 for k in range(15)}
                }
                for i in range(10)
            }
        }

        standard_file = self.standards_dir / "performance_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f, default_flow_style=False)

        parser = ContractsParser()

        if benchmark:
            result = benchmark(parser.parse_standard, "performance_test")
            self.assertEqual(result["contracts"]["id"], "performance_test_standard")
        else:
            # Fallback timing
            start_time = time.time()
            result = parser.parse_contract("performance_test")
            end_time = time.time()

            self.assertEqual(result["contracts"]["id"], "performance_test_standard")
            self.assertLess(end_time - start_time, 1.0)  # Should parse within 1 second

    def test_caching_performance_benefits(self):
        """Test performance benefits of caching."""
        # Create standard for caching test
        standard_content = {
            "contracts": {"id": "cache_perf_test", "name": "Cache Performance Test", "version": "1.0", "description": "Cache performance test"},
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "cache_perf_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        parser = ContractsParser()

        # Time first parse (cache miss) using high-precision timer
        start_time = time.perf_counter()
        first_result = parser.parse_contract("cache_perf_test")
        first_parse_time = time.perf_counter() - start_time

        # Time second parse (cache hit) using high-precision timer
        start_time = time.perf_counter()
        second_result = parser.parse_contract("cache_perf_test")
        second_parse_time = time.perf_counter() - start_time

        # Verify results are identical (core caching functionality)
        self.assertEqual(first_result, second_result)

        # Verify cache statistics show improvement
        cache_info = parser.get_cache_info()
        self.assertGreaterEqual(cache_info.hits, 1)  # At least one cache hit
        self.assertGreaterEqual(cache_info.misses, 1)  # At least one cache miss

        # Performance assertion: only assert if we can actually measure timing differences
        # On very fast systems (including Windows), operations may be too fast to measure reliably
        if first_parse_time > 0.001 and second_parse_time > 0:  # At least 1ms for first parse
            # Cache hit should be faster than cache miss
            self.assertLess(second_parse_time, first_parse_time)
        else:
            # For very fast operations, just verify caching is working via cache stats
            # This ensures the test passes on Windows with high-precision timing
            self.assertGreater(cache_info.hits + cache_info.misses, 0)

    def test_multiple_standards_loading_performance(self):
        """Test performance when loading multiple standards."""
        # Create multiple standards
        num_standards = 20
        for i in range(num_standards):
            standard_content = {
                "contracts": {
                    "id": f"multi_standard_{i}",
                    "name": f"Multi Standard {i}",
                    "version": "1.0.0",
                    "description": f"Multi standard {i}"
                },
                "requirements": {
                    "overall_minimum": 80.0 + i,
                    "dimension_requirements": {
                        "validity": {"minimum_score": 80.0, "weight": 3}
                    }
                },
                "dimensions": {
                    "validity": {"rules": [{"field": f"field_{j}", "type": "test"} for j in range(i + 1)]}
                }
            }

            standard_file = self.standards_dir / f"multi_standard_{i}.yaml"
            with open(standard_file, 'w', encoding='utf-8') as f:
                yaml.dump(standard_content, f)

        parser = ContractsParser()

        # Time listing all standards
        start_time = time.time()
        available_standards = parser.list_available_contracts()
        list_time = time.time() - start_time

        self.assertEqual(len(available_standards), num_standards)
        self.assertLess(list_time, 2.0)  # Should list within 2 seconds

        # Time parsing all standards
        start_time = time.time()
        parsed_standards = []
        for standard_name in available_standards:
            parsed = parser.parse_contract(standard_name)
            parsed_standards.append(parsed)
        parse_all_time = time.time() - start_time

        self.assertEqual(len(parsed_standards), num_standards)
        self.assertLess(parse_all_time, 5.0)  # Should parse all within 5 seconds

    def test_large_standard_parsing_performance(self):
        """Test performance with very large standards."""
        # Create large standard with many dimensions and rules
        large_standard = {
            "contracts": {
                "id": "large_standard",
                "name": "Large Performance Test Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Large performance test standard"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {"minimum_score": 80.0, "weight": 3}
                }
            },
            "dimensions": {}
        }

        # Add many dimensions with complex rules
        for i in range(50):
            large_standard["dimensions"][f"dimension_{i}"] = {
                "rules": [
                    {"field": f"field_{j}", "type": f"type_{j % 5}", "value": j}
                    for j in range(100)
                ],
                "thresholds": {f"threshold_{k}": k * 0.1 for k in range(50)},
                "complex_validation": {
                    "nested_rules": [
                        {"condition": f"value > {m}", "action": f"validate_{m}"}
                        for m in range(20)
                    ]
                }
            }

        large_file = self.standards_dir / "large_standard.yaml"
        with open(large_file, 'w', encoding='utf-8') as f:
            yaml.dump(large_standard, f, default_flow_style=False)

        parser = ContractsParser()

        # Time parsing large standard
        start_time = time.time()
        parsed_large = parser.parse_contract("large_standard")
        parse_time = time.time() - start_time

        self.assertEqual(parsed_large["contracts"]["id"], "large_standard")
        self.assertEqual(len(parsed_large["dimensions"]), 50)

        # Simple performance threshold - reasonable upper limit for all environments
        # Catches real performance regressions while allowing for normal CI variance
        self.assertLess(parse_time, 10.0)  # Should parse within 10 seconds (CI tolerance)

    def test_concurrent_parsing_performance(self):
        """Test performance with concurrent parsing operations."""
        # Create standard for concurrent testing
        standard_content = {
            "contracts": {"id": "concurrent_perf_test", "name": "Concurrent Performance Test", "version": "1.0", "description": "Concurrent performance test"},
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "concurrent_perf_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        parser = ContractsParser()
        results = []

        def parse_concurrent(thread_id):
            """Parse standard concurrently."""
            start_time = time.time()
            result = parser.parse_contract("concurrent_perf_test")
            parse_time = time.time() - start_time
            results.append((thread_id, parse_time, result["contracts"]["id"]))

        # Run concurrent parsing
        overall_start = time.time()
        threads = []
        for i in range(10):
            thread = threading.Thread(target=parse_concurrent, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        overall_time = time.time() - overall_start

        # Verify all completed successfully
        self.assertEqual(len(results), 10)
        for thread_id, parse_time, standard_id in results:
            self.assertEqual(standard_id, "concurrent_perf_test")

        # Concurrent execution should be efficient
        self.assertLess(overall_time, 5.0)

    def test_memory_usage_performance(self):
        """Test memory efficiency during parsing operations."""
        # Create multiple standards to test memory usage
        for i in range(10):
            standard_content = {
                "contracts": {"id": f"memory_test_{i}", "name": f"Memory Test {i}", "version": "1.0", "description": f"Memory test {i}"},
                "requirements": {
                    "overall_minimum": 80.0,
                    "dimension_requirements": {
                        "validity": {
                            "weight": 3,
                            "minimum_score": 80.0
                        }
                    }
                },
                "dimensions": {
                    f"dimension_{j}": {"rules": [{"field": f"field_{k}", "type": "test"} for k in range(20)]}
                    for j in range(10)
                }
            }

            standard_file = self.standards_dir / f"memory_test_{i}.yaml"
            with open(standard_file, 'w', encoding='utf-8') as f:
                yaml.dump(standard_content, f)

        parser = ContractsParser()

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss

            # Parse all standards
            parsed_standards = []
            for i in range(10):
                parsed = parser.parse_contract(f"memory_test_{i}")
                parsed_standards.append(parsed)

            memory_after = process.memory_info().rss
            memory_used = memory_after - memory_before

            # Verify parsing succeeded
            self.assertEqual(len(parsed_standards), 10)

            # Memory usage should be reasonable (less than 20MB)
            self.assertLess(memory_used, 20 * 1024 * 1024)

        except ImportError:
            # psutil not available, just verify parsing works
            parsed_standards = []
            for i in range(10):
                parsed = parser.parse_contract(f"memory_test_{i}")
                parsed_standards.append(parsed)
            self.assertEqual(len(parsed_standards), 10)


class TestContractsParserEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for comprehensive coverage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = Path(self.temp_dir) / "standards"
        self.standards_dir.mkdir()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.environ["ADRI_CONTRACTS_DIR"] = str(self.standards_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        if "ADRI_CONTRACTS_DIR" in os.environ:
            del os.environ["ADRI_CONTRACTS_DIR"]

    def test_yaml_with_special_characters(self):
        """Test YAML parsing with special characters and Unicode."""
        special_standard = {
            "contracts": {
                "id": "special_chars_standard",
                "name": "Standard with Special Characters: àáâãäåæçèéêë",
                "version": "1.0.0",
                "authority": "ADRI Framework 中文",
                "description": "Testing Unicode: Ñoñó español, 日本語, Русский, العربية"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            },
            "dimensions": {
                "validity": {
                    "special_rules": {
                        "unicode_field": "Müller & Sønner™",
                        "symbols": "€£¥$¢₹₽",
                        "math": "∀x∈ℝ: x²≥0",
                        "emoji": "👍✅❌🚀"
                    }
                }
            }
        }

        standard_file = self.standards_dir / "special_chars.yaml"
        with open(standard_file, "w", encoding="utf-8") as f:
            yaml.dump(special_standard, f, default_flow_style=False, allow_unicode=True)

        parser = ContractsParser()
        parsed = parser.parse_contract("special_chars")

        self.assertIn("中文", parsed["contracts"]["authority"])
        self.assertIn("español", parsed["contracts"]["description"])
        self.assertIn("€£¥", parsed["dimensions"]["validity"]["special_rules"]["symbols"])

    def test_empty_contracts_directory(self):
        """Test behavior with empty standards directory."""
        parser = ContractsParser()

        # Test listing standards in empty directory
        available_standards = parser.list_available_contracts()
        self.assertEqual(len(available_standards), 0)

        # Test checking existence in empty directory
        self.assertFalse(parser.contract_exists("any_standard"))

    def test_yaml_files_with_different_extensions(self):
        """Test handling of YAML files with different extensions."""
        # Create files with .yml extension
        yml_content = {
            "contracts": {"id": "yml_test", "name": "YML Test", "version": "1.0"},
            "requirements": {"overall_minimum": 80.0}
        }

        yml_file = self.standards_dir / "yml_test.yml"
        with open(yml_file, 'w', encoding='utf-8') as f:
            yaml.dump(yml_content, f)

        # Create files with .yaml extension
        yaml_content = {
            "contracts": {"id": "yaml_test", "name": "YAML Test", "version": "1.0"},
            "requirements": {"overall_minimum": 80.0}
        }

        yaml_file = self.standards_dir / "yaml_test.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f)

        parser = ContractsParser()

        # Only .yaml files should be recognized
        available_standards = parser.list_available_contracts()
        self.assertIn("yaml_test", available_standards)
        self.assertNotIn("yml_test", available_standards)  # .yml not recognized

    def test_standards_with_minimal_structure(self):
        """Test parsing standards with minimal required structure."""
        minimal_standard = {
            "contracts": {
                "id": "minimal",
                "name": "Minimal Standard",
                "version": "1.0",
                "description": "Minimal standard"
            },
            "requirements": {
                "overall_minimum": 50.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 50.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "minimal.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(minimal_standard, f)

        parser = ContractsParser()
        parsed = parser.parse_contract("minimal")

        self.assertEqual(parsed["contracts"]["id"], "minimal")
        self.assertEqual(parsed["requirements"]["overall_minimum"], 50.0)

        # Test metadata extraction for minimal standard
        metadata = parser.get_contract_metadata("minimal")
        self.assertEqual(metadata["name"], "Minimal Standard")
        self.assertEqual(metadata["description"], "Minimal standard")

    def test_very_long_standard_names(self):
        """Test handling of very long standard names."""
        long_name = "a" * 200  # 200 character name
        long_standard = {
            "contracts": {
                "id": long_name,
                "name": f"Long Name Standard: {long_name}",
                "version": "1.0",
                "description": "Long name standard"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / f"{long_name}.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(long_standard, f)

        parser = ContractsParser()

        # Test existence check with long name
        self.assertTrue(parser.contract_exists(long_name))

        # Test parsing with long name
        parsed = parser.parse_contract(long_name)
        self.assertEqual(parsed["contracts"]["id"], long_name)

    def test_numeric_and_special_field_values(self):
        """Test parsing with various numeric and special field values."""
        numeric_standard = {
            "contracts": {
                "id": "numeric_test",
                "name": "Numeric Values Test",
                "version": "1.0",
                "description": "Numeric values test"
            },
            "requirements": {
                "overall_minimum": 85.5,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 90.0
                    },
                    "completeness": {
                        "weight": 3,
                        "minimum_score": 0.0
                    },
                    "consistency": {
                        "weight": 3,
                        "minimum_score": 100.0
                    },
                    "freshness": {
                        "weight": 3,
                        "minimum_score": 99.999
                    },
                    "plausibility": {
                        "weight": 3,
                        "minimum_score": 5.0
                    }
                }
            },
            "dimensions": {
                "validity": {
                    "numeric_rules": {
                        "integer": 42,
                        "float": 3.14159,
                        "scientific": 1.23e-4,
                        "negative": -273.15,
                        "zero": 0,
                        "boolean_true": True,
                        "boolean_false": False,
                        "null_value": None
                    }
                }
            }
        }

        standard_file = self.standards_dir / "numeric_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(numeric_standard, f)

        parser = ContractsParser()
        parsed = parser.parse_contract("numeric_test")

        # Verify numeric values preserved
        self.assertEqual(parsed["requirements"]["overall_minimum"], 85.5)
        self.assertEqual(parsed["requirements"]["dimension_requirements"]["completeness"]["minimum_score"], 0.0)
        self.assertEqual(parsed["dimensions"]["validity"]["numeric_rules"]["integer"], 42)
        self.assertTrue(parsed["dimensions"]["validity"]["numeric_rules"]["boolean_true"])
        self.assertIsNone(parsed["dimensions"]["validity"]["numeric_rules"]["null_value"])

    def test_deeply_nested_standard_structures(self):
        """Test parsing deeply nested standard structures."""
        nested_standard = {
            "contracts": {"id": "deeply_nested", "name": "Deeply Nested Standard", "version": "1.0", "description": "Deeply nested standard"},
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            },
            "dimensions": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "deep_value": "found at level 5",
                                    "deep_array": [1, 2, {"nested_in_array": {"final_level": True}}]
                                }
                            }
                        }
                    }
                }
            }
        }

        standard_file = self.standards_dir / "deeply_nested.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(nested_standard, f)

        parser = ContractsParser()
        parsed = parser.parse_contract("deeply_nested")

        # Verify deep nesting is preserved
        deep_value = parsed["dimensions"]["level1"]["level2"]["level3"]["level4"]["level5"]["deep_value"]
        self.assertEqual(deep_value, "found at level 5")

        nested_in_array = parsed["dimensions"]["level1"]["level2"]["level3"]["level4"]["level5"]["deep_array"][2]
        self.assertTrue(nested_in_array["nested_in_array"]["final_level"])

    def test_standards_path_property(self):
        """Test standards_path property access."""
        parser = ContractsParser()

        # Test that standards_path property returns correct path
        self.assertEqual(parser.contracts_path, Path(self.standards_dir).resolve())
        self.assertTrue(parser.contracts_path.exists())
        self.assertTrue(parser.contracts_path.is_dir())

    def test_threading_safety(self):
        """Test thread safety of parser operations."""
        # Create test standard
        standard_content = {
            "contracts": {"id": "thread_safety_test", "name": "Thread Safety Test", "version": "1.0", "description": "Thread safety test"},
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            }
        }

        standard_file = self.standards_dir / "thread_safety_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_content, f)

        parser = ContractsParser()
        results = []
        errors = []

        def thread_operations(thread_id):
            """Perform various parser operations in thread."""
            try:
                # Parse standard
                parsed = parser.parse_contract("thread_safety_test")

                # Check existence
                exists = parser.contract_exists("thread_safety_test")

                # Get metadata
                metadata = parser.get_contract_metadata("thread_safety_test")

                # List standards
                standards_list = parser.list_available_contracts()

                # Get cache info
                cache_info = parser.get_cache_info()

                results.append({
                    "thread_id": thread_id,
                    "parsed_id": parsed["contracts"]["id"],
                    "exists": exists,
                    "metadata_name": metadata["name"],
                    "standards_count": len(standards_list),
                    "cache_hits": cache_info.hits
                })

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=thread_operations, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors and consistent results
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        self.assertEqual(len(results), 5)

        for result in results:
            self.assertEqual(result["parsed_id"], "thread_safety_test")
            self.assertTrue(result["exists"])
            self.assertEqual(result["metadata_name"], "Thread Safety Test")
            self.assertEqual(result["standards_count"], 1)

    def test_validation_with_warnings(self):
        """Test validation that produces warnings but not errors."""
        # Create standard that might produce warnings
        warning_standard = {
            "contracts": {
                "id": "warning_test",
                "name": "Warning Test Standard",
                "version": "1.0",
                "authority": "ADRI Framework",
                "description": "Warning test standard"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {
                        "weight": 3,
                        "minimum_score": 80.0
                    }
                }
            },
            "dimensions": {
                "validity": {
                    "rules": []
                }
            }
        }

        standard_file = self.standards_dir / "warning_test.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(warning_standard, f)

        parser = ContractsParser()

        # Standard should parse successfully
        parsed = parser.parse_contract("warning_test")
        self.assertEqual(parsed["contracts"]["id"], "warning_test")

        # Validation should pass
        validation_result = parser.validate_contract_file(str(standard_file))
        self.assertTrue(validation_result["is_valid"])


if __name__ == '__main__':
    unittest.main()
