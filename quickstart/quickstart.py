#!/usr/bin/env python3
"""
ADRI 5-Minute Quickstart
========================

See why your AI agents are crashing and how to fix it.
This demo takes less than 5 minutes.

Real scenario: Invoice processing agents can fail due to missing 
currency codes, causing significant financial errors. This is preventable.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adri import DataSourceAssessor
from adri.integrations.guard import adri_guarded


def main():
    print("\n🚀 ADRI 5-Minute Quickstart\n")
    print("=" * 60)
    
    # Step 1: Load sample data that looks fine but will crash agents
    print("\n📊 Step 1: Analyzing your 'perfect' customer data...")
    print("-" * 60)
    
    assessor = DataSourceAssessor()
    report = assessor.assess_file("samples/crash_test_data.csv")
    
    # Step 2: Show the scary truth
    print("\n⚠️  Step 2: Here's what we found:\n")
    report.print_summary()
    
    # Step 3: Show specific crash points
    print("\n💥 Step 3: Specific issues that WILL crash your agents:")
    print("-" * 60)
    
    # Get dimension results
    dimensions = report.dimension_results
    
    # Validity issues
    if dimensions['validity']['score'] < 15:
        print("\n🔴 VALIDITY ISSUES:")
        print("   • Invalid emails (invalid-email, anna.mueller@)")
        print("   • These will crash email automation agents")
        print("   • Impact: Failed customer communications")
    
    # Completeness issues  
    if dimensions['completeness']['score'] < 15:
        print("\n🔴 COMPLETENESS ISSUES:")
        print("   • Missing currency codes (row 3)")
        print("   • Missing email addresses (row 5)")
        print("   • Impact: Significant financial errors in production")
    
    # Consistency issues
    if dimensions['consistency']['score'] < 15:
        print("\n🔴 CONSISTENCY ISSUES:")
        print("   • Date formats: 2025-01-15, 01/22/2025, 22-01-2025")
        print("   • Status values: active, ACTIVE, Active")
        print("   • Impact: Scheduling chaos, workflow failures")
    
    # Plausibility issues
    if dimensions['plausibility']['score'] < 15:
        print("\n🔴 PLAUSIBILITY ISSUES:")
        print("   • Negative age: -5 years old")
        print("   • Impossible age: 150 years old")
        print("   • Extreme amount: $999,999,999.99")
        print("   • Impact: Business logic errors, trust issues")
    
    # Step 4: Show the solution
    print("\n\n✅ Step 4: How to protect your agents:")
    print("-" * 60)
    print("""
# Add ONE line to prevent crashes:

from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=80)
def process_customer(customer_data):
    # Your agent logic here
    send_email(customer_data['email'])  
    calculate_discount(customer_data['total_spent'])
    
# If data quality < 80, the function won't run
# Your agent stays safe! 🛡️
""")
    
    # Step 5: Show readiness by use case
    print("\n📈 Step 5: What you can safely do with this data:")
    print("-" * 60)
    
    score = report.overall_score
    if score < 50:
        print(f"   Score: {score}/100 ❌ DANGER ZONE")
        print("   ⛔ Safe for: Internal testing only")
        print("   ⚠️  NOT safe for: Customer-facing agents")
        print("   💀 Definitely not: Financial transactions")
    elif score < 80:
        print(f"   Score: {score}/100 ⚠️  RISKY")
        print("   ✓ Safe for: Internal tools with human oversight")
        print("   ⚠️  Risky for: Automated customer communications")
        print("   ⛔ Not safe for: Financial operations")
    else:
        print(f"   Score: {score}/100 ✅ PRODUCTION READY")
        print("   ✓ Safe for: Most agent operations")
        print("   ✓ Safe for: Customer communications")
        print("   ⚠️  Consider review for: High-value transactions")
    
    # Call to action
    print("\n\n🎯 Next Steps:")
    print("=" * 60)
    print("""
1. Run on YOUR data:
   adri assess your_data.csv

2. Add agent protection:
   See: examples/05_production_guard.py

3. Set data requirements:
   See: examples/02_requirements_as_code.py

4. Get the full story:
   Docs: https://adri.verodat.com
   GitHub: https://github.com/verodat/agent-data-readiness-index
""")
    
    print("\n💡 Remember: Agent reliability is fundamentally limited")
    print("   by data quality. You can't build reliable AI on unreliable data.\n")


# Bonus: Example of a protected agent function
@adri_guarded(min_score=80, required_dimensions={'validity': 18, 'completeness': 16})
def send_customer_email(customer_data):
    """This function will only run if data meets quality standards."""
    email = customer_data.get('email')
    name = customer_data.get('name')
    # Your email sending logic here
    print(f"Sending email to {name} at {email}")


if __name__ == "__main__":
    main()
