"""
LangChain tools for the Agent Data Readiness Index.

This module provides tools for integrating ADRI with LangChain agents.
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path

from ...assessor import DataSourceAssessor


def create_adri_tool(min_score: Optional[float] = None):
    """
    Create a LangChain Tool for ADRI assessment.
    
    This function creates a LangChain Tool that can be used by agents to
    assess the quality of data sources. If min_score is provided, the tool
    will raise an error if the data quality doesn't meet the minimum score.
    
    Args:
        min_score: Optional minimum score required (0-100)
        
    Returns:
        Tool: A LangChain Tool for data quality assessment
        
    Example:
        ```python
        from langchain.agents import initialize_agent, AgentType
        from langchain.llms import OpenAI
        from adri.integrations.langchain import create_adri_tool
        
        # Create LangChain agent with ADRI tool
        llm = OpenAI(temperature=0)
        adri_tool = create_adri_tool()
        agent = initialize_agent(
            [adri_tool], 
            llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
        )
        
        # Use the agent
        agent.run("Assess the quality of customer_data.csv for use in a recommendation system")
        ```
    """
    try:
        from langchain.tools import Tool
    except ImportError:
        raise ImportError(
            "LangChain is not installed. Please install it with: pip install langchain"
        )
        
    def run_assessment(data_source_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Assess the quality of a data source using ADRI.
        
        Args:
            data_source_path: Path to the data source
            
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
        
    return Tool(
        name="assess_data_quality",
        func=run_assessment,
        description=(
            "Assess the quality of a data source for use with AI agents. "
            "Input should be a path to a data file (CSV, JSON, etc.)."
        )
    )
