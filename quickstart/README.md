# ADRI Quickstart - Try It in 3 Steps!

This quickstart lets you experience ADRI's value without installing the full framework.

## 🚀 The 3-Step Journey

### 1️⃣ SEE IT (30 seconds) - No Installation Required!

See what ADRI finds in sample data:

```bash
# From the quickstart directory:
python see_it.py

# Or view directly online:
curl https://raw.githubusercontent.com/ThinkEvolveSolve/agent-data-readiness-index/main/quickstart/outputs/crm_audit.txt
```

### 2️⃣ TRY IT (2 minutes) - Run on Sample Data

Run a simplified version of ADRI (no dependencies required!):

```bash
# Assess sample CRM data
python try_it.py samples/crm_data.csv

# Try other samples
python try_it.py samples/inventory.csv
python try_it.py samples/customers.csv
```

### 3️⃣ USE IT (5 minutes) - Run on Your Data

Ready for the full power of ADRI?

**Option A: Install Locally**
```bash
# Go back to the main directory
cd ..

# Install ADRI
pip install -e .

# Run on your data
adri assess your_data.csv --output report
```

**Option B: Use the Full Examples**
```bash
# Try the Status Auditor demo
cd ../examples
python 07_status_auditor_demo.py
```

## 📁 What's in This Quickstart?

- `see_it.py` - Shows pre-generated ADRI output (no processing)
- `try_it.py` - Minimal ADRI implementation (zero dependencies)
- `samples/` - Sample CSV files with realistic data issues
- `outputs/` - Pre-generated reports for instant viewing
- `minimal_adri/` - Simplified ADRI logic using only Python stdlib

## 🎯 Key Insights You'll See

### From CRM Data:
- 💰 Revenue at risk from missing close dates
- 📧 Contacts without emails (can't run campaigns)
- 🔄 Ownership conflicts causing confusion

### From Inventory Data:
- 📦 Stale data leading to over-ordering
- ❌ Invalid values in critical fields
- ⚠️ Missing warehouse information

### From Customer Data:
- 👥 Duplicate customer records
- 📅 Outdated contact information
- 🌍 Invalid location data

## 💡 Why This Matters

**Without ADRI**: Your AI agents process bad data and make expensive mistakes
**With ADRI**: You catch issues BEFORE they cost you money

Ready to protect your AI workflows? Start with Step 1 above!
