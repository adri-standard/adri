"""
Example of using the adri_guarded decorator.

This script demonstrates how to use the adri_guarded decorator to enforce
data quality standards in agent functions.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from adri.integrations import adri_guarded


@adri_guarded(min_score=70)
def analyze_customer_data(data_source, analysis_type):
    """
    Analyze customer data for insights.
    
    This function will only run if data_source meets the minimum quality score of 70.
    
    Args:
        data_source: Path to the data source
        analysis_type: Type of analysis to perform
        
    Returns:
        str: Analysis results
    """
    print(f"Analyzing {data_source} for {analysis_type}")
    # In a real application, this would perform actual analysis
    return f"Analysis of {data_source} complete. Found interesting patterns for {analysis_type}."


def main():
    """Run the example."""
    # Path to the sample data file
    sample_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sample_data.csv'))
    
    print("=== ADRI Guard Decorator Example ===")
    print(f"Using sample data: {sample_data}")
    print()
    
    try:
        # Try to analyze the data
        print("Attempting to analyze data...")
        results = analyze_customer_data(sample_data, "customer segmentation")
        print("Analysis successful!")
        print(results)
    except ValueError as e:
        print(f"Analysis blocked: {e}")
        
    print()
    print("Example complete.")


if __name__ == "__main__":
    main()
