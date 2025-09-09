---
layout: default
title: AI Engineer Onboarding - ADRI
---

# ADRI for AI Agent Engineers: The Complete Guide

**From Production Failures to Bulletproof Agents in 60 Minutes**

## What ADRI Solves for You as an AI Agent Engineer

You know the pain: Your AI agents work perfectly in development with clean test data, then crash and burn in production when they encounter real-world messy data. **ADRI (AI Data Reliability Intelligence) is your safety net** - it's a data quality framework that automatically protects your agents from bad data before it causes problems.

### The Problem You Face Daily

```python
# This is what happens without ADRI
def my_langchain_customer_agent(customer_data):
    # Your beautiful agent logic...
    chain = prompt | model | parser
    return chain.invoke(customer_data)  # 💥 Breaks on bad data

# Production reality: Missing emails, invalid dates, null values,
# inconsistent formats = broken agents and angry stakeholders
```

### The ADRI Solution

```python
# With ADRI - One decorator protects everything
@adri_protected(data_param="customer_data")
def my_langchain_customer_agent(customer_data):
    # Exact same agent logic - zero changes needed!
    chain = prompt | model | parser
    return chain.invoke(customer_data)  # ✅ Only good data gets through

# ADRI automatically checks data quality first, blocks bad data,
# and gives you actionable reports on what needs fixing
```

## Why You Need This

✅ **Framework Agnostic**: Works with LangChain, CrewAI, AutoGen, LlamaIndex, Haystack, LangGraph, Semantic Kernel - any Python AI framework.

✅ **Zero Code Changes**: Just add one decorator to your existing functions.

✅ **Intelligent Protection**: 5-dimension quality assessment (validity, completeness, freshness, consistency, plausibility) with smart thresholds.

✅ **Actionable Feedback**: When data fails, you get detailed reports with CLI commands to fix issues and share with your data team.

---

# Your ADRI Onboarding Journey

## Step 1: Installation & Quick Win (5 minutes)

### Install ADRI
```bash
# Install ADRI
pip install adri

# Initialize in your project
adri setup
```

This creates your project structure:
```
ADRI/
├── dev/
│   ├── standards/          # Development data standards
│   ├── assessments/        # Quality reports
│   └── training-data/      # Sample data for testing
└── prod/
    ├── standards/          # Production data standards
    ├── assessments/        # Production quality reports
    └── training-data/      # Production reference data
```

### See What Got Created
```bash
# Check your new ADRI configuration
adri show-config

# List available bundled standards (15 built-in standards ready to use)
adri list-standards
```

## Step 2: Protect Your First Agent (2 minutes)

Take any existing agent function and add the decorator:

```python
from adri import adri_protected

# Before: Vulnerable to bad data
def process_customers(customer_data):
    # Your existing agent code
    return results

# After: Protected automatically
@adri_protected(data_param="customer_data")
def process_customers(customer_data):
    # Exact same code - ADRI handles quality checking
    return results
```

**That's it!** Your agent is now protected from bad data.

## Step 3: Test with Real Data (3 minutes)

```python
import pandas as pd

# Good data - agent runs normally
good_data = pd.DataFrame({
    'customer_id': ['C001', 'C002'],
    'email': ['john@example.com', 'jane@example.com'],
    'age': [25, 30]
})

result = process_customers(good_data)  # ✅ Works fine

# Bad data - ADRI blocks execution
bad_data = pd.DataFrame({
    'customer_id': [None, ''],
    'email': ['invalid-email', None],
    'age': [-5, 999]
})

result = process_customers(bad_data)  # 🛡️ ADRI blocks this
```

## Step 4: Understand the Protection (5 minutes)

When ADRI blocks bad data, you get detailed feedback:

```
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 45.2/100 (Required: 80.0/100)

📋 Dimension Details:
❌ Validity: 8.1/20     (Invalid emails, negative ages)
❌ Completeness: 12.3/20 (Missing customer IDs)
✅ Consistency: 18.4/20  (Formats are consistent)
✅ Freshness: 19.1/20    (Data is recent)
❌ Plausibility: 7.3/20  (Unrealistic age values)

🔧 Fix This Now:
1. adri export-report --latest
2. adri show-standard customer_data_standard
3. adri assess <fixed-data> --standard customer_data_standard

💬 Message for Your Data Team:
   "Our AI agent requires data meeting the attached ADRI standard. Current data fails
   quality checks (invalid emails, missing customer IDs). Please review the
   attached report and fix the identified issues."
```

## Step 5: Framework-Specific Integration (10 minutes)

ADRI works with your favorite AI frameworks:

### LangChain Example
```python
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from adri import adri_protected

@adri_protected(data_param="customer_data")
def langchain_customer_service(customer_data):
    llm = OpenAI(temperature=0.7)
    prompt = PromptTemplate.from_template(
        "Analyze this customer data: {customer_data}"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(customer_data=str(customer_data))
```

### CrewAI Example
```python
from crewai import Agent, Task, Crew
from adri import adri_protected

@adri_protected(data_param="market_data")
def crewai_market_analysis(market_data):
    analyst = Agent(
        role='Market Analyst',
        goal='Analyze market trends',
        backstory='Expert in market data analysis'
    )

    task = Task(
        description=f'Analyze this market data: {market_data}',
        agent=analyst
    )

    crew = Crew(agents=[analyst], tasks=[task])
    return crew.kickoff()
```

### AutoGen Example
```python
import autogen
from adri import adri_protected

@adri_protected(data_param="research_data")
def autogen_research_team(research_data):
    assistant = autogen.AssistantAgent(
        name="researcher",
        llm_config={"model": "gpt-4"}
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER"
    )

    user_proxy.initiate_chat(
        assistant,
        message=f"Research this data: {research_data}"
    )
    return {"analysis_complete": True}
```

**Want more frameworks?** Check our [complete framework guide](frameworks) with copy-paste ready code.

## Step 6: CLI Mastery (10 minutes)

ADRI's CLI tools make you look like a data quality expert:

### Generate Custom Standards
```bash
# Create a standard from your actual data
adri generate-standard customer_data.csv

# This creates customer_data_ADRI_standard.yaml with:
# - Field requirements (types, formats, ranges)
# - Quality thresholds based on your data
# - Validation rules for each dimension
```

### Assess Data Quality
```bash
# Test any dataset against a standard
adri assess new_customer_data.csv --standard customer_data_standard

# Get detailed output
adri assess new_customer_data.csv --standard customer_data_standard --verbose

# Results show exactly what passes/fails and why
```

### List and Explore
```bash
# See all available standards (bundled + your custom ones)
adri list-standards --verbose

# Understand what a standard checks
adri show-standard customer_data_standard --verbose

# See your assessment history
adri list-assessments --recent 5 --verbose
```

### Export Reports for Teams
```bash
# Create shareable reports for your data team
adri export-report --latest --format csv

# Explain failures in detail
adri explain-failure --latest
```

## Step 7: Advanced Protection (15 minutes)

### Custom Quality Thresholds
```python
# Strict protection for critical workflows
@adri_protected(data_param="financial_data", min_score=95)
def high_stakes_financial_agent(financial_data):
    return critical_analysis(financial_data)

# Permissive for development
@adri_protected(data_param="test_data", min_score=60, on_failure="warn")
def development_agent(test_data):
    return experimental_analysis(test_data)

# Custom failure handling
@adri_protected(data_param="user_data", on_failure="continue", verbose=True)
def resilient_agent(user_data):
    # Agent continues even with quality warnings
    return robust_analysis(user_data)
```

### Dimension-Specific Requirements
```python
@adri_protected(
    data_param="user_data",
    dimensions={
        "validity": 19,      # Almost perfect format compliance
        "completeness": 18,  # Very few missing values
        "consistency": 15    # Some format variations OK
    }
)
def precision_user_agent(user_data):
    return precise_analysis(user_data)
```

### Environment-Specific Configuration
ADRI automatically adapts to your environment:

```yaml
# adri-config.yaml
adri:
  environments:
    development:
      protection:
        default_min_score: 75    # More permissive for dev
        default_failure_mode: "warn"
    production:
      protection:
        default_min_score: 85    # Stricter for prod
        default_failure_mode: "raise"
```

## Step 8: Team Collaboration (10 minutes)

### Share Data Requirements with Your Team

```bash
# Show exactly what your agents need
adri show-standard customer_data_standard --verbose

# Export standards in various formats
adri export-report --latest --format csv
```

### When Data Fails Quality Checks

ADRI gives you everything you need to communicate with your data team:

```bash
# Get detailed failure explanation
adri explain-failure --latest

# Export actionable report
adri export-report --latest
```

### Message Template for Data Team
```
Subject: Data Quality Issues - Customer Agent Blocked

Hi Data Team,

Our customer service AI agent is currently blocked due to data quality issues.
ADRI assessment shows a score of 45.2/100 (minimum required: 80.0/100).

Issues found:
• Invalid email formats (23 records)
• Missing customer IDs (15 records)
• Unrealistic age values (8 records)

Please see the attached ADRI report for specific details and fix recommendations.

Once fixed, you can test the data with:
adri assess <your-fixed-data> --standard customer_data_standard

Thanks!
```

### Validate Fixes
```bash
# After data team fixes issues
adri assess fixed_customer_data.csv --standard customer_data_standard --verbose

# Should now show:
# ✅ ADRI Protection: ALLOWED
# 📊 Quality Score: 94.2/100 (Required: 80.0/100)
```

## Step 9: Production Deployment (5 minutes)

### Environment Configuration
```bash
# Set production environment
export ADRI_ENVIRONMENT=production

# Or specify in your deployment config
adri assess production_data.csv --environment production
```

### Monitoring and Alerts
```python
# Add monitoring to your production agents
@adri_protected(
    data_param="live_data",
    min_score=90,
    on_failure="raise",
    verbose=True  # Logs detailed protection info
)
def production_agent(live_data):
    # Your production agent logic
    return results
```

### Audit Trail
ADRI automatically logs all protection events:
```bash
# Review protection history
adri list-assessments --environment production --recent 50

# Check for patterns
grep "BLOCKED" ADRI/prod/assessments/*.json
```

---

## What You Get as an AI Agent Engineer

✅ **Reliable Agents**: Your agents only run on quality data
✅ **Clear Communication**: Data teams get specific, actionable feedback
✅ **Framework Freedom**: Works with any Python AI framework
✅ **Zero Refactoring**: Add one decorator, keep existing code
✅ **Professional Reports**: Generate data quality reports for stakeholders
✅ **Fast Development**: Catch data issues early, not in production
✅ **Production Ready**: Built-in audit trails and monitoring

## Real-World Success Stories

### Before ADRI
```
❌ Agent fails randomly in production
❌ Data team gets vague "fix the data" requests
❌ Debugging takes hours per incident
❌ Stakeholders lose confidence in AI systems
❌ Engineers spend time on data issues, not AI logic
```

### After ADRI
```
✅ Agents are predictably reliable
✅ Data team gets specific fix instructions
✅ Issues caught before production deployment
✅ Stakeholders see professional data quality reports
✅ Engineers focus on AI innovation, not data debugging
```

## Advanced Scenarios

### Multi-Dataset Agents
```python
@adri_protected(data_param="customer_data")
@adri_protected(data_param="product_data", standard_file="product_standard.yaml")
def cross_dataset_agent(customer_data, product_data):
    # Both datasets are validated before processing
    return complex_analysis(customer_data, product_data)
```

### Dynamic Standards
```python
def get_standard_for_source(data_source):
    return f"{data_source}_data_standard.yaml"

@adri_protected(
    data_param="data",
    standard_file=lambda: get_standard_for_source(current_source)
)
def adaptive_agent(data):
    return source_specific_analysis(data)
```

### Custom Validation Rules
```python
# Create custom standards with domain-specific rules
adri generate-standard financial_data.csv --output financial_standard.yaml

# Edit the YAML to add custom validation:
# field_requirements:
#   transaction_amount:
#     type: "float"
#     min_value: 0.01
#     max_value: 1000000.0
#     custom_rules:
#       - "Must not exceed daily limit"
```

### Scaling Considerations
As you protect more agents across your organization, you may want to understand our philosophy on [why ADRI is open source](why-open-source) and how we think about enterprise-scale AI data management.

## Troubleshooting Common Issues

### "Standard not found"
```bash
# Check available standards
adri list-standards

# Generate missing standard
adri generate-standard your_data.csv
```

### "Assessment taking too long"
```python
# Use sampling for large datasets
@adri_protected(data_param="big_data", cache_assessments=True)
def big_data_agent(big_data):
    return results
```

### "Too many false positives"
```python
# Adjust thresholds
@adri_protected(data_param="data", min_score=70)  # More permissive
def lenient_agent(data):
    return results
```

## Next Steps

### Immediate Actions (Next 30 minutes)
1. **Install and test** ADRI with your current agent
2. **Generate a standard** from your production data
3. **Test with real data** to see protection in action

### This Week
1. **Protect your critical agents** with appropriate thresholds
2. **Set up CLI workflows** for your team
3. **Create standards** for your main data sources

### This Month
1. **Deploy to production** with monitoring
2. **Train your data team** on ADRI reports
3. **Establish data quality processes** using ADRI assessments

## Resources

- **[Quick Technical Reference](quick-start)** - Fast setup without the story
- **[Framework Examples](frameworks)** - Copy-paste code for your framework
- **[API Documentation](https://github.com/adri-standard/adri/blob/main/docs/API_REFERENCE.md)** - Complete technical reference
- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs or request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Ask questions and share ideas

---

## Join the ADRI Community

🌟 **Help build the future of AI data reliability**

### If ADRI Solved Your Production Issues
- **⭐ Star the repo** on [GitHub](https://github.com/adri-standard/adri) - It helps other AI engineers discover ADRI
- **🍴 Fork and contribute** - We welcome PRs for new frameworks, standards, and improvements
- **💬 Share your success story** in [GitHub Discussions](https://github.com/adri-standard/adri/discussions)
- **📢 Tell your team** - Help your colleagues build reliable AI systems

### Ways to Contribute

**🔧 Code Contributions**
- **New Framework Support** - Add integrations for emerging AI frameworks (Anthropic, Cohere, etc.)
- **Custom Standards** - Contribute domain-specific validation standards (finance, healthcare, etc.)
- **Performance** - Optimize validation algorithms for large-scale data processing
- **CLI Enhancements** - Improve the developer experience with better commands and output

**📚 Documentation & Community**
- **Guides & Tutorials** - Help other AI engineers with framework-specific guides
- **Example Applications** - Share real-world implementations and patterns
- **Bug Reports** - Help us make ADRI bulletproof by reporting edge cases
- **Feature Ideas** - Suggest improvements based on your production experience

**🧪 Standards & Testing**
- **Industry Standards** - Create validation rules for your domain (e-commerce, IoT, etc.)
- **Test Cases** - Add test coverage for complex data scenarios
- **Benchmarks** - Help us measure and improve ADRI's performance

### Community Resources

- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Ask questions, share ideas, and get help
- **[Contributing Guide](https://github.com/adri-standard/adri/blob/main/CONTRIBUTING.md)** - How to contribute code and documentation
- **[Code of Conduct](https://github.com/adri-standard/adri/blob/main/CODE_OF_CONDUCT.md)** - Our commitment to an inclusive community

### Recognition

Contributors get recognition through:
- **Contributor Credits** in release notes and documentation
- **Community Highlights** for significant contributions
- **Direct Access** to maintainers for complex technical discussions
- **Early Access** to new features and enterprise integrations

---

## Ready to Build Bulletproof AI Agents?

You now have everything you need to protect your AI agents from bad data. Start with the 5-minute quick win above, then work through the journey at your own pace.

**Your future self (and your stakeholders) will thank you for making your AI systems reliable.**

*For organizations scaling ADRI across multiple teams and systems, [Verodat Enterprise](https://verodat.com/adri-enterprise) provides centralized governance and advanced features. The open source version works perfectly standalone.*
