"""
CrewAI Basic Example with ADRI Protection

This example shows how to protect CrewAI workflows from bad data using the @adri_protected decorator.
The decorator automatically checks data quality before your CrewAI crew processes it.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock CrewAI imports for demonstration
# In real usage, you would import from actual CrewAI packages
try:
    from crewai import Agent, Crew, Task
except ImportError:
    # Mock classes for when CrewAI is not installed
    class Agent:
        def __init__(self, role, goal, backstory="", **kwargs):
            self.role = role
            self.goal = goal
            self.backstory = backstory

    class Task:
        def __init__(self, description, agent, **kwargs):
            self.description = description
            self.agent = agent

    class Crew:
        def __init__(self, agents, tasks, **kwargs):
            self.agents = agents
            self.tasks = tasks

        def kickoff(self, inputs=None):
            return f"CrewAI processed data with {len(self.agents)} agents and {len(self.tasks)} tasks"


@adri_protected(data_param="market_data")
def market_analysis_crew(market_data):
    """
    CrewAI market analysis crew with ADRI protection.

    This function demonstrates how to protect a CrewAI workflow:
    1. The @adri_protected decorator checks data quality first
    2. Only good quality data reaches your CrewAI crew
    3. Your existing CrewAI code stays exactly the same

    Args:
        market_data (pd.DataFrame): Market data for analysis

    Returns:
        str: Analysis result from CrewAI crew
    """
    # Define CrewAI agents
    market_analyst = Agent(
        role="Market Analyst",
        goal="Analyze market trends and identify opportunities",
        backstory="Expert in financial markets with 10+ years experience",
    )

    risk_assessor = Agent(
        role="Risk Assessor",
        goal="Evaluate risks and provide recommendations",
        backstory="Specialist in risk management and compliance",
    )

    # Define tasks
    analysis_task = Task(
        description=f"Analyze the provided market data: {market_data.to_string()}",
        agent=market_analyst,
    )

    risk_task = Task(
        description="Assess risks based on the market analysis", agent=risk_assessor
    )

    # Create and run the crew
    crew = Crew(
        agents=[market_analyst, risk_assessor], tasks=[analysis_task, risk_task]
    )

    result = crew.kickoff()

    return result


@adri_protected(data_param="customer_data", min_score=85)
def customer_support_crew(customer_data):
    """
    CrewAI customer support crew with moderate quality requirements.
    """
    # Customer support agents
    support_agent = Agent(
        role="Customer Support Specialist",
        goal="Resolve customer issues efficiently",
        backstory="Experienced customer service professional",
    )

    escalation_agent = Agent(
        role="Escalation Manager",
        goal="Handle complex customer issues",
        backstory="Senior support manager with escalation expertise",
    )

    # Support tasks
    triage_task = Task(
        description=f"Triage customer issues: {customer_data.to_string()}",
        agent=support_agent,
    )

    escalation_task = Task(
        description="Handle any escalated issues", agent=escalation_agent
    )

    # Create support crew
    crew = Crew(
        agents=[support_agent, escalation_agent], tasks=[triage_task, escalation_task]
    )

    result = crew.kickoff()

    return f"Customer Support Result: {result}"


def demonstrate_crewai_protection():
    """Demonstrate CrewAI protection with good and bad data."""

    print("🤖 CrewAI + ADRI Protection Demo")
    print("=" * 40)

    # Good market data
    good_market_data = pd.DataFrame(
        {
            "symbol": ["AAPL", "GOOGL", "MSFT"],
            "price": [150.25, 2800.50, 300.75],
            "volume": [1000000, 500000, 750000],
            "change": [2.5, -1.2, 0.8],
            "sector": ["Technology", "Technology", "Technology"],
        }
    )

    # Bad market data
    bad_market_data = pd.DataFrame(
        {
            "symbol": [None, "GOOGL", ""],
            "price": [-150.25, None, "invalid"],
            "volume": [None, 500000, -750000],
            "change": ["invalid", -1.2, None],
            "sector": ["", "Technology", None],
        }
    )

    print("\n1️⃣ Testing market analysis crew with GOOD data...")
    try:
        result = market_analysis_crew(good_market_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2️⃣ Testing market analysis crew with BAD data...")
    try:
        result = market_analysis_crew(bad_market_data)
        print(f"✅ Unexpected success: {result}")
    except Exception as e:
        print(f"🛡️ ADRI Protection activated: {str(e)[:100]}...")

    # Good customer data
    good_customer_data = pd.DataFrame(
        {
            "ticket_id": ["T001", "T002", "T003"],
            "customer_name": ["Alice Johnson", "Bob Smith", "Charlie Brown"],
            "issue_type": ["Billing", "Technical", "Account"],
            "priority": ["High", "Medium", "Low"],
            "description": ["Billing error", "Login issues", "Password reset"],
        }
    )

    print("\n3️⃣ Testing customer support crew with good data...")
    try:
        result = customer_support_crew(good_customer_data)
        print(f"✅ Customer support success: {result}")
    except Exception as e:
        print(f"❌ Customer support error: {e}")


if __name__ == "__main__":
    demonstrate_crewai_protection()
