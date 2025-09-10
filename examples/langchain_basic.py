"""
LangChain Basic Example with ADRI Protection

This example shows how to protect LangChain agents from bad data using the @adri_protected decorator.
The decorator automatically checks data quality before your LangChain agent processes it.
"""

import pandas as pd

from adri.decorators.guard import adri_protected

# Mock LangChain imports for demonstration
# In real usage, you would import from actual LangChain packages
try:
    from langchain.chains import LLMChain
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
except ImportError:
    # Mock classes for when LangChain is not installed
    class OpenAI:
        def __init__(self, **kwargs):
            pass

    class PromptTemplate:
        def __init__(self, **kwargs):
            self.template = kwargs.get("template", "")

        @classmethod
        def from_template(cls, template):
            return cls(template=template)

    class LLMChain:
        def __init__(self, **kwargs):
            self.llm = kwargs.get("llm")
            self.prompt = kwargs.get("prompt")

        def run(self, **kwargs):
            data = list(kwargs.values())[0] if kwargs else "data"
            return f"Processed customer inquiries with LangChain: {str(data)[:50]}..."


@adri_protected(data_param="customer_data")
def customer_service_agent(customer_data):
    """
    LangChain customer service agent with ADRI protection.

    This function demonstrates how to protect a LangChain agent:
    1. The @adri_protected decorator checks data quality first
    2. Only good quality data reaches your LangChain code
    3. Your existing LangChain code stays exactly the same

    Args:
        customer_data (pd.DataFrame): Customer inquiry data

    Returns:
        str: Analysis result from LangChain agent
    """
    # Initialize LangChain components
    llm = OpenAI(temperature=0.7)

    prompt = PromptTemplate.from_template(
        "Analyze these customer inquiries and provide insights:\n"
        "Customer Data: {customer_info}\n"
        "Provide a summary of common themes and recommended actions."
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    # Convert DataFrame to string for LangChain processing
    customer_info = customer_data.to_string()

    # Run the LangChain analysis
    result = chain.run(customer_info=customer_info)

    return result


@adri_protected(data_param="customer_data", min_score=90, verbose=True)
def high_priority_customer_agent(customer_data):
    """
    High-priority customer service agent with strict data quality requirements.

    This example shows how to use stricter quality requirements for critical workflows.
    """
    llm = OpenAI(temperature=0.3)  # Lower temperature for more consistent responses

    prompt = PromptTemplate.from_template(
        "URGENT: High-priority customer analysis required.\n"
        "Customer Data: {customer_info}\n"
        "Identify any customers requiring immediate attention and escalation."
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    customer_info = customer_data.to_string()

    result = chain.run(customer_info=customer_info)

    return f"HIGH PRIORITY ANALYSIS: {result}"


def demonstrate_langchain_protection():
    """Demonstrate LangChain protection with good and bad data."""

    print("🔗 LangChain + ADRI Protection Demo")
    print("=" * 40)

    # Good customer data
    good_data = pd.DataFrame(
        {
            "customer_id": ["CUST001", "CUST002", "CUST003"],
            "name": ["Alice Johnson", "Bob Smith", "Charlie Brown"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
            "inquiry": ["Billing question", "Product support", "Account access"],
            "priority": ["Medium", "High", "Low"],
        }
    )

    # Bad customer data
    bad_data = pd.DataFrame(
        {
            "customer_id": [None, "CUST002", ""],
            "name": ["", None, "Charlie"],
            "email": ["invalid-email", "bob@example.com", "not-an-email"],
            "inquiry": ["", "Product support", None],
            "priority": ["", "High", "Invalid"],
        }
    )

    print("\n1️⃣ Testing with GOOD customer data...")
    try:
        result = customer_service_agent(good_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2️⃣ Testing with BAD customer data...")
    try:
        result = customer_service_agent(bad_data)
        print(f"✅ Unexpected success: {result}")
    except Exception as e:
        print(f"🛡️ ADRI Protection activated: {str(e)[:100]}...")

    print("\n3️⃣ Testing high-priority agent with good data...")
    try:
        result = high_priority_customer_agent(good_data)
        print(f"✅ High-priority success: {result}")
    except Exception as e:
        print(f"❌ High-priority error: {e}")


if __name__ == "__main__":
    demonstrate_langchain_protection()
