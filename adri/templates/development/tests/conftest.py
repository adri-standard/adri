"""
Shared test fixtures and utilities for template testing
"""

import pytest
import pandas as pd
from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path


@pytest.fixture
def mock_assessor():
    """Mock assessor for testing without ADRI installed"""
    class MockDimensionResult:
        def __init__(self, score: float, issues: list = None):
            self.score = score
            self.issues = issues or []
    
    class MockAssessmentResult:
        def __init__(self, overall: float, validity: float = 20, 
                     completeness: float = 20, consistency: float = 20,
                     freshness: float = 20, plausibility: float = 20):
            self.overall_score = overall
            self.validity = MockDimensionResult(validity)
            self.completeness = MockDimensionResult(completeness)
            self.consistency = MockDimensionResult(consistency)
            self.freshness = MockDimensionResult(freshness)
            self.plausibility = MockDimensionResult(plausibility)
    
    class MockAssessor:
        def assess(self, data: pd.DataFrame, template: str) -> MockAssessmentResult:
            # Simple mock logic for testing
            if data.empty:
                return MockAssessmentResult(0)
            
            # Check for various conditions
            score = 100
            validity_score = 20
            completeness_score = 20
            plausibility_score = 20
            freshness_score = 20
            
            # Check completeness
            if 'amount' in data.columns and data['amount'].isna().any():
                completeness_score = 10
                score -= 20
            
            # Check validity
            if 'currency' in data.columns and data['currency'].eq('INVALID').any():
                validity_score = 10
                score -= 20
            
            # Check plausibility
            if 'amount' in data.columns and (data['amount'] < 0).any():
                plausibility_score = 10
                score -= 20
            
            return MockAssessmentResult(
                overall=score,
                validity=validity_score,
                completeness=completeness_score,
                plausibility=plausibility_score,
                freshness=freshness_score
            )
    
    return MockAssessor()


@pytest.fixture
def mock_template_loader():
    """Mock template loader for testing"""
    class MockTemplateLoader:
        @staticmethod
        def load(template_id: str) -> Dict[str, Any]:
            # Return a basic template structure
            return {
                "template": {
                    "id": template_id,
                    "name": "Mock Template"
                },
                "pattern_matching": {
                    "required_columns": ["invoice_number", "vendor_id", "amount", "currency", "due_date"]
                },
                "requirements": {
                    "overall_minimum": 85
                },
                "dimensions": {
                    "validity": {
                        "rules": [
                            {"column": "currency", "validation": {"type": "enum"}}
                        ]
                    }
                }
            }
    
    return MockTemplateLoader()


@pytest.fixture
def template_dev_path():
    """Path to template development directory"""
    return Path(__file__).parent.parent / "templates"


@pytest.fixture
def save_test_template():
    """Fixture to save test templates"""
    def _save(template_id: str, content: Dict[str, Any]):
        path = Path(__file__).parent.parent / "templates" / f"{template_id.replace('/', '_')}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(content, f, default_flow_style=False)
        return path
    
    return _save


# Test data generators
def generate_perfect_data(record_count: int = 10) -> pd.DataFrame:
    """Generate perfect test data"""
    from datetime import datetime, timedelta
    
    records = []
    for i in range(record_count):
        records.append({
            "id": f"ID-{i:05d}",
            "amount": 1000.00 + (i * 100),
            "currency": "USD" if i % 2 == 0 else "EUR",
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "status": "active",
            "category": f"CAT-{i % 5}"
        })
    
    return pd.DataFrame(records)


def generate_poor_data(record_count: int = 10) -> pd.DataFrame:
    """Generate poor quality test data"""
    from datetime import datetime, timedelta
    import numpy as np
    
    records = []
    for i in range(record_count):
        records.append({
            "id": f"ID-{i:05d}" if i % 3 != 0 else None,  # Missing IDs
            "amount": -1000.00 if i % 4 == 0 else 1000.00 + (i * 100),  # Negative amounts
            "currency": "INVALID" if i % 5 == 0 else "USD",  # Invalid currency
            "date": "invalid-date" if i % 6 == 0 else (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "status": np.nan if i % 2 == 0 else "active",  # Missing status
            "category": f"CAT-{i % 5}"
        })
    
    return pd.DataFrame(records)


# Assertion helpers
def assert_dimension_score(result, dimension: str, min_score: float, max_score: float = 20):
    """Assert dimension score is within range"""
    score = getattr(result, dimension).score
    assert min_score <= score <= max_score, \
        f"{dimension} score {score} not in range [{min_score}, {max_score}]"


def assert_overall_score(result, min_score: float, max_score: float = 100):
    """Assert overall score is within range"""
    assert min_score <= result.overall_score <= max_score, \
        f"Overall score {result.overall_score} not in range [{min_score}, {max_score}]"
