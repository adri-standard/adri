"""
CrewAI agents for the Agent Data Readiness Index.

This module provides agents and tasks for integrating ADRI with CrewAI.
"""

from typing import Dict, Any, Optional, Union, Callable
from pathlib import Path

from ...assessor import DataSourceAssessor


def assess_data_quality(data_source_path: Union[str, Path], min_score: Optional[float] = None) -> Dict[str, Any]:
    """
    Assess the quality of a data source using ADRI.
    
    This function can be used as a tool by CrewAI agents to assess
    the quality of data sources.
    
    Args:
        data_source_path: Path to the data source
        min_score: Optional minimum score required (0-100)
        
    Returns:
        Dict: Assessment report
        
    Raises:
        ValueError: If min_score is set and data quality is insufficient
    """
    assessor = DataSourceAssessor()
    report = assessor.assess_file(data_source_path)
    
    # Check if quality meets minimum score
    if min_score is not None and report.overall_score < min_score:
        raise ValueError(
            f"Data quality insufficient for agent use. "
            f"ADRI Score: {report.overall_score}/100 "
            f"(Required: {min_score}/100)\n"
            f"Readiness Level: {report.readiness_level}\n"
            f"Top Issues: {report.summary_findings[:3]}"
        )
        
    return report.to_dict()


def create_data_quality_agent(min_score: Optional[float] = None):
    """
    Create a CrewAI agent for data quality assessment.
    
    This function creates a CrewAI agent that can assess the quality
    of data sources using ADRI.
    
    Args:
        min_score: Optional minimum score required (0-100)
        
    Returns:
        Agent: A CrewAI agent for data quality assessment
        
    Example:
        ```python
        from crewai import Crew, Task
        from adri.integrations.crewai import create_data_quality_agent
        
        # Create a data quality agent
        data_quality_agent = create_data_quality_agent(min_score=70)
        
        # Create a task for the agent
        assess_task = Task(
            description="Assess the quality of customer_data.csv",
            expected_output="A detailed assessment of data quality",
            agent=data_quality_agent
        )
        
        # Create a crew with the agent and task
        crew = Crew(
            agents=[data_quality_agent],
            tasks=[assess_task]
        )
        
        # Run the crew
        result = crew.kickoff()
        ```
    """
    try:
        from crewai import Agent
    except ImportError:
        raise ImportError(
            "CrewAI is not installed. Please install it with: pip install crewai"
        )
        
    # Create a wrapper function that includes the min_score
    def assess_with_min_score(data_source_path: Union[str, Path]) -> Dict[str, Any]:
        return assess_data_quality(data_source_path, min_score)
    
    return Agent(
        name="DataQualityAgent",
        role="Data Quality Assessor",
        goal="Assess data quality for agent readiness",
        backstory="I evaluate data sources to ensure they're suitable for AI agents",
        tools=[assess_with_min_score]
    )
