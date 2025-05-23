"""
Example of rule evaluation with actual data.

This script demonstrates how to use the ADRI rules to evaluate 
actual data and generate assessment results.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(parent_dir))

from adri.rules import RuleRegistry
from adri.config import get_config

# Import rule modules to register rules
import adri.rules.validity
import adri.rules.plausibility


def create_sample_data(rows=1000):
    """Create a sample DataFrame for testing."""
    # Create data with some intentional quality issues
    np.random.seed(42)  # For reproducibility
    
    # Create mostly integer column with some non-integers
    integers = np.random.randint(1, 100, rows)
    # Add some strings to create inconsistency
    integers_with_issues = [
        str(x) if i % 50 != 0 else f"{x}A" 
        for i, x in enumerate(integers)
    ]
    
    # Create dates with some inconsistencies
    dates = pd.date_range('2023-01-01', periods=rows).strftime('%Y-%m-%d').tolist()
    # Add some inconsistent date formats
    for i in range(0, rows, 100):
        if i < len(dates):
            # Convert YYYY-MM-DD to MM/DD/YYYY
            parts = dates[i].split('-')
            dates[i] = f"{parts[1]}/{parts[2]}/{parts[0]}"
    
    # Create IDs with some inconsistencies
    ids = [f"ID-{str(i).zfill(5)}" for i in range(rows)]
    # Add some inconsistencies
    for i in range(0, rows, 75):
        if i < len(ids):
            ids[i] = ids[i].lower()  # Make lowercase
    
    # Create numeric column with outliers
    normal_values = np.random.normal(50, 10, rows)
    # Add some extreme outliers
    for i in range(0, rows, 200):
        if i < len(normal_values):
            normal_values[i] = np.random.choice([200, -50, 300])
    
    # Create the DataFrame
    df = pd.DataFrame({
        'id': ids,
        'integer_col': integers_with_issues,
        'date_col': dates,
        'numeric_col': normal_values,
        'category_col': np.random.choice(['A', 'B', 'C', 'D'], size=rows)
    })
    
    return df


def evaluate_rules_on_data(df):
    """Evaluate rules on a DataFrame."""
    print("\n=== Evaluating Rules on Sample Data ===\n")
    
    # Get configuration
    config = get_config()
    
    # Rules to evaluate
    rule_ids = [
        "validity.type_consistency",
        "plausibility.outlier_detection"
    ]
    
    results = {}
    
    for rule_id in rule_ids:
        print(f"\nEvaluating {rule_id}...")
        
        # Get rule configuration
        rule_config = config.get_rule_config(rule_id)
        
        # Create rule instance
        rule = RuleRegistry.create_rule(rule_id, rule_config)
        
        # Evaluate rule
        result = rule.evaluate(df)
        
        # Generate narrative
        narrative = rule.generate_narrative(result)
        
        # Store results
        results[rule_id] = {
            "result": result,
            "narrative": narrative
        }
        
        # Print summary
        print(f"Score: {result.get('score', 0)}/{rule_config.get('weight', 0)}")
        print(f"Valid: {result.get('valid', False)}")
        print(f"Narrative:")
        print(f"{narrative}")
    
    return results


if __name__ == "__main__":
    # Create sample data
    print("Creating sample data...")
    sample_df = create_sample_data(1000)
    print(f"Sample data shape: {sample_df.shape}")
    print(f"Sample data columns: {', '.join(sample_df.columns)}")
    print("\nSample data preview:")
    print(sample_df.head(3))
    
    # Evaluate rules
    results = evaluate_rules_on_data(sample_df)
