"""
Example of using ADRI with DSPy.

This script demonstrates how to integrate ADRI with DSPy pipelines.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from adri.integrations.dspy import ADRIModule


def main():
    """Run the example."""
    # Path to the sample data file
    sample_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sample_data.csv'))
    
    print("=== ADRI DSPy Integration Example ===")
    print(f"Using sample data: {sample_data}")
    print()
    
    try:
        # Import DSPy (will fail if not installed)
        import dspy
    except ImportError:
        print("DSPy is not installed. Please install it with: pip install dspy")
        return
    
    try:
        # Create a DSPy pipeline with ADRI assessment
        print("Creating a DSPy pipeline with ADRI assessment...")
        
        class DataQualityPipeline(dspy.Module):
            """DSPy pipeline that uses ADRI for data quality assessment."""
            
            def __init__(self):
                super().__init__()
                self.adri = ADRIModule(min_score=70)
                # In a real application, you would use a real LM
                self.analyzer = dspy.Predict("data_analysis")
                
            def forward(self, data_path):
                """Run the pipeline on a data source."""
                print(f"Pipeline: Assessing quality of {data_path}")
                
                try:
                    # First assess data quality
                    quality_report = self.adri(data_path)
                    
                    print(f"Quality assessment complete.")
                    print(f"Score: {quality_report.score}/100")
                    print(f"Readiness level: {quality_report.readiness_level}")
                    
                    # Only proceed if quality is sufficient
                    if quality_report.score >= 70:
                        print("Quality is sufficient, proceeding with analysis...")
                        # In a real application, this would perform actual analysis
                        return dspy.Prediction(
                            analysis="Data analysis complete. Found interesting patterns."
                        )
                    else:
                        return dspy.Prediction(
                            error=f"Data quality insufficient: {quality_report.readiness_level}"
                        )
                except ValueError as e:
                    return dspy.Prediction(error=str(e))
        
        # Create and run the pipeline
        pipeline = DataQualityPipeline()
        print("\nRunning the pipeline...")
        result = pipeline(sample_data)
        
        # Display the result
        if hasattr(result, 'error'):
            print(f"Pipeline error: {result.error}")
        else:
            print(f"Pipeline result: {result.analysis}")
            
    except Exception as e:
        print(f"Error: {e}")
        
    print()
    print("Example complete.")


if __name__ == "__main__":
    main()
