"""Test finance scenario: stock market data freshness."""

import pytest
import tempfile
import os
import pandas as pd
from datetime import datetime, timedelta

from adri.assessor import DataSourceAssessor


class TestFinanceScenario:
    """Test real-world financial data scenarios."""
    
    def test_stock_market_data_freshness(self):
        """Test stock market data freshness requirements."""
        # Create market data with different levels of staleness
        now = datetime.now()
        data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
            'last_price': [175.50, 142.30, 378.90, 178.25, 238.75],
            'bid': [175.48, 142.28, 378.85, 178.20, 238.70],
            'ask': [175.52, 142.32, 378.95, 178.30, 238.80],
            'volume': [52341000, 23456000, 18765000, 41234000, 89123000],
            'last_update': [
                now - timedelta(seconds=5),     # AAPL: 5 seconds old
                now - timedelta(minutes=2),     # GOOGL: 2 minutes old
                now - timedelta(minutes=35),    # MSFT: 35 minutes old (after market close)
                now - timedelta(hours=2),       # AMZN: 2 hours old
                now - timedelta(days=1)         # TSLA: 1 day old
            ],
            'market_status': ['open', 'open', 'closed', 'closed', 'closed']
        })
        
        # Add freshness metadata for trading
        freshness_metadata = {
            "time_field": "last_update",
            "market_based_requirements": {
                "open": {
                    "max_age_seconds": 60,  # 1 minute during market hours
                    "update_frequency": "real-time",
                    "staleness_action": "halt_trading"
                },
                "closed": {
                    "max_age_hours": 24,  # 24 hours when market closed
                    "update_frequency": "end-of-day",
                    "staleness_action": "warning"
                }
            },
            "business_criticality": "critical",
            "regulatory_requirement": "MiFID II compliant"
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
            
            # Freshness should be impacted by stale data during market hours
            freshness_score = report.dimension_results['freshness']['score']
            assert freshness_score < 15, "Stale market data should reduce freshness score"
            
            # Should flag critical freshness issues
            findings_text = ' '.join(report.summary_findings).lower()
            assert any(term in findings_text for term in ['fresh', 'stale', 'update', 'time'])
            
            # Should not be suitable for real-time trading
            # Check if the readiness level is not in the higher tiers
            assert not any(level in report.readiness_level for level in ["Advanced", "Proficient"])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(freshness_file):
                os.unlink(freshness_file)
    
    def test_financial_calculation_consistency(self):
        """Test consistency in financial calculations."""
        # Create financial data with calculation inconsistencies
        data = pd.DataFrame({
            'portfolio_id': ['P001', 'P002', 'P003', 'P004'],
            'total_value': [100000, 250000, 75000, 500000],
            'cash': [20000, 50000, 15000, 100000],
            'equities': [50000, 150000, 40000, 300000],
            'bonds': [30000, 50000, 25000, 100000],  # P003 total doesn't add up
            'return_pct': [12.5, -5.2, 8.3, 15.7],
            'start_value': [88888, 263158, 69284, 432000],  # P001 return calc is wrong
            'risk_score': [3, 7, 2, 9],
            'max_risk_allowed': [5, 5, 5, 5]  # P002 and P004 exceed risk limits
        })
        
        # Add consistency rules for financial data
        consistency_metadata = {
            "rules": [
                {
                    "name": "Portfolio value calculation",
                    "type": "calculation",
                    "formula": "total_value == cash + equities + bonds"
                },
                {
                    "name": "Return calculation check",
                    "type": "calculation",
                    "formula": "abs((total_value - start_value) / start_value * 100 - return_pct) < 0.1"
                },
                {
                    "name": "Risk limit compliance",
                    "type": "cross_field",
                    "condition": "risk_score <= max_risk_allowed"
                }
            ],
            "calculation_tolerance": 0.01  # 1% tolerance for rounding
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
            
            # Consistency should be low due to calculation errors
            consistency_score = report.dimension_results['consistency']['score']
            assert consistency_score < 12, "Calculation errors should reduce consistency score"
            
            # Should identify calculation mismatches
            findings_text = ' '.join(report.summary_findings).lower()
            assert any(term in findings_text for term in ['calculation', 'consistency', 'mismatch'])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(consistency_file):
                os.unlink(consistency_file)
    
    def test_trading_data_validity(self):
        """Test validity of trading data formats."""
        # Create trading data with format issues
        data = pd.DataFrame({
            'trade_id': ['T001', 'T002', 'T003', 'T004', 'T005'],
            'symbol': ['AAPL', 'INVALID_SYMBOL_123', 'MSFT', '', 'GOOGL'],
            'price': ['175.50', '$142.30', '378.90', '178.25', 'N/A'],  # Mixed formats
            'quantity': [100, -50, 0, 1000, 250],  # Negative and zero quantities
            'trade_type': ['BUY', 'SELL', 'HOLD', 'BUY', 'SELL'],  # HOLD is not valid
            'timestamp': [
                '2025-01-27T10:30:00Z',
                '2025-01-27T10:31:00',  # Missing timezone
                '27/01/2025 10:32:00',  # Wrong format
                '2025-01-27T10:33:00Z',
                '2025-01-27T10:34:00Z'
            ]
        })
        
        # Add validity rules
        validity_metadata = {
            "field_specifications": {
                "symbol": {
                    "type": "string",
                    "pattern": "^[A-Z]{1,5}$",
                    "required": True
                },
                "price": {
                    "type": "decimal",
                    "format": "numeric",
                    "min": 0.01,
                    "max": 999999.99
                },
                "quantity": {
                    "type": "integer",
                    "min": 1,
                    "max": 1000000
                },
                "trade_type": {
                    "type": "enum",
                    "values": ["BUY", "SELL"]
                },
                "timestamp": {
                    "type": "datetime",
                    "format": "ISO8601",
                    "timezone_required": True
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create validity metadata file
        import json
        validity_file = test_file.replace('.csv', '.validation.json')
        with open(validity_file, 'w') as f:
            json.dump(validity_metadata, f)
        
        try:
            # Assess validity
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Validity should be reduced due to format violations
            validity_score = report.dimension_results['validity']['score']
            assert validity_score < 16, "Multiple format violations should reduce validity"
            
            # Should not be suitable for automated trading
            assert "Inadequate" in report.readiness_level
            
        finally:
            os.unlink(test_file)
            if os.path.exists(validity_file):
                os.unlink(validity_file)
