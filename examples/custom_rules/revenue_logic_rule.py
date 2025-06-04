#!/usr/bin/env python3
"""
Revenue Logic Rule - Example Custom ADRI Rule

This rule validates that revenue calculations follow expected business logic.
It checks cross-field relationships like: revenue = quantity * unit_price * (1 - discount)

Usage:
    python revenue_logic_rule.py  # Run standalone demo
    
    # Or use in ADRI assessment:
    from revenue_logic_rule import RevenueLogicRule
"""

from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
import numpy as np
from typing import Dict, Any


@RuleRegistry.register
class RevenueLogicRule(DiagnosticRule):
    """Validates revenue calculations and business logic."""
    
    rule_id = "custom.revenue_logic"
    dimension = "plausibility"
    name = "Revenue Business Logic"
    description = "Ensures revenue calculations follow business rules"
    version = "1.0.0"
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate revenue = quantity * unit_price * (1 - discount)."""
        required_cols = ['quantity', 'unit_price', 'discount', 'revenue']
        missing = [c for c in required_cols if c not in data.columns]
        
        if missing:
            return {
                "score": 0.0,
                "valid": False,
                "findings": [f"Missing required columns: {missing}"],
                "details": {"missing_columns": missing}
            }
        
        # Handle potential nulls
        clean_data = data[required_cols].dropna()
        if len(clean_data) == 0:
            return {
                "score": self.params.get("weight", 1.0),
                "valid": True,
                "findings": ["No complete records to validate"],
                "details": {"records_checked": 0}
            }
        
        # Calculate expected revenue
        expected_revenue = (
            clean_data['quantity'] * 
            clean_data['unit_price'] * 
            (1 - clean_data['discount'])
        )
        
        # Check accuracy within tolerance
        tolerance = self.params.get("tolerance", 0.01)  # 1 cent default
        differences = abs(clean_data['revenue'] - expected_revenue)
        accurate = differences <= tolerance
        accuracy_rate = accurate.sum() / len(clean_data)
        
        # Find discrepancies
        discrepancies = clean_data[~accurate].copy()
        discrepancies['expected'] = expected_revenue[~accurate]
        discrepancies['difference'] = discrepancies['revenue'] - discrepancies['expected']
        
        # Analyze patterns in discrepancies
        findings = [
            f"Revenue accuracy: {accuracy_rate:.1%}",
            f"Checked {len(clean_data)} records"
        ]
        
        if len(discrepancies) > 0:
            avg_error = discrepancies['difference'].abs().mean()
            max_error = discrepancies['difference'].abs().max()
            findings.append(f"Average discrepancy: ${avg_error:.2f}")
            findings.append(f"Maximum discrepancy: ${max_error:.2f}")
            
            # Check for systematic errors
            if discrepancies['difference'].std() < tolerance * 10:
                # Low variance suggests systematic error
                mean_error = discrepancies['difference'].mean()
                if abs(mean_error) > tolerance:
                    findings.append(f"Systematic bias detected: ${mean_error:.2f} average")
            
            # Check for common patterns
            # Pattern 1: Discount not applied
            no_discount_error = discrepancies[
                abs(discrepancies['expected'] - 
                    discrepancies['quantity'] * discrepancies['unit_price']) < tolerance
            ]
            if len(no_discount_error) > 0:
                findings.append(f"Discount not applied in {len(no_discount_error)} cases")
            
            # Pattern 2: Rounding errors
            rounding_errors = discrepancies[
                (discrepancies['difference'].abs() < 0.10) & 
                (discrepancies['difference'].abs() > tolerance)
            ]
            if len(rounding_errors) > 0:
                findings.append(f"Possible rounding errors in {len(rounding_errors)} cases")
        
        # Prepare largest errors for details
        largest_errors = []
        if len(discrepancies) > 0:
            top_errors = discrepancies.nlargest(5, 'difference', keep='all')
            for _, row in top_errors.iterrows():
                largest_errors.append({
                    'quantity': float(row['quantity']),
                    'unit_price': float(row['unit_price']),
                    'discount': float(row['discount']),
                    'revenue': float(row['revenue']),
                    'expected': float(row['expected']),
                    'difference': float(row['difference'])
                })
        
        return {
            "score": accuracy_rate * self.params.get("weight", 1.0),
            "valid": accuracy_rate >= self.params.get("threshold", 0.99),
            "findings": findings,
            "details": {
                "accuracy_rate": accuracy_rate,
                "discrepancy_count": len(discrepancies),
                "total_records": len(clean_data),
                "null_records": len(data) - len(clean_data),
                "largest_errors": largest_errors
            }
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """Generate detailed narrative about revenue validation."""
        details = result.get("details", {})
        accuracy = details.get("accuracy_rate", 0)
        total = details.get("total_records", 0)
        
        if total == 0:
            return "No complete records found to validate revenue calculations."
        
        narrative = f"Revenue calculations show {accuracy:.1%} accuracy across {total} records. "
        
        discrepancy_count = details.get("discrepancy_count", 0)
        if discrepancy_count > 0:
            narrative += f"{discrepancy_count} records have calculation errors. "
            
            # Add info about largest errors
            largest = details.get("largest_errors", [])
            if largest:
                max_error = max(abs(e['difference']) for e in largest)
                narrative += f"Largest discrepancy: ${max_error:.2f}. "
            
            # Check for systematic issues
            findings = result.get("findings", [])
            for finding in findings:
                if "Systematic bias" in finding or "Discount not applied" in finding:
                    narrative += f"{finding}. "
                    break
        
        narrative += "Rule " + ("passed" if result["valid"] else "failed") + "."
        return narrative


if __name__ == "__main__":
    """Standalone demo of the revenue logic rule."""
    print("Revenue Logic Rule Demo")
    print("=" * 50)
    
    # Create test data with various scenarios
    np.random.seed(42)
    n_records = 20
    
    # Generate base data
    test_data = pd.DataFrame({
        'order_id': [f'ORD{i:03d}' for i in range(1, n_records + 1)],
        'quantity': np.random.randint(1, 10, n_records),
        'unit_price': np.random.uniform(10, 100, n_records).round(2),
        'discount': np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], n_records)
    })
    
    # Calculate correct revenue for most records
    test_data['revenue'] = (
        test_data['quantity'] * 
        test_data['unit_price'] * 
        (1 - test_data['discount'])
    ).round(2)
    
    # Introduce errors in some records
    # Error 1: Forget to apply discount (rows 5-7)
    mask1 = test_data.index.isin([5, 6, 7])
    test_data.loc[mask1, 'revenue'] = (
        test_data.loc[mask1, 'quantity'] * 
        test_data.loc[mask1, 'unit_price']
    ).round(2)
    
    # Error 2: Calculation mistakes (rows 10-11)
    test_data.loc[10, 'revenue'] = test_data.loc[10, 'revenue'] + 50.00
    test_data.loc[11, 'revenue'] = test_data.loc[11, 'revenue'] - 25.00
    
    # Error 3: Small rounding errors (rows 15-16)
    test_data.loc[15, 'revenue'] = test_data.loc[15, 'revenue'] + 0.03
    test_data.loc[16, 'revenue'] = test_data.loc[16, 'revenue'] - 0.02
    
    print("\nTest Data (showing first 10 rows):")
    print(test_data.head(10))
    print(f"... ({len(test_data)} total rows)")
    
    # Test 1: Strict validation (1 cent tolerance)
    print("\n" + "-" * 50)
    print("Test 1: Strict validation (1 cent tolerance)")
    
    rule = RevenueLogicRule()
    rule.params = {
        'weight': 1.0,
        'threshold': 0.99,  # Require 99% accuracy
        'tolerance': 0.01   # 1 cent tolerance
    }
    
    result1 = rule.evaluate(test_data)
    
    print("\nResults:")
    print(f"Score: {result1['score']:.2f}")
    print(f"Valid: {result1['valid']}")
    print("\nFindings:")
    for finding in result1['findings']:
        print(f"  - {finding}")
    
    if result1['details']['largest_errors']:
        print("\nLargest Errors:")
        for i, error in enumerate(result1['details']['largest_errors'][:3]):
            print(f"  {i+1}. Expected ${error['expected']:.2f}, "
                  f"Got ${error['revenue']:.2f} "
                  f"(Diff: ${error['difference']:.2f})")
    
    print("\nAI Narrative:")
    print(rule.generate_narrative(result1))
    
    # Test 2: Relaxed validation (10 cent tolerance)
    print("\n" + "-" * 50)
    print("Test 2: Relaxed validation (10 cent tolerance)")
    
    rule.params['tolerance'] = 0.10  # 10 cents
    rule.params['threshold'] = 0.90  # 90% accuracy
    
    result2 = rule.evaluate(test_data)
    
    print(f"\nValid: {result2['valid']}")
    print(f"Accuracy: {result2['details']['accuracy_rate']:.1%}")
    print(f"Narrative: {rule.generate_narrative(result2)}")
    
    # Test 3: Data with nulls
    print("\n" + "-" * 50)
    print("Test 3: Handling null values")
    
    test_data_nulls = test_data.copy()
    test_data_nulls.loc[0:2, 'revenue'] = np.nan
    test_data_nulls.loc[3:4, 'quantity'] = np.nan
    
    result3 = rule.evaluate(test_data_nulls)
    
    print(f"\nRecords with nulls: {result3['details']['null_records']}")
    print(f"Records validated: {result3['details']['total_records']}")
    print(f"Narrative: {rule.generate_narrative(result3)}")
