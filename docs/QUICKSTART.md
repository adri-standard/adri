# 🚀 ADRI 5-Minute Quickstart

**Stop AI agents from crashing on bad data** - See why in under 5 minutes.

> **Real scenario**: Invoice processing agents can fail due to missing currency codes, causing significant financial errors. This guide will show you how to prevent this.

## The Problem: Your Agent Works in Dev, Crashes in Production

You've built an AI agent. It works perfectly on test data. You deploy it. Then:
- ❌ It crashes on invalid emails
- ❌ It sends invoices with missing currency codes (major financial impact)
- ❌ It fails on inconsistent date formats
- ❌ It makes decisions based on impossible data (negative ages?)

**The truth**: Most AI agents fail due to bad data, not bad models.

## 1. Install ADRI (30 seconds)

```bash
pip install adri
```

## 2. Run the Crash Test (2 minutes)

We've included sample data that looks fine but will crash agents. Run this:

```bash
cd quickstart
python quickstart.py
```

Or write your own:

```python
from adri import DataSourceAssessor

# Assess your data
assessor = DataSourceAssessor()
report = assessor.assess_file("your_data.csv")

# See the truth
report.print_summary()
```

## 3. What You'll See (The "Oh No" Moment)

```
✨ ADRI Score Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 68/100 (Grade: D+)
Status: Will Crash Agents ❌

Dimension Scores:
• Validity       12/20 ████████████░░░░░░░░ 
• Completeness   14/20 ██████████████░░░░░░
• Freshness      16/20 ████████████████░░░░
• Consistency    13/20 █████████████░░░░░░░
• Plausibility   13/20 █████████████░░░░░░░

💥 Specific issues that WILL crash your agents:

🔴 VALIDITY ISSUES:
   • Invalid emails (invalid-email, anna.mueller@)
   • These will crash email automation agents
   • Impact: Failed customer communications

🔴 COMPLETENESS ISSUES:
   • Missing currency codes (row 3)
   • Missing email addresses (row 5)
   • Impact: Significant financial errors in production

🔴 CONSISTENCY ISSUES:
   • Date formats: 2025-01-15, 01/22/2025, 22-01-2025
   • Status values: active, ACTIVE, Active
   • Impact: Scheduling chaos, workflow failures
```

## 4. Protect Your Agent (1 minute)

Add ONE line to prevent crashes:

```python
from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=80)
def process_customer(customer_data):
    # Your agent logic here
    send_email(customer_data['email'])  
    calculate_discount(customer_data['total_spent'])
    
# If data quality < 80, the function won't run
# Your agent stays safe! 🛡️
```

### Advanced Protection

Set specific requirements:

```python
@adri_guarded(
    min_score=85,
    required_dimensions={
        'validity': 18,      # Email fields must be valid
        'completeness': 16   # No missing critical data
    }
)
def send_invoice(invoice_data):
    # This won't run unless data meets ALL requirements
    process_payment(invoice_data)
```

## 5. What Your Score Means

| Score | Safe For | NOT Safe For |
|-------|----------|--------------|
| 0-49  | Internal testing only | Any production use |
| 50-79 | Internal tools with human oversight | Customer-facing agents, Financial operations |
| 80-89 | Most agent operations | High-value transactions without review |
| 90-99 | Mission-critical operations | (You're good!) |
| 99+   | Everything | The dream! |

### The Math That Matters

- **Low reliability** → Limited to internal testing
- **Moderate reliability** → Requires human oversight
- **High reliability** → Enables automation
- **Near-perfect reliability** → Unlocks mission-critical uses

**Small improvements in reliability unlock disproportionate value.**

## Next Steps

### 1. Test Your Production Data

```bash
adri assess your_production_data.csv
```

### 2. Set Requirements for Your Use Case

```python
# Define what "good" means for your agent
from adri import DataRequirements

requirements = DataRequirements()
requirements.add_rule("email_valid", dimension="validity", threshold=0.95)
requirements.add_rule("no_missing_currency", dimension="completeness", threshold=1.0)

# Check if data meets requirements
result = requirements.validate(your_data)
```

### 3. Learn More

- **[Production Guard Pattern](../examples/05_production_guard.py)** - Full production implementation
- **[Requirements as Code](../examples/02_requirements_as_code.py)** - Define your data contract
- **[Multi-Source Assessment](../examples/04_multi_source.py)** - Compare data sources
- **[Template Compliance](../examples/08_template_compliance.py)** - Industry standards

### 4. Join the Movement

- ⭐ [Star us on GitHub](https://github.com/verodat/agent-data-readiness-index)
- 📖 [Read the full docs](https://adri.verodat.com)
- 💬 [Join our Discord](https://discord.gg/adri-community)
- 🐦 [Follow updates on X](https://x.com/adri_standard)

## FAQ

**Q: Is this just data quality repackaged?**  
A: No. ADRI is specifically designed for AI agent failure modes. Traditional data quality tools don't catch the issues that crash agents.

**Q: How is this different from data validation?**  
A: Validation checks structure. ADRI checks if your data will actually work with AI agents - including edge cases models can't handle.

**Q: Can I use this with LangChain/CrewAI/AutoGen?**  
A: Yes! See our [integration guides](INTEGRATIONS.md).

**Q: What about real-time data?**  
A: ADRI can run in streaming mode. See [advanced usage](API_REFERENCE.md#streaming).

---

**Remember**: Agent reliability is fundamentally limited by data quality. You can't build reliable AI on unreliable data.

**Start now**: Prevent your next agent crash in 5 minutes.

```bash
cd quickstart && python quickstart.py
