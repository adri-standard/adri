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
        
        # Add consistency rules
        consistency_metadata = {
            "rules": [
                {
                    "name": "Active status requires valid subscription",
                    "type": "cross_field",
                    "condition": "status == 'active'",
                    "requirement": "subscription_end > now() or subscription_end is None"
                },
                {
                    "name": "Churned customers have past end dates",
                    "type": "cross_field",
                    "condition": "status == 'churned'",
                    "requirement": "subscription_end < now()"
                },
                {
                    "name": "Active customers need recent payments",
                    "type": "cross_field",
                    "condition": "status == 'active'",
                    "requirement": "(now() - last_payment_date).days < 60"
                },
                {
                    "name": "Suspended customers shouldn't have recent payments",
                    "type": "cross_field",
                    "condition": "status == 'suspended'",
                    "requirement": "(now() - last_payment_date).days > 30"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create consistency metadata file
        import json
        consistency_file = test_file.replace('.csv', '.consistency.json')
        with open(consistency_file, 'w') as f:
            json.dump(consistency_metadata, f)
        
        try:
            # Assess consistency
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Consistency should be low due to status conflicts
            consistency_score = report.dimension_results['consistency']['score']
            assert consistency_score < 12, "Status inconsistencies should reduce score"
            
            # Should identify specific consistency issues
            findings_text = ' '.join(report.summary_findings).lower()
            assert any(term in findings_text for term in ['consistency', 'status', 'subscription'])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(consistency_file):
                os.unlink(consistency_file)
    
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
        
        # Add completeness requirements
        completeness_metadata = {
            "required_fields": ["customer_id", "email", "first_name", "gdpr_consent"],
            "conditional_requirements": [
                {
                    "condition": "preferred_contact == 'email'",
                    "required": ["email"]
                },
                {
                    "condition": "preferred_contact == 'phone'",
                    "required": ["phone"]
                },
                {
                    "condition": "segment == 'premium'",
                    "required": ["email", "phone", "address"]
                }
            ],
            "completeness_targets": {
                "overall": 0.95,
                "email": 0.98,  # Critical for communication
                "gdpr_consent": 1.0  # Legal requirement
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create completeness metadata file
        import json
        completeness_file = test_file.replace('.csv', '.completeness.json')
        with open(completeness_file, 'w') as f:
            json.dump(completeness_metadata, f)
        
        try:
            # Assess completeness
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Completeness should be impacted
            completeness_score = report.dimension_results['completeness']['score']
            assert completeness_score < 16, "Missing required fields should reduce score"
            
            # Should flag GDPR consent issues
            findings_text = ' '.join(report.summary_findings).lower()
            assert 'missing' in findings_text or 'completeness' in findings_text
            
        finally:
            os.unlink(test_file)
            if os.path.exists(completeness_file):
                os.unlink(completeness_file)
    
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
        
        # Add plausibility rules
        plausibility_metadata = {
            "rules": [
                {
                    "name": "Account age plausibility",
                    "field": "account_age_days",
                    "min": 0,
                    "max": 7300,  # 20 years max
                    "typical_range": [30, 1825]  # 1 month to 5 years
                },
                {
                    "name": "Login frequency plausibility",
                    "field": "login_count_30d",
                    "min": 0,
                    "max": 120,  # 4 times per day max
                    "typical_range": [1, 30]
                },
                {
                    "name": "Purchase count plausibility",
                    "field": "purchase_count_lifetime",
                    "min": 0,
                    "max": 500,
                    "typical_range": [1, 50]
                },
                {
                    "name": "Session duration plausibility",
                    "field": "avg_session_duration_minutes",
                    "min": 0.5,
                    "max": 120,  # 2 hours max
                    "typical_range": [5, 30]
                },
                {
                    "name": "Satisfaction score range",
                    "field": "customer_satisfaction_score",
                    "min": 1,
                    "max": 10,
                    "typical_range": [6, 9]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create plausibility metadata file
        import json
        plausibility_file = test_file.replace('.csv', '.plausibility.json')
        with open(plausibility_file, 'w') as f:
            json.dump(plausibility_metadata, f)
        
        try:
            # Assess plausibility
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Plausibility should be low
            plausibility_score = report.dimension_results['plausibility']['score']
            assert plausibility_score < 12, "Implausible behavior metrics should reduce score"
            
            # Should not be suitable for behavior analysis
            # Check if the readiness level is not in the higher tiers
            assert not any(level in report.readiness_level for level in ["Advanced", "Proficient"])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(plausibility_file):
                os.unlink(plausibility_file)
