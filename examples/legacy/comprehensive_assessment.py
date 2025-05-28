"""
Comprehensive Data Quality Assessment Example

This example demonstrates how to use all dimensions of the ADRI framework together
to perform a comprehensive data quality assessment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

from adri import ADRIAssessor
from adri.datasource import CSVDataSource
from adri.rules.validity import TypeValidityRule, FormatValidityRule, RangeValidityRule
from adri.rules.completeness import RecordCompletenessRule, FieldCompletenessRule
from adri.rules.freshness import TimestampFreshnessRule
from adri.rules.consistency import CrossFieldConsistencyRule, UniformRepresentationRule, CalculationConsistencyRule
from adri.rules.plausibility import OutlierDetectionRule, ValueDistributionRule, RangeCheckRule, PatternFrequencyRule
from adri.rules.registry import RuleRegistry
from adri.config import Config

# Create a comprehensive sample dataset with various quality issues
def create_sample_data():
    # Create sample data with 500 records
    np.random.seed(42)
    
    # Timestamp range for the last 30 days with some older records
    now = datetime.now()
    recent_dates = [(now - timedelta(days=np.random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S") 
                   for _ in range(450)]
    # Add some older timestamps
    old_dates = [(now - timedelta(days=np.random.randint(90, 365))).strftime("%Y-%m-%d %H:%M:%S") 
                for _ in range(50)]
    all_dates = recent_dates + old_dates
    np.random.shuffle(all_dates)
    
    # Generate customer names with some invalid formats
    first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Jennifer", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    
    names = []
    for _ in range(500):
        if np.random.random() < 0.05:  # 5% with numbers in name (validity issue)
            names.append(f"{np.random.choice(first_names)}123 {np.random.choice(last_names)}")
        else:
            names.append(f"{np.random.choice(first_names)} {np.random.choice(last_names)}")
    
    # Generate email addresses with some invalid formats
    emails = []
    for i in range(500):
        name_parts = names[i].lower().split()
        if len(name_parts) > 1:
            base_email = f"{name_parts[0][0]}{name_parts[-1]}"
            if np.random.random() < 0.07:  # 7% invalid emails (validity issue)
                emails.append(f"{base_email}@example")  # Missing .com
            else:
                emails.append(f"{base_email}@example.com")
        else:
            emails.append(f"user{i}@example.com")
    
    # Generate ages with some impossibly high values (plausibility issue)
    ages = np.random.randint(18, 80, 500)
    ages[np.random.choice(range(500), 20)] = np.random.randint(120, 200, 20)  # Invalid ages
    
    # Generate income values with outliers
    incomes = np.random.normal(60000, 15000, 500)
    incomes[incomes < 0] = 0  # No negative incomes
    # Add some extreme outliers (plausibility issue)
    incomes[np.random.choice(range(500), 10)] = np.random.uniform(300000, 1000000, 10)
    
    # Generate account balances with some calculation inconsistencies
    savings = np.random.uniform(1000, 50000, 500)
    checking = np.random.uniform(500, 10000, 500)
    total_balance = savings + checking
    # Add some calculation errors (consistency issue)
    total_balance[np.random.choice(range(500), 30)] += np.random.uniform(100, 1000, 30)
    
    # Generate subscription data with missing values (completeness issue)
    subscription_types = ["Basic", "Premium", "Enterprise", None, "Trial"]
    subscriptions = np.random.choice(subscription_types, 500, p=[0.4, 0.3, 0.1, 0.15, 0.05])
    
    # Generate Zip codes with varying formats (consistency issue with representation)
    zip_codes = []
    for _ in range(500):
        zip_num = np.random.randint(10000, 99999)
        if np.random.random() < 0.2:  # 20% with dashes (inconsistent format)
            formatted_zip = f"{zip_num // 1000}-{zip_num % 1000:03d}"
        else:
            formatted_zip = f"{zip_num}"
        zip_codes.append(formatted_zip)
    
    # Generate purchase counts with non-integers (validity issue)
    purchase_counts = np.random.randint(0, 50, 500).astype(float)
    # Replace some with non-integers
    purchase_counts[np.random.choice(range(500), 25)] += 0.5
    
    # Generate countries with unusual frequencies (plausibility pattern issue)
    countries = np.random.choice(
        ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan", "China", "Other"],
        500,
        p=[0.5, 0.15, 0.1, 0.05, 0.05, 0.05, 0.05, 0.03, 0.02]
    )
    
    # Create the DataFrame with all our columns
    df = pd.DataFrame({
        'customer_id': range(1001, 1501),
        'timestamp': all_dates,
        'name': names,
        'email': emails,
        'age': ages,
        'income': incomes,
        'savings_balance': savings,
        'checking_balance': checking,
        'total_balance': total_balance,
        'subscription_type': subscriptions,
        'zip_code': zip_codes,
        'purchase_count': purchase_counts,
        'country': countries
    })
    
    # Introduce missing values (completeness issue)
    for col in ['email', 'age', 'income', 'savings_balance', 'checking_balance']:
        mask = np.random.choice([True, False], size=len(df), p=[0.05, 0.95])  # 5% missing values
        df.loc[mask, col] = np.nan
    
    return df

def main():
    print("Creating sample data for comprehensive assessment...")
    df = create_sample_data()
    
    # Save to CSV for inspection
    csv_path = "comprehensive_sample.csv"
    df.to_csv(csv_path, index=False)
    print(f"Sample data saved to {csv_path}")
    
    # Create data source
    data_source = CSVDataSource(csv_path)
    
    # Create a registry with rules for all dimensions
    registry = RuleRegistry()
    
    print("Configuring rules for all dimensions...")
    
    # Register validity rules
    registry.register(TypeValidityRule(params={
        "column": "age",
        "expected_type": "int",
        "weight": 1.0
    }))
    
    registry.register(TypeValidityRule(params={
        "column": "purchase_count",
        "expected_type": "int",
        "weight": 1.0
    }))
    
    registry.register(FormatValidityRule(params={
        "column": "email",
        "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        "weight": 1.5
    }))
    
    registry.register(RangeValidityRule(params={
        "column": "age",
        "min_value": 0,
        "weight": 1.0
    }))
    
    # Register completeness rules
    registry.register(FieldCompletenessRule(params={
        "column": "email",
        "weight": 1.0
    }))
    
    registry.register(FieldCompletenessRule(params={
        "column": "subscription_type",
        "weight": 1.0
    }))
    
    registry.register(RecordCompletenessRule(params={
        "required_columns": ["name", "email"],
        "weight": 1.5
    }))
    
    # Register freshness rules
    registry.register(TimestampFreshnessRule(params={
        "column": "timestamp",
        "max_age_days": 30,
        "weight": 1.0
    }))
    
    # Register consistency rules
    registry.register(CrossFieldConsistencyRule(params={
        "validation_type": "expression",
        "fields": ["savings_balance", "checking_balance", "total_balance"],
        "expression": "abs((subset_df['savings_balance'] + subset_df['checking_balance']) - subset_df['total_balance']) < 1.0",
        "weight": 1.0
    }))
    
    registry.register(UniformRepresentationRule(params={
        "column": "zip_code",
        "format_type": "pattern",
        "pattern": r"^\d{5}$",
        "weight": 0.8
    }))
    
    registry.register(CalculationConsistencyRule(params={
        "result_column": "total_balance",
        "calculation_type": "expression",
        "expression": "subset_df['savings_balance'] + subset_df['checking_balance']",
        "input_columns": ["savings_balance", "checking_balance"],
        "tolerance": 0.01,
        "weight": 1.0
    }))
    
    # Register plausibility rules
    registry.register(OutlierDetectionRule(params={
        "column": "income",
        "method": "zscore",
        "threshold": 3.0,
        "weight": 1.0
    }))
    
    registry.register(RangeCheckRule(params={
        "column": "age",
        "min_value": 0,
        "max_value": 120,
        "weight": 1.0
    }))
    
    registry.register(PatternFrequencyRule(params={
        "column": "country",
        "max_categories": 10,
        "min_frequency": 0.01,
        "max_frequency": 0.6,
        "weight": 0.8
    }))
    
    # Create assessor and run comprehensive assessment
    print("Running comprehensive data quality assessment...")
    assessor = ADRIAssessor(registry=registry)
    report = assessor.assess(data_source)
    
    # Display dimension scores
    print("\nDimension Scores:")
    print("=" * 50)
    for dimension, score in report.dimension_scores.items():
        print(f"{dimension.capitalize()}: {score:.2f}")
    
    print("\nOverall Data Quality Score: {:.2f}".format(report.overall_score))
    
    # Display top issues by dimension
    print("\nTop Issues By Dimension:")
    print("=" * 50)
    
    dimensions = ["validity", "completeness", "freshness", "consistency", "plausibility"]
    
    for dim in dimensions:
        print(f"\n{dim.upper()} ISSUES:")
        print("-" * 30)
        
        # Filter results by dimension and sort by score (lowest first)
        dim_results = sorted(
            [r for r in report.rule_results if r["dimension"] == dim],
            key=lambda x: x["score"]
        )
        
        if dim_results:
            for i, result in enumerate(dim_results[:2]):  # Show top 2 issues
                print(f"{i+1}. {result['rule_name']}: {result['score']:.2f}")
                print(f"   {result['narrative'][:150]}...")
        else:
            print("No issues found.")
    
    # Save detailed report
    html_path = "comprehensive_report.html"
    report.save_html(html_path)
    print(f"\nDetailed report saved to {html_path}")
    
    # Get full path for easier user access
    abs_path = os.path.abspath(html_path)
    print(f"Full path: {abs_path}")

if __name__ == "__main__":
    main()
