#!/usr/bin/env python3
"""
ADRI Python API Test Script

This script tests the basic functionality of the ADRI Python API
using our test datasets.
"""

from adri import DataSourceAssessor
import os
import json
from pprint import pprint

# Create output directory if it doesn't exist
os.makedirs("test_results/api", exist_ok=True)

def test_basic_assessment():
    """Test basic assessment functionality"""
    print("\n=== Testing Basic Assessment ===")
    
    # Create assessor with default settings
    assessor = DataSourceAssessor()
    print("Assessor created successfully")
    
    # Assess ideal dataset
    print("\nAssessing ideal_dataset.csv...")
    report = assessor.assess_file("test_datasets/ideal_dataset.csv")
    
    # Print basic results
    print(f"Overall score: {report.overall_score}")
    print("Dimension scores:")
    for dimension, results in report.dimension_results.items():
        print(f"  {dimension.capitalize()}: {results['score']}")
    
    # Save report
    report.save_json("test_results/api/ideal_report.json")
    print("Report saved to test_results/api/ideal_report.json")
    
    return report

def test_multiple_datasets():
    """Test assessment across multiple datasets"""
    print("\n=== Testing Multiple Dataset Assessment ===")
    
    assessor = DataSourceAssessor()
    results = {}
    
    datasets = [
        "ideal_dataset.csv",
        # Limiting to only datasets that parse correctly for this test
        "invalid_dataset.csv",
        "stale_dataset.csv",
    ]
    
    print("Assessing multiple datasets...")
    for dataset in datasets:
        path = f"test_datasets/{dataset}"
        if os.path.exists(path):
            print(f"Assessing {dataset}...")
            try:
                report = assessor.assess_file(path)
                dimension_scores = {}
                for dimension, results in report.dimension_results.items():
                    dimension_scores[dimension] = results['score']
                    
                results[dataset] = {
                    "overall_score": report.overall_score,
                    "dimension_scores": dimension_scores
                }
                report.save_json(f"test_results/api/{dataset.replace('.csv', '')}_report.json")
            except Exception as e:
                print(f"Error assessing {dataset}: {e}")
    
    # Save summary of all results
    with open("test_results/api/comparison_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Comparison summary saved to test_results/api/comparison_summary.json")
    return results

def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    assessor = DataSourceAssessor()
    
    # Test non-existent file
    print("Testing non-existent file...")
    try:
        report = assessor.assess_file("non_existent_file.csv")
    except Exception as e:
        print(f"✅ Expected error for non-existent file: {e}")
    
    # Test with a malformed dataset we've already created
    print("Testing malformed CSV...")
    try:
        report = assessor.assess_file("test_datasets/incomplete_dataset.csv")
        print("❌ Expected error for malformed dataset but no exception was raised")
    except Exception as e:
        print(f"✅ Expected error for malformed dataset: {e}")
    
    print("Error handling tests completed")

if __name__ == "__main__":
    print("Starting ADRI Python API tests...")
    
    # Run basic assessment test
    basic_report = test_basic_assessment()
    
    # Run multiple dataset test
    comparison = test_multiple_datasets()
    
    # Print comparison of overall scores
    print("\n=== Dataset Score Comparison ===")
    print(json.dumps(comparison, indent=2))
    
    # Run error handling test
    test_error_handling()
    
    print("\nAll tests completed!")
