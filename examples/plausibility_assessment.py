"""
Plausibility Assessment Example

This example demonstrates how to use the plausibility rules to validate data
for statistical likelihood and reasonableness.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from adri import ADRIAssessor
from adri.datasource import CSVDataSource
from adri.rules.plausibility import OutlierDetectionRule, ValueDistributionRule, RangeCheckRule, PatternFrequencyRule
from adri.rules.registry import RuleRegistry
from adri.config import Config

# Create a sample dataset with plausibility issues
def create_sample_data():
    # Create sample data with 1000 records
    np.random.seed(42)
    
    # Generate normal distribution data with some outliers
    normal_data = np.random.normal(loc=100, scale=15, size=950)
    outliers = np.concatenate([
        np.random.uniform(10, 30, 25),  # Low outliers
        np.random.uniform(170, 200, 25)  # High outliers
    ])
    numeric_with_outliers = np.concatenate([normal_data, outliers])
    np.random.shuffle(numeric_with_outliers)
    
    # Generate uniform distribution data
    uniform_data = np.random.uniform(0, 100, 1000)
    
    # Generate skewed data (log-normal distribution)
    skewed_data = np.random.lognormal(mean=1.0, sigma=0.5, size=1000)
    
    # Generate categorical data with uneven distribution
    countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Australia', 'Japan', 'China', 'India', 'Brazil']
    country_probs = [0.4, 0.15, 0.1, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02]  # Intentionally imbalanced
    countries_data = np.random.choice(countries, size=1000, p=country_probs)
    
    # Create dataframe
    df = pd.DataFrame({
        'id': range(1, 1001),
        'measurement': numeric_with_outliers,
        'uniform_value': uniform_data,
        'skewed_value': skewed_data,
        'country': countries_data,
        'age': np.random.randint(0, 110, 1000),  # Some ages will be implausibly high
        'salary': np.random.gamma(shape=2, scale=30000, size=1000),  # Right-skewed salary distribution
        'ratings': np.random.randint(1, 6, 1000)  # Rating from 1 to 5
    })
    
    # Add some values outside plausible ranges
    df.loc[np.random.choice(df.index, 50), 'age'] = np.random.randint(110, 150, 50)  # Too old ages
    df.loc[np.random.choice(df.index, 20), 'ratings'] = np.random.randint(6, 10, 20)  # Out of range ratings
    
    # Add some unusual frequency patterns
    unusual_countries = ['Monaco', 'Vatican', 'San Marino', 'Liechtenstein', 'Nauru']
    df.loc[np.random.choice(df.index, 5), 'country'] = unusual_countries  # Very rare countries
    df.loc[np.random.choice(df.index, 70), 'country'] = 'Missing'  # Suspiciously many missing values
    
    return df

def main():
    # Create sample data
    df = create_sample_data()
    
    # Save to CSV for inspection
    df.to_csv("sample_plausibility.csv", index=False)
    print(f"Sample data saved to sample_plausibility.csv")
    
    # Create data source
    data_source = CSVDataSource("sample_plausibility.csv")
    
    # Create rules to test plausibility
    rules = [
        # Outlier detection for measurement values
        OutlierDetectionRule(params={
            "column": "measurement",
            "method": "zscore",
            "threshold": 3.0,
            "exclude_outliers": True,
            "weight": 1.0
        }),
        
        # Distribution check to verify if values follow expected distribution
        ValueDistributionRule(params={
            "column": "uniform_value",
            "distribution_type": "uniform",
            "test_method": "ks",
            "p_threshold": 0.05,
            "weight": 1.0
        }),
        
        # Range check to verify values are within expected ranges
        RangeCheckRule(params={
            "column": "age",
            "min_value": 0,
            "max_value": 100,
            "quantile_based": False,
            "weight": 1.0
        }),
        
        # Another range check with different parameters
        RangeCheckRule(params={
            "column": "ratings",
            "min_value": 1,
            "max_value": 5,
            "weight": 1.5
        }),
        
        # Pattern frequency analysis for categorical data
        PatternFrequencyRule(params={
            "column": "country",
            "max_categories": 15,
            "min_frequency": 0.01,
            "max_frequency": 0.3,
            "expected_frequencies": {
                "USA": 0.25,
                "Canada": 0.10,
                "UK": 0.10
            },
            "tolerance": 0.1,
            "weight": 1.2
        }),
        
        # Distribution check for skewed data
        ValueDistributionRule(params={
            "column": "salary",
            "distribution_type": "exponential",
            "test_method": "chi2",
            "p_threshold": 0.01,
            "weight": 0.8
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
    print("\nPlausibility Assessment Results:")
    print("=" * 50)
    print(f"Overall Plausibility Score: {report.dimension_scores.get('plausibility', 0):.2f}")
    print("\nDetailed Results:")
    
    for rule_result in report.rule_results:
        if rule_result["dimension"] == "plausibility":
            rule_name = rule_result["rule_name"]
            score = rule_result["score"]
            narrative = rule_result["narrative"]
            
            print(f"\n{rule_name}: {score:.2f}")
            print("-" * 30)
            print(narrative)
    
    # Save detailed report
    report.save_html("plausibility_report.html")
    print("\nDetailed report saved to plausibility_report.html")

if __name__ == "__main__":
    main()
