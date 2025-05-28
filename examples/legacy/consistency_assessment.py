"""
Consistency Assessment Example

This example demonstrates how to use the consistency rules to validate data
for internal coherence and alignment across fields.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from adri import ADRIAssessor
from adri.datasource import CSVDataSource
from adri.rules.consistency import CrossFieldConsistencyRule, UniformRepresentationRule, CalculationConsistencyRule
from adri.rules.registry import RuleRegistry
from adri.config import Config

# Create a sample dataset with consistency issues
def create_sample_data():
    # Create sample data with 100 records
    np.random.seed(42)
    
    # Generate data
    data = {
        # Customer information
        "customer_id": list(range(1, 101)),
        "age": np.random.randint(18, 80, 100),
        "birth_date": [(datetime.now() - timedelta(days=365*age)).strftime("%Y-%m-%d") 
                      for age in np.random.randint(18, 80, 100)],
        
        # Order information
        "order_id": list(range(101, 201)),
        "order_date": [(datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime("%Y-%m-%d") 
                      for _ in range(100)],
        "order_amount": np.random.uniform(10, 500, 100).round(2),
        "discount": np.random.uniform(0, 0.3, 100).round(2),
        
        # Product information
        "product_id": np.random.randint(1000, 2000, 100),
        "quantity": np.random.randint(1, 10, 100),
        "unit_price": np.random.uniform(5, 100, 100).round(2),
        
        # Additional fields for verification
        "shipping_address": ["123 Main St"] * 80 + ["456 Elm Ave"] * 10 + ["789 Oak Rd"] * 10,
        "shipping_method": ["Standard"] * 60 + ["Express"] * 30 + ["2-Day"] * 5 + ["Next Day"] * 5,
        "payment_status": ["Paid"] * 85 + ["Pending"] * 10 + ["Failed"] * 5
    }
    
    # Add calculated fields (with some inconsistencies)
    data["total_price"] = np.array(data["quantity"]) * np.array(data["unit_price"])
    
    # Add 15 errors in the total_price calculation
    error_indices = np.random.choice(range(100), 15, replace=False)
    for idx in error_indices:
        # Introduce an error in the calculation
        data["total_price"][idx] += np.random.uniform(5, 20)
    
    # Calculate discounted total (with some inconsistencies)
    data["discounted_total"] = [
        round(total * (1 - discount), 2)
        for total, discount in zip(data["total_price"], data["discount"])
    ]
    
    # Add 10 errors in the discounted_total calculation
    error_indices = np.random.choice(range(100), 10, replace=False)
    for idx in error_indices:
        # Introduce an error in the calculation
        data["discounted_total"][idx] += np.random.uniform(5, 15)
    
    # Add inconsistent date formats to 20% of the dates
    date_error_indices = np.random.choice(range(100), 20, replace=False)
    for idx in date_error_indices:
        date_obj = datetime.strptime(data["birth_date"][idx], "%Y-%m-%d")
        # Use different format MM/DD/YYYY
        data["birth_date"][idx] = date_obj.strftime("%m/%d/%Y")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df

def main():
    # Create sample data
    df = create_sample_data()
    
    # Save to CSV for inspection
    df.to_csv("sample_orders.csv", index=False)
    print(f"Sample data saved to sample_orders.csv")
    
    # Create data source
    data_source = CSVDataSource("sample_orders.csv")
    
    # Create custom rules
    rules = [
        # Check if birth_date is consistent with age
        CrossFieldConsistencyRule(params={
            "validation_type": "expression",
            "fields": ["age", "birth_date"],
            "expression": "(pd.to_datetime('today') - pd.to_datetime(subset_df['birth_date'])).dt.days / 365 - subset_df['age'] < 1.0"
        }),
        
        # Check for uniform date format
        UniformRepresentationRule(params={
            "column": "birth_date",
            "format_type": "pattern",
            "pattern": r"^\d{4}-\d{2}-\d{2}$"
        }),
        
        # Check if total_price is correctly calculated
        CalculationConsistencyRule(params={
            "result_column": "total_price",
            "calculation_type": "expression",
            "expression": "subset_df['quantity'] * subset_df['unit_price']",
            "input_columns": ["quantity", "unit_price"],
            "tolerance": 0.01
        }),
        
        # Check if discounted_total is correctly calculated
        CalculationConsistencyRule(params={
            "result_column": "discounted_total",
            "calculation_type": "expression",
            "expression": "subset_df['total_price'] * (1 - subset_df['discount'])",
            "input_columns": ["total_price", "discount"],
            "tolerance": 0.01
        }),
        
        # Check shipping method is one of the allowed values
        UniformRepresentationRule(params={
            "column": "shipping_method",
            "format_type": "categorical",
            "allowed_values": ["Standard", "Express", "2-Day", "Next Day"],
            "case_sensitive": True
        })
    ]
    
    # Register rules
    registry = RuleRegistry()
    for rule in rules:
        registry.register(rule)
    
    # Create assessor
    assessor = ADRIAssessor(registry=registry)
    
    # Run assessment
    report = assessor.assess(data_source)
    
    # Display results
    print("\nConsistency Assessment Results:")
    print("=" * 50)
    print(f"Overall Consistency Score: {report.dimension_scores.get('consistency', 0):.2f}")
    print("\nDetailed Results:")
    
    for rule_result in report.rule_results:
        if rule_result["dimension"] == "consistency":
            rule_name = rule_result["rule_name"]
            score = rule_result["score"]
            narrative = rule_result["narrative"]
            
            print(f"\n{rule_name}: {score:.2f}")
            print("-" * 30)
            print(narrative)
    
    # Save detailed report
    report.save_html("consistency_report.html")
    print("\nDetailed report saved to consistency_report.html")

if __name__ == "__main__":
    main()
