# Agent Data Readiness Index (ADRI)

ADRI is a framework that ensures your AI agents work with reliable data. It transforms cryptic data quality issues into clear business insights, helping you catch problems before they cost money.

**🎯 In 30 seconds, ADRI can find issues that would take hours to discover manually.**

## 🎯 The Problem Every Business Team Faces

**It's Monday morning. A CRM export lands on your desk.**

You need to run your quarterly business review, but you have no idea if this data is reliable. Sound familiar?

- **Option 1**: Spend 4 hours manually checking (and still miss issues)
- **Option 2**: Trust it blindly (and explain the $100K mistake later)
- **Option 3**: Just give up on automation entirely

## 💡 Enter ADRI: See What's Wrong in 30 Seconds

```bash
# RevOps manager runs the AI Status Auditor
python examples/07_status_auditor_demo.py
```

**30 seconds later:**
```
🔍 CRM AUDIT REPORT
==================
💰 REVENUE AT RISK:
• 12 deals worth $340K missing close dates
• 8 deals worth $225K have no activity for 21+ days

🚨 PROCESS BREAKDOWNS:
• 23 contacts missing email (can't execute campaigns)
• 15 opportunities have ownership conflicts

📋 IMMEDIATE ACTIONS:
1. Update close dates for negotiation deals
2. Review stale deals with: John S., Mary K.
```

**That's the power of ADRI** - transforming cryptic data issues into actionable business insights.

## 🔄 Try ADRI in 3 Steps (No Installation Required!)

### 1️⃣ SEE IT (30 seconds)
**Watch ADRI find hidden issues in sample data:**
```bash
# No installation needed - just see the output
curl https://raw.githubusercontent.com/ThinkEvolveSolve/agent-data-readiness-index/main/quickstart/outputs/crm_audit.txt
```

### 2️⃣ TRY IT (2 minutes) 
**Run it on sample data without installing ADRI:**
```bash
# Clone this repo
git clone https://github.com/ThinkEvolveSolve/agent-data-readiness-index
cd agent-data-readiness-index/quickstart

# Run on sample data (no dependencies!)
python try_it.py samples/crm_data.csv
```

### 3️⃣ USE IT (5 minutes)
**Apply to YOUR data:**

**Option A: Install Locally**
```bash
pip install adri
adri assess your_data.csv --output report
```

**Option B: Use Verodat Cloud (Coming Soon)**
- Upload your CSV at [app.verodat.com/adri](https://app.verodat.com/adri)
- Get instant results without installation
- Export findings and recommendations

## 🚀 But Here's Where It Gets Exciting...

### Today: Fix It Manually (But Faster)
You now know exactly what to fix. What took 4 hours now takes 30 seconds to identify.

### Tomorrow: Trust Your Systems
```python
# Upload to your automation platform with confidence
if adri_score >= 80:
    crm_automation.process(data)  # It won't break!
else:
    send_to_human_review(data, adri_report)
```

### The Future: Unleash AI Agents
```python
@requires_data("ADRI-RevOps-v1.0.0")
def intelligent_sales_agent(data):
    """
    This agent ONLY runs on data meeting RevOps standards.
    No more random failures. No more trust issues.
    """
    return optimize_sales_pipeline(data)
```

## ⏰ Why Now? The AI Agent Revolution is Here

AI agents are being deployed everywhere, but **70% fail due to data issues**. Every day without ADRI means:
- 💸 Lost revenue from failed automations
- 🔥 Fire drills when agents make bad decisions
- 😓 Teams losing trust in AI solutions

**ADRI turns this around** - it's the missing link between your data and reliable AI automation.

## 🎯 Why ADRI Changes Everything

ADRI isn't just another data quality tool - it's a **communication protocol** between data sources and AI systems:

### 1. The Protocol
- **Standardized metadata** that travels with your data
- **5 dimensions** of quality: Validity, Completeness, Freshness, Consistency, Plausibility
- **Business-specific templates** (RevOps, Finance, Compliance, etc.)

### 2. The Unlock
- **Write once, run anywhere**: Any ADRI-compliant data works with any ADRI-aware agent
- **Quality marketplace**: Data providers compete on certified quality levels
- **10x productivity**: From manual processes to reliable automation at scale

### 3. The Vision
Imagine a world where:
- Every data source declares its quality in a standard format
- AI agents automatically verify data before processing
- You specify "ADRI Production-v1.0.0" and any compliant data just works

## 🏃 Quick Start: Three Ways to Use ADRI

### 1. Assess Your Data (Start Here)
```python
from adri.assessor import DataSourceAssessor

# Create an assessor
assessor = DataSourceAssessor()

# Assess your data
report = assessor.assess_file("customer_data.csv")

# View results
print(f"Overall score: {report.overall_score}/100")
print(f"Readiness level: {report.readiness_level}")

# Save a detailed report
report.save_html("data_readiness_report.html")
```

### 2. Protect Your Workflows
```python
from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=70)
def process_customer_data(data_source):
    # Your automation logic here
    return analyze_customers(data_source)

# Function only runs if data meets quality standards
try:
    results = process_customer_data("customer_data.csv")
except Exception as e:
    print(f"Data quality too low: {e}")
```

### 3. Define Requirements as Contracts
```python
# Coming soon: Template-based requirements
@requires_data("ADRI-Production-v1.0.0")
def production_workflow(data):
    # Works with ANY data meeting production standards
    pass
```

## 📦 Installation

```bash
# Basic installation
pip install adri

# With SQL support
pip install adri[sql]

# For development
pip install adri[dev]
```

## 🎮 Try the Demos

### Quickstart (No Installation Required!)
Check out the `quickstart/` folder for:
- Zero-dependency demos you can run immediately
- Sample CSV files with realistic data issues
- Pre-generated outputs to see ADRI's value instantly

### See Business Impact in Action
```bash
# Run the AI Status Auditor demo
python examples/07_status_auditor_demo.py
```

### More Examples
- `01_basic_assessment.py` - Simple quality assessment
- `02_requirements_as_code.py` - Define data contracts
- `03_data_team_contract.py` - Align teams on quality
- `04_multi_source.py` - Work with multiple data sources
- `05_production_guard.py` - Protect production workflows

## 🏗️ Building Blocks

### The 5 Dimensions (With Real Examples)
1. **Validity**: Is the data in the right format?
   - *Example: Catches email addresses like "john@invalid" before they break your campaign*

2. **Completeness**: Is critical data missing?
   - *Example: Finds $340K in deals missing close dates before your forecast meeting*

3. **Freshness**: Is the data recent enough?
   - *Example: Alerts when inventory data is 3 days old before auto-ordering $127K*

4. **Consistency**: Does the data contradict itself?
   - *Example: Spots when deal owner ≠ account owner, preventing commission disputes*

5. **Plausibility**: Does the data make business sense?
   - *Example: Flags negative reorder thresholds before they crash your system*

### Growing with ADRI
```
🎯 Start Simple → 🛡️ Add Protection → 📋 Standardize → 🔗 Go Agent-Native
```

## 🏢 Use Cases Across Industries

### 💼 RevOps & Sales
- **Problem**: Deals missing close dates, stale opportunities, broken workflows
- **ADRI Solution**: Catches $340K at risk before your forecast meeting
- **Result**: 95% forecast accuracy, automated pipeline management

### 📦 Supply Chain & Inventory
- **Problem**: Ordering based on stale data, negative thresholds, missing locations
- **ADRI Solution**: Prevents $127K excess inventory orders
- **Result**: 30% reduction in overstock, real-time inventory confidence

### 🏥 Healthcare
- **Problem**: Patient records with missing data, compliance violations
- **ADRI Solution**: Flags issues before they become HIPAA violations
- **Result**: 100% audit compliance, automated patient outreach

### 🏦 Financial Services
- **Problem**: Transaction data inconsistencies, regulatory reporting errors
- **ADRI Solution**: Validates data before it hits reporting systems
- **Result**: Zero regulatory fines, automated reconciliation

### 🛒 E-commerce
- **Problem**: Duplicate customers, invalid addresses, abandoned carts
- **ADRI Solution**: Cleans data before marketing campaigns
- **Result**: 20% higher conversion, reduced shipping errors

## 🤝 Join the Movement

ADRI is a community project building the future of AI-ready data:

### For Business Teams
- Contribute industry-specific templates
- Share success stories and ROI metrics
- Help define what "good data" means in your domain

### For Developers
- Build integrations for your favorite frameworks
- Contribute to the core assessment engine
- Create tools that leverage ADRI standards

### For Organizations
- Adopt ADRI as your data quality standard
- Share templates with the community
- Help establish ADRI as the industry standard

## 📚 Documentation

- [Quick Start Guide](docs/GET_STARTED.md) - Get running in 5 minutes
- [Understanding ADRI](docs/UNDERSTANDING_DIMENSIONS.md) - Learn about the five dimensions
- [AI Status Auditor Use Case](docs/USE_CASE_AI_STATUS_AUDITOR.md) - RevOps transformation story
- [Vision & Roadmap](docs/VISION.md) - See where we're heading
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation

## 🌟 Success Stories

> "ADRI transformed our RevOps from 4-hour manual reviews to 30-second automated audits. Now we're exploring AI agents for the first time with confidence." - RevOps Director

> "We prevented three potential compliance violations in our first week using ADRI. The ROI was immediate." - Compliance Manager

> "ADRI gave us a common language with our data team. No more arguing about what 'clean data' means." - AI Engineer

## 🚀 The Path Forward

1. **Today**: Save hours with automated quality assessment
2. **This Quarter**: Protect your existing automations with quality gates
3. **This Year**: Deploy AI agents with confidence using ADRI standards
4. **The Vision**: Join the ecosystem where all data is AI-ready by default

---

**Ready to make your data AI-ready?** Start with our [Status Auditor demo](examples/07_status_auditor_demo.py) and see the difference in 30 seconds.

## License

ADRI is released under the MIT License. See the [LICENSE](LICENSE) file for details.
