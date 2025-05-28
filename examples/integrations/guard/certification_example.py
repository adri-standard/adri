"""
Example demonstrating the ADRI data certification workflow.

This example shows two key workflows:
1. Data Provider: How to certify a data source before distribution
2. Agent Developer: How to leverage pre-certified data sources for efficiency

The example uses a sample dataset that gets certified, then used by an agent
function with guard protection.
"""

import os
import logging
from pathlib import Path

from adri import DataSourceAssessor, adri_guarded


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_sample_dataset_path():
    """Get the path to a sample dataset for demonstration."""
    # In a real-world scenario, this would be the path to your actual dataset
    example_dir = Path(__file__).parent.parent
    sample_path = example_dir / "plausibility" / "sample_dataset.csv"
    
    # If the sample dataset doesn't exist, use a test dataset
    if not sample_path.exists():
        repo_root = Path(__file__).parent.parent.parent
        sample_path = repo_root / "test_datasets" / "ideal_dataset.csv"
        
    if not sample_path.exists():
        raise FileNotFoundError("Could not find a sample dataset for the example.")
        
    return str(sample_path)


# PART 1: DATA PROVIDER CERTIFICATION WORKFLOW
def certify_data_source(data_path, certification_threshold=70):
    """
    Certification workflow for data providers before distribution.
    
    Args:
        data_path: Path to the data source to certify
        certification_threshold: Minimum score required for certification
        
    Returns:
        bool: Whether the data was successfully certified
    """
    logger.info(f"Starting certification process for: {data_path}")
    
    # Create an assessor with default configuration
    assessor = DataSourceAssessor()
    
    # Run the assessment
    report = assessor.assess_file(data_path)
    
    # Output the assessment results
    logger.info(f"Assessment complete. Overall score: {report.overall_score}/100")
    logger.info(f"Readiness level: {report.readiness_level}")
    
    # Show dimension scores
    for dimension, results in report.dimension_results.items():
        logger.info(f"{dimension} score: {results['score']}/20")
    
    # Check if data meets certification threshold
    if report.overall_score >= certification_threshold:
        # Save certification report alongside the data source
        report_path = Path(data_path).with_suffix('.report.json')
        report.save_json(report_path)
        logger.info(f"Certification SUCCESSFUL. Report saved to: {report_path}")
        return True
    else:
        logger.warning(f"Certification FAILED. Score {report.overall_score} below threshold {certification_threshold}")
        logger.warning("Top issues to fix:")
        for finding in report.summary_findings[:3]:
            logger.warning(f"- {finding}")
        return False


# PART 2: AGENT USING CERTIFIED DATA
@adri_guarded(
    min_score=5,  # Lower threshold for demonstration purposes 
    dimensions={"plausibility": 5},  # Lower plausibility requirement
    use_cached_reports=True,
    max_report_age_hours=24,
    verbose=True
)
def agent_analyze_data(data_source):
    """
    Example agent function that processes data with ADRI guard protection.
    The guard will first check for an existing certification report before
    running a new assessment.
    """
    logger.info(f"Agent analyzing data from: {data_source}")
    
    # In a real application, this would be your actual agent processing code
    # For this example, we'll just simulate the work
    logger.info("Agent processing data successfully!")
    return {"status": "success", "data_source": data_source}


# MAIN WORKFLOW DEMONSTRATION
def main():
    """Run the complete certification and agent workflow demonstration."""
    try:
        # Get sample dataset path
        sample_data_path = get_sample_dataset_path()
        logger.info(f"Using sample dataset: {sample_data_path}")
        
        # STEP 1: Data Provider certifies the data
        print("\n=== DATA PROVIDER WORKFLOW ===")
        # Using a lower threshold for demonstration purposes
        # In a real-world scenario, you'd want a higher threshold like 70
        certification_result = certify_data_source(sample_data_path, certification_threshold=5)
        
        if certification_result:
            print("\nData has been certified and is ready for distribution!")
        else:
            print("\nData needs improvement before distribution!")
            return
        
        # STEP 2: Agent uses the certified data
        print("\n=== AGENT DEVELOPER WORKFLOW ===")
        print("\nScenario 1: First use (certification already exists)")
        try:
            result = agent_analyze_data(sample_data_path)
            print(f"Agent processed certified data successfully!")
        except ValueError as e:
            print(f"Data quality issue prevented agent processing: {e}")
            
        # STEP 3: Demonstrate what happens with uncertified data
        print("\nScenario 2: Using data that fails quality standards")
        # Create a temporary file path that doesn't exist or doesn't have a report
        uncertified_path = sample_data_path.replace('.csv', '_uncertified.csv')
        if not os.path.exists(uncertified_path):
            with open(sample_data_path, 'r') as src, open(uncertified_path, 'w') as dst:
                dst.write(src.read())
                
        # Remove any existing report for this file
        uncertified_report = uncertified_path.replace('.csv', '.report.json')
        if os.path.exists(uncertified_report):
            os.remove(uncertified_report)
            
        # Change verbose parameter to see assessment details
        @adri_guarded(min_score=95, use_cached_reports=True, verbose=True)  # Using high threshold to force failure
        def process_uncertified(data_source):
            return {"status": "processed", "source": data_source}
        
        try:
            result = process_uncertified(uncertified_path)
            print("Data was processed successfully (unexpected)")
        except ValueError as e:
            print(f"As expected, uncertified data was rejected: {e}")
            
        # Clean up the temporary file
        try:
            if os.path.exists(uncertified_path):
                os.remove(uncertified_path)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Test coverage for this example is documented in:
# docs/test_coverage/certification_example_test_coverage.md
