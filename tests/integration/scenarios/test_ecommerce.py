"""Test e-commerce scenario: pricing plausibility."""

import pytest
import tempfile
import os
import pandas as pd

from adri.assessor import DataSourceAssessor


class TestEcommerceScenario:
    """Test real-world e-commerce data scenarios."""
    
    def test_implausible_product_pricing(self):
        """Test handling of implausible product prices."""
        # Create product data with pricing issues
        data = pd.DataFrame({
            'product_id': ['PROD001', 'PROD002', 'PROD003', 'PROD004', 'PROD005', 'PROD006'],
            'product_name': ['USB Cable', 'Laptop', 'Toaster', 'iPhone 15', 'Coffee Mug', 'Diamond Ring'],
            'category': ['Electronics', 'Electronics', 'Appliances', 'Electronics', 'Home', 'Jewelry'],
            'price': [0.99, 5.00, 10000.00, 999.99, 150.00, 25.00],  # Laptop $5, Toaster $10k, Ring $25
            'cost': [0.50, 400.00, 25.00, 800.00, 5.00, 1500.00],  # Cost > Price for some
            'discount_percent': [10, 95, 0, 0, 90, 99],  # Extreme discounts
            'inventory_count': [500, 10, 5, 100, 0, 1]
        })
        
        # Add plausibility metadata
        plausibility_metadata = {
            "rules": [
                {
                    "name": "Electronics price range",
                    "field": "price",
                    "condition": "category == 'Electronics'",
                    "subcategory_ranges": {
                        "USB Cable": [5, 50],
                        "Laptop": [200, 5000],
                        "iPhone": [500, 2000]
                    }
                },
                {
                    "name": "Appliances price range",
                    "field": "price",
                    "condition": "category == 'Appliances'",
                    "range": [20, 1000]
                },
                {
                    "name": "Jewelry price range",
                    "field": "price", 
                    "condition": "category == 'Jewelry'",
                    "range": [50, 50000]
                },
                {
                    "name": "Price vs Cost check",
                    "type": "relationship",
                    "fields": ["price", "cost"],
                    "rule": "price > cost * 1.1"  # At least 10% margin
                },
                {
                    "name": "Discount sanity check",
                    "field": "discount_percent",
                    "range": [0, 75]  # Max 75% discount
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
            # Assess the data
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Plausibility should be impacted by implausible prices
            plausibility_score = report.dimension_results['plausibility']['score']
            assert plausibility_score <= 16, "Implausible prices should impact plausibility score"
            
            # Just verify the dimension was assessed
            assert 'plausibility' in report.dimension_results
            assert report.dimension_results['plausibility']['score'] >= 0
            
        finally:
            os.unlink(test_file)
            if os.path.exists(plausibility_file):
                os.unlink(plausibility_file)
    
    def test_inventory_consistency(self):
        """Test inventory data consistency."""
        # Create inventory data with consistency issues
        data = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003', 'P004'],
            'status': ['in_stock', 'out_of_stock', 'discontinued', 'in_stock'],
            'inventory_count': [50, 100, 25, 0],  # P002 out of stock but has inventory, P004 opposite
            'can_order': [True, True, True, True],  # Can order discontinued?
            'last_restock_date': ['2025-01-01', '2025-01-15', '2023-06-01', '2025-01-20'],
            'next_restock_date': ['2025-02-01', None, '2025-02-15', '2025-01-25'],  # Discontinued has restock date
            'warehouse_location': ['A1', 'B2', None, 'C3']  # In stock but no location
        })
        
        # Add consistency rules
        consistency_metadata = {
            "rules": [
                {
                    "name": "Stock status vs inventory count",
                    "type": "cross_field",
                    "condition": "status == 'out_of_stock'",
                    "requirement": "inventory_count == 0"
                },
                {
                    "name": "In stock requires inventory",
                    "type": "cross_field",
                    "condition": "status == 'in_stock'",
                    "requirement": "inventory_count > 0"
                },
                {
                    "name": "Discontinued products cannot be ordered",
                    "type": "cross_field",
                    "condition": "status == 'discontinued'",
                    "requirement": "can_order == False"
                },
                {
                    "name": "Discontinued products no restock",
                    "type": "cross_field",
                    "condition": "status == 'discontinued'",
                    "requirement": "next_restock_date is None"
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
            
            # Consistency should be impacted by violations
            consistency_score = report.dimension_results['consistency']['score']
            assert consistency_score <= 15, "Consistency violations should impact score"
            
            # Should be flagged as risky for agents
            # Check if the readiness level is not in the higher tiers
            assert not any(level in report.readiness_level for level in ["Advanced", "Proficient"])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(consistency_file):
                os.unlink(consistency_file)
    
    def test_dynamic_pricing_freshness(self):
        """Test freshness requirements for dynamic pricing."""
        # Create pricing data with varying freshness
        data = pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'current_price': [29.99, 49.99, 19.99, 199.99, 9.99],
            'competitor_price': [28.99, 52.99, 18.99, 189.99, 10.99],
            'last_price_update': [
                '2025-01-27 09:00:00',  # 13 hours ago
                '2025-01-27 21:00:00',  # 1 hour ago
                '2025-01-25 12:00:00',  # 2.5 days ago
                '2025-01-20 08:00:00',  # 7+ days ago
                '2025-01-27 22:00:00'   # Current
            ],
            'price_volatility': ['low', 'high', 'medium', 'high', 'low']
        })
        
        # Add freshness requirements based on volatility
        freshness_metadata = {
            "time_field": "last_price_update",
            "volatility_based_requirements": {
                "high": {
                    "max_age_hours": 1,
                    "update_frequency": "hourly"
                },
                "medium": {
                    "max_age_hours": 24,
                    "update_frequency": "daily"
                },
                "low": {
                    "max_age_hours": 168,  # 1 week
                    "update_frequency": "weekly"
                }
            },
            "business_criticality": "high",
            "affects": "pricing_decisions"
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
            
            # Freshness should be moderate (some stale, some fresh)
            freshness_score = report.dimension_results['freshness']['score']
            assert freshness_score <= 17, "Mixed freshness should have moderate freshness score"
            
            # Just verify the dimension was assessed
            assert 'freshness' in report.dimension_results
            assert report.dimension_results['freshness']['score'] >= 0
            
        finally:
            os.unlink(test_file)
            if os.path.exists(freshness_file):
                os.unlink(freshness_file)
