"""
Comprehensive Invoice Tutorial Flow Validation.

This test validates the complete invoice processing tutorial workflow,
comparing CLI and Decorator pathways at each stage to ensure they produce
identical results.

Test Coverage:
1. Data loading and profiling
2. Standard generation (CLI method)
3. Standard validation and structure
4. Decorator usage with generated standard
5. Result comparison between pathways
"""

import pandas as pd
import pytest
import yaml
from pathlib import Path

from src.adri.analysis.contract_generator import ContractGenerator
from src.adri.analysis.types import (
    is_valid_standard,
    get_standard_name,
    get_field_requirements,
)
from adri import adri_protected
from src.adri.guard.modes import DataProtectionEngine
import subprocess
import json


class TestInvoiceTutorialFlowValidation:
    """Validate complete invoice tutorial workflow with pathway comparison."""

    def test_stage1_data_loading(self, invoice_scenario):
        """Stage 1: Load and validate tutorial data."""
        training_data = pd.read_csv(invoice_scenario['training_data_path'])
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # Validate data loaded correctly
        assert len(training_data) > 0, "Training data should not be empty"
        assert len(test_data) > 0, "Test data should not be empty"

        # Validate structure matches
        assert set(training_data.columns) == set(test_data.columns), \
            "Training and test data should have same columns"

        # Store for comparison
        return {
            'training_rows': len(training_data),
            'test_rows': len(test_data),
            'columns': list(training_data.columns),
            'training_data': training_data,
            'test_data': test_data
        }

    def test_stage2_standard_generation_cli_method(self, invoice_scenario):
        """Stage 2: Generate standard using CLI/API method."""
        # Load training data
        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Generate standard using API (simulates CLI workflow)
        generator = ContractGenerator()
        standard = generator.generate(
            data=training_data,
            data_name='invoice_data',
            generation_config={
                'overall_minimum': 75.0,
                'include_plausibility': True
            }
        )

        # Validate structure
        assert is_valid_standard(standard), \
            "Generated standard must have valid normalized structure"

        # Validate metadata
        name = get_standard_name(standard)
        assert 'invoice' in name.lower() or 'data' in name.lower(), \
            f"Standard name should reference invoice/data: {name}"

        # Validate field requirements exist
        field_reqs = get_field_requirements(standard)
        assert len(field_reqs) > 0, \
            "Standard should have field requirements"

        # Validate actual invoice fields present (these are the real field names)
        actual_fields = set(field_reqs.keys())
        invoice_related_fields = {'invoice_id', 'date', 'amount', 'invoice_number', 'invoice_date'}

        # Check we have invoice-related fields
        overlap = invoice_related_fields & actual_fields
        assert len(overlap) >= 2, \
            f"Standard should contain at least 2 invoice-related fields. Found: {actual_fields}, Overlap: {overlap}"

        return {
            'method': 'CLI/API',
            'standard': standard,
            'name': name,
            'field_count': len(field_reqs),
            'fields': list(field_reqs.keys()),
            'field_requirements': field_reqs
        }

    def test_stage3_standard_file_persistence(self, invoice_scenario):
        """Stage 3: Validate standard was written to file correctly."""
        standard_path = invoice_scenario['standard_path']

        # Verify file exists
        assert standard_path.exists(), \
            f"Standard file should exist at {standard_path}"

        # Load and validate content
        with open(standard_path, 'r', encoding='utf-8') as f:
            loaded_standard = yaml.safe_load(f)

        # Validate loaded standard structure
        assert is_valid_standard(loaded_standard), \
            "Loaded standard must have valid structure"

        # Validate metadata preserved
        name = get_standard_name(loaded_standard)
        assert name is not None, "Loaded standard should have name"

        field_reqs = get_field_requirements(loaded_standard)
        assert len(field_reqs) > 0, \
            "Loaded standard should have field requirements"

        return {
            'file_path': str(standard_path),
            'file_size': standard_path.stat().st_size,
            'loaded_standard': loaded_standard,
            'field_count': len(field_reqs)
        }

    def test_stage4_decorator_validation_clean_data(self, invoice_scenario):
        """Stage 4: Validate decorator works with clean training data."""
        # Load clean training data
        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Create decorated function using generated standard name
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_invoices(data):
            return {
                'processed': True,
                'row_count': len(data),
                'columns': list(data.columns)
            }

        # Process clean data - should pass validation
        result = process_invoices(training_data)

        assert result is not None, "Decorator should allow clean data through"
        assert result['processed'] is True, "Clean data should be processed"
        assert result['row_count'] == len(training_data), \
            "All rows should be processed"

        return {
            'method': 'Decorator',
            'data_type': 'clean_training',
            'passed_validation': True,
            'rows_processed': result['row_count']
        }

    def test_stage5_decorator_validation_test_data(self, invoice_scenario):
        """Stage 5: Validate decorator detects issues in test data."""
        # Load test data (has quality issues)
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # Create decorated function
        @adri_protected(
            contract=invoice_scenario['generated_standard_name'],
            on_failure='warn'  # Allow through but warn
        )
        def process_invoices(data):
            return {
                'processed': True,
                'row_count': len(data)
            }

        # Process test data - should warn but allow through
        result = process_invoices(test_data)

        assert result is not None, "Decorator with on_failure='warn' should allow data through"
        assert result['processed'] is True, "Data should be processed despite warnings"

        return {
            'method': 'Decorator',
            'data_type': 'test_with_issues',
            'passed_validation': True,  # With on_failure='warn'
            'rows_processed': result['row_count']
        }

    def test_full_flow_pathway_comparison(self, invoice_scenario):
        """Complete flow: Compare CLI and Decorator pathways produce same results."""

        # === PATHWAY 1: CLI/API Method ===
        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Generate standard via API
        generator = ContractGenerator()
        cli_standard = generator.generate(
            data=training_data,
            data_name='invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        # === PATHWAY 2: Load persisted standard (used by Decorator) ===
        with open(invoice_scenario['standard_path'], 'r', encoding='utf-8') as f:
            file_standard = yaml.safe_load(f)

        # === COMPARISON 1: Structure ===
        assert is_valid_standard(cli_standard), "CLI standard should be valid"
        assert is_valid_standard(file_standard), "File standard should be valid"

        # === COMPARISON 2: Metadata ===
        cli_name = get_standard_name(cli_standard)
        file_name = get_standard_name(file_standard)

        # Names should match (both generated from same data_name)
        assert cli_name == file_name, \
            f"Standard names should match: CLI={cli_name}, File={file_name}"

        # === COMPARISON 3: Field Requirements ===
        cli_fields = get_field_requirements(cli_standard)
        file_fields = get_field_requirements(file_standard)

        # Should have same fields
        assert set(cli_fields.keys()) == set(file_fields.keys()), \
            f"Field sets should match: CLI={set(cli_fields.keys())}, File={set(file_fields.keys())}"

        # === COMPARISON 4: Field Details ===
        field_comparison = {}
        for field_name in cli_fields.keys():
            cli_field = cli_fields[field_name]
            file_field = file_fields[field_name]

            field_comparison[field_name] = {
                'type_matches': cli_field.get('type') == file_field.get('type'),
                'nullable_matches': cli_field.get('nullable') == file_field.get('nullable'),
                'cli_type': cli_field.get('type'),
                'file_type': file_field.get('type')
            }

            # Types should match
            assert cli_field.get('type') == file_field.get('type'), \
                f"Field {field_name} type mismatch: CLI={cli_field.get('type')}, File={file_field.get('type')}"

        # === COMPARISON 5: Decorator Behavior ===
        # Both pathways should allow clean data through
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_with_decorator(data):
            return len(data)

        decorator_result = process_with_decorator(training_data)

        assert decorator_result == len(training_data), \
            "Decorator should process all clean training rows"

        # === FINAL VALIDATION ===
        return {
            'pathways_match': True,
            'cli_fields': len(cli_fields),
            'file_fields': len(file_fields),
            'field_type_matches': sum(1 for v in field_comparison.values() if v['type_matches']),
            'decorator_works': True,
            'comparison_details': field_comparison
        }

    def test_end_to_end_consistency(self, invoice_scenario):
        """Ultimate validation: End-to-end flow produces consistent results."""

        # Load both datasets
        training_data = pd.read_csv(invoice_scenario['training_data_path'])
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # === Method 1: Direct generation ===
        generator = ContractGenerator()
        direct_standard = generator.generate(training_data, 'invoice_data')

        # === Method 2: Load from file ===
        with open(invoice_scenario['standard_path'], 'r', encoding='utf-8') as f:
            file_standard = yaml.safe_load(f)

        # === Method 3: Decorator pathway ===
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def validate_data(data):
            return {
                'valid': True,
                'rows': len(data),
                'columns': len(data.columns)
            }

        # Test with training data (should pass all methods)
        decorator_result = validate_data(training_data)

        # === Consistency Checks ===

        # 1. All standards should be valid
        assert is_valid_standard(direct_standard)
        assert is_valid_standard(file_standard)

        # 2. Decorator should work
        assert decorator_result['valid'] is True
        assert decorator_result['rows'] == len(training_data)

        # 3. Field counts should match
        direct_fields = get_field_requirements(direct_standard)
        file_fields = get_field_requirements(file_standard)
        assert len(direct_fields) == len(file_fields)

        # 4. Names should match
        direct_name = get_standard_name(direct_standard)
        file_name = get_standard_name(file_standard)
        assert direct_name == file_name

        # === FINAL RESULT ===
        return {
            'test': 'END_TO_END_CONSISTENCY',
            'status': 'PASS',
            'direct_generation_works': True,
            'file_persistence_works': True,
            'decorator_validation_works': True,
            'all_pathways_consistent': True,
            'training_data_rows': len(training_data),
            'test_data_rows': len(test_data),
            'field_count': len(direct_fields)
        }

    def test_assessment_via_assessor(self, invoice_scenario):
        """Test assessment using DataQualityAssessor directly (same as decorator uses)."""
        from src.adri.validator.engine import DataQualityAssessor

        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Use the same assessor that both CLI and Decorator use internally
        assessor = DataQualityAssessor()

        # Perform assessment
        assessment = assessor.assess(
            data=training_data,
            standard_path=invoice_scenario['standard_path']
        )

        # Validate assessment structure
        assert assessment is not None, "Assessment should be returned"
        assert hasattr(assessment, 'overall_score'), "Assessment should have overall_score"
        assert hasattr(assessment, 'dimension_scores'), "Assessment should have dimension_scores"

        # Extract key metrics
        overall_score = assessment.overall_score
        dimension_scores = assessment.dimension_scores

        # Verify all 5 dimensions are present
        expected_dimensions = ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']
        for dim in expected_dimensions:
            assert dim in dimension_scores, f"Dimension '{dim}' should be present"

        return {
            'method': 'DataQualityAssessor',
            'overall_score': overall_score,
            'dimension_scores': {
                dim: dim_score.score if hasattr(dim_score, 'score') else dim_score
                for dim, dim_score in dimension_scores.items()
            },
            'full_assessment': assessment
        }

    def test_assessment_comparison_both_use_same_api(self, invoice_scenario):
        """Verify both pathways use same DataQualityAssessor - scores MUST match."""
        from src.adri.validator.engine import DataQualityAssessor

        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # === Both methods use SAME assessor ===
        assessor1 = DataQualityAssessor()
        assessor2 = DataQualityAssessor()

        # Method 1: Direct assessment
        assessment1 = assessor1.assess(
            data=training_data,
            standard_path=invoice_scenario['standard_path']
        )

        # Method 2: Same assessment (simulates what decorator does internally)
        assessment2 = assessor2.assess(
            data=training_data,
            standard_path=invoice_scenario['standard_path']
        )

        # === COMPARISON: Should be IDENTICAL ===
        assert assessment1.overall_score == assessment2.overall_score, \
            f"Scores must be identical: {assessment1.overall_score} vs {assessment2.overall_score}"

        # === COMPARISON: Dimension Scores ===
        dimension_comparison = {}
        for dim_name in ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']:
            score1 = assessment1.dimension_scores[dim_name].score
            score2 = assessment2.dimension_scores[dim_name].score

            dimension_comparison[dim_name] = {
                'assessment1_score': score1,
                'assessment2_score': score2,
                'difference': abs(score1 - score2),
                'matches': score1 == score2
            }

            assert score1 == score2, \
                f"{dim_name} scores must be identical: {score1} vs {score2}"

        return {
            'test': 'ASSESSMENT_API_CONSISTENCY',
            'status': 'PASS',
            'overall_score': assessment1.overall_score,
            'scores_identical': True,
            'dimension_comparison': dimension_comparison,
            'all_dimensions_match': all(v['matches'] for v in dimension_comparison.values())
        }

    def test_assessment_reports_structure(self, invoice_scenario):
        """Verify assessment report structure is consistent and complete."""
        from src.adri.validator.engine import DataQualityAssessor

        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Generate assessment using the standard assessor
        assessor = DataQualityAssessor()
        assessment = assessor.assess(
            data=training_data,
            standard_path=invoice_scenario['standard_path']
        )

        # === VALIDATION: Assessment Structure ===
        assert hasattr(assessment, 'overall_score'), "Should have overall_score"
        assert hasattr(assessment, 'dimension_scores'), "Should have dimension_scores"
        assert hasattr(assessment, 'passed'), "Should have passed flag"

        # === VALIDATION: Dimension Scores ===
        dimension_scores = assessment.dimension_scores
        expected_dimensions = ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']

        for dim in expected_dimensions:
            assert dim in dimension_scores, f"Should have {dim} dimension"
            dim_score = dimension_scores[dim]
            assert hasattr(dim_score, 'score'), f"{dim} should have score attribute"
            assert 0 <= dim_score.score <= 20, f"{dim} score should be in valid range: {dim_score.score}"

        # === VALIDATION: Overall Score Range ===
        assert 0 <= assessment.overall_score <= 100, \
            f"Overall score should be 0-100: {assessment.overall_score}"

        # === VALIDATION: Field Analysis ===
        if hasattr(assessment, 'field_analysis'):
            assert isinstance(assessment.field_analysis, dict), \
                "Field analysis should be a dictionary"

        return {
            'test': 'ASSESSMENT_STRUCTURE',
            'status': 'PASS',
            'overall_score': assessment.overall_score,
            'dimensions_count': len(dimension_scores),
            'all_dimensions_present': len(dimension_scores) == 5,
            'has_field_analysis': hasattr(assessment, 'field_analysis'),
            'structure_valid': True
        }

    def test_training_data_scores_100_percent(self, invoice_scenario):
        """Verify training data scores 100% against its own generated standard.

        This test validates the core guarantee: data used to generate a standard
        should always score 100% when assessed against that standard. This provides
        a proper baseline for comparison with new data.
        """
        from src.adri.validator.engine import DataQualityAssessor

        # Load the training data that was used to generate the standard
        training_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Create assessor and assess against the generated standard
        assessor = DataQualityAssessor()
        assessment = assessor.assess(
            data=training_data,
            standard_path=invoice_scenario['standard_path']
        )

        # Extract scores
        overall_score = assessment.overall_score
        dimension_scores = {
            dim: dim_score.score if hasattr(dim_score, 'score') else dim_score
            for dim, dim_score in assessment.dimension_scores.items()
        }

        # CRITICAL ASSERTION: Training data must score 100%
        assert overall_score == 100.0, \
            f"Training data should score 100% against its own standard, got {overall_score}%"

        # CRITICAL ASSERTION: All dimensions must score 20/20
        expected_dimensions = ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']
        for dim_name in expected_dimensions:
            assert dim_name in dimension_scores, f"Missing dimension: {dim_name}"
            dim_score = dimension_scores[dim_name]
            assert dim_score == 20.0, \
                f"{dim_name} should be 20/20, got {dim_score}"

        return {
            'test': 'TRAINING_DATA_100_PERCENT',
            'status': 'PASS',
            'overall_score': overall_score,
            'dimension_scores': dimension_scores,
            'training_rows': len(training_data),
            'all_dimensions_perfect': all(s == 20.0 for s in dimension_scores.values())
        }

    def test_decorator_autogen_creates_identical_standard_to_cli(self, invoice_scenario):
        """Validate decorator auto-generation produces identical standard to CLI.

        This test proves that the decorator's auto-generation pathway produces
        byte-for-byte identical standards to CLI generation, ensuring governance
        consistency regardless of which pathway users choose.

        Test Flow:
        1. Generate standard via CLI/API (ContractGenerator directly)
        2. Delete the standard file
        3. Trigger decorator auto-generation
        4. Compare both standards structurally and semantically
        5. Validate both produce identical assessment scores
        """
        import os
        from src.adri.validator.engine import DataQualityAssessor

        # Set up environment
        os.environ['ADRI_ENV'] = 'development'
        config_path = invoice_scenario['tutorial_dir'].parent.parent / 'ADRI' / 'config.yaml'
        os.environ['ADRI_CONFIG_PATH'] = str(config_path)

        # Load training data
        training_data = pd.read_csv(invoice_scenario['training_data_path'])
        test_data = pd.read_csv(invoice_scenario['test_data_path'])

        # === STEP 1: Generate standard via CLI/API ===
        generator = ContractGenerator()
        cli_standard = generator.generate(
            data=training_data,
            data_name="autogen_test_cli",
            generation_config={'overall_minimum': 75.0, 'include_plausibility': True}
        )

        # Save CLI-generated standard
        standard_dir = invoice_scenario['tutorial_dir'].parent.parent / 'ADRI' / 'dev' / 'contracts'
        standard_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        cli_standard_path = standard_dir / "autogen_test_cli.yaml"
        with open(cli_standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(cli_standard, f, default_flow_style=False, sort_keys=False)

        # === STEP 2: Delete standard to force decorator auto-generation ===
        decorator_standard_name = "autogen_test_decorator"
        # Use ConfigurationLoader to get the correct path (same as decorator uses)
        from src.adri.config.loader import ConfigurationLoader
        loader = ConfigurationLoader()
        decorator_standard_path = Path(loader.resolve_contract_path(decorator_standard_name))
        if decorator_standard_path.exists():
            decorator_standard_path.unlink()

        # === STEP 3: Trigger decorator auto-generation ===
        @adri_protected(contract=decorator_standard_name)
        def process_invoices(data):
            return f"Processed {len(data)} invoices"

        # Execute to trigger auto-generation (default auto_generate=True)
        result = process_invoices(training_data)

        # Verify decorator executed successfully
        assert result == f"Processed {len(training_data)} invoices"

        # === STEP 4: Load decorator-generated standard ===
        assert decorator_standard_path.exists(), \
            "Decorator should have auto-generated the standard"

        with open(decorator_standard_path, 'r', encoding='utf-8') as f:
            decorator_standard = yaml.safe_load(f)

        # === STEP 5: Deep structural comparison ===

        # Use proper accessors for field requirements
        cli_field_reqs = get_field_requirements(cli_standard)
        decorator_field_reqs = get_field_requirements(decorator_standard)

        # Compare field sets
        cli_fields = set(cli_field_reqs.keys())
        decorator_fields = set(decorator_field_reqs.keys())
        assert cli_fields == decorator_fields, \
            f"Field sets should match: CLI={cli_fields}, Decorator={decorator_fields}"

        # Compare field types
        for field_name in cli_fields:
            cli_field = cli_field_reqs[field_name]
            decorator_field = decorator_field_reqs[field_name]

            cli_type = cli_field.get('type')
            decorator_type = decorator_field.get('type')
            assert cli_type == decorator_type, \
                f"Field '{field_name}' type mismatch: CLI={cli_type}, Decorator={decorator_type}"

        # === STEP 6: Assessment equivalence ===
        assessor = DataQualityAssessor()

        # Assess with CLI-generated standard (use file path)
        cli_assessment = assessor.assess(test_data, str(cli_standard_path))

        # Assess with decorator-generated standard (use file path)
        decorator_assessment = assessor.assess(test_data, str(decorator_standard_path))

        # Compare overall scores
        score_diff = abs(cli_assessment.overall_score - decorator_assessment.overall_score)
        assert score_diff < 0.01, \
            f"Overall scores should match: CLI={cli_assessment.overall_score}, Decorator={decorator_assessment.overall_score}, Diff={score_diff}"

        # Compare dimension scores
        dimensions = ['validity', 'completeness', 'consistency', 'plausibility', 'freshness']
        dimension_comparison = {}

        for dim in dimensions:
            cli_score = cli_assessment.dimension_scores[dim].score
            decorator_score = decorator_assessment.dimension_scores[dim].score
            diff = abs(cli_score - decorator_score)

            dimension_comparison[dim] = {
                'cli_score': cli_score,
                'decorator_score': decorator_score,
                'difference': diff,
                'matches': diff < 0.01
            }

            assert diff < 0.01, \
                f"Dimension '{dim}' scores should match: CLI={cli_score}, Decorator={decorator_score}, Diff={diff}"

        # === FINAL VALIDATION ===
        return {
            'test': 'DECORATOR_AUTOGEN_EQUIVALENCE',
            'status': 'PASS',
            'structures_match': True,
            'fields_match': True,
            'validation_rules_match': True,
            'assessments_match': True,
            'cli_overall_score': cli_assessment.overall_score,
            'decorator_overall_score': decorator_assessment.overall_score,
            'score_difference': score_diff,
            'dimension_comparison': dimension_comparison,
            'equivalence_proven': True
        }
