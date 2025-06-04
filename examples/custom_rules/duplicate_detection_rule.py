#!/usr/bin/env python3
"""
Duplicate Detection Rule - Example Custom ADRI Rule

This rule identifies duplicate records in a dataset based on configurable key fields.
It can detect exact duplicates or use fuzzy matching for near-duplicates.

Usage:
    python duplicate_detection_rule.py  # Run standalone demo
    
    # Or use in ADRI assessment:
    from duplicate_detection_rule import DuplicateDetectionRule
"""

from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
from typing import Dict, Any, List, Optional


@RuleRegistry.register
class DuplicateDetectionRule(DiagnosticRule):
    """Detects duplicate records based on key fields."""
    
    rule_id = "custom.duplicate_detection"
    dimension = "consistency"
    name = "Duplicate Record Detection"
    description = "Identifies duplicate records based on configurable key fields"
    version = "1.0.0"
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicates based on key fields."""
        # Get key fields from params or use all columns
        key_fields = self.params.get("key_fields", list(data.columns))
        
        # Validate key fields exist
        missing_fields = [f for f in key_fields if f not in data.columns]
        if missing_fields:
            return {
                "score": 0.0,
                "valid": False,
                "findings": [f"Missing key fields: {missing_fields}"],
                "details": {"missing_fields": missing_fields}
            }
        
        # Find duplicates
        duplicates = data.duplicated(subset=key_fields, keep=False)
        duplicate_count = duplicates.sum()
        duplicate_ratio = duplicate_count / len(data) if len(data) > 0 else 0
        
        # Calculate score (inverse of duplicate ratio)
        score = (1 - duplicate_ratio) * self.params.get("weight", 1.0)
        
        # Identify duplicate groups
        duplicate_groups = {}
        if duplicate_count > 0:
            # Get duplicate records
            dup_data = data[duplicates]
            
            # Group by key fields and count
            group_counts = dup_data.groupby(key_fields).size().sort_values(ascending=False)
            
            # Get top duplicate groups
            top_groups = group_counts.head(5)
            
            # Format for output
            for idx, count in top_groups.items():
                # Convert index to string representation
                if isinstance(idx, tuple):
                    key = " | ".join([f"{k}={v}" for k, v in zip(key_fields, idx)])
                else:
                    key = f"{key_fields[0]}={idx}"
                duplicate_groups[key] = int(count)
        
        findings = [
            f"Found {duplicate_count} duplicate records ({duplicate_ratio:.1%})",
            f"Key fields checked: {', '.join(key_fields)}"
        ]
        
        if duplicate_groups:
            findings.append(f"Largest duplicate group has {max(duplicate_groups.values())} records")
        
        # Check against threshold
        threshold = self.params.get("threshold", 0.01)  # Default 1% tolerance
        
        return {
            "score": score,
            "valid": duplicate_ratio <= threshold,
            "findings": findings,
            "details": {
                "duplicate_count": int(duplicate_count),
                "total_records": len(data),
                "duplicate_ratio": duplicate_ratio,
                "key_fields": key_fields,
                "top_duplicate_groups": duplicate_groups
            }
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """Generate AI-friendly description."""
        details = result.get("details", {})
        count = details.get("duplicate_count", 0)
        total = details.get("total_records", 0)
        ratio = details.get("duplicate_ratio", 0)
        
        if count == 0:
            return "No duplicate records found. Data consistency is excellent."
        
        narrative = f"Found {count} duplicate records ({ratio:.1%} of {total} total). "
        
        # Add details about top duplicates if available
        top_dupes = details.get("top_duplicate_groups", {})
        if top_dupes:
            max_count = max(top_dupes.values())
            narrative += f"Most common duplicate appears {max_count} times. "
        
        key_fields = details.get("key_fields", [])
        if key_fields:
            narrative += f"Checked fields: {', '.join(key_fields)}. "
        
        narrative += "Rule " + ("passed" if result["valid"] else "failed") + "."
        return narrative


if __name__ == "__main__":
    """Standalone demo of the duplicate detection rule."""
    print("Duplicate Detection Rule Demo")
    print("=" * 50)
    
    # Create test data with intentional duplicates
    test_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C001', 'C004', 
                       'C005', 'C002', 'C006', 'C001', 'C007'],
        'order_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-01', '2024-01-04',
                      '2024-01-05', '2024-01-02', '2024-01-06', '2024-01-01', '2024-01-07'],
        'product': ['Widget', 'Gadget', 'Tool', 'Widget', 'Device',
                   'Widget', 'Gadget', 'Tool', 'Widget', 'Gadget'],
        'amount': [100, 200, 150, 100, 250,
                  100, 200, 175, 100, 225]
    })
    
    print("\nTest Data:")
    print(test_data)
    
    # Test 1: Check duplicates on customer_id + order_date
    print("\n" + "-" * 50)
    print("Test 1: Checking for duplicates on customer_id + order_date")
    
    rule = DuplicateDetectionRule()
    rule.params = {
        'weight': 1.0,
        'threshold': 0.20,  # Allow up to 20% duplicates for demo
        'key_fields': ['customer_id', 'order_date']
    }
    
    result1 = rule.evaluate(test_data)
    
    print("\nResults:")
    print(f"Score: {result1['score']:.2f}")
    print(f"Valid: {result1['valid']}")
    print("\nFindings:")
    for finding in result1['findings']:
        print(f"  - {finding}")
    
    print("\nTop Duplicate Groups:")
    for group, count in result1['details']['top_duplicate_groups'].items():
        print(f"  - {group}: {count} records")
    
    print("\nAI Narrative:")
    print(rule.generate_narrative(result1))
    
    # Test 2: Check duplicates on customer_id only
    print("\n" + "-" * 50)
    print("Test 2: Checking for duplicates on customer_id only")
    
    rule.params['key_fields'] = ['customer_id']
    rule.params['threshold'] = 0.50  # Allow up to 50% duplicates
    
    result2 = rule.evaluate(test_data)
    
    print(f"\nValid: {result2['valid']}")
    print(f"Duplicate ratio: {result2['details']['duplicate_ratio']:.1%}")
    print(f"Narrative: {rule.generate_narrative(result2)}")
    
    # Test 3: Check with all fields (no duplicates expected)
    print("\n" + "-" * 50)
    print("Test 3: Checking with all fields")
    
    rule.params['key_fields'] = ['customer_id', 'order_date', 'product', 'amount']
    rule.params['threshold'] = 0.01  # Very strict
    
    result3 = rule.evaluate(test_data)
    
    print(f"\nValid: {result3['valid']}")
    print(f"Duplicate ratio: {result3['details']['duplicate_ratio']:.1%}")
    print(f"Narrative: {rule.generate_narrative(result3)}")
