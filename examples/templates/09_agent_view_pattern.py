#!/usr/bin/env python3
"""
Example 09: Agent View Pattern

Shows how to create denormalized views for agents while maintaining
ADRI's single dataset assessment model.

This pattern allows you to:
1. Combine multiple tables into a single view
2. Create custom templates for specific agent workflows
3. Assess complex data as a single dataset
4. Maintain ADRI's simplicity while handling complex use cases
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from adri.assessor import DataSourceAssessor
from adri.templates.yaml_template import YAMLTemplate
import tempfile
import os

def create_sample_data():
    """Create sample multi-table data that would normally exist in a database."""
    
    # Customers table
    customers = pd.DataFrame({
        'customer_id': range(1, 101),
        'name': [f'Customer {i}' for i in range(1, 101)],
        'email': [f'customer{i}@example.com' for i in range(1, 101)],
        'created_date': [datetime.now() - timedelta(days=random.randint(1, 365)) for _ in range(100)],
        'lifetime_value': np.random.randint(100, 10000, 100)
    })
    
    # Orders table
    orders_data = []
    for customer_id in range(1, 101):
        num_orders = random.randint(0, 10)
        for _ in range(num_orders):
            orders_data.append({
                'order_id': len(orders_data) + 1,
                'customer_id': customer_id,
                'order_date': datetime.now() - timedelta(days=random.randint(0, 90)),
                'order_total': random.randint(50, 500)
            })
    orders = pd.DataFrame(orders_data)
    
    # Support tickets table
    tickets_data = []
    for customer_id in range(1, 101):
        num_tickets = random.randint(0, 5)
        for _ in range(num_tickets):
            tickets_data.append({
                'ticket_id': len(tickets_data) + 1,
                'customer_id': customer_id,
                'created_date': datetime.now() - timedelta(days=random.randint(0, 60)),
                'satisfaction_score': random.choice([1, 2, 3, 4, 5])
            })
    tickets = pd.DataFrame(tickets_data)
    
    return customers, orders, tickets

def create_agent_view(customers, orders, tickets):
    """
    Create a denormalized view combining customer, order, and support data.
    This is what an agent would actually work with.
    """
    
    # Aggregate order data per customer
    order_summary = orders.groupby('customer_id').agg({
        'order_id': 'count',
        'order_date': 'max',
        'order_total': ['sum', 'mean']
    }).reset_index()
    order_summary.columns = ['customer_id', 'total_orders', 'last_order_date', 
                           'total_order_value', 'avg_order_value']
    
    # Aggregate ticket data per customer
    ticket_summary = tickets.groupby('customer_id').agg({
        'ticket_id': 'count',
        'satisfaction_score': 'mean'
    }).reset_index()
    ticket_summary.columns = ['customer_id', 'total_tickets', 'avg_satisfaction']
    
    # Create the denormalized view
    agent_view = customers.merge(order_summary, on='customer_id', how='left')
    agent_view = agent_view.merge(ticket_summary, on='customer_id', how='left')
    
    # Fill NaN values for customers with no orders/tickets
    agent_view['total_orders'] = agent_view['total_orders'].fillna(0).astype(int)
    agent_view['total_tickets'] = agent_view['total_tickets'].fillna(0).astype(int)
    agent_view['avg_satisfaction'] = agent_view['avg_satisfaction'].fillna(0)
    
    # Calculate days since last order
    agent_view['days_since_last_order'] = (datetime.now() - agent_view['last_order_date']).dt.days
    
    # Add some data quality issues for demonstration
    # Missing emails for some customers
    agent_view.loc[agent_view.index % 20 == 0, 'email'] = None
    
    # Some implausible lifetime values
    agent_view.loc[agent_view.index % 15 == 0, 'lifetime_value'] = -100
    
    return agent_view

def create_agent_view_template():
    """Create a custom template for the customer 360 agent view."""
    
    template_yaml = """
template:
  id: "customer-360-agent-view"
  version: "1.0.0"
  name: "Customer 360 Agent View"
  description: "Quality standards for denormalized customer view used by support agents"
  category: "agent-views"
  authority: "Data Quality Team"
  
metadata:
  created_by: "Data Team"
  use_case: "Customer service and retention agents"
  data_source_type: "denormalized_view"

requirements:
  minimum_overall_score: 85
  
  dimension_requirements:
    validity:
      minimum_score: 18
      critical_checks:
        - "email_format"
        - "positive_values"
    
    completeness:
      minimum_score: 17
      critical_fields:
        - "customer_id"
        - "email"
        - "lifetime_value"
        - "total_orders"
        - "days_since_last_order"
      warning_threshold: 0.95  # 95% completeness required
    
    freshness:
      minimum_score: 16
      max_age_days:
        default: 1  # View should be refreshed daily
        last_order_date: 90  # Orders older than 90 days are stale
    
    consistency:
      minimum_score: 17
      rules:
        - "lifetime_value should be >= total_order_value"
        - "customers with orders should have last_order_date"
    
    plausibility:
      minimum_score: 17
      rules:
        - "lifetime_value should be positive"
        - "avg_satisfaction between 1 and 5"
        - "days_since_last_order should be positive or null"

gap_analysis:
  completeness:
    - field: "email"
      issue: "Missing email addresses"
      impact: "Cannot send automated communications"
      remediation: "Update CRM with customer emails"
    
  plausibility:
    - field: "lifetime_value"
      issue: "Negative lifetime values"
      impact: "Incorrect customer segmentation"
      remediation: "Fix data pipeline calculation"
"""
    
    # Save template to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(template_yaml)
        return f.name

def demonstrate_agent_view_pattern():
    """Main demonstration of the agent view pattern."""
    
    print("=" * 70)
    print("AGENT VIEW PATTERN: Assessing Complex Data as Single Datasets")
    print("=" * 70)
    
    # Step 1: Show the problem
    print("\n📊 Step 1: The Challenge")
    print("-" * 40)
    print("Your customer service agent needs data from:")
    print("  • customers table (profile info)")
    print("  • orders table (purchase history)")
    print("  • tickets table (support interactions)")
    print("\nAssessing these separately doesn't help the agent!")
    
    # Step 2: Create sample data
    print("\n🔨 Step 2: Creating Sample Multi-Table Data")
    print("-" * 40)
    customers, orders, tickets = create_sample_data()
    print(f"  ✓ {len(customers)} customers")
    print(f"  ✓ {len(orders)} orders")
    print(f"  ✓ {len(tickets)} support tickets")
    
    # Step 3: Create denormalized view
    print("\n🔄 Step 3: Creating Denormalized Agent View")
    print("-" * 40)
    agent_view = create_agent_view(customers, orders, tickets)
    print("Combined into single view with columns:")
    for col in agent_view.columns:
        print(f"  • {col}")
    
    # Save the view
    view_file = 'customer_360_agent_view.csv'
    agent_view.to_csv(view_file, index=False)
    print(f"\nSaved as: {view_file}")
    
    # Step 4: Create custom template
    print("\n📋 Step 4: Creating Custom Template for Agent View")
    print("-" * 40)
    template_file = create_agent_view_template()
    print("Template defines requirements specific to this view:")
    print("  • Critical fields for agent workflow")
    print("  • Business rules (e.g., lifetime_value >= total_order_value)")
    print("  • Freshness requirements (daily refresh)")
    print("  • Plausibility checks (positive values, valid ranges)")
    
    # Step 5: Assess with custom template
    print("\n🔍 Step 5: Assessing View with Custom Template")
    print("-" * 40)
    
    # Load template and assess
    template = YAMLTemplate.from_file(template_file)
    assessor = DataSourceAssessor()
    report = assessor.assess_file(view_file)
    
    # Evaluate against template
    evaluation = template.evaluate(report)
    
    print(f"\nOverall Score: {report.overall_score}/100")
    print(f"Template Compliance: {'✅ PASS' if evaluation.compliant else '❌ FAIL'}")
    
    # Show dimension scores
    print("\nDimension Scores:")
    template_requirements = template.get_requirements()
    dim_requirements = template_requirements.get('dimension_requirements', {})
    for dim, result in report.dimension_results.items():
        score = result.get('score', 0)
        required = dim_requirements.get(dim, {}).get('minimum_score', 0)
        status = "✅" if score >= required else "❌"
        print(f"  {status} {dim.capitalize()}: {score}/20 (required: {required})")
    
    # Show specific issues found
    print("\n⚠️ Issues Found:")
    if report.dimension_results.get('completeness', {}).get('missing_critical_fields'):
        print("  • Missing critical email addresses")
    if report.dimension_results.get('plausibility', {}).get('implausible_values'):
        print("  • Negative lifetime values detected")
    
    # Step 6: Show the benefits
    print("\n✨ Step 6: Benefits of This Approach")
    print("-" * 40)
    print("1. **Single Assessment**: One ADRI score for the complete view")
    print("2. **Custom Standards**: Template tailored to agent needs")
    print("3. **Performance**: Agent works with pre-joined data")
    print("4. **Flexibility**: Can create different views for different agents")
    
    # Clean up
    os.unlink(view_file)
    os.unlink(template_file)
    
    # Show example agent code
    print("\n💻 Example Agent Code:")
    print("-" * 40)
    print("""
@adri_guarded(template="customer-360-agent-view-v1.0.0")
def customer_service_agent(view_data):
    '''
    Agent only processes data that meets the custom view standards.
    No need to worry about joins, missing data, or quality issues!
    '''
    for customer in view_data:
        if customer.days_since_last_order > 60:
            send_retention_offer(customer)
        if customer.avg_satisfaction < 3:
            escalate_to_manager(customer)
    """)
    
    print("\n🎯 Key Takeaway:")
    print("ADRI's single dataset focus + agent views = best of both worlds!")
    print("Complex data models simplified into quality-assured views for agents.")

def show_additional_examples():
    """Show other examples of agent views."""
    
    print("\n\n" + "=" * 70)
    print("MORE AGENT VIEW EXAMPLES")
    print("=" * 70)
    
    examples = [
        {
            "name": "Sales Forecast Agent View",
            "tables": ["opportunities", "accounts", "sales_reps", "historical_closes"],
            "view_fields": ["opp_id", "amount", "probability", "days_in_stage", 
                          "rep_quota_attainment", "account_health_score"],
            "template": "sales-forecast-agent-v1.0.0"
        },
        {
            "name": "Inventory Reorder Agent View",
            "tables": ["products", "inventory", "suppliers", "sales_velocity"],
            "view_fields": ["sku", "current_stock", "reorder_point", "lead_time_days",
                          "30_day_velocity", "supplier_reliability"],
            "template": "inventory-reorder-agent-v1.0.0"
        },
        {
            "name": "Compliance Monitoring Agent View",
            "tables": ["transactions", "customers", "risk_scores", "regulatory_flags"],
            "view_fields": ["transaction_id", "amount", "customer_risk_level",
                          "pep_status", "sanctions_check", "days_since_kyc"],
            "template": "compliance-monitor-agent-v1.0.0"
        }
    ]
    
    for example in examples:
        print(f"\n📊 {example['name']}")
        print(f"   Source tables: {', '.join(example['tables'])}")
        print(f"   Key fields: {', '.join(example['view_fields'][:3])}...")
        print(f"   Template: {example['template']}")

if __name__ == "__main__":
    demonstrate_agent_view_pattern()
    show_additional_examples()
    
    print("\n" + "=" * 70)
    print("🚀 Ready to implement agent views in your organization?")
    print("   1. Identify agent workflows needing multiple tables")
    print("   2. Create denormalized views in your data platform")
    print("   3. Build custom ADRI templates for each view")
    print("   4. Assess and maintain quality with ADRI")
    print("=" * 70)
