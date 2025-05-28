"""
Example of using ADRI with LangChain.

This script demonstrates how to integrate ADRI with LangChain agents.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from adri.integrations.langchain import create_adri_tool


def main():
    """Run the example."""
    # Path to the sample data file
    sample_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sample_data.csv'))
    
    print("=== ADRI LangChain Integration Example ===")
    print(f"Using sample data: {sample_data}")
    print()
    
    try:
        # Import LangChain (will fail if not installed)
        from langchain.agents import initialize_agent, AgentType
        from langchain.llms import OpenAI
    except ImportError:
        print("LangChain is not installed. Please install it with: pip install langchain")
        print("You'll also need an OpenAI API key for this example.")
        return
    
    try:
        # Create the ADRI tool
        print("Creating ADRI tool for LangChain...")
        adri_tool = create_adri_tool(min_score=70)
        
        # In a real application, you would use a real LLM
        # For this example, we'll just simulate the agent's behavior
        print("\nIn a real application, you would initialize a LangChain agent like this:")
        print("```python")
        print("llm = OpenAI(temperature=0)")
        print("agent = initialize_agent(")
        print("    [adri_tool],")
        print("    llm,")
        print("    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION")
        print(")")
        print("```")
        
        # Simulate using the tool directly
        print("\nSimulating agent using the ADRI tool...")
        try:
            print(f"Agent: I'll assess the quality of {sample_data}")
            result = adri_tool.func(sample_data)
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
