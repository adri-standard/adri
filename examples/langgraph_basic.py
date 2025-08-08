"""
LangGraph Basic Example with ADRI Protection

This example shows how to protect LangGraph workflows from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock LangGraph imports for demonstration
try:
    from langchain.schema import BaseMessage
    from langgraph import StateGraph
except ImportError:
    # Mock classes for when LangGraph is not installed
    class StateGraph:
        def __init__(self):
            self.nodes = {}
            self.edges = []

        def add_node(self, name, func):
            self.nodes[name] = func

        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))

        def compile(self):
            return MockCompiledGraph()

    class MockCompiledGraph:
        def invoke(self, state):
            return {"result": f"LangGraph workflow result for: {str(state)[:50]}..."}


@adri_protected(data_param="workflow_data")
def graph_workflow(workflow_data):
    """
    LangGraph workflow with ADRI protection.

    Args:
        workflow_data (pd.DataFrame): Data for graph workflow

    Returns:
        dict: Result from LangGraph workflow
    """

    # Define workflow nodes
    def analyze_node(state):
        data = state.get("data", "")
        return {"analysis": f"Analyzed: {data[:50]}..."}

    def process_node(state):
        analysis = state.get("analysis", "")
        return {"processed": f"Processed: {analysis[:50]}..."}

    def summarize_node(state):
        processed = state.get("processed", "")
        return {"summary": f"Summary: {processed[:50]}..."}

    # Create graph
    graph = StateGraph()

    # Add nodes
    graph.add_node("analyze", analyze_node)
    graph.add_node("process", process_node)
    graph.add_node("summarize", summarize_node)

    # Add edges
    graph.add_edge("analyze", "process")
    graph.add_edge("process", "summarize")

    # Compile graph
    compiled_graph = graph.compile()

    # Execute workflow
    initial_state = {"data": workflow_data.to_string()}
    result = compiled_graph.invoke(initial_state)

    return result


def demonstrate_langgraph_protection():
    """Demonstrate LangGraph protection."""

    print("🔗 LangGraph + ADRI Protection Demo")
    print("=" * 40)

    # Good workflow data
    good_data = pd.DataFrame(
        {
            "step": ["Input", "Process", "Output"],
            "description": ["Receive data", "Transform data", "Generate result"],
            "status": ["Complete", "Complete", "Pending"],
        }
    )

    print("\n1️⃣ Testing LangGraph workflow with GOOD data...")
    try:
        result = graph_workflow(good_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    demonstrate_langgraph_protection()
