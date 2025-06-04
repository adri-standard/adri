"""
Unit tests for ADRI assessment modes.

Tests the Discovery, Validation, and Auto mode functionality.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd

from adri.assessment_modes import AssessmentMode, ModeConfig
from adri.assessor import DataSourceAssessor
from adri.connectors import BaseConnector


class TestAssessmentModes:
    """Test assessment mode functionality."""
    
    def test_assessment_mode_enum(self):
        """Test AssessmentMode enum values."""
        assert AssessmentMode.DISCOVERY.value == "discovery"
        assert AssessmentMode.VALIDATION.value == "validation"
        assert AssessmentMode.AUTO.value == "auto"
    
    def test_mode_config_discovery(self):
        """Test Discovery mode configuration - facilitation approach."""
        config = ModeConfig.get_mode_config(AssessmentMode.DISCOVERY)
        
        assert config["require_explicit_metadata"] is False
        assert config["suggest_templates"] is True
        assert config["generate_metadata"] is True
        # Facilitation approach: score based purely on intrinsic quality
        assert config["intrinsic_quality_weight"] == 1.0
        assert config["metadata_quality_weight"] == 0.0
        # Auto-generate metadata to help users
        assert config["auto_generate_metadata"] is True
        assert config["business_logic_enabled"] is True
    
    def test_mode_config_validation(self):
        """Test Validation mode configuration."""
        config = ModeConfig.get_mode_config(AssessmentMode.VALIDATION)
        
        assert config["require_explicit_metadata"] is True
        assert config["suggest_templates"] is False
        assert config["generate_metadata"] is False
        assert config["intrinsic_quality_weight"] == 0.2
        assert config["metadata_quality_weight"] == 0.0  # No metadata quality score
        assert config["claims_compliance_weight"] == 0.8  # Weight on meeting claims
        assert config["business_logic_enabled"] is False
        assert config["verify_claims"] is True
        assert config["metadata_penalty"] is False
    
    def test_mode_config_auto(self):
        """Test Auto mode configuration."""
        config = ModeConfig.get_mode_config(AssessmentMode.AUTO)
        
        assert config["require_explicit_metadata"] is False
        assert config["suggest_templates"] is True
        assert config["generate_metadata"] is True
        assert config["intrinsic_quality_weight"] == 0.5
        assert config["metadata_quality_weight"] == 0.5
        assert config["business_logic_enabled"] is True
    
    def test_detect_mode_no_metadata(self):
        """Test mode detection with no metadata."""
        mock_connector = Mock(spec=BaseConnector)
        mock_connector.get_schema.return_value = {}
        
        mode = ModeConfig.detect_mode(mock_connector, has_metadata=False)
        assert mode == AssessmentMode.DISCOVERY
    
    def test_detect_mode_with_metadata(self):
        """Test mode detection with metadata."""
        mock_connector = Mock(spec=BaseConnector)
        
        mode = ModeConfig.detect_mode(mock_connector, has_metadata=True)
        assert mode == AssessmentMode.VALIDATION
    
    def test_detect_mode_with_template(self):
        """Test mode detection with template."""
        mock_connector = Mock(spec=BaseConnector)
        
        mode = ModeConfig.detect_mode(mock_connector, has_template=True)
        assert mode == AssessmentMode.VALIDATION
    
    def test_detect_mode_with_comprehensive_schema(self):
        """Test mode detection with comprehensive schema."""
        mock_connector = Mock(spec=BaseConnector)
        mock_connector.get_schema.return_value = {
            "fields": [
                {"name": "id", "type": "integer", "min_value": 1},
                {"name": "email", "type": "string", "format": "email"},
                {"name": "age", "type": "integer", "min_value": 0, "max_value": 150},
                {"name": "status", "type": "string", "allowed_values": ["active", "inactive"]}
            ]
        }
        
        mode = ModeConfig.detect_mode(mock_connector, has_metadata=False)
        assert mode == AssessmentMode.VALIDATION
    
    def test_detect_mode_with_basic_schema(self):
        """Test mode detection with basic schema."""
        mock_connector = Mock(spec=BaseConnector)
        mock_connector.get_schema.return_value = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "email", "type": "string"},
                {"name": "age", "type": "integer"},
                {"name": "status", "type": "string"}
            ]
        }
        
        mode = ModeConfig.detect_mode(mock_connector, has_metadata=False)
        assert mode == AssessmentMode.DISCOVERY


class TestAssessorModes:
    """Test assessor integration with modes."""
    
    @pytest.fixture
    def sample_data_file(self, tmp_path):
        """Create a sample CSV file for testing."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'email': ['a@test.com', 'b@test.com', None],
            'age': [25, 30, 35],
            'status': ['active', 'active', 'inactive']
        })
        filepath = tmp_path / "test_data.csv"
        df.to_csv(filepath, index=False)
        return filepath
    
    def test_assessor_auto_mode(self, sample_data_file):
        """Test assessor with auto mode."""
        assessor = DataSourceAssessor()
        assert assessor.mode == AssessmentMode.AUTO
        
        report = assessor.assess_file(sample_data_file)
        assert report.assessment_mode == "discovery"  # Should detect discovery for raw data
    
    def test_assessor_explicit_discovery(self, sample_data_file):
        """Test assessor with explicit discovery mode."""
        assessor = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)
        assert assessor.mode == AssessmentMode.DISCOVERY
        
        report = assessor.assess_file(sample_data_file)
        assert report.assessment_mode == "discovery"
        assert report.mode_config["business_logic_enabled"] is True
    
    def test_assessor_explicit_validation(self, sample_data_file):
        """Test assessor with explicit validation mode."""
        assessor = DataSourceAssessor(mode=AssessmentMode.VALIDATION)
        assert assessor.mode == AssessmentMode.VALIDATION
        
        report = assessor.assess_file(sample_data_file)
        assert report.assessment_mode == "validation"
        assert report.mode_config["business_logic_enabled"] is False
    
    def test_assessor_mode_from_string(self):
        """Test assessor creation with mode as string."""
        assessor = DataSourceAssessor(mode="discovery")
        assert assessor.mode == AssessmentMode.DISCOVERY
        
        assessor = DataSourceAssessor(mode="validation")
        assert assessor.mode == AssessmentMode.VALIDATION
        
        assessor = DataSourceAssessor(mode="auto")
        assert assessor.mode == AssessmentMode.AUTO
    
    def test_mode_config_inheritance(self):
        """Test that mode config is properly inherited by dimensions."""
        assessor = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)
        
        # Check that effective config includes mode settings
        assert assessor.effective_config["business_logic_enabled"] is True
        assert assessor.effective_config["require_explicit_metadata"] is False
        
        # User config should override mode config
        assessor = DataSourceAssessor(
            mode=AssessmentMode.DISCOVERY,
            config={"business_logic_enabled": False}
        )
        assert assessor.effective_config["business_logic_enabled"] is False
    
    @patch('adri.assessor.logger')
    def test_auto_mode_detection_logging(self, mock_logger, sample_data_file):
        """Test that auto mode detection is logged."""
        assessor = DataSourceAssessor(mode=AssessmentMode.AUTO)
        assessor.assess_file(sample_data_file)
        
        # Check that mode detection was logged
        mock_logger.info.assert_any_call("Auto-detected assessment mode: discovery")
    
    @pytest.mark.skip(reason="Scoring differences between modes not yet implemented")
    def test_scoring_differences_between_modes(self, tmp_path):
        """Test that scores differ between discovery and validation modes."""
        # Create data with some quality issues
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'email': ['a@test.com', None, 'c@test.com', None, 'e@test.com'],
            'age': [25, 30, 250, 35, 40],  # Invalid age
            'status': ['active', 'active', 'unknown', 'inactive', 'active']
        })
        filepath = tmp_path / "quality_test.csv"
        df.to_csv(filepath, index=False)
        
        # Test Discovery mode
        assessor_discovery = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)
        report_discovery = assessor_discovery.assess_file(filepath)
        
        # Test Validation mode
        assessor_validation = DataSourceAssessor(mode=AssessmentMode.VALIDATION)
        report_validation = assessor_validation.assess_file(filepath)
        
        # Scores should be different
        assert report_discovery.overall_score != report_validation.overall_score
        
        # Discovery should generally score higher for raw data without metadata
        assert report_discovery.overall_score > report_validation.overall_score


class TestBusinessLogicIntegration:
    """Test business logic enablement in different modes."""
    
    @pytest.fixture
    def crm_data_file(self, tmp_path):
        """Create CRM-like data for business logic testing."""
        df = pd.DataFrame({
            'deal_name': ['Deal A', 'Deal B', 'Deal C'],
            'stage': ['negotiation', 'proposal', 'qualification'],
            'amount': [45000, 38000, 15000],
            'close_date': [None, None, '2025-06-01'],  # Missing critical dates
            'contact_email': ['a@test.com', None, 'c@test.com'],  # Missing emails
            'last_activity_date': ['2025-05-01', '2025-04-15', '2025-05-25']
        })
        filepath = tmp_path / "crm_data.csv"
        df.to_csv(filepath, index=False)
        return filepath
    
    def test_discovery_mode_business_findings(self, crm_data_file):
        """Test that discovery mode produces business-specific findings."""
        assessor = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)
        report = assessor.assess_file(crm_data_file)
        
        # Should find business-specific issues in dimension findings
        all_findings = []
        for dim_results in report.dimension_results.values():
            all_findings.extend(dim_results.get('findings', []))
        
        business_findings = [f for f in all_findings if any(
            keyword in f.lower() for keyword in ['deal', 'email', 'close', 'negotiation']
        )]
        
        assert len(business_findings) > 0, "Discovery mode should find business issues"
    
    def test_validation_mode_no_business_findings(self, crm_data_file):
        """Test that validation mode doesn't produce business findings."""
        assessor = DataSourceAssessor(mode=AssessmentMode.VALIDATION)
        report = assessor.assess_file(crm_data_file)
        
        # Should not find business-specific issues in dimension findings
        all_findings = []
        for dim_results in report.dimension_results.values():
            all_findings.extend(dim_results.get('findings', []))
        
        # Look for business-context specific findings (not just column names)
        business_findings = [f for f in all_findings if any(
            keyword in f.lower() for keyword in ['negotiation stage', 'proposal stage', 'deals in']
        )]
        
        assert len(business_findings) == 0, "Validation mode should not find business issues"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
