"""Test banking scenario: transaction format issues."""

import pytest
import tempfile
import os
import pandas as pd
from decimal import Decimal

from adri.assessor import DataSourceAssessor


class TestBankingScenario:
    """Test real-world banking data scenarios."""
    
    def test_mixed_transaction_formats(self):
        """Test handling of mixed transaction amount formats."""
        # Create banking data with mixed formats
        data = pd.DataFrame({
            'transaction_id': [1, 2, 3, 4, 5],
            'account_id': ['ACC001', 'ACC002', 'ACC003', 'ACC004', 'ACC005'],
            'amount': ['$1,000.00', '2500.50', '$3,750.25', '500', '$12,000.00'],
            'transaction_type': ['deposit', 'withdrawal', 'deposit', 'withdrawal', 'deposit'],
            'timestamp': pd.date_range('2025-01-01', periods=5, freq='H')
        })
        
        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            # Assess the data
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Validity should be impacted by mixed formats
            validity_score = report.dimension_results['validity']['score']
            assert validity_score < 20, "Mixed formats should reduce validity score"
            
            # Check findings mention format issues
            findings_text = ' '.join(report.summary_findings)
            assert any(term in findings_text.lower() for term in ['format', 'type', 'mixed'])
            
        finally:
            os.unlink(test_file)
    
    def test_transaction_validation_rules(self):
        """Test banking-specific validation rules."""
        # Create banking data with validation issues
        data = pd.DataFrame({
            'transaction_id': [1, 2, 3, 4, 5],
            'account_id': ['ACC001', 'ACC002', 'ACC003', 'ACC004', 'ACC005'],
            'amount': [1000.00, -50000.00, 0.001, 1500000.00, 250.50],  # Some problematic amounts
            'balance_after': [5000.00, -45000.00, 1000.001, 2000000.00, 1250.50],
            'transaction_type': ['deposit', 'withdrawal', 'deposit', 'deposit', 'withdrawal']
        })
        
        # Add metadata file with banking rules
        metadata = {
            "rules": [
                {
                    "name": "Minimum transaction amount",
                    "field": "amount",
                    "type": "range",
                    "min": 0.01,
                    "max": 1000000.00
                },
                {
                    "name": "No negative balances",
                    "field": "balance_after",
                    "type": "range",
                    "min": 0
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create validation metadata file
        import json
        validation_file = test_file.replace('.csv', '.validation.json')
        with open(validation_file, 'w') as f:
            json.dump(metadata, f)
        
        try:
            # Assess with validation rules
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Should detect validation failures
            validity_score = report.dimension_results['validity']['score']
            assert validity_score < 15, "Validation failures should significantly reduce score"
            
            # Plausibility should also be affected
            plausibility_score = report.dimension_results['plausibility']['score']
            assert plausibility_score < 15, "Implausible values should reduce score"
            
        finally:
            os.unlink(test_file)
            if os.path.exists(validation_file):
                os.unlink(validation_file)
    
    def test_transaction_freshness_requirements(self):
        """Test banking data freshness requirements."""
        # Create stale banking data
        data = pd.DataFrame({
            'transaction_id': range(1, 101),
            'amount': [100.00 + i * 10 for i in range(100)],
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='D')  # Old data
        })
        
        # Add freshness metadata
        freshness_metadata = {
            "update_frequency": "real-time",
            "max_age_hours": 24,
            "time_field": "timestamp",
            "business_criticality": "high"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create freshness metadata file
        import json
        freshness_file = test_file.replace('.csv', '.freshness.json')
        with open(freshness_file, 'w') as f:
            json.dump(freshness_metadata, f)
        
        try:
            # Assess freshness
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Freshness should be very low
            freshness_score = report.dimension_results['freshness']['score']
            assert freshness_score < 5, "Stale data should have very low freshness score"
            
            # Should be flagged as inadequate for real-time requirements
            assert "Inadequate" in report.readiness_level
            
        finally:
            os.unlink(test_file)
            if os.path.exists(freshness_file):
                os.unlink(freshness_file)
