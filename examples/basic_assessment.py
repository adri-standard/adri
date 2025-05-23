"""
Basic example of using the ADRI framework.

This example demonstrates how to:
1. Create a simple CSV data source
2. Configure a basic assessment
3. Run the assessment
4. Display the results
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adri import ADRIAssessor, Config
from adri.datasource import CSVDataSource
from adri.rules.validity_rules import EmailFormatRule, NumericRangeRule, DataTypeRule
from adri.registry import RuleRegistry
from adri.dimensions import Validity


def create_sample_data():
    """Create a sample CSV file with test data."""
    # Create a directory for sample data if it doesn't exist
    os.makedirs("examples/data", exist_ok=True)
    
    # Sample data with some quality issues
    data = {
        "id": [1, 2, 3, 4, 5, "6", 7, 8, 9, 10],
        "name": ["John Doe", "Jane Smith", "Bob Johnson", "Alice Brown", "Charlie Davis", 
                 "Eva Wilson", "Frank Miller", "Grace Lee", "Henry Garcia", "Ivy Clark"],
        "email": ["john.doe@example.com", "jane.smith@example.com", "bobjohnson@example", 
                  "alice@brown@example.com", "charlie.davis@example.com", 
                  "eva.wilson@example.com", "frank.miller", "grace.lee@example.com", 
                  "henrygarcia@example.com", "ivy.clark@example.com"],
        "age": [30, 25, 45, 35, 50, 22, 38, -5, 42, 29],
        "active": [True, True, False, True, True, "yes", 1, 0, "no", "invalid"],
    }
    
    df = pd.DataFrame(data)
    
    # Save the data to a CSV file
    file_path = "examples/data/sample_data.csv"
    df.to_csv(file_path, index=False)
    
    print(f"Created sample data at: {file_path}")
    return file_path


def main():
    """Run a basic ADRI assessment."""
    # Create sample data
    file_path = create_sample_data()
    
    # Create a data source
    data_source = CSVDataSource(file_path)
    
    # Create a custom configuration
    config = Config.default()
    config.set("dimensions.validity.threshold", 0.8)
    config.set("assessment.parallel", True)
    config.set("assessment.workers", 4)
    
    # Create a rule registry and register some rules
    registry = RuleRegistry()
    
    # Register a rule to check email format
    registry.register(EmailFormatRule(severity=4))
    
    # Register a rule to check age range
    registry.register(NumericRangeRule(
        min_value=0,
        max_value=120,
        severity=3
    ))
    
    # Register a rule to check ID type
    registry.register(DataTypeRule(
        expected_type="int",
        severity=2
    ))
    
    # Register a rule to check active status
    registry.register(DataTypeRule(
        expected_type="bool",
        severity=2
    ))
    
    # Create an assessor with the custom configuration and registry
    assessor = ADRIAssessor(config=config, registry=registry)
    
    # Run the assessment
    print("Running ADRI assessment...")
    results = assessor.assess(
        data_source=data_source,
        dimensions=["Validity"],
        columns=["id", "email", "age", "active"]
    )
    
    # Display the results
    print("\nAssessment Results:")
    print(f"Overall Score: {results['overall_score']:.2f}")
    
    for dimension, dim_result in results["dimension_scores"].items():
        print(f"\n{dimension} Score: {dim_result['score']:.2f}")
        print(f"Is Acceptable: {'Yes' if dim_result['acceptable'] else 'No'}")
        print(f"Rules Executed: {dim_result['rules_executed']}")
        print(f"Rules with Issues: {dim_result['rules_with_issues']}")
    
    # Show detailed results for each rule
    print("\nDetailed Rule Results:")
    for rule_result in results["rule_results"]:
        print(f"\nRule: {rule_result['rule_name']}")
        print(f"Dimension: {rule_result['dimension']}")
        print(f"Severity: {rule_result['severity']}")
        print(f"Status: {rule_result['status']}")
        print(f"Total Records: {rule_result['total_records']}")
        print(f"Invalid Records: {rule_result['invalid_records']}")
        
        # Show a sample of the issues found (up to 5)
        if rule_result["invalid_records"] > 0:
            print("Sample Issues:")
            for i, issue in enumerate(rule_result["results"][:5]):
                print(f"  - {issue['message']}")
            
            if rule_result["invalid_records"] > 5:
                print(f"  ... and {rule_result['invalid_records'] - 5} more issues")
    
    # Save the results to a JSON file
    output_path = "examples/data/assessment_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nSaved detailed results to: {output_path}")


if __name__ == "__main__":
    main()
