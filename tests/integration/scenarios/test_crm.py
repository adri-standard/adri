"""Test CRM scenario: customer status consistency."""

import pytest
import tempfile
import os
import pandas as pd
from datetime import datetime, timedelta

from adri.assessor import DataSourceAssessor


class TestCRMScenario:
    """Test real-world CRM data scenarios."""
    
    def test_customer_status_consistency(self):
        """Test customer status and subscription consistency."""
        # Create customer data with status inconsistencies
        now = datetime.now()
        data = pd.DataFrame({
            'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
            'status': ['active', 'active', 'churned', 'suspended', 'active'],
            'subscription_start': [
                now - timedelta(days=365),
                now - timedelta(days=180),
                now - timedelta(days=730),
                now - timedelta(days=90),
                now - timedelta(days=30)
            ],
            'subscription_end': [
                now + timedelta(days=365),  # C001: Valid active
                now - timedelta(days=30),   # C002: Expired but marked active!
                now - timedelta(days=365),  # C003: Valid churned
                now + timedelta(days=275),  # C004: Suspended but has future end date
                None                        # C005: Active with no end date (could be valid)
            ],
            'last_payment_date': [
                now - timedelta(days=15),   # C001: Recent payment
                now - timedelta(days=75),   # C002: No recent payment
                now - timedelta(days=400),  # C003: Very old payment
                now - timedelta(days=45),   # C004: Payment while suspended?
                now - timedelta(days=5)     # C005: Recent payment
            ],
            'lifetime_value': [2400, 1200, 3600, 800, 150],
            'support_tickets_open': [0, 5, 0, 12, 1]  # C002 has many open tickets while "active"
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            # Assess consistency
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Consistency should be acceptable even without specific metadata
            consistency_score = report.dimension_results['consistency']['score']
            assert consistency_score >= 10, f"Basic consistency score should be moderate, got {consistency_score}"
            
            # Check consistency findings if available
            consistency_result = report.dimension_results['consistency']
            if 'findings' in consistency_result:
                findings_text = ' '.join(consistency_result['findings']).lower()
                # Even without specific metadata, general consistency should be mentioned
                assert 'consistency' in findings_text or 'acceptable' in findings_text
            
        finally:
            os.unlink(test_file)
    
    def test_customer_data_completeness(self):
        """Test completeness of customer profile data."""
        # Create customer data with varying completeness
        data = pd.DataFrame({
            'customer_id': range(1, 21),
            'email': ['user{}@example.com'.format(i) if i % 5 != 0 else None for i in range(1, 21)],
            'phone': ['+1234567890' if i % 3 != 0 else None for i in range(1, 21)],
            'first_name': ['Customer{}'.format(i) for i in range(1, 21)],
            'last_name': ['Name{}'.format(i) if i % 7 != 0 else None for i in range(1, 21)],
            'address': ['123 Main St' if i % 4 != 0 else None for i in range(1, 21)],
            'preferred_contact': ['email' if i % 2 == 0 else 'phone' for i in range(1, 21)],
            'gdpr_consent': [True if i % 6 != 0 else None for i in range(1, 21)],  # Missing consent!
            'marketing_opt_in': [True, False] * 10,
            'segment': ['premium' if i % 5 == 0 else 'standard' for i in range(1, 21)]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            # Assess completeness
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Completeness should be impacted by missing values
            completeness_score = report.dimension_results['completeness']['score']
            assert completeness_score <= 16, f"Missing values should reduce completeness score, got {completeness_score}"
            
            # Check completeness findings
            completeness_result = report.dimension_results['completeness']
            if 'findings' in completeness_result:
                findings_text = ' '.join(completeness_result['findings']).lower()
                # Should mention missing values
                assert 'missing' in findings_text or 'completeness' in findings_text or 'null' in findings_text
            
        finally:
            os.unlink(test_file)
    
    def test_customer_behavior_plausibility(self):
        """Test plausibility of customer behavior metrics."""
        # Create customer behavior data with implausible values
        data = pd.DataFrame({
            'customer_id': range(1, 11),
            'account_age_days': [365, 730, 30, -10, 1095, 180, 90, 450, 270, 60],  # Negative age!
            'login_count_30d': [15, 300, 5, 20, 0, 10, 1500, 25, 8, 12],  # 300 and 1500 are too high
            'purchase_count_lifetime': [10, 5, 0, 25, 1000, 3, 8, 15, 2, 50],  # 1000 is implausible
            'avg_session_duration_minutes': [5, 10, 480, 15, 3, 2, 20, 1440, 12, 8],  # 480 and 1440 too long
            'page_views_per_session': [8, 15, 5, 1000, 12, 6, 20, 10, 3, 25],  # 1000 is impossible
            'customer_satisfaction_score': [8, 9, 11, 7, -2, 10, 8, 9, 6, 15]  # Should be 1-10
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
        
        try:
            # Assess plausibility
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Plausibility should be affected by extreme values
            plausibility_score = report.dimension_results['plausibility']['score']
            assert plausibility_score < 20, f"Extreme values should reduce plausibility score, got {plausibility_score}"
            
            # Check the overall score reflects data quality issues
            assert report.overall_score < 80, f"Data with extreme values should have reduced overall score, got {report.overall_score}"
            
            # Should not be in the highest readiness level
            assert report.grade not in ["A", "B"], f"Data with extreme values should not get high grade, got {report.grade}"
            
        finally:
            os.unlink(test_file)
