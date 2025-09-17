# Customer Support Agent with ADRI Protection

This example shows how to protect a customer support AI agent from poor quality customer data.

## Scenario
Your customer support agent processes incoming customer tickets and needs reliable customer profile data to provide personalized responses. Poor data quality leads to incorrect responses and frustrated customers.

## Implementation

### 1. Customer Support Agent Function
```python
from adri import adri_protected
import pandas as pd

@adri_protected(
    standard="customer_profile_standard",
    data_param="customer_profile",
    min_score=80,
    dimensions={
        "completeness": 18,  # Need complete customer info
        "validity": 17       # Email/phone must be valid for follow-up
    },
    on_failure="warn",      # Don't block support, but warn agents
    verbose=True
)
def generate_support_response(customer_profile, ticket_data):
    """
    Generate personalized customer support response.

    Args:
        customer_profile: Customer profile data (protected by ADRI)
        ticket_data: Support ticket information

    Returns:
        Personalized response with customer context
    """
    # Extract customer context
    customer_name = customer_profile.get("name", "Valued Customer")
    customer_tier = customer_profile.get("tier", "standard")
    purchase_history = customer_profile.get("recent_purchases", [])

    # Generate context-aware response
    if customer_tier == "premium":
        response_tone = "priority"
        escalation_available = True
    else:
        response_tone = "standard"
        escalation_available = False

    # Build personalized response
    response = {
        "greeting": f"Hello {customer_name}",
        "response_tone": response_tone,
        "escalation_available": escalation_available,
        "context": {
            "tier": customer_tier,
            "recent_purchases": len(purchase_history),
            "profile_quality": "verified"  # ADRI ensures this
        }
    }

    return response
```

### 2. Customer Profile Standard
Create `customer_profile_standard.yaml`:

```yaml
standards:
  id: customer_profile_standard
  name: Customer Profile Standard
  version: 1.0.0
  authority: Customer Support Team
  description: Quality standard for customer profile data used in support agent

requirements:
  overall_minimum: 80.0

  field_requirements:
    customer_id:
      type: string
      nullable: false
      description: Unique customer identifier

    name:
      type: string
      nullable: false
      description: Customer full name

    email:
      type: string
      nullable: false
      pattern: "^[^@]+@[^@]+\\.[^@]+$"
      description: Valid email address for follow-up

    phone:
      type: string
      nullable: true
      pattern: "^\\+?[0-9\\s\\-\\(\\)]+$"
      description: Phone number in standard format

    tier:
      type: string
      nullable: false
      allowed_values: ["standard", "premium", "enterprise"]
      description: Customer service tier

    account_status:
      type: string
      nullable: false
      allowed_values: ["active", "suspended", "closed"]
      description: Current account status

    registration_date:
      type: date
      nullable: false
      description: Customer registration date

  dimension_requirements:
    validity:
      minimum_score: 17.0
      description: Email and phone must be valid for customer contact

    completeness:
      minimum_score: 18.0
      description: Must have complete customer information for personalization

    consistency:
      minimum_score: 15.0
      description: Data formats must be consistent across records

    freshness:
      minimum_score: 16.0
      description: Customer data should be reasonably recent

    plausibility:
      minimum_score: 14.0
      description: Customer information should be realistic
```

### 3. Usage Example

```python
# Example customer profile data
customer_profile = {
    "customer_id": "CUST_12345",
    "name": "Alice Johnson",
    "email": "alice.johnson@email.com",
    "phone": "+1-555-123-4567",
    "tier": "premium",
    "account_status": "active",
    "registration_date": "2023-01-15",
    "recent_purchases": [
        {"product": "Premium Plan", "date": "2024-01-10"},
        {"product": "Add-on Service", "date": "2024-02-05"}
    ]
}

ticket_data = {
    "ticket_id": "TICK_67890",
    "subject": "Billing Question",
    "priority": "medium",
    "category": "billing"
}

# Process support request with data quality protection
try:
    response = generate_support_response(customer_profile, ticket_data)
    print("✅ Support response generated successfully")
    print(f"Response: {response}")

except Exception as e:
    print(f"❌ Support response failed: {e}")
    # Handle poor data quality scenario
    fallback_response = {
        "greeting": "Hello",
        "message": "We're processing your request and will follow up soon",
        "escalation_available": True
    }
```

## Benefits

### For Support Agents
- **Reliable Responses**: ADRI ensures agent has quality customer data
- **Context Awareness**: Complete profiles enable personalized responses
- **Error Prevention**: Invalid contact info is caught before sending responses

### For Customers
- **Better Experience**: Agents have accurate customer context
- **Faster Resolution**: No delays from missing/incorrect customer data
- **Appropriate Tone**: Customer tier information ensures proper response level

### For Support Management
- **Quality Monitoring**: Audit logs track data quality issues
- **Performance Insights**: Understand impact of data quality on support metrics
- **Continuous Improvement**: Identify common data quality patterns

## CLI Workflow

```bash
# 1. Initialize ADRI in your support system
adri setup --project-name "customer-support-system"

# 2. Generate standard from your customer data
adri generate-standard customer_profiles.csv

# 3. Assess data quality before going live
adri assess customer_profiles.csv --standard customer_profile_standard

# 4. Monitor ongoing quality
adri assess daily_customer_updates.csv --standard customer_profile_standard --output daily_quality_report.json
```

## Monitoring and Alerts

Set up monitoring for your support agent data quality:

```python
# Daily quality check script
import schedule
from adri.validator.loaders import load_data
from adri.validator.engine import DataQualityAssessor

def daily_quality_check():
    """Run daily customer data quality assessment."""
    data = load_data("daily_customer_updates.csv")
    assessor = DataQualityAssessor()
    result = assessor.assess(data, "customer_profile_standard.yaml")

    if result.overall_score < 85:
        send_alert_to_data_team(result)

    log_quality_metrics(result)

# Schedule daily at 8 AM
schedule.every().day.at("08:00").do(daily_quality_check)
```

This ensures your customer support agents always have reliable data for providing excellent customer service.
