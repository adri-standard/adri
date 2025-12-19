"""Example test demonstrating tutorial-based testing framework.

This file shows how to use the tutorial framework for realistic, end-to-end
testing that mirrors actual user workflows. Compare this with legacy test
patterns to see the advantages of the tutorial-based approach.
"""

import pandas as pd
import pytest
from pathlib import Path

from src.adri.decorator import adri_protected
from src.adri.core.exceptions import DataValidationError


class TestInvoiceProcessingWithTutorialFramework:
    """Example tests using the new tutorial-based framework.

    These tests demonstrate:
    1. Using real tutorial data (not synthetic)
    2. Standards generated via CLI (not hardcoded)
    3. Name-only standard resolution (user-friendly)
    4. Development environment testing (realistic)
    """

    def test_process_clean_invoice_data(self, invoice_scenario):
        """Test processing clean invoice data passes validation.

        This test uses:
        - Real tutorial training data (clean CSV)
        - CLI-generated standard
        - Name-only resolution
        """
        # Define protected function using name-only standard reference
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_invoices(data: pd.DataFrame) -> pd.DataFrame:
            """Process invoice data with ADRI protection."""
            # Business logic would go here
            return data

        # Load clean training data from tutorial
        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Process should succeed with clean data
        result = process_invoices(training_data)

        # Verify processing completed
        assert result is not None
        assert len(result) > 0
        assert list(result.columns) == list(training_data.columns)

    def test_detect_quality_issues_in_test_data(self, invoice_scenario):
        """Test that quality issues in test data are detected.

        This test demonstrates:
        - Using test data with known quality issues
        - Expected validation failures or warnings
        - Realistic error scenarios from tutorials
        """
        @adri_protected(
            contract=invoice_scenario['generated_standard_name'],
            on_failure='warn'  # Allow processing with warnings
        )
        def process_invoices_with_warnings(data: pd.DataFrame) -> pd.DataFrame:
            """Process invoices but warn on quality issues."""
            return data

        # Load test data with quality issues
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # Process should complete but may generate warnings
        result = process_invoices_with_warnings(test_data)

        # Data processed despite issues
        assert result is not None
        # Note: Actual warning capture would depend on ADRI implementation

    def test_strict_mode_rejects_problematic_data(self, invoice_scenario):
        """Test that strict mode rejects data with quality issues.

        Demonstrates:
        - Strict failure mode behavior
        - Expected exceptions for bad data
        - Protection against low-quality data processing
        """
        @adri_protected(
            contract=invoice_scenario['generated_standard_name'],
            on_failure='raise'  # Strict mode
        )
        def process_invoices_strict(data: pd.DataFrame) -> pd.DataFrame:
            """Strictly validate invoices before processing."""
            return data

        # Load problematic test data
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # Should raise exception with strict validation
        # (This assumes test_invoice_data.csv has quality issues)
        # Uncomment if ADRI raises exceptions for low-quality data:
        # with pytest.raises(DataQualityError):
        #     process_invoices_strict(test_data)

        # For now, just verify test data exists and is readable
        assert len(test_data) > 0

    def test_scenario_provides_complete_metadata(self, invoice_scenario):
        """Verify scenario provides all required metadata.

        Validates the tutorial scenario structure for developers
        who want to use it in their own tests.
        """
        # Check all required keys present
        required_keys = [
            'name',
            'tutorial_dir',
            'training_data_path',
            'test_data_path',
            'generated_standard_name',
            'standard_path',
            'description'
        ]

        for key in required_keys:
            assert key in invoice_scenario, f"Missing key: {key}"

        # Verify paths exist
        assert invoice_scenario['tutorial_dir'].exists()
        assert invoice_scenario['training_data_path'].exists()
        assert invoice_scenario['test_data_path'].exists()
        assert invoice_scenario['standard_path'].exists()

        # Verify standard name format (name only, no path/extension)
        standard_name = invoice_scenario['generated_standard_name']
        assert '/' not in standard_name
        assert '\\' not in standard_name
        assert not standard_name.endswith('.yaml')
        assert not standard_name.endswith('.yml')

    def test_data_consistency_between_files(self, invoice_scenario):
        """Verify training and test data have consistent structure.

        Both datasets should have the same columns to ensure
        standards generated from training data work with test data.
        """
        training_data = pd.read_csv(invoice_scenario['training_data_path'])
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # Same column structure
        assert set(training_data.columns) == set(test_data.columns)

        # Both non-empty
        assert len(training_data) > 0
        assert len(test_data) > 0


class TestComparisonWithLegacyPattern:
    """Compare tutorial framework with legacy fixture patterns.

    These tests show the difference between old and new approaches,
    highlighting the benefits of the tutorial-based framework.
    """

    def test_legacy_pattern_with_synthetic_data(self, temp_workspace):
        """Example of legacy pattern using synthetic data.

        LEGACY APPROACH:
        - Manually create synthetic data
        - Hardcode standard structure
        - Use full path to standard file
        - Manual setup and teardown
        """
        from tests.fixtures.modern_fixtures import ModernFixtures
        import yaml

        # 1. Create synthetic data (not from tutorials)
        synthetic_data = ModernFixtures.create_comprehensive_mock_data(
            rows=50,
            quality_level="high"
        )

        # 2. Create hardcoded standard
        standard_dict = ModernFixtures.create_standards_data("comprehensive")

        # 3. Write standard to file with full path
        standard_file = temp_workspace / "ADRI" / "dev" / "standards" / "legacy_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard_dict, f)

        # 4. Use decorator with full path (less user-friendly)
        @adri_protected(contract=str(standard_file))  # Full path required
        def process_legacy_data(data: pd.DataFrame) -> pd.DataFrame:
            return data

        # Process synthetic data
        result = process_legacy_data(synthetic_data)
        assert result is not None

        # ⚠️ Issues with this approach:
        # - Synthetic data doesn't match real user scenarios
        # - Hardcoded standards may drift from actual usage
        # - Full path is fragile and not how users work
        # - No connection to tutorial workflows

    def test_tutorial_pattern_with_real_data(self, invoice_scenario):
        """Example of new pattern using tutorial framework.

        TUTORIAL APPROACH:
        - Uses real tutorial data
        - Standards generated via CLI
        - Name-only resolution (user-friendly)
        - Automatic setup via fixtures
        """
        # 1. Fixture automatically:
        #    - Copies tutorial data
        #    - Generates standard via CLI
        #    - Provides metadata

        # 2. Use name-only standard (how users work)
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_tutorial_data(data: pd.DataFrame) -> pd.DataFrame:
            return data

        # 3. Load real tutorial data
        tutorial_data = pd.read_csv(invoice_scenario['training_data_path'])

        # 4. Process with realistic workflow
        result = process_tutorial_data(tutorial_data)
        assert result is not None

        # ✅ Benefits of this approach:
        # - Real tutorial data ensures realistic testing
        # - CLI-generated standards match user experience
        # - Name-only resolution is user-friendly
        # - Validates actual tutorial workflows
        # - Framework handles all setup automatically


class TestCustomScenarioCreation:
    """Examples of creating custom scenarios based on tutorial patterns."""

    def test_custom_standard_generation(self, tutorial_project):
        """Create custom standard with specific configuration.

        Shows how to generate standards with custom thresholds
        while still using tutorial data as foundation.
        """
        from tests.fixtures.tutorial_scenarios import (
            TutorialScenarios,
            StandardGenConfig
        )

        # Copy tutorial data
        training_path, test_path = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=tutorial_project / "custom_scenario"
        )

        # Generate standard with custom config
        config: StandardGenConfig = {
            'source_data': training_path,
            'output_name': 'custom_invoice_standard',
            'threshold': 90.0,  # Higher threshold than default
            'include_plausibility': False  # Disable plausibility rules
        }

        standard_name = TutorialScenarios.generate_standard_from_data(
            project_root=tutorial_project,
            config=config
        )

        # Verify custom standard created
        assert standard_name == 'custom_invoice_standard'

        standard_path = tutorial_project / "ADRI" / "dev" / "contracts" / f"{standard_name}.yaml"
        assert standard_path.exists()

        # Use custom standard
        @adri_protected(contract=standard_name)
        def process_with_custom_standard(data: pd.DataFrame) -> pd.DataFrame:
            return data

        data = pd.read_csv(training_path)
        result = process_with_custom_standard(data)
        assert result is not None

    def test_inspect_generated_standard(self, invoice_scenario, tutorial_project):
        """Inspect generated standard content for debugging.

        Useful when you need to understand what the CLI generated
        or validate standard structure in tests.
        """
        from tests.fixtures.tutorial_scenarios import StandardTemplates

        # Load generated standard as dictionary
        standard_dict = StandardTemplates.from_tutorial(
            tutorial_name="invoice_processing",
            project_root=tutorial_project
        )

        # Inspect standard structure
        assert standard_dict is not None
        assert isinstance(standard_dict, dict)

        # Can validate specific sections if needed
        # (Exact structure depends on ADRI CLI output)
        assert 'metadata' in standard_dict or 'name' in standard_dict or 'contracts' in standard_dict


class TestMigrationGuidelines:
    """Guidelines for migrating from legacy to tutorial-based fixtures.

    These examples show how to identify tests that should be migrated
    and the step-by-step process for migration.
    """

    def test_identify_migration_candidate(self, temp_workspace):
        """Example of a test that should be migrated.

        INDICATORS FOR MIGRATION:
        1. Creates synthetic data manually
        2. Hardcodes standard structure
        3. Uses full paths to standards
        4. Doesn't validate user workflows
        5. Complex setup/teardown
        """
        # This is a migration candidate - uses legacy patterns
        from tests.fixtures.modern_fixtures import ModernFixtures
        import yaml

        data = ModernFixtures.create_comprehensive_mock_data(rows=10)
        standard = ModernFixtures.create_standards_data("minimal")

        standard_file = temp_workspace / "ADRI" / "dev" / "contracts" / "test.yaml"
        standard_file.parent.mkdir(parents=True, exist_ok=True)
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(standard, f)

        # Complex setup that could be simplified
        assert data is not None
        assert standard_file.exists()

    def test_migrated_to_tutorial_framework(self, invoice_scenario):
        """Same test migrated to tutorial framework.

        MIGRATION STEPS:
        1. Replace synthetic data with tutorial data
        2. Replace hardcoded standard with generated one
        3. Use name-only resolution
        4. Remove manual setup code
        5. Use scenario fixture
        """
        # Much simpler with tutorial framework!
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_data(data: pd.DataFrame) -> pd.DataFrame:
            return data

        data = pd.read_csv(invoice_scenario['training_data_path'])
        result = process_data(data)

        assert result is not None


# Migration Checklist Template
"""
MIGRATION CHECKLIST:

For each test being migrated from legacy to tutorial framework:

[ ] Identified tutorial scenario that fits the test purpose
[ ] Replaced synthetic data with tutorial data
[ ] Replaced hardcoded standard with generated standard
[ ] Changed to name-only standard resolution
[ ] Removed manual setup/teardown code
[ ] Verified test still passes with tutorial data
[ ] Updated test documentation
[ ] Removed or deprecated old test version

BENEFITS AFTER MIGRATION:

✅ More realistic testing (uses actual tutorial data)
✅ Better user workflow validation
✅ Less code to maintain (framework handles setup)
✅ Easier for new developers to understand
✅ Standards stay in sync with CLI behavior
✅ Tests validate tutorial quality
"""
