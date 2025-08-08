"""
Generic Python Function Example with ADRI Protection

This example shows how to protect any Python function from bad data
using the @adri_protected decorator.
"""

import pandas as pd

from adri.decorators.guard import adri_protected


@adri_protected(data_param="input_data")
def data_processor(input_data):
    """
    Generic data processor with ADRI protection.

    This function demonstrates how to protect any Python function:
    1. The @adri_protected decorator checks data quality first
    2. Only good quality data reaches your function
    3. Your existing function code stays exactly the same

    Args:
        input_data (pd.DataFrame): Input data for processing

    Returns:
        dict: Processing results
    """
    # Basic data processing
    total_rows = len(input_data)
    total_columns = len(input_data.columns)

    # Calculate some statistics
    numeric_columns = input_data.select_dtypes(include=["number"]).columns
    if len(numeric_columns) > 0:
        numeric_stats = input_data[numeric_columns].describe()
        avg_values = numeric_stats.loc["mean"].to_dict()
    else:
        avg_values = {}

    # Count missing values
    missing_counts = input_data.isnull().sum().to_dict()

    # Generate summary
    result = {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "numeric_averages": avg_values,
        "missing_values": missing_counts,
        "processing_status": "completed",
    }

    return result


@adri_protected(data_param="sales_data", min_score=85)
def sales_analyzer(sales_data):
    """
    Sales data analyzer with moderate quality requirements.
    """
    # Sales-specific analysis
    total_sales = sales_data["amount"].sum() if "amount" in sales_data.columns else 0
    avg_sale = sales_data["amount"].mean() if "amount" in sales_data.columns else 0

    # Customer analysis
    unique_customers = (
        sales_data["customer_id"].nunique()
        if "customer_id" in sales_data.columns
        else 0
    )

    # Product analysis
    if "product" in sales_data.columns:
        top_products = sales_data["product"].value_counts().head(3).to_dict()
    else:
        top_products = {}

    return {
        "total_sales": total_sales,
        "average_sale": avg_sale,
        "unique_customers": unique_customers,
        "top_products": top_products,
        "analysis_type": "sales_summary",
    }


@adri_protected(data_param="user_data", min_score=95, verbose=True)
def user_profile_analyzer(user_data):
    """
    User profile analyzer with strict quality requirements.
    """
    # User demographics
    if "age" in user_data.columns:
        avg_age = user_data["age"].mean()
        age_groups = (
            pd.cut(
                user_data["age"],
                bins=[0, 25, 45, 65, 100],
                labels=["Young", "Adult", "Middle", "Senior"],
            )
            .value_counts()
            .to_dict()
        )
    else:
        avg_age = 0
        age_groups = {}

    # Geographic analysis
    if "location" in user_data.columns:
        top_locations = user_data["location"].value_counts().head(5).to_dict()
    else:
        top_locations = {}

    # Activity analysis
    if "last_login" in user_data.columns:
        recent_users = len(user_data[user_data["last_login"] > "2024-01-01"])
    else:
        recent_users = 0

    return {
        "total_users": len(user_data),
        "average_age": avg_age,
        "age_distribution": age_groups,
        "top_locations": top_locations,
        "recent_active_users": recent_users,
        "profile_analysis": "comprehensive",
    }


def demonstrate_generic_protection():
    """Demonstrate generic function protection with various data types."""

    print("🐍 Generic Python + ADRI Protection Demo")
    print("=" * 40)

    # Good general data
    good_data = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "value": [100, 200, 150, 300, 250],
            "category": ["A", "B", "A", "C", "B"],
            "active": [True, True, False, True, True],
        }
    )

    # Bad general data
    bad_data = pd.DataFrame(
        {
            "id": [None, 2, 3, "", 5],
            "name": ["", None, "Charlie", "Diana", ""],
            "value": [100, "invalid", 150, None, -250],
            "category": [None, "B", "", "C", "Invalid"],
            "active": ["yes", True, None, "maybe", True],
        }
    )

    print("\n1️⃣ Testing generic processor with GOOD data...")
    try:
        result = data_processor(good_data)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n2️⃣ Testing generic processor with BAD data...")
    try:
        result = data_processor(bad_data)
        print(f"✅ Unexpected success: {result}")
    except Exception as e:
        print(f"🛡️ ADRI Protection activated: {str(e)[:100]}...")

    # Good sales data
    good_sales = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C001", "C004"],
            "product": ["Widget A", "Widget B", "Widget A", "Widget C", "Widget B"],
            "amount": [99.99, 149.99, 99.99, 199.99, 149.99],
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
        }
    )

    print("\n3️⃣ Testing sales analyzer with good data...")
    try:
        result = sales_analyzer(good_sales)
        print(f"✅ Sales analysis success: {result}")
    except Exception as e:
        print(f"❌ Sales analysis error: {e}")

    # Good user data
    good_users = pd.DataFrame(
        {
            "user_id": ["U001", "U002", "U003", "U004", "U005"],
            "age": [25, 34, 45, 29, 52],
            "location": ["New York", "London", "Tokyo", "New York", "Paris"],
            "last_login": [
                "2024-01-15",
                "2024-01-14",
                "2024-01-13",
                "2024-01-16",
                "2024-01-12",
            ],
        }
    )

    print("\n4️⃣ Testing user profile analyzer with good data...")
    try:
        result = user_profile_analyzer(good_users)
        print(f"✅ User analysis success: {result}")
    except Exception as e:
        print(f"❌ User analysis error: {e}")


if __name__ == "__main__":
    demonstrate_generic_protection()
