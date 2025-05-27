"""
Example 1: The Agent Blindness Problem

This example demonstrates how ADRI reveals data quality issues that would
otherwise cause agent failures. It shows the "before and after" - how agents
fail silently without ADRI, and how ADRI provides clear visibility.

Real scenario: An AI agent processing customer orders with stale inventory data.
"""

import pandas as pd
from datetime import datetime, timedelta
from adri import DataSourceAssessor

# Simulate a real-world scenario
def simulate_agent_without_adri(data):
    """
    This represents a typical agent that processes data without quality checks.
    It will happily process bad data and make costly mistakes.
    """
    print("🤖 Agent: Processing customer orders...")
    
    # Agent analyzes inventory and makes decisions
    low_stock_items = data[data['stock_level'] < 100]
    
    print(f"🤖 Agent: Found {len(low_stock_items)} items to reorder")
    print("🤖 Agent: Placing orders for 50,000 units...")
    print("✅ Agent: Orders placed successfully!\n")
    
    # The hidden disaster: This data was 3 days old!
    # We just ordered 50,000 units we don't need
    # Cost: $127,000 in excess inventory

def demonstrate_agent_blindness():
    """Shows how agents fail without data quality visibility."""
    
    print("=" * 60)
    print("SCENARIO: Friday 4:47 PM - Deploying inventory agent")
    print("=" * 60)
    
    # Create sample data that LOOKS fine but has hidden issues
    inventory_data = pd.DataFrame({
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'product_name': ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E'],
        'stock_level': [45, 23, 67, 12, 89],  # Looks normal
        'last_updated': [datetime.now() - timedelta(days=3)] * 5,  # 3 days old!
        'warehouse': ['East', 'East', 'West', None, 'North'],  # Missing data
        'reorder_threshold': [50, 50, 50, 50, -10]  # Invalid negative value
    })
    
    # Save to CSV for assessment
    inventory_data.to_csv('inventory_demo.csv', index=False)
    
    print("\n1️⃣ WITHOUT ADRI - Agent operates blindly:")
    print("-" * 40)
    simulate_agent_without_adri(inventory_data)
    
    print("💥 Monday morning: 'Why do we have 50,000 extra widgets?!'")
    print("💸 Loss: $127,000 in excess inventory\n")
    
    print("\n2️⃣ WITH ADRI - See the problems immediately:")
    print("-" * 40)
    
    # Now let's see what ADRI reveals
    assessor = DataSourceAssessor()
    report = assessor.assess_file('inventory_demo.csv')
    
    print(f"📊 ADRI Score: {report.overall_score}/100")
    print(f"⚠️  Readiness Level: {report.readiness_level}\n")
    
    print("🔍 ADRI Findings:")
    for dimension, score in report.dimension_scores.items():
        if score < 15:  # Highlight critical issues
            print(f"   ❌ {dimension}: {score}/20 - CRITICAL")
        elif score < 18:
            print(f"   ⚠️  {dimension}: {score}/20 - Warning")
        else:
            print(f"   ✅ {dimension}: {score}/20")
    
    print("\n📋 Specific Issues Found:")
    # Show actual problems from the report
    if report.validity_issues:
        print("   • Invalid reorder threshold (negative value)")
    if report.freshness_issues:
        print("   • Data is 3 days old (threshold: 24 hours)")
    if report.completeness_issues:
        print("   • Missing warehouse information")
    
    print("\n✨ With ADRI Guard - Prevent the disaster:")
    print("-" * 40)
    
    # Demonstrate the guard in action
    from adri import adri_guard
    
    @adri_guard(min_score=80, explain_on_fail=True)
    def safe_inventory_agent(data_file):
        # This would be your actual agent logic
        return "Processing inventory..."
    
    try:
        result = safe_inventory_agent('inventory_demo.csv')
    except Exception as e:
        print(f"🛡️ ADRI Guard: {e}")
        print("✅ Crisis averted! Agent blocked from processing bad data")
    
    print("\n💡 The Difference:")
    print("   Without ADRI: $127,000 loss discovered Monday")
    print("   With ADRI: Problem prevented before deployment")

if __name__ == "__main__":
    demonstrate_agent_blindness()
    
    print("\n" + "=" * 60)
    print("🎯 KEY TAKEAWAY: ADRI transforms invisible problems into")
    print("   actionable insights BEFORE they cost you money.")
    print("=" * 60)
    
    # Clean up
    import os
    if os.path.exists('inventory_demo.csv'):
        os.remove('inventory_demo.csv')
