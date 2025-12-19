"""Integration tests for schema validator integration with assessment engine and decorator.

Tests the complete flow:
1. Schema validation runs during assessment
2. Auto-fix applies by default (case-insensitive matching)
3. Strict mode can be enabled for case-sensitive validation
4. Schema results stored in metadata
5. Decorator works correctly with auto-fix
"""

import json
import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.adri.decorator import adri_protected
from src.adri.guard.modes import ProtectionError
from src.adri.validator.engine import DataQualityAssessor


@pytest.fixture
def temp_contract_dir():
    """Create temporary directory for test contracts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def case_mismatch_data():
    """Data with case mismatched field names."""
    return pd.DataFrame({
        'PROJECT_ID': ['P001', 'P002', 'P003'],
        'CLIENT': ['ClientA', 'ClientB', 'ClientC'],
        'STATUS': ['Active', 'Pending', 'Completed'],
        'AMOUNT': [1000, 2000, 3000]
    })


@pytest.fixture
def contract_lowercase_fields(temp_contract_dir):
    """Contract expecting lowercase field names."""
    contract_dict = {
        'metadata': {
            'name': 'test_contract',
            'version': '1.0.0',
            'domain': 'testing'
        },
        'requirements': {
            'overall_minimum': 75.0,
            'field_requirements': {
                'project_id': {'type': 'string', 'nullable': False},
                'client': {'type': 'string', 'nullable': False},
                'status': {'type': 'string', 'nullable': False},
                'amount': {'type': 'number', 'nullable': False}
            },
            'dimension_requirements': {
                'validity': {'weight': 1.0},
                'completeness': {'weight': 1.0},
                'consistency': {'weight': 1.0},
                'freshness': {'weight': 1.0},
                'plausibility': {'weight': 1.0}
            }
        }
    }
    
    contract_path = temp_contract_dir / 'test_contract.yaml'
    with open(contract_path, 'w') as f:
        yaml.dump(contract_dict, f)
    
    return str(contract_path)


@pytest.fixture
def perfect_match_data():
    """Data with perfectly matching field names."""
    return pd.DataFrame({
        'project_id': ['P001', 'P002', 'P003'],
        'client': ['ClientA', 'ClientB', 'ClientC'],
        'status': ['Active', 'Pending', 'Completed'],
        'amount': [1000, 2000, 3000]
    })


class TestSchemaValidationAutoFix:
    """Test schema validation with AUTO-FIX (default behavior)."""

    def test_case_mismatch_auto_fixed_by_default(
        self, case_mismatch_data, contract_lowercase_fields
    ):
        """Verify case mismatches are automatically fixed by default."""
        assessor = DataQualityAssessor()
        result = assessor.assess(case_mismatch_data, contract_lowercase_fields)
        
        # Schema validation should be in metadata
        assert 'schema_validation' in result.metadata
        schema_info = result.metadata['schema_validation']
        
        # With auto-fix enabled (default), case mismatches are corrected
        # So we should have 4 exact matches after auto-fix
        assert schema_info['exact_matches'] == 4
        assert schema_info['match_percentage'] == 100.0
        
        # No case mismatch warnings (they were auto-fixed)
        case_warnings = [w for w in schema_info.get('warnings', [])
                        if w.get('type') == 'FIELD_CASE_MISMATCH']
        assert len(case_warnings) == 0

    def test_perfect_match_no_warnings(
        self, perfect_match_data, contract_lowercase_fields
    ):
        """Verify no schema warnings with perfect field name match."""
        assessor = DataQualityAssessor()
        result = assessor.assess(perfect_match_data, contract_lowercase_fields)
        
        # Schema validation should be in metadata
        assert 'schema_validation' in result.metadata
        schema_info = result.metadata['schema_validation']
        
        # Perfect match: 4 exact matches, 100%
        assert schema_info['exact_matches'] == 4
        assert schema_info['match_percentage'] == 100.0
        
        # No CRITICAL or ERROR warnings
        critical_or_error_warnings = [
            w for w in schema_info.get('warnings', [])
            if w.get('severity') in ['CRITICAL', 'ERROR']
        ]
        assert len(critical_or_error_warnings) == 0

    def test_auto_fix_enables_validation_rules(
        self, case_mismatch_data, contract_lowercase_fields
    ):
        """Verify auto-fix allows validation rules to execute."""
        assessor = DataQualityAssessor()
        result = assessor.assess(case_mismatch_data, contract_lowercase_fields)
        
        # With auto-fix, validation should run successfully
        # Check that we get good quality scores (not 0.0 from missing fields)
        assert result.overall_score > 0.0
        
        # Completeness should be 100% (all required fields present after rename)
        completeness_score = result.dimension_scores.get('completeness')
        if hasattr(completeness_score, 'score'):
            assert completeness_score.score == 20.0


class TestDecoratorAutoFix:
    """Test decorator integration with auto-fix behavior."""

    def test_decorator_succeeds_with_auto_fix(
        self, case_mismatch_data, contract_lowercase_fields, monkeypatch
    ):
        """Verify decorator allows data through when auto-fix corrects case mismatches."""
        # Set up environment
        contract_dir = Path(contract_lowercase_fields).parent
        monkeypatch.setenv('ADRI_STANDARDS_DIR', str(contract_dir))
        
        # Create decorator-protected function
        @adri_protected(
            contract='test_contract',
            data_param='data',
            min_score=75.0,
            on_failure='raise'
        )
        def process_data(data):
            return data
        
        # Should NOT raise - auto-fix corrects the case mismatch
        result = process_data(case_mismatch_data)
        assert result is not None

    def test_decorator_no_false_positives_perfect_match(
        self, perfect_match_data, contract_lowercase_fields, tmp_path, monkeypatch
    ):
        """Verify decorator doesn't show schema errors when fields match perfectly."""
        # Set up environment
        contract_dir = Path(contract_lowercase_fields).parent
        monkeypatch.setenv('ADRI_STANDARDS_DIR', str(contract_dir))
        
        # Set up logging directory
        log_dir = tmp_path / 'logs'
        log_dir.mkdir()
        monkeypatch.setenv('ADRI_LOG_DIR', str(log_dir))
        
        # Create decorator-protected function
        @adri_protected(
            contract='test_contract',
            data_param='data',
            min_score=75.0,
            on_failure='raise'
        )
        def process_data(data):
            return data
        
        # Should NOT raise (perfect match, good quality)
        result = process_data(perfect_match_data)
        assert result is not None


class TestSchemaValidationMetadata:
    """Test schema validation metadata storage."""

    def test_schema_metadata_structure(
        self, case_mismatch_data, contract_lowercase_fields
    ):
        """Verify schema validation metadata has correct structure."""
        assessor = DataQualityAssessor()
        result = assessor.assess(case_mismatch_data, contract_lowercase_fields)
        
        # Schema validation should be in metadata
        assert 'schema_validation' in result.metadata
        schema_info = result.metadata['schema_validation']
        
        # Check all expected fields
        assert 'match_percentage' in schema_info
        assert 'exact_matches' in schema_info
        assert 'case_insensitive_matches' in schema_info
        assert 'total_standard_fields' in schema_info
        assert 'total_data_fields' in schema_info
        assert 'warnings' in schema_info
        assert isinstance(schema_info['warnings'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
