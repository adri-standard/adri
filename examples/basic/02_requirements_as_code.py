"""
Example 2: Requirements as Code - The Standardized Framework

This example shows how ADRI transforms vague data requirements into
concrete, measurable standards that both AI engineers and data teams
can understand and implement.

Real scenario: AI engineer needs to communicate data requirements to
the data team for a customer churn prediction agent.
"""

import pandas as pd
from datetime import datetime, timedelta
from adri.assessor import DataSourceAssessor
from adri.config import Config

def show_the_old_way():
    """Demonstrates the painful communication without standards."""
    
    print("=" * 60)
    print("THE OLD WAY: Email Thread of Confusion")
    print("=" * 60)
    
    print("\n📧 Email #1 (AI Engineer → Data Team):")
    print("   'We need fresh customer data for the churn agent'")
    
    print("\n📧 Email #7 (Data Team → AI Engineer):")
    print("   'How fresh? Daily? Hourly?'")
    
    print("\n📧 Email #15 (AI Engineer → Data Team):")
    print("   'Fresh enough for predictions'")
    
    print("\n📧 Email #23 (Data Team → AI Engineer):")
    print("   'What fields do you need?'")
    
    print("\n📧 Email #31 (AI Engineer → Data Team):")
    print("   'All the important ones'")
    
    print("\n📧 Email #47 (Manager → Both):")
    print("   'Why is this taking 3 weeks?!'")
    
    print("\n😭 Result: Frustration, delays, and misaligned expectations")

def demonstrate_requirements_as_code():
    """Shows how ADRI creates clear, measurable requirements."""
    
    print("\n\n" + "=" * 60)
    print("THE ADRI WAY: Clear Requirements in Code")
    print("=" * 60)
    
    # Create a configuration that represents requirements
    requirements = Config()
    
    # Define specific, measurable requirements
    requirements.set("dimensions.freshness.weight", 2.0)  # Double importance
    requirements.set("dimensions.freshness.max_age_hours", 2)
    
    requirements.set("dimensions.completeness.weight", 1.5)
    requirements.set("dimensions.completeness.required_fields", [
        "customer_id",
        "last_purchase_date", 
        "total_spend",
        "support_tickets",
        "engagement_score"
    ])
    
    requirements.set("dimensions.validity.weight", 1.0)
    requirements.set("dimensions.validity.email_format", True)
    requirements.set("dimensions.validity.date_format", "ISO8601")
    
    requirements.set("dimensions.consistency.weight", 1.2)
    requirements.set("dimensions.plausibility.weight", 0.8)
    
    requirements.set("thresholds.minimum_score", 85)
    requirements.set("thresholds.critical_dimensions", ["freshness", "completeness"])
    
    print("\n📋 ADRI Requirements (churn-prediction-v1):")
    print("-" * 40)
    print("Freshness:")
    print("  • Maximum age: 2 hours")
    print("  • Weight: 2.0x (critical)")
    print("  • Required score: ≥18/20")
    
    print("\nCompleteness:")
    print("  • Required fields: customer_id, last_purchase_date,")
    print("    total_spend, support_tickets, engagement_score")
    print("  • Weight: 1.5x (important)")
    print("  • Required score: ≥17/20")
    
    print("\nOverall:")
    print("  • Minimum acceptable score: 85/100")
    print("  • Template: churn-prediction-v1")
    
    # Simulate testing data against requirements
    print("\n\n🧪 Testing Current Data Against Requirements:")
    print("-" * 40)
    
    # Create sample data
    test_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'email': ['user1@example.com', 'user2@example.com', 'invalid-email', 
                  'user4@example.com', 'user5@example.com'],
        'last_purchase_date': [
            datetime.now() - timedelta(hours=1),   # Fresh
            datetime.now() - timedelta(hours=3),   # Too old
            datetime.now() - timedelta(days=2),    # Way too old
            datetime.now() - timedelta(minutes=30), # Fresh
            None                                    # Missing
        ],
        'total_spend': [1500.00, 2300.00, 450.00, None, 3200.00],
        'support_tickets': [2, 5, 1, 3, None],
        # Note: engagement_score is completely missing!
    })
    
    test_data.to_csv('churn_data_test.csv', index=False)
    
    # Assess against requirements
    assessor = DataSourceAssessor(config=requirements)
    report = assessor.assess_file('churn_data_test.csv')
    
    print(f"\n📊 Assessment Results:")
    print(f"   Overall Score: {report.overall_score}/100")
    print(f"   Meets Requirements: {'❌ NO' if report.overall_score < 85 else '✅ YES'}")
    
    print(f"\n📈 Dimension Breakdown:")
    for dimension, results in report.dimension_results.items():
        score = results['score']
        status = "✅" if score >= 17 else "❌"
        print(f"   {status} {dimension}: {score}/20")
    
    print("\n🔍 Specific Gaps (for Data Team):")
    print("   • Missing required field: 'engagement_score'")
    print("   • 40% of data is older than 2-hour threshold")
    print("   • Invalid email format in 20% of records")
    print("   • Missing values in 'total_spend' and 'support_tickets'")
    
    # Show how to share requirements
    print("\n\n📤 Sharing Requirements with Data Team:")
    print("-" * 40)
    
    print("1. Export as YAML:")
    print("   ```yaml")
    print("   name: churn-prediction-v1")
    print("   version: 1.0.0")
    print("   requirements:")
    print("     freshness:")
    print("       max_age_hours: 2")
    print("       weight: 2.0")
    print("   ```")
    
    print("\n2. Share validation script:")
    print("   ```python")
    print("   # validate_churn_data.py")
    print("   from adri import validate_against_template")
    print("   score = validate_against_template(data, 'churn-v1')")
    print("   print(f'Data quality: {score}/100')")
    print("   ```")
    
    print("\n3. Track progress:")
    print("   Day 1: 67/100 ❌")
    print("   Day 2: 78/100 ❌ (improved freshness)")
    print("   Day 3: 92/100 ✅ (added missing fields)")

def show_the_impact():
    """Demonstrates the real-world impact of clear requirements."""
    
    print("\n\n" + "=" * 60)
    print("THE IMPACT: Real Results from Real Teams")
    print("=" * 60)
    
    print("\n⏱️ Time to Agreement:")
    print("   Without ADRI: 3 weeks of back-and-forth")
    print("   With ADRI: 30 minutes to review requirements")
    
    print("\n🎯 Accuracy:")
    print("   Without ADRI: 'The data seems wrong but we're not sure why'")
    print("   With ADRI: 'Freshness score is 12/20, needs improvement'")
    
    print("\n🤝 Collaboration:")
    print("   Without ADRI: Finger-pointing when agent fails")
    print("   With ADRI: Clear ownership and measurable progress")
    
    print("\n💰 Business Value:")
    print("   Without ADRI: Agent failures discovered in production")
    print("   With ADRI: Issues caught and fixed before deployment")

if __name__ == "__main__":
    show_the_old_way()
    demonstrate_requirements_as_code()
    show_the_impact()
    
    print("\n\n" + "=" * 60)
    print("🎯 KEY TAKEAWAY: ADRI turns vague requirements into")
    print("   concrete, measurable standards everyone understands.")
    print("=" * 60)
    
    # Clean up
    import os
    if os.path.exists('churn_data_test.csv'):
        os.remove('churn_data_test.csv')
