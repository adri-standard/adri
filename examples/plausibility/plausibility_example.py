"""
Example of testing the plausibility dimension.

This script demonstrates how to use the plausibility dimension to assess
whether data values are reasonable based on context and domain knowledge.
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from adri.assessor import DataSourceAssessor
from adri.config.config import Configuration
from adri.connectors import FileConnector


def main():
    """Run the plausibility assessment example."""
    # Path to the implausible dataset file
    implausible_data = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../test_datasets/implausible_dataset.csv'))
    
    # Path to plausibility metadata file
    plausibility_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../../examples/plausibility_files/sample_dataset.plausibility.json'))
    
    # Ensure the plausibility file has the correct name to match the CSV
    target_plausibility_path = Path(implausible_data).with_suffix('.plausibility.json')
    
    # Copy plausibility file to match dataset name (if needed)
    if not target_plausibility_path.exists():
        with open(plausibility_file, 'r') as src_file:
            plausibility_data = json.load(src_file)
        
        with open(target_plausibility_path, 'w') as dest_file:
            json.dump(plausibility_data, dest_file, indent=2)
        
        print(f"Created plausibility metadata file: {target_plausibility_path}")
    
    print("=== ADRI Plausibility Dimension Example ===")
    print(f"Using dataset: {implausible_data}")
    print()
    
    # Create custom configuration with emphasis on plausibility
    config = Configuration({
        "assessment": {
            "dimension_weights": {
                "validity": 0.5,
                "completeness": 0.5,
                "freshness": 0.5,
                "consistency": 0.5,
                "plausibility": 2.0  # Double weight for plausibility
            }
        },
        "plausibility_scoring": {
            "REQUIRE_EXPLICIT_METADATA": True  # Require explicit plausibility metadata
        }
    })
    
    # Create assessor with the custom configuration
    assessor = DataSourceAssessor(config=config.get_assessment_config())
    
    # Direct connector usage for more control
    connector = FileConnector(implausible_data)
    
    # Check if plausibility checking is supported
    if connector.supports_plausibility_check():
        print("Plausibility checking is supported for this dataset")
    else:
        print("Plausibility checking is not explicitly supported, but basic checks will be performed")
    
    # Get plausibility results directly from the connector
    plausibility_results = connector.get_plausibility_results()
    if plausibility_results:
        print("\nPlausibility Results Preview:")
        if plausibility_results.get("has_explicit_plausibility_info", False):
            print("- Dataset has explicit plausibility metadata")
        else:
            print("- Dataset has automatically generated plausibility information")
        
        rule_count = len(plausibility_results.get("rule_results", []))
        print(f"- Found {rule_count} plausibility rules")
        
        valid_overall = plausibility_results.get("valid_overall", True)
        print(f"- Overall plausibility valid: {valid_overall}")
        
        # Show some example rules
        if rule_count > 0:
            print("\nSample Rule Results:")
            for i, rule in enumerate(plausibility_results.get("rule_results", [])[:2]):
                print(f"  Rule {i+1}: {rule.get('rule_name', 'Unnamed')}")
                print(f"  - Type: {rule.get('type', 'unknown')}")
                print(f"  - Valid: {rule.get('valid', True)}")
                if not rule.get('valid', True):
                    print(f"  - Message: {rule.get('message', 'No message')}")
                    if 'examples' in rule:
                        print(f"  - Examples: {rule['examples']}")
                print()
    
    # Run the full assessment
    print("\nRunning full assessment...")
    report = assessor.assess_source(connector)
    
    # Display the results
    print("\n=== Assessment Results ===")
    print(f"Overall Score: {report.overall_score:.1f}/100")
    
    # Display dimension scores
    for dim_name, result in report.dimension_results.items():
        weight = config.get_assessment_config()["dimension_weights"].get(dim_name, 1.0)
        print(f"{dim_name.capitalize()} Score: {result['score']:.1f}/20 (weight: {weight})")
    
    # Focus on plausibility findings and recommendations
    if "plausibility" in report.dimension_results:
        plausibility_result = report.dimension_results["plausibility"]
        
        print("\n=== Plausibility Findings ===")
        for finding in plausibility_result['findings']:
            print(f"- {finding}")
        
        print("\n=== Plausibility Recommendations ===")
        for rec in plausibility_result['recommendations']:
            print(f"- {rec}")
    
    # Save the report as JSON
    report_path = Path(implausible_data).with_suffix('.report.json')
    report.save_json(report_path)
    
    print(f"\nFull report saved to: {report_path}")
    print("\nExample complete.")


if __name__ == "__main__":
    main()
