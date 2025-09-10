"""
Semantic Kernel Basic Example with ADRI Protection

This example shows how to protect Semantic Kernel functions from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock Semantic Kernel imports for demonstration
try:
    import semantic_kernel as sk
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
except ImportError:
    # Mock classes for when Semantic Kernel is not installed
    class MockKernel:
        def add_text_completion_service(self, name, service):
            pass

        def create_semantic_function(self, prompt, **kwargs):
            return lambda context: f"Semantic Kernel result for: {str(context)[:50]}..."

    class MockChatCompletion:
        def __init__(self, **kwargs):
            pass


@adri_protected(data_param="task_data")
def kernel_function(task_data):
    """
    Semantic Kernel function with ADRI protection.

    Args:
        task_data (pd.DataFrame): Task data for processing

    Returns:
        str: Result from Semantic Kernel function
    """
    # Initialize kernel
    kernel = MockKernel()

    # Add AI service
    kernel.add_text_completion_service(
        "chat-gpt", MockChatCompletion(api_key="mock-key")
    )

    # Create semantic function
    prompt = """
    Analyze the following task data and provide insights:
    {{$input}}

    Provide a summary and recommendations.
    """

    analyze_function = kernel.create_semantic_function(
        prompt, max_tokens=500, temperature=0.7
    )

    # Convert data to context
    context_data = task_data.to_string()

    # Execute function
    result = analyze_function(context_data)

    return result


def demonstrate_semantic_kernel_protection():
    """Demonstrate Semantic Kernel protection."""

    print("🧠 Semantic Kernel + ADRI Protection Demo")
    print("=" * 40)

    # Good task data
    good_data = pd.DataFrame(
        {
            "task_id": ["T001", "T002", "T003"],
            "description": [
                "Analyze sales data",
                "Review customer feedback",
                "Optimize workflow",
            ],
            "priority": ["High", "Medium", "Low"],
            "status": ["In Progress", "Pending", "Completed"],
        }
    )

    print("\n1️⃣ Testing Semantic Kernel with GOOD data...")
    try:
        result = kernel_function(good_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    demonstrate_semantic_kernel_protection()
