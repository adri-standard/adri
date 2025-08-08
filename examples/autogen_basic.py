"""
AutoGen Basic Example with ADRI Protection

This example shows how to protect AutoGen multi-agent conversations from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock AutoGen imports for demonstration
# In real usage, you would import from actual AutoGen packages
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    # Mock classes for when AutoGen is not installed
    class AssistantAgent:
        def __init__(self, name, **kwargs):
            self.name = name
            self.system_message = kwargs.get("system_message", "")

        def generate_reply(self, messages, sender):
            return f"AutoGen {self.name} processed the conversation"

    class UserProxyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def initiate_chat(self, recipient, message):
            return f"AutoGen conversation initiated: {message[:50]}..."


@adri_protected(data_param="conversation_data")
def multi_agent_conversation(conversation_data):
    """
    AutoGen multi-agent conversation with ADRI protection.

    This function demonstrates how to protect AutoGen workflows:
    1. The @adri_protected decorator checks data quality first
    2. Only good quality data reaches your AutoGen agents
    3. Your existing AutoGen code stays exactly the same

    Args:
        conversation_data (pd.DataFrame): Data for agent conversation

    Returns:
        str: Result from AutoGen multi-agent conversation
    """
    # Create AutoGen agents
    assistant = AssistantAgent(
        name="data_analyst",
        system_message="You are a data analyst. Analyze the provided data and give insights.",
    )

    user_proxy = UserProxyAgent(
        name="user_proxy", human_input_mode="NEVER", code_execution_config=False
    )

    # Convert data to message format
    data_summary = f"Please analyze this data:\n{conversation_data.to_string()}"

    # Initiate the conversation
    result = user_proxy.initiate_chat(assistant, message=data_summary)

    return result


@adri_protected(data_param="research_data", min_score=88)
def research_team_conversation(research_data):
    """
    AutoGen research team with higher quality requirements.
    """
    # Research team agents
    researcher = AssistantAgent(
        name="researcher",
        system_message="You are a research scientist. Analyze data and propose hypotheses.",
    )

    critic = AssistantAgent(
        name="critic",
        system_message="You are a research critic. Review findings and suggest improvements.",
    )

    coordinator = UserProxyAgent(name="coordinator", human_input_mode="NEVER")

    # Start research conversation
    research_prompt = f"Research team, please analyze: {research_data.to_string()}"

    result = coordinator.initiate_chat(researcher, message=research_prompt)

    return f"Research Team Analysis: {result}"


def demonstrate_autogen_protection():
    """Demonstrate AutoGen protection with good and bad data."""

    print("🤖 AutoGen + ADRI Protection Demo")
    print("=" * 40)

    # Good conversation data
    good_data = pd.DataFrame(
        {
            "participant": ["Alice", "Bob", "Charlie"],
            "message": [
                "Hello team",
                "Great to meet you",
                "Looking forward to working together",
            ],
            "timestamp": ["2024-01-01 10:00", "2024-01-01 10:01", "2024-01-01 10:02"],
            "sentiment": ["positive", "positive", "positive"],
            "topic": ["greeting", "introduction", "collaboration"],
        }
    )

    # Bad conversation data
    bad_data = pd.DataFrame(
        {
            "participant": [None, "Bob", ""],
            "message": ["", None, "Looking forward"],
            "timestamp": ["invalid-date", "2024-01-01 10:01", None],
            "sentiment": ["", "positive", "invalid"],
            "topic": [None, "introduction", ""],
        }
    )

    print("\n1️⃣ Testing AutoGen conversation with GOOD data...")
    try:
        result = multi_agent_conversation(good_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2️⃣ Testing AutoGen conversation with BAD data...")
    try:
        result = multi_agent_conversation(bad_data)
        print(f"✅ Unexpected success: {result}")
    except Exception as e:
        print(f"🛡️ ADRI Protection activated: {str(e)[:100]}...")

    # Good research data
    good_research_data = pd.DataFrame(
        {
            "experiment_id": ["EXP001", "EXP002", "EXP003"],
            "hypothesis": ["A causes B", "B influences C", "C correlates with A"],
            "result": [0.85, 0.72, 0.91],
            "confidence": [0.95, 0.88, 0.92],
            "status": ["completed", "completed", "completed"],
        }
    )

    print("\n3️⃣ Testing research team with good data...")
    try:
        result = research_team_conversation(good_research_data)
        print(f"✅ Research team success: {result}")
    except Exception as e:
        print(f"❌ Research team error: {e}")


if __name__ == "__main__":
    demonstrate_autogen_protection()
