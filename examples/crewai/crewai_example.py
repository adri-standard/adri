"""
Example of using ADRI with CrewAI.

This script demonstrates how to integrate ADRI with CrewAI agents.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from adri.integrations.crewai import create_data_quality_agent, assess_data_quality


def main():
    """Run the example."""
    # Path to the sample data file
    sample_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sample_data.csv'))
    
    print("=== ADRI CrewAI Integration Example ===")
    print(f"Using sample data: {sample_data}")
    print()
    
    try:
        # Import CrewAI (will fail if not installed)
        from crewai import Crew, Task
    except ImportError:
        print("CrewAI is not installed. Please install it with: pip install crewai")
        return
    
    # Example 1: Using the assess_data_quality function directly
    print("Example 1: Using the assess_data_quality function directly")
    try:
        print(f"Assessing quality of {sample_data}...")
        result = assess_data_quality(sample_data)
        print(f"Assessment complete.")
        print(f"Overall score: {result['overall_score']}/100")
        print(f"Readiness level: {result['readiness_level']}")
        print("Top findings:")
        for finding in result['summary_findings'][:3]:
            print(f"  - {finding}")
    except ValueError as e:
        print(f"Assessment error: {e}")
    
    print()
    
    # Example 2: Using the data quality agent
    print("Example 2: Using the data quality agent")
    try:
        # Create a data quality agent
        print("Creating a data quality agent...")
        data_quality_agent = create_data_quality_agent(min_score=70)
        
        # In a real application, you would create tasks and a crew
        print("\nIn a real application, you would create tasks and a crew like this:")
        print("```python")
        print("# Create a task for the agent")
        print("assess_task = Task(")
        print(f"    description=\"Assess the quality of {sample_data}\",")
        print("    expected_output=\"A detailed assessment of data quality\",")
        print("    agent=data_quality_agent")
        print(")")
        print()
        print("# Create a crew with the agent and task")
        print("crew = Crew(")
        print("    agents=[data_quality_agent],")
        print("    tasks=[assess_task]")
        print(")")
        print()
        print("# Run the crew")
        print("result = crew.kickoff()")
        print("```")
        
        # Simulate using the agent's tool directly
        print("\nSimulating agent using its tool...")
        try:
            print(f"Agent: I'll assess the quality of {sample_data}")
            # Get the assess_data_quality tool from the agent
            tool = data_quality_agent.tools[0]
            result = tool(sample_data)
            print(f"Tool result: Data quality assessment complete.")
            print(f"Overall score: {result['overall_score']}/100")
            print(f"Readiness level: {result['readiness_level']}")
            print("Top findings:")
            for finding in result['summary_findings'][:3]:
                print(f"  - {finding}")
        except ValueError as e:
            print(f"Tool error: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        
    print()
    print("Example complete.")


if __name__ == "__main__":
    main()
