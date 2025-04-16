"""
DSPy modules for the Agent Data Readiness Index.

This module provides DSPy modules for integrating ADRI with DSPy pipelines.
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path

from ...assessor import DataSourceAssessor


class ADRIModule:
    """
    DSPy module for data quality assessment.
    
    This module can be used in DSPy pipelines to assess the quality of
    data sources before they are used by other modules.
    
    Example:
        ```python
        import dspy
        from adri.integrations.dspy import ADRIModule
        
        # Create a DSPy pipeline with ADRI assessment
        class DataQualityPipeline(dspy.Module):
            def __init__(self):
                super().__init__()
                self.adri = ADRIModule()
                self.analyzer = dspy.ChainOfThought("data_analysis")
                
            def forward(self, data_path):
                # First assess data quality
                quality_report = self.adri(data_path)
                
                # Only proceed if quality is sufficient
                if quality_report.score >= 60:
                    analysis = self.analyzer(
                        data=data_path,
                        quality_report=quality_report
                    )
                    return analysis
                else:
                    return f"Data quality insufficient: {quality_report.readiness_level}"
        ```
    """
    
    def __init__(self, min_score: Optional[float] = None):
        """
        Initialize the ADRI module.
        
        Args:
            min_score: Optional minimum score required (0-100)
        """
        try:
            import dspy
        except ImportError:
            raise ImportError(
                "DSPy is not installed. Please install it with: pip install dspy"
            )
            
        self.min_score = min_score
        self.assessor = DataSourceAssessor()
        
    def __call__(self, data_source_path: Union[str, Path]):
        """
        Assess the quality of a data source.
        
        Args:
            data_source_path: Path to the data source
            
        Returns:
            Prediction: DSPy Prediction with assessment results
            
        Raises:
            ValueError: If min_score is set and data quality is insufficient
        """
        import dspy
        
        report = self.assessor.assess_file(data_source_path)
        
        # Check if quality meets minimum score
        if self.min_score is not None and report.overall_score < self.min_score:
            raise ValueError(
                f"Data quality insufficient for agent use. "
                f"ADRI Score: {report.overall_score}/100 "
                f"(Required: {self.min_score}/100)\n"
                f"Readiness Level: {report.readiness_level}\n"
                f"Top Issues: {report.summary_findings[:3]}"
            )
            
        return dspy.Prediction(
            score=report.overall_score,
            readiness_level=report.readiness_level,
            findings=report.summary_findings,
            recommendations=report.summary_recommendations,
            dimension_results=report.dimension_results
        )
