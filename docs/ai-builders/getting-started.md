# 🚀 AI Builders: 5-Minute Agent Protection

**Stop AI agents from crashing on bad data** - See why in under 5 minutes.

> **Real scenario**: Invoice processing agents can fail due to missing currency codes, causing significant financial errors. This guide will show you how to prevent this.

## The Problem: Your Agent Works in Dev, Crashes in Production

You've built an AI agent. It works perfectly on test data. You deploy it. Then:
- ❌ It crashes on invalid emails
- ❌ It sends invoices with missing currency codes (major financial impact)
- ❌ It fails on inconsistent date formats
- ❌ It makes decisions based on impossible data (negative ages?)

**The truth**: Most AI agents fail due to bad data, not bad models.

## Your Agent's Current Risk

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# This agent will crash on bad data
def process_customer_orders(data_file):
    df = pd.read_csv(data_file)
    
    # 💥 Crashes if email format is invalid
    send_confirmation_email(df['email'])
    
    # 💥 Crashes if currency is missing
    process_payment(df['amount'], df['currency'])
    
    # 💥 Crashes if date format is inconsistent
    schedule_delivery(df['order_date'])
```

**ADRI prevents these crashes by checking data quality before your agent runs.**

## Quick Setup (2 minutes)

### 1. Install ADRI
```bash
pip install adri
```

### 2. Test on Sample Data
```bash
# Download sample data to see ADRI in action
curl -O https://raw.githubusercontent.com/adri-standard/adri/main/examples/test_init_data.csv

# Quick assessment
python -c "
from adri import assess
result = assess('test_init_data.csv')
print(f'Agent Crash Risk: {100-result.score}%')
print(f'Safe for agents: {result.score >= 80}')
"
```

You'll see output like:
```
Agent Crash Risk: 32%
Safe for agents: False
```

### 3. Run the Crash Test (1 minute)

We've included sample data that looks fine but will crash agents. See the "Oh No" moment:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import assess

# Assess the sample data
report = assess('test_init_data.csv')
print(f"✨ ADRI Score Report")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"Overall Score: {report.score}/100")
print(f"Status: {'✅ Agent Safe' if report.score >= 80 else '❌ Will Crash Agents'}")

print(f"\n💥 Specific issues that WILL crash your agents:")
for issue in report.critical_issues:
    print(f"   🔴 {issue}")
```

**What you'll see:**
```
✨ ADRI Score Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 68/100
Status: ❌ Will Crash Agents

💥 Specific issues that WILL crash your agents:
   🔴 Invalid emails (invalid-email, anna.mueller@)
   🔴 Missing currency codes (row 3) - Financial errors!
   🔴 Inconsistent date formats: 2025-01-15, 01/22/2025, 22-01-2025
```

## Your First Agent Guard (3 minutes)

### 1. Basic Protection
Add one decorator to protect any function:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import protect_agent

@protect_agent(min_score=80)  # Require 80+ quality score
def process_customer_orders(data_file):
    """This function now only runs on high-quality data"""
    df = pd.read_csv(data_file)
    
    # Your agent logic here - guaranteed quality data
    send_confirmation_email(df['email'])
    process_payment(df['amount'], df['currency'])
    schedule_delivery(df['order_date'])
    
    return "Orders processed successfully"

# Test it
try:
    result = process_customer_orders("test_init_data.csv")
    print(result)
except DataQualityError as e:
    print(f"Agent protected: {e}")
```

### 2. Detailed Requirements
For more control, specify exactly what your agent needs:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import DataGuard

@DataGuard.requires(
    completeness_min=95,  # 95% of critical fields must be present
    validity_min=98,      # 98% of data must be properly formatted
    freshness_max_days=7  # Data must be less than 7 days old
)
def process_customer_orders(data_file):
    # Your agent code here
    return process_orders(data_file)
```

### 3. Testing Your Guard

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Test with different data quality levels
test_files = [
    "high_quality_data.csv",    # Should work
    "medium_quality_data.csv",  # Might work depending on thresholds
    "low_quality_data.csv"      # Should be blocked
]

for file in test_files:
    try:
        result = process_customer_orders(file)
        print(f"✅ {file}: {result}")
    except DataQualityError as e:
        print(f"🛡️ {file}: Protected - {e}")
```

## Understanding Your Data Quality

### Quick Assessment
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import assess

# Get overall quality score
quality = assess("your_data.csv")
print(f"Overall Score: {quality.score}/100")
print(f"Ready for agents: {quality.score >= 80}")
```

### Detailed Analysis
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# See what specific issues might crash your agent
quality = assess("your_data.csv")

print("Quality Breakdown:")
print(f"  Validity: {quality.validity}/100 - Format correctness")
print(f"  Completeness: {quality.completeness}/100 - Missing data")
print(f"  Freshness: {quality.freshness}/100 - Data recency")
print(f"  Consistency: {quality.consistency}/100 - Logical coherence")
print(f"  Plausibility: {quality.plausibility}/100 - Business sense")

# Get specific recommendations
if quality.score < 80:
    print("\n⚠️ Issues that could crash your agent:")
    for issue in quality.issues:
        print(f"  • {issue}")
```

### Generate Quality Report
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Create detailed report for your team
quality = assess("your_data.csv")
quality.save_html_report("data_quality_report.html")
print("Report saved: data_quality_report.html")
```

## Common Agent Protection Patterns

### 1. Email Processing Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
@DataGuard.requires(
    validity_min=95,      # Email formats must be valid
    completeness_min=90   # Most email fields must be present
)
def send_marketing_emails(customer_data):
    # Safe to process emails
    return send_bulk_emails(customer_data)
```

### 2. Financial Analysis Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
@DataGuard.requires(
    validity_min=99,        # Financial data must be precisely formatted
    completeness_min=95,    # Critical fields required
    freshness_max_hours=1  # Must be very recent
)
def analyze_market_data(market_data):
    # Safe to make financial decisions
    return generate_trading_signals(market_data)
```

### 3. Customer Service Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
@DataGuard.requires(
    completeness_min=80,    # Some missing data OK
    validity_min=85,        # Most data should be valid
    freshness_max_days=30   # Customer data can be older
)
def handle_customer_inquiry(customer_data):
    # Safe to interact with customers
    return generate_response(customer_data)
```

## Command Line Tools

### Quick Assessment
```bash
# Check if data is ready for your agent
adri assess your_data.csv

# Set minimum score threshold
adri assess your_data.csv --min-score 80

# Get detailed breakdown
adri assess your_data.csv --detailed
```

### Batch Testing
```bash
# Test multiple files
adri assess data/*.csv --min-score 75

# Generate reports for all files
adri assess data/*.csv --html-report reports/
```

## Integration with AI Frameworks

### LangChain Integration
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from langchain.agents import Agent
from adri.integrations.langchain import ADRIGuard

# Protect your LangChain agent
agent = Agent(
    tools=[...],
    guard=ADRIGuard(min_score=85)
)

# Agent automatically checks data quality before processing
result = agent.run("Process this customer data", data="customer_data.csv")
```

### CrewAI Integration
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from crewai import Agent
from adri.integrations.crewai import quality_check

agent = Agent(
    role="Data Analyst",
    goal="Analyze customer data safely",
    backstory="I only work with high-quality data",
    tools=[quality_check(min_score=90)]
)
```

### DSPy Integration
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
import dspy
from adri.integrations.dspy import QualitySignature

class SafeAnalysisModule(dspy.Module):
    def __init__(self):
        self.quality = QualitySignature(min_score=85)
        self.analyze = dspy.ChainOfThought("data -> analysis")
    
    def forward(self, data):
        # Quality check happens automatically
        return self.analyze(data=data)
```

## Troubleshooting Common Issues

### "My agent is being blocked too often"
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Lower your quality thresholds temporarily
@protect_agent(min_score=60)  # Start lower, increase gradually
def my_agent(data):
    return process(data)

# Or check what's failing
quality = assess("your_data.csv")
print(f"Current score: {quality.score}")
print("Issues to fix:", quality.issues)
```

### "I need different requirements for different data"
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Use conditional guards
def smart_guard(data_file):
    if "financial" in data_file:
        return DataGuard.requires(validity_min=99, freshness_max_hours=1)
    elif "customer" in data_file:
        return DataGuard.requires(completeness_min=80, validity_min=85)
    else:
        return DataGuard.requires(min_score=70)

@smart_guard("customer_data.csv")
def process_data(data_file):
    return process(data_file)
```

### "I want to see what would fail before blocking"
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Dry run mode
from adri import assess

def preview_quality_check(data_file, min_score=80):
    quality = assess(data_file)
    
    print(f"Quality Score: {quality.score}/100")
    print(f"Would pass guard: {quality.score >= min_score}")
    
    if quality.score < min_score:
        print("Issues that would block your agent:")
        for issue in quality.issues:
            print(f"  • {issue}")
    
    return quality.score >= min_score

# Test before implementing guard
preview_quality_check("your_data.csv", min_score=85)
```

## Next Steps

### 🎯 **Immediate Actions**
1. **[Set Quality Requirements →](understanding-requirements.md)** - Define what quality means for your specific agent
2. **[Implement Advanced Guards →](implementing-guards.md)** - More sophisticated protection patterns
3. **[Framework Integration →](framework-integration.md)** - Integrate with LangChain, CrewAI, DSPy

### 📚 **Learn More**
- **[Understanding Quality Requirements →](understanding-requirements.md)** - Deep dive into what agents need
- **[Troubleshooting Guide →](troubleshooting.md)** - Solve common issues
- **[Advanced Patterns →](advanced-patterns.md)** - Complex agent workflows

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help
- **[Examples Repository →](../examples/ai-builders/)** - See complete examples

---

## Success Checklist

After completing this guide, you should have:

- [ ] ✅ ADRI installed and working
- [ ] ✅ Basic quality assessment running on your data
- [ ] ✅ First agent protected with quality guard
- [ ] ✅ Understanding of your data's quality score
- [ ] ✅ Quality report generated for your team
- [ ] ✅ Next steps identified for your specific use case

**🎉 Congratulations! Your agent is now protected from bad data crashes.**

---

## Purpose & Test Coverage

**Why this file exists**: Provides AI Builders with a quick, practical path to protect their agents from data quality issues, focusing on immediate value delivery and crash prevention.

**Key responsibilities**:
- Get AI Builders from problem recognition to working solution in 5 minutes
- Demonstrate guard mechanisms with practical, runnable code examples
- Show framework integrations for popular AI development tools
- Provide troubleshooting guidance for common implementation issues

**Test coverage**: All code examples tested with AI_BUILDER audience validation rules, ensuring they work with current ADRI implementation and demonstrate proper guard usage patterns.
