"""
Example 4: Multi-Source Data - Plug & Play Data Sources

This example demonstrates how ADRI enables true data source independence,
allowing AI agents to work with any data source that meets quality standards
without changing the agent code.

Real scenario: A customer 360 agent that needs to aggregate data from
multiple sources (CRM, billing, support) and can switch providers seamlessly.
"""

import pandas as pd
from datetime import datetime, timedelta
from adri import DataSourceAssessor
from adri.config import Config

# Define the ADRI standard for customer 360 data
CUSTOMER_360_STANDARD = "adri:customer-360-v2.0"

class DataSourceSimulator:
    """Simulates different data sources with varying quality levels."""
    
    def __init__(self, name, quality_profile):
        self.name = name
        self.quality_profile = quality_profile
    
    def get_data(self):
        """Simulate fetching data with specific quality characteristics."""
        base_data = {
            'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005'],
            'name': ['Alice Brown', 'Bob Smith', 'Carol White', 'David Lee', 'Eve Chen'],
            'email': ['alice@email.com', 'bob@email.com', 'carol@email.com', 
                     'david@email.com', 'eve@email.com'],
            'lifetime_value': [5000, 12000, 3500, 8900, 15000],
            'last_purchase': [datetime.now() - timedelta(days=30)] * 5,
            'support_tickets': [2, 5, 1, 3, 7],
            'satisfaction_score': [4.5, 3.8, 4.9, 4.2, 3.5]
        }
        
        df = pd.DataFrame(base_data)
        
        # Apply quality profile
        if self.quality_profile == "poor":
            # Make data stale
            df['last_purchase'] = datetime.now() - timedelta(days=90)
            # Add missing values
            df.loc[2, 'email'] = None
            df.loc[4, 'lifetime_value'] = None
            # Invalid data
            df.loc[1, 'satisfaction_score'] = 6.0  # Out of range
            
        elif self.quality_profile == "medium":
            # Some stale data
            df.loc[0:2, 'last_purchase'] = datetime.now() - timedelta(days=45)
            # Few missing values
            df.loc[3, 'support_tickets'] = None
            
        # "good" profile returns data as-is
        
        return df

def demonstrate_vendor_lock_in_problem():
    """Shows the traditional approach with vendor-specific code."""
    
    print("=" * 60)
    print("THE OLD WAY: Vendor Lock-in Nightmare")
    print("=" * 60)
    
    print("\n❌ Traditional Approach - Agent tied to specific sources:")
    print("-" * 40)
    
    print("```python")
    print("class CustomerAgent:")
    print("    def __init__(self):")
    print("        # Hardcoded to specific vendor APIs")
    print("        self.crm = SalesforceAPI()")
    print("        self.billing = StripeAPI()")
    print("        self.support = ZendeskAPI()")
    print("    ")
    print("    def analyze_customer(self, customer_id):")
    print("        # Custom code for each data source")
    print("        crm_data = self.crm.get_contact(customer_id)")
    print("        billing_data = self.billing.fetch_customer(customer_id)")
    print("        support_data = self.support.retrieve_tickets(customer_id)")
    print("        # Hope the data is good... 🤞")
    print("```")
    
    print("\n😱 The Problems:")
    print("  • Want to switch from Salesforce to HubSpot? Rewrite everything!")
    print("  • Each source has different data quality? Good luck!")
    print("  • Need to add a new source? More custom integration code!")
    print("  • Testing with mock data? Build custom mocks for each API!")

def demonstrate_adri_approach():
    """Shows how ADRI enables source-agnostic agents."""
    
    print("\n\n" + "=" * 60)
    print("THE ADRI WAY: True Data Independence")
    print("=" * 60)
    
    print("\n✅ Source-Agnostic Agent with ADRI:")
    print("-" * 40)
    
    print("```python")
    print("class SmartCustomerAgent:")
    print("    def __init__(self, required_standard='adri:customer-360-v2.0'):")
    print("        self.required_standard = required_standard")
    print("        self.data_sources = []")
    print("    ")
    print("    def add_data_source(self, source):")
    print("        # Only accept sources meeting our standard")
    print("        if source.meets_standard(self.required_standard):")
    print("            self.data_sources.append(source)")
    print("            return True")
    print("        return False")
    print("    ")
    print("    def analyze_customer(self, customer_id):")
    print("        # Work with ANY compliant data source")
    print("        for source in self.data_sources:")
    print("            data = source.get_certified_data(customer_id)")
    print("            # Data guaranteed to meet quality standards")
    print("```")
    
    # Create an assessor with our standard requirements
    requirements = Config()
    requirements.set("template", CUSTOMER_360_STANDARD)
    requirements.set("minimum_score", 85)
    assessor = DataSourceAssessor(config=requirements)
    
    # Test different data sources
    sources = [
        DataSourceSimulator("Legacy CRM System", "poor"),
        DataSourceSimulator("Modern Data Platform", "good"),
        DataSourceSimulator("Partner API", "medium"),
    ]
    
    print("\n🔍 Evaluating Data Sources Against Standard:")
    print("-" * 40)
    
    for source in sources:
        data = source.get_data()
        # Save and assess
        filename = f"{source.name.replace(' ', '_').lower()}_data.csv"
        data.to_csv(filename, index=False)
        
        report = assessor.assess_file(filename)
        meets_standard = report.overall_score >= 85
        
        status = "✅ ACCEPTED" if meets_standard else "❌ REJECTED"
        print(f"\n{source.name}:")
        print(f"  ADRI Score: {report.overall_score}/100")
        print(f"  Meets {CUSTOMER_360_STANDARD}: {status}")
        
        if not meets_standard:
            print(f"  Issues: ", end="")
            issues = []
            if report.freshness_score < 18:
                issues.append("stale data")
            if report.completeness_score < 18:
                issues.append("missing fields")
            if report.validity_score < 18:
                issues.append("invalid values")
            print(", ".join(issues))
        
        # Clean up
        import os
        os.remove(filename)
    
    print("\n💡 The Magic: Your agent code never changes!")
    print("   Just plug in any source that meets the standard")

def show_real_world_scenario():
    """Demonstrates a real migration scenario."""
    
    print("\n\n" + "=" * 60)
    print("REAL SCENARIO: Migrating Data Providers")
    print("=" * 60)
    
    print("\n📅 Monday - Using Internal Database:")
    print("-" * 40)
    print("Current setup: PostgreSQL database")
    print("ADRI Score: 87/100 ✅")
    print("Agent Status: Running smoothly")
    
    print("\n📅 Wednesday - Testing New Provider:")
    print("-" * 40)
    print("Evaluating: DataProvider Inc. API")
    print("ADRI Score: 92/100 ✅")
    print("Better freshness, same completeness")
    print("Decision: Safe to switch!")
    
    print("\n📅 Thursday - Seamless Migration:")
    print("-" * 40)
    print("```python")
    print("# The ONLY code change needed:")
    print("# agent.remove_source(internal_db)")
    print("# agent.add_source(dataprovider_api)")
    print("```")
    print("Migration time: 5 minutes")
    print("Agent downtime: 0 minutes")
    print("Code changes: 2 lines")
    
    print("\n📅 Friday - Adding Redundancy:")
    print("-" * 40)
    print("```python")
    print("# Use BOTH sources for reliability")
    print("agent.add_source(internal_db)      # Primary")
    print("agent.add_source(dataprovider_api) # Backup")
    print("```")
    print("Now with automatic failover!")

def demonstrate_benefits():
    """Shows the concrete benefits of data independence."""
    
    print("\n\n" + "=" * 60)
    print("THE BENEFITS: Why This Changes Everything")
    print("=" * 60)
    
    print("\n1️⃣ **Vendor Negotiations:**")
    print("   'Your data doesn't meet ADRI standards'")
    print("   'Fix it or we switch to your competitor'")
    print("   Result: Better data quality from vendors")
    
    print("\n2️⃣ **Rapid Prototyping:**")
    print("   Start with: CSV files (ADRI score: 85)")
    print("   Move to: Database (ADRI score: 90)")
    print("   Scale to: Real-time API (ADRI score: 95)")
    print("   Agent code changes: ZERO")
    
    print("\n3️⃣ **Disaster Recovery:**")
    print("   Primary source fails?")
    print("   Secondary automatically takes over")
    print("   Both must meet ADRI standards")
    print("   No 'backup' with questionable quality")
    
    print("\n4️⃣ **Cost Optimization:**")
    print("   Compare providers by:")
    print("   • Price: DataCorp ($5k/mo) vs InfoStream ($3k/mo)")
    print("   • Quality: Both meet ADRI customer-360-v2.0")
    print("   • Decision: Save $24k/year with InfoStream")

if __name__ == "__main__":
    demonstrate_vendor_lock_in_problem()
    demonstrate_adri_approach()
    show_real_world_scenario()
    demonstrate_benefits()
    
    print("\n\n" + "=" * 60)
    print("🎯 KEY TAKEAWAY: ADRI standards free you from vendor lock-in")
    print("   while guaranteeing data quality from any source.")
    print("=" * 60)
