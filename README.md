# ADRI: Stop AI Agents from Crashing on Bad Data

**Most AI agents fail due to bad data. ADRI prevents this.**

[![GitHub stars](https://img.shields.io/github/stars/adri-standard/adri?style=social)](https://github.com/adri-standard/adri)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ADRI Version](https://img.shields.io/badge/ADRI-v0.4.2-blue.svg)](https://github.com/adri-standard/adri/releases)
[![PyPI](https://img.shields.io/pypi/v/adri)](https://pypi.org/project/adri/)

## 🚨 The Hidden Cost of Bad Data

**Your AI agent works perfectly in development. Then it hits production data and crashes.**

Common failure scenarios:
- 💸 Missing currency codes → Multi-million dollar invoice errors
- 📧 Invalid emails → Customer service disruptions
- 🚚 Inconsistent addresses → Costly logistics mistakes

**The truth**: High agent reliability requires high data reliability. You can't achieve one without the other.

## 🚀 5-Minute Quickstart: See Your Agent's Crash Risk

```bash
# Install
pip install adri

# Run crash test on sample data
cd quickstart && python quickstart.py
```

**What you'll see in 5 minutes:**
```
✨ ADRI Score Report
━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 68/100 ❌
Status: Will Crash Agents

💥 Critical Issues Found:
• Invalid emails → Email agents will fail
• Missing currency → Invoice processing errors
• Date chaos → Scheduling failures
```

**[→ Full 5-Minute Quickstart Guide](docs/ai-builders/getting-started.md)**

## 🎯 Choose Your Path

ADRI serves three distinct audiences. **Select your path** to get the most relevant guidance:

### 🤖 **AI Builders** - "Protect Your Agents"
You're building AI applications that need reliable data to function correctly.

**Your challenges**: Agents crash on bad data, inconsistent quality across sources, time-consuming debugging

**Your solution**: [**Start Your AI Builder Journey →**](docs/ai-builders/index.md)

---

### 📊 **Data Providers** - "Make Data AI-Ready"  
You manage data that AI systems need to consume reliably.

**Your challenges**: Unclear what "AI-ready" means, no standard way to communicate quality, difficulty proving reliability

**Your solution**: [**Start Your Data Provider Journey →**](docs/data-providers/index.md)

---

### 🛠️ **Standard Contributors** - "Extend ADRI"
You want to improve the ADRI standard itself with rules, templates, or enhancements.

**Your challenges**: Understanding ADRI's architecture, contributing validation logic, building industry templates

**Your solution**: [**Start Your Contributor Journey →**](docs/standard-contributors/index.md)

---

**Not sure which path?** [**Explore all documentation →**](docs/index.md)

## 💡 The Solution: Prevent Crashes Before They Happen

Add one line to protect any agent:

```python
from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=80)
def process_customer(data):
    # Your agent logic here
    send_email(data['email'])
    process_payment(data['amount'], data['currency'])
    
# If data quality < 80, the function won't run
# No more crashes! 🛡️
```

## 📊 The Reliability Relationship

| Data Reliability | Agent Capability | What You Can Build |
|------------------|------------------|-------------------|
| Low | Limited | Internal tools only |
| Medium | Moderate | Customer-facing with human backup |
| High | Advanced | Automated workflows |
| **Very High** | **Full** | **Mission-critical AI agents** |

**Small improvements in data reliability enable exponentially more use cases.**

## 🎯 How ADRI Works

### 1. Define Requirements First
```yaml
# invoice-processor.adri.yaml
name: Invoice Processing Agent
requires:
  completeness:
    critical_fields: [invoice_number, amount, currency, date]
    min_score: 95
  validity:
    formats:
      date: ISO8601
      amount: decimal(10,2)
    min_score: 98
```

### 2. Data Suppliers Know What to Build
```python
# Any data source can target the standard
from adri import DataSourceAssessor

assessor = DataSourceAssessor()
result = assessor.assess_file("my_data.csv")
print(f"Data quality score: {result.overall_score}/100")
```

### 3. Agents Trust Their Inputs
```python
# Agents can require compliant data
from adri import adri_guarded

@adri_guarded(min_score=80)
def process_invoices(data_source):
    # Agent knows data meets requirements
    return execute_with_confidence(data_source)
```

### 4. True Marketplace Emerges
- **Data providers** compete on quality scores
- **Agent builders** can target any ADRI data
- **Enterprises** mix and match components
- **Innovation** happens at every layer

## ⚡ See It In Action

### For Data Teams: "What Standard Do I Need to Meet?"
```bash
# Assess your data against a standard
adri assess invoices.csv --standard invoice-processor-v1

# Get specific remediation steps
📊 Assessment Report:
✗ Completeness: 76% (FAIL - requires 95%)
  Missing: currency in 24% of records
  Action: Add currency codes to all records

✓ Validity: 98% (PASS)
```

### For AI Engineers: "What Data Can I Trust?"
```python
# Discover compatible data sources
available_sources = adri.find_sources("invoice-processor-v1")
# Returns: ["warehouse.invoices", "erp.billing", "api.invoices"]

# Use any compliant source
for source in available_sources:
    my_agent.process(source)  # They all just work!
```

### For Enterprises: "Show Me the Ecosystem"
Visit the [ADRI Marketplace](https://adri-ai.github.io/adri/) to find:
- 📦 **Certified Data Sources** by industry
- 🤖 **Compatible Agents** for your data
- 📋 **Standard Templates** for common use cases
- 🔧 **Implementation Partners** for support

## 🏗️ The Standard Components

### 1. Five Universal Dimensions
Every ADRI assessment measures:
- **Validity**: Is the data in the right format?
- **Completeness**: Are required fields present?
- **Freshness**: Is the data recent enough?
- **Consistency**: Does the data contradict itself?
- **Plausibility**: Does the data make business sense?

### 2. Industry Templates
Pre-built standards for common use cases:
```
adri-finance-invoice-v1
adri-retail-inventory-v1
adri-healthcare-patient-v1
adri-logistics-shipment-v1
```

### 3. Scoring System
- 0-100 score per dimension
- Pass/fail thresholds per use case
- Clear remediation guidance

## 🚀 Quick Start

### Install the Reference Implementation
```bash
pip install adri
```

### Try It on Sample Data
```bash
# Download a sample invoice dataset
curl -O https://adri-standard.github.io/adri/samples/invoices.csv

# See what standards it could meet
adri discover invoices.csv

# Assess against a specific standard
adri assess invoices.csv --standard invoice-processor-v1
```

### Build Your First Compliant Pipeline
```python
from adri import adri_guarded

# Define your pipeline
@adri_guarded(min_score=70)
def load_invoice_data():
    data = pd.read_csv("raw_invoices.csv")
    # Add any transformations
    return data

# Now any agent can trust this data
compliant_data = load_invoice_data()
```

## 🌍 Join the Standard

### For Developers
- ⭐ Star this repo to show support
- 📝 [Contribute templates](CONTRIBUTING.md) for your industry
- 🐛 [Report issues](https://github.com/adri-standard/adri/issues)
- 💬 [Join discussions](https://github.com/adri-standard/adri/discussions)

### For Organizations
- 🏢 Implement ADRI internally (immediate ROI)
- 📊 Contribute industry requirements
- 🤝 [Become a standards partner](GOVERNANCE.md#partners)
- 🎯 Shape the future of AI interoperability

### For Vendors
- 🏪 Offer ADRI-certified data products
- 🤖 Build ADRI-compliant agents
- 🔧 Provide implementation services
- 📢 [List in the marketplace](https://adri-ai.github.io/adri/)

## 📚 Documentation

- **[Quality Dimensions](docs/reference/dimensions/index.md)** - Core quality assessment concepts
- **[Implementation Guide](docs/ai-builders/implementing-guards.md)** - Step-by-step agent protection
- **[Data Assessment Guide](docs/data-providers/assessment-guide.md)** - Make data AI-ready
- **[API Reference](docs/reference/api/index.md)** - Complete technical reference
- **[Frequently Asked Questions](docs/frequently-asked-questions.md)** - Common questions answered

## 🏛️ Governance

ADRI is an open standard governed by its community:

- **License**: MIT (use freely in any context)
- **Governance**: [Open governance model](docs/reference/governance/governance.md)
- **Charter**: [Read our mission](docs/reference/governance/charter.md)
- **Maintainers**: Community-elected board

## 🎯 The Vision

Imagine a world where:
- Any AI agent can work with any data source
- Data quality is measurable and guaranteed
- Innovation happens at every layer
- The ecosystem grows exponentially

**This is what standards enable. This is ADRI.**

## 🤝 Key Partners

### Founding Contributors
- [Verodat](https://verodat.io) - Initial implementation
- [Your Organization Here] - Join as a founding partner

### Implementations
- **Python**: Reference implementation (this repo)
- **JavaScript**: [adri-js](https://github.com/adri-ai/adri-js)
- **Go**: [adri-go](https://github.com/adri-ai/adri-go)
- **Your Language**: [Contribute an implementation](CONTRIBUTING.md#implementations)

## 🚦 Roadmap

### Now (v1.0)
- ✅ Core standard definition
- ✅ Python reference implementation
- ✅ Initial industry templates

### Next (v1.1)
- 🔄 Streaming data support
- 🔄 Multi-source assessments
- 🔄 Advanced remediation AI

### Future (v2.0)
- 🎯 Real-time compliance monitoring
- 🎯 Blockchain-verified assessments
- 🎯 Autonomous quality improvement

## 📞 Get Involved

The future of AI interoperability is being built now. Join us:

- **Website**: [adri-standard.github.io/adri](https://adri-standard.github.io/adri/)
- **GitHub**: [github.com/adri-standard](https://github.com/adri-standard)
- **Discord**: [discord.gg/adri](https://discord.gg/adri)
- **Twitter**: [@adri_standard](https://github.com/adri-ai/adri/discussions)

---

<p align="center">
  <strong>ADRI: Making AI agents work everywhere, with any data.</strong>
</p>

<p align="center">
  <i>An open standard by the community, for the community.</i>
</p>

## Purpose & Test Coverage

**Why this file exists**: Main entry point for the ADRI project, providing immediate understanding of the standard's value proposition and quick paths to adoption.

**Key responsibilities**:
- Communicate the interoperability crisis and ADRI's solution
- Provide clear quick-start instructions
- Showcase ecosystem benefits with concrete examples
- Guide different stakeholders to appropriate resources
- Establish ADRI as THE open standard for agent-data interoperability

**Test coverage**: Verified by tests documented in [README_test_coverage.md](docs/test_coverage/README_test_coverage.md)

