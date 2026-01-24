"""
Sample test data for end-to-end documentation tests.

Provides realistic test datasets that match examples in documentation,
including both clean data and data with intentional quality issues.
"""

from typing import Dict, List


def get_customer_data_clean() -> List[Dict[str, any]]:
    """Get clean customer data matching GETTING_STARTED.md examples.
    
    Returns:
        List of customer records with valid data
    """
    return [
        {
            "customer_id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "age": 25,
            "purchase_value": 100.0,
            "signup_date": "2024-01-01"
        },
        {
            "customer_id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "age": 30,
            "purchase_value": 150.0,
            "signup_date": "2024-01-02"
        },
        {
            "customer_id": 3,
            "name": "Charlie",
            "email": "charlie@example.com",
            "age": 35,
            "purchase_value": 200.0,
            "signup_date": "2024-01-03"
        }
    ]


def get_customer_data_with_issues() -> List[Dict[str, any]]:
    """Get customer data with quality issues for testing validation.
    
    Matches the "bad data" examples in GETTING_STARTED.md:
    - Missing values
    - Invalid formats
    - Out of range values
    
    Returns:
        List of customer records with intentional quality issues
    """
    return [
        {
            "customer_id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "age": 25,
            "purchase_value": 100.0,
            "signup_date": "2024-01-01"
        },
        {
            "customer_id": 2,
            "name": "B",  # Too short
            "email": "invalid-email",  # Invalid format
            "age": 15,  # Under minimum
            "purchase_value": 0.0,  # Below minimum
            "signup_date": "2020-01-02"  # Too old
        },
        {
            "customer_id": None,  # Missing ID
            "name": "Charlie",
            "email": "charlie@example.com",
            "age": 35,
            "purchase_value": 200.0,
            "signup_date": "2024-01-03"
        }
    ]


def get_invoice_data_clean() -> str:
    """Get clean invoice data for guide walkthrough tests.
    
    Matches the tutorial data used in `adri guide` command.
    
    Returns:
        CSV string with clean invoice data
    """
    return """invoice_id,customer_id,amount,date,status
INV-001,CUST-101,1500.00,2024-01-15,paid
INV-002,CUST-102,2300.50,2024-01-16,paid
INV-003,CUST-103,890.00,2024-01-17,pending
INV-004,CUST-104,1200.00,2024-01-18,paid
INV-005,CUST-105,3400.75,2024-01-19,paid
"""


def get_invoice_data_with_issues() -> str:
    """Get invoice data with quality issues for guide testing.
    
    Contains intentional issues to demonstrate ADRI detection:
    - Missing required fields
    - Negative amounts
    - Invalid date formats
    
    Returns:
        CSV string with problematic invoice data
    """
    return """invoice_id,customer_id,amount,date,status
INV-101,CUST-101,1500.00,2024-01-15,paid
INV-102,,2300.50,2024-01-16,paid
INV-103,CUST-103,-890.00,2024-01-17,pending
INV-104,CUST-104,1200.00,invalid-date,paid
INV-105,CUST-105,3400.75,2024-01-19,unknown_status
"""


def get_api_response_data() -> Dict[str, any]:
    """Get sample API response data for contract template testing.
    
    Returns:
        Dictionary matching API response template structure
    """
    return {
        "status": "success",
        "code": 200,
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": True}
            ],
            "total": 2
        },
        "timestamp": "2024-01-15T10:30:00Z"
    }


def get_langchain_input_data() -> Dict[str, any]:
    """Get sample LangChain chain input data.
    
    Returns:
        Dictionary matching LangChain contract template
    """
    return {
        "query": "What is the weather today?",
        "context": "User is asking about current weather conditions",
        "metadata": {
            "user_id": "user123",
            "session_id": "session456",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }


def get_crewai_context_data() -> Dict[str, any]:
    """Get sample CrewAI task context data.
    
    Returns:
        Dictionary matching CrewAI contract template
    """
    return {
        "task_id": "task_001",
        "task_description": "Analyze customer feedback",
        "inputs": {
            "feedback_text": "Great product, very satisfied!",
            "customer_id": "CUST-123"
        },
        "agent_role": "sentiment_analyzer",
        "expected_output": "sentiment_score"
    }


def get_llamaindex_documents() ->List[Dict[str, any]]:
    """Get sample LlamaIndex document data.
    
    Returns:
        List of documents matching LlamaIndex template
    """
    return [
        {
            "doc_id": "doc_001",
            "text": "This is a sample document for indexing.",
            "metadata": {
                "source": "internal_docs",
                "author": "Alice",
                "date": "2024-01-15"
            }
        },
        {
            "doc_id": "doc_002",
            "text": "Another document with important information.",
            "metadata": {
                "source": "external_api",
                "author": "Bob",
                "date": "2024-01-16"
            }
        }
    ]


def get_time_series_data() -> List[Dict[str, any]]:
    """Get sample time series data for template testing.
    
    Returns:
        List of time series records
    """
    return [
        {"timestamp": "2024-01-15T00:00:00Z", "value": 100.5, "metric": "cpu_usage"},
        {"timestamp": "2024-01-15T01:00:00Z", "value": 95.3, "metric": "cpu_usage"},
        {"timestamp": "2024-01-15T02:00:00Z", "value": 102.1, "metric": "cpu_usage"},
    ]


# CSV data as strings for file-based tests

CUSTOMER_CSV_CLEAN = """customer_id,name,email,age,purchase_value,signup_date
1,Alice,alice@example.com,25,100.0,2024-01-01
2,Bob,bob@example.com,30,150.0,2024-01-02
3,Charlie,charlie@example.com,35,200.0,2024-01-03
"""

CUSTOMER_CSV_BAD = """customer_id,name,email,age,purchase_value,signup_date
1,Alice,alice@example.com,25,100.0,2024-01-01
2,B,invalid-email,15,0.0,2020-01-02
,Charlie,charlie@example.com,35,200.0,2024-01-03
"""

SIMPLE_CSV = """id,name,value
1,item1,100
2,item2,200
3,item3,300
"""
