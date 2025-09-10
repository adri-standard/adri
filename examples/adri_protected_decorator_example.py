"""
ADRI Protected Decorator Examples

Demonstrates how to use the @adri_protected decorator to guard agent workflows
from dirty data with automatic quality assessment and protection.
"""

import pandas as pd

from adri.core.protection import ProtectionError
from adri.decorators.guard import (
    adri_financial,
    adri_permissive,
    adri_protected,
    adri_strict,
)


def create_sample_data():
    """Create sample datasets for demonstration."""

    # High-quality customer data
    good_customers = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "name": [
                "Alice Johnson",
                "Bob Smith",
                "Charlie Brown",
                "Diana Prince",
                "Eve Adams",
            ],
            "email": [
                "alice@example.com",
                "bob@example.com",
                "charlie@example.com",
                "diana@example.com",
                "eve@example.com",
            ],
            "age": [28, 34, 45, 29, 52],
            "account_balance": [1250.50, 3400.75, 890.25, 5600.00, 2100.30],
            "registration_date": [
                "2023-01-15",
                "2023-02-20",
                "2023-03-10",
                "2023-04-05",
                "2023-05-12",
            ],
        }
    )

    # Poor-quality customer data (missing values, inconsistencies)
    bad_customers = pd.DataFrame(
        {
            "customer_id": [1, 2, None, 4, 5],
            "name": ["Alice", "", "Charlie Brown", "Diana", None],
            "email": [
                "alice@invalid",
                "bob@example.com",
                "not-an-email",
                "diana@example.com",
                "",
            ],
            "age": [28, -5, 200, 29, None],
            "account_balance": [1250.50, None, -500.00, 5600.00, "invalid"],
            "registration_date": ["2023-01-15", "invalid-date", "2023-03-10", "", None],
        }
    )

    return good_customers, bad_customers


# Example 1: Basic Protection with Auto-Generated Standards
@adri_protected(data_param="customer_data")
def process_customer_orders(customer_data):
    """
    Process customer orders with basic data quality protection.

    This will:
    1. Auto-generate a standard named 'process_customer_orders_customer_data_standard.yaml'
    2. Assess data quality against the standard
    3. Raise ProtectionError if quality is insufficient (default behavior)
    """
    print(f"Processing {len(customer_data)} customer orders...")

    # Simulate order processing
    total_value = customer_data["account_balance"].sum()
    avg_age = customer_data["age"].mean()

    return {
        "orders_processed": len(customer_data),
        "total_value": total_value,
        "avg_customer_age": avg_age,
    }


# Example 2: Explicit Standard File
@adri_protected(
    data_param="financial_data", standard_file="financial_transactions_v2.yaml"
)
def validate_financial_transactions(financial_data):
    """
    Validate financial transactions using a specific standard file.

    Uses an explicit standard file instead of auto-generation.
    """
    print(f"Validating {len(financial_data)} financial transactions...")

    # Simulate validation logic
    valid_transactions = financial_data[financial_data["account_balance"] > 0]

    return {
        "total_transactions": len(financial_data),
        "valid_transactions": len(valid_transactions),
        "validation_rate": len(valid_transactions) / len(financial_data) * 100,
    }


# Example 3: Custom Quality Requirements
@adri_protected(
    data_param="customer_data",
    min_score=90,  # Require 90% quality score
    dimensions={
        "validity": 19,  # Require 19/20 validity score
        "completeness": 18,  # Require 18/20 completeness score
    },
    on_failure="raise",
    verbose=True,
)
def high_stakes_customer_analysis(customer_data):
    """
    High-stakes customer analysis with strict quality requirements.

    This function requires very high data quality:
    - Overall score must be 90% or higher
    - Validity dimension must score 19/20 or higher
    - Completeness dimension must score 18/20 or higher
    """
    print(f"Performing high-stakes analysis on {len(customer_data)} customers...")

    # Simulate complex analysis
    risk_score = customer_data["age"].std() / customer_data["account_balance"].mean()

    return {
        "customers_analyzed": len(customer_data),
        "risk_score": risk_score,
        "analysis_confidence": "HIGH",
    }


# Example 4: Development-Friendly Configuration
@adri_protected(
    data_param="test_data",
    min_score=70,  # Lower threshold for development
    on_failure="warn",  # Just warn, don't stop execution
    verbose=True,  # Show detailed logs
)
def development_data_pipeline(test_data):
    """
    Development data pipeline with permissive quality settings.

    This configuration is ideal for development and testing:
    - Lower quality threshold (70%)
    - Warnings instead of errors
    - Verbose logging for debugging
    """
    print(f"Running development pipeline on {len(test_data)} records...")

    # Simulate pipeline processing
    processed_records = len(test_data[test_data["name"].notna()])

    return {
        "input_records": len(test_data),
        "processed_records": processed_records,
        "pipeline_status": "DEVELOPMENT",
    }


# Example 5: Using Convenience Decorators
@adri_strict(data_param="sensitive_data")
def process_sensitive_data(sensitive_data):
    """
    Process sensitive data with strict protection.

    Equivalent to @adri_protected with min_score=90 and on_failure="raise".
    """
    print(
        f"Processing {len(sensitive_data)} sensitive records with strict protection..."
    )
    return {"status": "PROCESSED_SECURELY"}


@adri_permissive(data_param="experimental_data")
def experimental_analysis(experimental_data):
    """
    Experimental analysis with permissive protection.

    Equivalent to @adri_protected with min_score=70 and on_failure="warn".
    """
    print(f"Running experimental analysis on {len(experimental_data)} records...")
    return {"status": "EXPERIMENTAL_COMPLETE"}


@adri_financial(data_param="transaction_data")
def process_financial_transactions(transaction_data):
    """
    Process financial transactions with financial-grade protection.

    Equivalent to @adri_protected with min_score=95 and strict dimension requirements.
    """
    print(
        f"Processing {len(transaction_data)} financial transactions with financial-grade protection..."
    )
    return {"status": "FINANCIAL_PROCESSED"}


def demonstrate_protection_scenarios():
    """Demonstrate various protection scenarios."""

    print("🔒 ADRI Protected Decorator Examples")
    print("=" * 50)

    good_data, bad_data = create_sample_data()

    # Scenario 1: Good data passes protection
    print("\n📊 Scenario 1: High-quality data (should pass)")
    try:
        result = process_customer_orders(good_data)
        print(f"✅ Success: {result}")
    except ProtectionError as e:
        print(f"❌ Protection failed: {e}")

    # Scenario 2: Bad data fails protection
    print("\n📊 Scenario 2: Poor-quality data (should fail)")
    try:
        result = process_customer_orders(bad_data)
        print(f"✅ Unexpected success: {result}")
    except ProtectionError as e:
        print(f"❌ Protection correctly blocked execution:")
        print(f"    {str(e)[:100]}...")

    # Scenario 3: Development-friendly mode (warns but continues)
    print("\n📊 Scenario 3: Development mode (warns but continues)")
    try:
        result = development_data_pipeline(bad_data)
        print(f"⚠️  Completed with warnings: {result}")
    except ProtectionError as e:
        print(f"❌ Unexpected failure: {e}")

    # Scenario 4: Strict protection
    print("\n📊 Scenario 4: Strict protection (high requirements)")
    try:
        result = high_stakes_customer_analysis(good_data)
        print(f"✅ Strict protection passed: {result}")
    except ProtectionError as e:
        print(f"❌ Strict protection failed: {str(e)[:100]}...")

    # Scenario 5: Convenience decorators
    print("\n📊 Scenario 5: Convenience decorators")
    try:
        result1 = process_sensitive_data(good_data)
        result2 = experimental_analysis(bad_data)  # Should warn but continue
        result3 = process_financial_transactions(good_data)

        print(f"✅ Sensitive data: {result1}")
        print(f"⚠️  Experimental: {result2}")
        print(f"✅ Financial: {result3}")

    except ProtectionError as e:
        print(f"❌ Convenience decorator failed: {e}")


if __name__ == "__main__":
    demonstrate_protection_scenarios()
