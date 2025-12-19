"""
Tests for source code bug fixes uncovered during TDD.

These tests validate that the bugs discovered during tutorial framework
development have been properly fixed in the source code.
"""

import pytest
import pandas as pd
from src.adri.analysis.data_profiler import ProfileResult, DataProfiler
from src.adri.analysis.types import (
    is_valid_standard,
    get_standard_name,
    get_field_requirements,
)


class TestDataProfilerInterface:
    """Validate ProfileResult has clear dict-like interface."""

    def test_profile_result_to_dict(self):
        """Test that ProfileResult.to_dict() works."""
        profile = ProfileResult(
            field_profiles={'field1': 'profile1'},
            summary_statistics={'total_rows': 10},
            data_quality_score=85.0,
            metadata={'key': 'value'}
        )

        result_dict = profile.to_dict()

        assert isinstance(result_dict, dict)
        assert 'field_profiles' in result_dict
        assert 'summary_statistics' in result_dict
        assert 'data_quality_score' in result_dict
        assert 'metadata' in result_dict
        assert result_dict['data_quality_score'] == 85.0

    def test_profile_result_get_field_profile(self):
        """Test that ProfileResult.get_field_profile() works."""
        profile = ProfileResult(
            field_profiles={'field1': 'profile1', 'field2': 'profile2'},
            summary_statistics={},
            data_quality_score=80.0
        )

        field_profile = profile.get_field_profile('field1')
        assert field_profile == 'profile1'

        with pytest.raises(KeyError):
            profile.get_field_profile('nonexistent')

    def test_profile_result_get_field_names(self):
        """Test that ProfileResult.get_field_names() works."""
        profile = ProfileResult(
            field_profiles={'field1': 'prof1', 'field2': 'prof2', 'field3': 'prof3'},
            summary_statistics={},
            data_quality_score=75.0
        )

        names = profile.get_field_names()
        assert isinstance(names, list)
        assert len(names) == 3
        assert 'field1' in names
        assert 'field2' in names
        assert 'field3' in names

    def test_profile_result_has_field(self):
        """Test that ProfileResult.has_field() works."""
        profile = ProfileResult(
            field_profiles={'field1': 'prof1'},
            summary_statistics={},
            data_quality_score=70.0
        )

        assert profile.has_field('field1') is True
        assert profile.has_field('nonexistent') is False

    def test_profile_result_attribute_access(self):
        """Test that ProfileResult supports direct attribute access."""
        profile = ProfileResult(
            field_profiles={'field1': 'prof1'},
            summary_statistics={'rows': 100},
            data_quality_score=90.0
        )

        # Test direct attribute access
        assert profile.field_profiles == {'field1': 'prof1'}
        assert profile.summary_statistics == {'rows': 100}
        assert profile.data_quality_score == 90.0

    def test_profiler_returns_profile_result_with_interface(self):
        """Test that DataProfiler returns ProfileResult with new interface."""
        data = pd.DataFrame({
            'field1': [1, 2, 3],
            'field2': ['a', 'b', 'c']
        })

        profiler = DataProfiler()
        profile = profiler.profile_data(data)

        # Verify it's a ProfileResult with the new interface
        assert isinstance(profile, ProfileResult)
        assert hasattr(profile, 'to_dict')
        assert hasattr(profile, 'get_field_profile')
        assert hasattr(profile, 'get_field_names')
        assert hasattr(profile, 'has_field')

        # Test the methods work
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict, dict)

        field_names = profile.get_field_names()
        assert 'field1' in field_names
        assert 'field2' in field_names


class TestStandardStructureConsistency:
    """Validate standard structure - ONLY normalized format supported."""

    def test_is_valid_standard_accepts_normalized(self):
        """Test that valid normalized structure is accepted."""
        normalized = {
            'contracts': {'id': 'test', 'name': 'Test'},
            'requirements': {'field_requirements': {}}
        }

        assert is_valid_standard(normalized) is True

    def test_is_valid_standard_rejects_legacy(self):
        """Test that legacy/flat structure is rejected."""
        legacy = {
            'id': 'test',
            'name': 'Test',
            'field_requirements': {}
        }

        assert is_valid_standard(legacy) is False

    def test_is_valid_standard_rejects_missing_contracts(self):
        """Test that structure missing 'contracts' section is rejected."""
        invalid = {
            'requirements': {'field_requirements': {}}
        }

        assert is_valid_standard(invalid) is False

    def test_is_valid_standard_rejects_missing_requirements(self):
        """Test that structure missing 'requirements' section is rejected."""
        invalid = {
            'contracts': {'id': 'test', 'name': 'Test'}
        }

        assert is_valid_standard(invalid) is False

    def test_get_standard_name_from_normalized(self):
        """Test extracting name from normalized format."""
        normalized = {
            'contracts': {'name': 'Customer Data'},
            'requirements': {}
        }

        name = get_standard_name(normalized)
        assert name == 'Customer Data'

    def test_get_standard_name_rejects_legacy(self):
        """Test that legacy format raises ValueError."""
        legacy = {'name': 'Customer Data', 'id': 'customer_data'}

        with pytest.raises(ValueError) as exc_info:
            get_standard_name(legacy)

        assert 'normalized format' in str(exc_info.value)

    def test_get_field_requirements_from_normalized(self):
        """Test extracting field requirements from normalized format."""
        normalized = {
            'contracts': {},
            'requirements': {
                'field_requirements': {
                    'field1': {'type': 'string'},
                    'field2': {'type': 'integer'}
                }
            }
        }

        reqs = get_field_requirements(normalized)
        assert 'field1' in reqs
        assert 'field2' in reqs
        assert reqs['field1']['type'] == 'string'

    def test_get_field_requirements_rejects_legacy(self):
        """Test that legacy format raises ValueError."""
        legacy = {
            'field_requirements': {
                'field1': {'type': 'string'},
                'field2': {'type': 'integer'}
            }
        }

        with pytest.raises(ValueError) as exc_info:
            get_field_requirements(legacy)

        assert 'normalized format' in str(exc_info.value)


class TestParameterNaming:
    """Validate parameter names clearly indicate what they accept."""

    def test_decorator_standard_parameter_accepts_name(self):
        """Test that decorator standard parameter accepts name strings."""
        from adri import adri_protected

        # This should work with a name string
        @adri_protected(contract="test_standard")
        def process_data(data):
            return data

        # Check the decorator configuration
        assert hasattr(process_data, '_adri_protected')
        assert process_data._adri_config['contract'] == 'test_standard'

    def test_decorator_standard_parameter_requires_value(self):
        """Test that decorator raises clear error when standard is missing."""
        from adri import adri_protected

        with pytest.raises(ValueError) as exc_info:
            @adri_protected()  # Missing standard parameter
            def process_data(data):
                return data

        error_msg = str(exc_info.value)
        assert 'contract' in error_msg.lower()
        assert 'required' in error_msg.lower() or 'missing' in error_msg.lower()


class TestContractGeneratorFormat:
    """Validate ContractGenerator produces normalized format only."""

    def test_generate_produces_normalized_format(self):
        """Test that generate() produces normalized format."""
        from src.adri.analysis.contract_generator import ContractGenerator

        data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['NYC', 'LA', 'Chicago']
        })

        generator = ContractGenerator()
        standard = generator.generate(data, 'test_data')

        # Verify normalized structure
        assert is_valid_standard(standard)
        assert 'contracts' in standard
        assert 'requirements' in standard

        # Verify we can use utility functions
        name = get_standard_name(standard)
        assert name is not None
        assert 'test' in name.lower() or 'data' in name.lower()

        field_reqs = get_field_requirements(standard)
        assert isinstance(field_reqs, dict)
        assert 'name' in field_reqs or 'age' in field_reqs

    def test_convenience_function_produces_normalized_format(self):
        """Test that convenience function produces normalized format."""
        from src.adri.analysis.contract_generator import generate_contract_from_data

        data = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [100, 200, 300]
        })

        standard = generate_contract_from_data(data, 'test_standard')

        # Verify normalized structure
        assert is_valid_standard(standard)
        assert 'contracts' in standard
        assert 'requirements' in standard
