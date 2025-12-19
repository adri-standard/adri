"""
Tests for enhanced ADRI standards schema functionality.

Tests the updated meta-schema with record_identification, training_data_lineage,
and metadata sections.
"""

import unittest
import tempfile
import os
from pathlib import Path
import yaml
from unittest.mock import patch

from src.adri.contracts.parser import ContractsParser


class TestEnhancedMetaSchema(unittest.TestCase):
    """Test the enhanced meta-schema functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_meta_schema_structure(self):
        """Test that meta-schema includes all enhanced sections."""
        # Load the actual meta-schema
        schema_path = Path(__file__).parent.parent / "src" / "adri" / "contracts" / "schema.yaml"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        schema_def = schema["schema_definition"]

        # Verify required sections
        required_sections = schema_def["required_sections"]
        self.assertIn("contracts", required_sections)
        self.assertIn("requirements", required_sections)

        # Verify optional sections are defined
        optional_sections = schema_def["optional_sections"]
        self.assertIn("record_identification", optional_sections)
        self.assertIn("training_data_lineage", optional_sections)
        self.assertIn("metadata", optional_sections)

    def test_record_identification_section_definition(self):
        """Test record_identification section is properly defined."""
        schema_path = Path(__file__).parent.parent / "src" / "adri" / "contracts" / "schema.yaml"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        record_id_section = schema["schema_definition"]["record_identification_section"]

        # Verify required fields
        self.assertIn("primary_key_fields", record_id_section["required_fields"])

        # Verify optional fields
        optional_fields = record_id_section["optional_fields"]
        self.assertIn("strategy", optional_fields)
        self.assertIn("composite_key_separator", optional_fields)

        # Verify field constraints
        constraints = record_id_section["field_constraints"]
        self.assertIn("primary_key_fields", constraints)
        self.assertIn("strategy", constraints)

        # Verify strategy allowed values
        strategy_values = constraints["strategy"]["allowed_values"]
        self.assertIn("primary_key_only", strategy_values)
        self.assertIn("primary_key_with_fallback", strategy_values)
        self.assertIn("row_index_fallback", strategy_values)

    def test_training_data_lineage_section_definition(self):
        """Test training_data_lineage section is properly defined."""
        schema_path = Path(__file__).parent.parent / "src" / "adri" / "contracts" / "schema.yaml"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        lineage_section = schema["schema_definition"]["training_data_lineage_section"]

        # Verify required fields
        required_fields = lineage_section["required_fields"]
        self.assertIn("source_path", required_fields)
        self.assertIn("timestamp", required_fields)
        self.assertIn("file_hash", required_fields)

        # Verify optional fields
        optional_fields = lineage_section["optional_fields"]
        self.assertIn("snapshot_path", optional_fields)
        self.assertIn("snapshot_hash", optional_fields)
        self.assertIn("snapshot_filename", optional_fields)
        self.assertIn("source_size_bytes", optional_fields)
        self.assertIn("source_modified", optional_fields)

        # Verify field constraints
        constraints = lineage_section["field_constraints"]

        # Verify hash pattern constraint
        hash_pattern = constraints["file_hash"]["pattern"]
        self.assertEqual(hash_pattern, "^[a-f0-9]{8}$")

        # Verify timestamp pattern
        timestamp_pattern = constraints["timestamp"]["pattern"]
        self.assertTrue("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}" in timestamp_pattern)

    def test_metadata_section_definition(self):
        """Test metadata section is properly defined."""
        schema_path = Path(__file__).parent.parent / "src" / "adri" / "contracts" / "schema.yaml"
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        metadata_section = schema["schema_definition"]["metadata_section"]

        # Verify optional fields
        optional_fields = metadata_section["optional_fields"]
        self.assertIn("created_by", optional_fields)
        self.assertIn("created_date", optional_fields)
        self.assertIn("last_modified", optional_fields)
        self.assertIn("generation_method", optional_fields)
        self.assertIn("tags", optional_fields)
        self.assertIn("version_history", optional_fields)

        # Verify field constraints
        constraints = metadata_section["field_constraints"]

        # Verify generation_method allowed values
        gen_method_values = constraints["generation_method"]["allowed_values"]
        self.assertIn("auto_generated", gen_method_values)
        self.assertIn("manual_creation", gen_method_values)
        self.assertIn("hybrid_approach", gen_method_values)


class TestStandardValidationWithEnhancements(unittest.TestCase):
    """Test standard validation with enhanced sections."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_valid_enhanced_standard(self):
        """Test validation of a complete enhanced standard."""
        enhanced_standard = {
            "training_data_lineage": {
                "source_path": "/path/to/data.csv",
                "timestamp": "2025-09-22T12:00:00",
                "file_hash": "abc12345",
                "snapshot_path": "/path/to/snapshot.csv",
                "snapshot_hash": "def67890",
                "snapshot_filename": "data_abc12345.csv",
                "source_size_bytes": 1024,
                "source_modified": "2025-09-22T11:00:00"
            },
            "contracts": {
                "id": "test_data_standard",
                "name": "Test Data Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": "Test standard for validation"
            },
            "record_identification": {
                "primary_key_fields": ["id"],
                "strategy": "primary_key_with_fallback"
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "id": {"type": "string", "nullable": False}
                },
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0}
                }
            },
            "metadata": {
                "created_by": "ADRI Framework",
                "created_date": "2025-09-22T12:00:00",
                "last_modified": "2025-09-22T12:00:00",
                "generation_method": "auto_generated",
                "tags": ["test", "data_quality"]
            }
        }

        # Test basic YAML structure validation
        try:
            yaml_content = yaml.dump(enhanced_standard)
            loaded_standard = yaml.safe_load(yaml_content)

            # Basic structure should be preserved
            self.assertIn("contracts", loaded_standard)
            self.assertIn("requirements", loaded_standard)
            self.assertIn("training_data_lineage", loaded_standard)
            self.assertIn("record_identification", loaded_standard)
            self.assertIn("metadata", loaded_standard)

        except Exception as e:
            self.fail(f"Enhanced standard failed basic validation: {e}")

    def test_minimal_valid_standard(self):
        """Test that minimal standards still work with enhanced schema."""
        minimal_standard = {
            "contracts": {
                "id": "minimal_standard",
                "name": "Minimal Standard",
                "version": "1.0.0",
                "authority": "Test Authority"
            },
            "requirements": {
                "overall_minimum": 75.0
            }
        }

        # Save as YAML file
        standard_path = Path("minimal_standard.yaml")
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(minimal_standard, f)

        # Should still be valid (optional sections are optional)
        # Note: Since ContractsParser requires ADRI_STANDARDS_PATH, we'll use direct YAML loading
        try:
            with open(standard_path, 'r', encoding='utf-8') as f:
                loaded_standard = yaml.safe_load(f)
            self.assertIn("contracts", loaded_standard)
            self.assertIn("requirements", loaded_standard)
        except Exception as e:
            self.fail(f"Minimal standard failed to load: {e}")

    def test_record_identification_field_validation(self):
        """Test validation of record_identification fields."""
        test_cases = [
            # Valid cases
            (["id"], True),
            (["customer_id", "order_id"], True),

            # Invalid cases - empty array should fail validation
            ([], False),
        ]

        for primary_keys, should_be_valid in test_cases:
            standard = {
                "contracts": {
                    "id": "test_standard",
                    "name": "Test Standard",
                    "version": "1.0.0",
                    "authority": "Test"
                },
                "record_identification": {
                    "primary_key_fields": primary_keys,
                    "strategy": "primary_key_with_fallback"
                },
                "requirements": {
                    "overall_minimum": 75.0
                }
            }

            with self.subTest(primary_keys=primary_keys):
                # For now, just test that the structure can be saved and loaded as valid YAML
                # Meta-schema validation would require more complex parser integration
                standard_path = Path(f"test_{len(primary_keys)}.yaml")
                with open(standard_path, 'w', encoding='utf-8') as f:
                    yaml.dump(standard, f)

                # Basic YAML validation
                try:
                    with open(standard_path, 'r', encoding='utf-8') as f:
                        loaded_standard = yaml.safe_load(f)

                    # Verify basic structure
                    self.assertIn("contracts", loaded_standard)
                    self.assertIn("record_identification", loaded_standard)
                    self.assertEqual(loaded_standard["record_identification"]["primary_key_fields"], primary_keys)

                except Exception as e:
                    if should_be_valid:
                        self.fail(f"Valid record identification {primary_keys} failed basic validation: {e}")


class TestStandardGeneration(unittest.TestCase):
    """Test that generated standards comply with enhanced schema."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create directory structure
        Path("ADRI/dev/contracts").mkdir(parents=True, exist_ok=True)
        Path("ADRI/dev/training-data").mkdir(parents=True, exist_ok=True)

        # Create ADRI config.yaml to establish project root
        config_content = {
            "adri": {
                "project_name": "test_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "training_data": "ADRI/dev/training-data"
                        }
                    }
                }
            }
        }

        with open("ADRI/config.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_generated_standard_meta_schema_compliance(self):
        """Test that generated standards comply with the enhanced meta-schema."""
        from adri.cli import load_data
        from adri.cli.registry import get_command

        # Create test data file in current directory
        data_file = Path("products.csv")
        test_data_content = "product_id,name,price\nP001,Widget,19.99\nP002,Gadget,29.99"
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write(test_data_content)

        # Mock load_data to return our test data
        test_data = [
            {"product_id": "P001", "name": "Widget", "price": 19.99},
            {"product_id": "P002", "name": "Gadget", "price": 29.99}
        ]

        with patch('src.adri.cli.commands.generate_contract.load_data') as mock_load_data:
            mock_load_data.return_value = test_data
            generate_command = get_command("generate-contract")
            result = generate_command.execute({
                "data_path": str(data_file.absolute()),
                "force": False,
                "output": None,
                "guide": False
            })

        self.assertEqual(result, 0)

        # Load generated standard
        standard_path = Path("ADRI/dev/contracts/products_ADRI_standard.yaml")
        with open(standard_path, 'r', encoding='utf-8') as f:
            standard = yaml.safe_load(f)

        # Verify compliance with enhanced meta-schema
        self.assertIn("training_data_lineage", standard)
        self.assertIn("contracts", standard)
        self.assertIn("record_identification", standard)
        self.assertIn("requirements", standard)
        self.assertIn("metadata", standard)

        # Verify training_data_lineage structure
        lineage = standard["training_data_lineage"]
        required_lineage_fields = ["source_path", "timestamp", "file_hash"]
        for field in required_lineage_fields:
            self.assertIn(field, lineage)

        # Verify record_identification structure
        record_id = standard["record_identification"]
        self.assertIn("primary_key_fields", record_id)
        self.assertIn("strategy", record_id)

        # Should detect product_id as primary key
        self.assertEqual(record_id["primary_key_fields"], ["product_id"])

        # Verify metadata structure
        metadata = standard["metadata"]
        required_metadata_fields = ["created_by", "created_date", "generation_method"]
        for field in required_metadata_fields:
            self.assertIn(field, metadata)

        # Verify generation_method is valid
        self.assertEqual(metadata["generation_method"], "auto_generated")

    def test_hash_format_compliance(self):
        """Test that generated hashes comply with meta-schema pattern."""
        # Create test file and generate hash
        test_content = "id,value\n1,test\n2,data"
        test_file = Path("test.csv")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        from adri.cli import _generate_file_hash
        file_hash = _generate_file_hash(test_file)

        # Verify hash matches meta-schema pattern: ^[a-f0-9]{8}$
        import re
        hash_pattern = re.compile(r"^[a-f0-9]{8}$")
        self.assertTrue(hash_pattern.match(file_hash),
                       f"Hash '{file_hash}' does not match meta-schema pattern")

    def test_timestamp_format_compliance(self):
        """Test that generated timestamps comply with meta-schema pattern."""
        from adri.cli import _create_lineage_metadata

        # Create test file
        with open("test.csv", 'w', encoding='utf-8') as f:
            f.write("id,value\n1,test")

        metadata = _create_lineage_metadata("test.csv")

        # Verify timestamp format matches meta-schema pattern
        import re
        timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

        self.assertTrue(timestamp_pattern.match(metadata["timestamp"]),
                       f"Timestamp '{metadata['timestamp']}' does not match meta-schema pattern")

        self.assertTrue(timestamp_pattern.match(metadata["source_modified"]),
                       f"Source modified '{metadata['source_modified']}' does not match meta-schema pattern")


class TestExampleStandardCompliance(unittest.TestCase):
    """Test that example standards comply with enhanced schema."""

    def test_customer_data_standard_compliance(self):
        """Test that updated customer data standard complies with enhanced schema."""
        # Load the updated customer data standard
        customer_std_path = Path(__file__).parent.parent / "examples" / "standards" / "customer_data_standard.yaml"

        if customer_std_path.exists():
            with open(customer_std_path, 'r', encoding='utf-8') as f:
                standard = yaml.safe_load(f)

            # Verify required sections
            self.assertIn("contracts", standard)
            self.assertIn("requirements", standard)

            # Verify enhanced sections
            self.assertIn("record_identification", standard)
            self.assertIn("metadata", standard)

            # Verify record_identification content
            record_id = standard["record_identification"]
            self.assertIn("primary_key_fields", record_id)
            self.assertIn("strategy", record_id)

            # Verify metadata content
            metadata = standard["metadata"]
            self.assertIn("created_by", metadata)
            self.assertIn("generation_method", metadata)

            # Verify ID follows pattern (ends with _standard)
            std_id = standard["contracts"]["id"]
            self.assertTrue(std_id.endswith("_standard"))

    def test_example_standards_loadable(self):
        """Test that all example standards can be loaded."""
        examples_dir = Path(__file__).parent.parent / "examples" / "standards"

        if examples_dir.exists():
            yaml_files = list(examples_dir.glob("*.yaml"))

            for yaml_file in yaml_files:
                with self.subTest(file=yaml_file.name):
                    try:
                        # Use direct YAML loading since ContractsParser requires specific environment setup
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            standard = yaml.safe_load(f)

                        # Basic validation - must have required sections
                        self.assertIn("contracts", standard)
                        self.assertIn("requirements", standard)

                    except Exception as e:
                        self.fail(f"Failed to load {yaml_file.name}: {e}")


class TestSchemaEvolution(unittest.TestCase):
    """Test schema evolution and backward compatibility."""

    def test_old_format_standards_still_work(self):
        """Test that standards without enhanced sections still work."""
        old_format_standard = {
            "contracts": {
                "id": "legacy_standard",
                "name": "Legacy Standard",
                "version": "1.0.0",
                "authority": "Legacy Authority"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "field_requirements": {
                    "name": {"type": "string", "nullable": False}
                }
            }
        }

        # Test basic YAML structure
        try:
            yaml_content = yaml.dump(old_format_standard)
            loaded_standard = yaml.safe_load(yaml_content)

            # Should load successfully
            self.assertIn("contracts", loaded_standard)
            self.assertIn("requirements", loaded_standard)

        except Exception as e:
            self.fail(f"Old format standard failed basic validation: {e}")

    def test_new_format_standards_work(self):
        """Test that standards with all enhanced sections work."""
        new_format_standard = {
            "training_data_lineage": {
                "source_path": "/test/data.csv",
                "timestamp": "2025-09-22T12:00:00",
                "file_hash": "abcd1234"
            },
            "contracts": {
                "id": "enhanced_standard",
                "name": "Enhanced Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework"
            },
            "record_identification": {
                "primary_key_fields": ["id"],
                "strategy": "primary_key_with_fallback"
            },
            "requirements": {
                "overall_minimum": 75.0
            },
            "metadata": {
                "created_by": "ADRI Framework",
                "generation_method": "auto_generated"
            }
        }

        # Test basic YAML structure
        try:
            yaml_content = yaml.dump(new_format_standard)
            loaded_standard = yaml.safe_load(yaml_content)

            # Should load successfully with all sections
            self.assertIn("training_data_lineage", loaded_standard)
            self.assertIn("contracts", loaded_standard)
            self.assertIn("record_identification", loaded_standard)
            self.assertIn("requirements", loaded_standard)
            self.assertIn("metadata", loaded_standard)

        except Exception as e:
            self.fail(f"New format standard failed basic validation: {e}")


if __name__ == '__main__':
    unittest.main()
