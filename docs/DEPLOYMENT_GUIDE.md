# ADRI - Deployment Guide

**Stop AI Agents Breaking on Bad Data**  
One line of code. Any framework. Bulletproof agents.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation Methods](#installation-methods)
3. [Framework Integration](#framework-integration)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Setup](#advanced-setup)

---

## Quick Start

### 30-Second Setup

```bash
# 1. Install ADRI
pip install adri

# 2. Protect your agent (any framework)
```

```python
from adri.decorators.guard import adri_protected

# Before: Agent breaks on bad data
def your_agent(data):
    return process_data(data)  # 💥 Breaks

# After: Agent protected by ADRI  
@adri_protected(data_param="data")
def your_agent(data):
    return process_data(data)  # ✅ Reliable
```

### Framework Examples

**LangChain**:
```python
@adri_protected(data_param="customer_data")
def langchain_agent(customer_data):
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(customer_data)
```

**CrewAI**:
```python
@adri_protected(data_param="market_data") 
def crewai_analysis(market_data):
    crew = Crew(agents=[analyst], tasks=[task])
    return crew.kickoff()
```

**LlamaIndex**:
```python
@adri_protected(data_param="documents")
def llamaindex_rag(documents):
    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine()
```

---

## Installation Methods

### Method 1: pip Install (Recommended)

```bash
# Install from PyPI
pip install adri

# Install from GitHub  
pip install git+https://github.com/adri-standard/adri.git

# Install specific version
pip install adri==4.0.0
```

### Method 2: Install from Source

```bash
# Clone repository
git clone https://github.com/adri-standard/adri.git
cd adri

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir .

# Verify installation
RUN python -m adri.utils.verification

CMD ["python", "-m", "adri"]
```

Build and run:
```bash
docker build -t adri-validator .
docker run -it adri-validator
```

### Method 4: Air-Gapped Installation

For environments without internet access:

1. **Download wheel on connected machine:**
```bash
pip download adri-validator --no-deps -d ./offline_packages
pip download pandas pyyaml click pyarrow -d ./offline_packages
```

2. **Transfer to air-gapped system**

3. **Install from local files:**
```bash
pip install --no-index --find-links ./offline_packages adri-validator
```

---

## System Requirements

### Minimum Requirements
- **Python**: 3.10 or higher
- **Memory**: 512 MB RAM
- **Disk**: 100 MB free space
- **OS**: Linux, macOS, Windows

### Recommended Requirements
- **Python**: 3.11 or 3.12
- **Memory**: 2 GB RAM
- **Disk**: 500 MB free space
- **CPU**: 2+ cores for parallel processing

### Python Dependencies
```
pandas >= 1.5.0
pyyaml >= 6.0
click >= 8.0
pyarrow >= 14.0.0
```

---

## Quick Start

### 1. Install Package
```bash
pip install adri-validator
```

### 2. Verify Installation
```bash
# Run verification
python -m adri.utils.verification

# Or use CLI
adri verify
```

### 3. List Available Standards
```bash
adri list-standards
```

### 4. Basic Usage
```python
import pandas as pd
from adri.decorators import adri_protected

@adri_protected(standard="customer_data_standard")
def process_data(df):
    return df

# Your data
df = pd.DataFrame({
    'customer_id': [1, 2, 3],
    'email': ['a@b.com', 'c@d.com', 'e@f.com'],
    'age': [25, 30, 35]
})

# Process with validation
result = process_data(df)
```

---

## Advanced Installation

### Virtual Environment Setup

**Using venv:**
```bash
python -m venv adri_env
source adri_env/bin/activate  # On Windows: adri_env\Scripts\activate
pip install adri-validator
```

**Using conda:**
```bash
conda create -n adri_env python=3.11
conda activate adri_env
pip install adri-validator
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/adri-standard/adri.git
cd adri

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e .[dev,test]

# Run tests
pytest
```

### Enterprise Deployment

**1. Proxy Configuration:**
```bash
pip install --proxy http://proxy.company.com:8080 adri-validator
```

**2. Private PyPI Repository:**
```bash
pip install --index-url https://pypi.company.com/simple adri-validator
```

**3. Custom Standards Path:**
```bash
export ADRI_STANDARDS_PATH=/opt/company/adri-standards
python -m adri
```

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adri-validator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: adri-validator
  template:
    metadata:
      labels:
        app: adri-validator
    spec:
      containers:
      - name: adri-validator
        image: adri-validator:3.0.1
        env:
        - name: ADRI_CONFIG_PATH
          value: /config/adri-config.yaml
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: adri-config
```

---

## Configuration

### Configuration File

Create `adri-config.yaml`:
```yaml
adri:
  protection:
    min_score: 75.0
    failure_mode: "raise"  # raise | warn | log
    cache_duration: 300
    cache_enabled: true

  audit:
    enabled: true
    log_location: "./logs/adri_audit.jsonl"
    log_level: "INFO"
    include_data_samples: false
    max_log_size_mb: 100

  standards:
    path: null  # Uses bundled standards
    cache_enabled: true
```

### Environment Variables

```bash
# Custom configuration path
export ADRI_CONFIG_PATH=/etc/adri/config.yaml

# Custom standards directory
export ADRI_STANDARDS_PATH=/opt/adri/standards

# Environment name
export ADRI_ENV=PRODUCTION

# Enable audit logging
export ADRI_AUDIT_ENABLED=true

# Set log level
export ADRI_LOG_LEVEL=DEBUG
```

### Programmatic Configuration

```python
from adri.config.manager import ConfigManager

config = ConfigManager()
config.update_config({
    "min_score": 90.0,
    "failure_mode": "warn",
    "cache_duration": 600
}, section="protection")
```

---

## Verification

### Post-Installation Verification

**1. Run built-in verification:**
```bash
python -m adri.utils.verification
```

Expected output:
```
============================================================
ADRI VALIDATOR STANDALONE VERIFICATION
============================================================

1. Verifying Standalone Installation
----------------------------------------
   ✅ No external adri-standards dependency found
   ✅ 15 bundled standards available
   ✅ Using correct standards path: .../bundled
   ✅ Module adri.core.assessor loaded successfully
   ✅ Module adri.core.protection loaded successfully
   ✅ Module adri.core.audit_logger loaded successfully
   ✅ Module adri.config.manager loaded successfully
   ✅ Module adri.decorators.adri loaded successfully
   ℹ️  ADRI Validator version: 3.0.1

2. Checking System Compatibility
----------------------------------------
   Python: (3, 11, 0)
   Platform: Linux-5.10.0-x86_64
   Python Compatible: ✅
   Packages Compatible: ✅

3. Bundled Standards
----------------------------------------
   • agent_input_standard (v1.0.0)
   • agent_output_standard (v1.0.0)
   • customer_data_standard (v1.0.0)
   • financial_data_standard (v1.0.0)
   • healthcare_data_standard (v1.0.0)
   ... and 10 more

4. Verifying Audit Logging
----------------------------------------
   ✅ AuditLogger instantiated (enabled=False)
   ✅ VerodatLogger module available (optional)
   ✅ AuditLoggerCSV module available

============================================================
✅ ALL VERIFICATIONS PASSED - STANDALONE MODE CONFIRMED
============================================================
```

**2. Test basic functionality:**
```python
# test_installation.py
import pandas as pd
from adri.decorators import adri_protected

@adri_protected(standard="test_standard", min_score=50.0)
def test_function(df):
    return df

df = pd.DataFrame({'id': [1,2,3], 'value': [10,20,30]})
result = test_function(df)
print("✅ Installation verified successfully")
```

Run:
```bash
python test_installation.py
```

### Health Checks

**CLI health check:**
```bash
adri verify --verbose
```

**Programmatic health check:**
```python
from adri.utils.verification import run_full_verification

if run_full_verification(verbose=True):
    print("System healthy")
else:
    print("Issues detected")
```

---

## Troubleshooting

### Common Issues

#### 1. Import Error: Module not found
```
ImportError: No module named 'adri'
```
**Solution:**
- Verify installation: `pip list | grep adri`
- Reinstall: `pip install --force-reinstall adri-validator`
- Check Python path: `python -c "import sys; print(sys.path)"`

#### 2. Standards Not Found
```
StandardsDirectoryNotFoundError: Bundled standards directory not found
```
**Solution:**
- Verify package integrity: `pip show -f adri-validator`
- Check standards path: `python -c "from adri.standards.loader import StandardsLoader; print(StandardsLoader().standards_path)"`
- Reinstall package: `pip uninstall adri-validator && pip install adri-validator`

#### 3. Python Version Error
```
ERROR: Package 'adri-validator' requires a different Python: 3.9 not in '>=3.10'
```
**Solution:**
- Upgrade Python to 3.10 or higher
- Use pyenv or conda to manage Python versions

#### 4. Dependency Conflicts
```
ERROR: pip's dependency resolver does not currently take into account all the packages
```
**Solution:**
```bash
# Create clean environment
python -m venv clean_env
source clean_env/bin/activate
pip install --upgrade pip
pip install adri-validator
```

#### 5. Permission Denied
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages/adri'
```
**Solution:**
- Use user installation: `pip install --user adri-validator`
- Or use virtual environment (recommended)

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from adri.decorators import adri_protected
# Debug logs will now be visible
```

### Getting Help

1. **Check documentation:**
   - [API Reference](./API_REFERENCE.md)
   - [Architecture Guide](./STANDALONE_ARCHITECTURE.md)

2. **Run diagnostics:**
```bash
# System info
python -c "from adri.utils.verification import check_system_compatibility; print(check_system_compatibility())"

# List standards
python -c "from adri.standards.loader import list_bundled_standards; print(list_bundled_standards())"

# Check boundaries
python -c "from adri.core.boundary import validate_standalone_operation; print(validate_standalone_operation())"
```

3. **Report issues:**
   - GitHub Issues: https://github.com/adri-standard/adri/issues

---

## Updates and Maintenance

### Updating the Package

**Check current version:**
```bash
pip show adri-validator | grep Version
```

**Update to latest:**
```bash
pip install --upgrade adri-validator
```

**Update to specific version:**
```bash
pip install adri-validator==3.0.2
```

### Version Management

**Check for updates:**
```python
from adri.version import __version__
print(f"Current version: {__version__}")
# Check GitHub for latest releases
```

**Rollback if needed:**
```bash
pip uninstall adri-validator
pip install adri-validator==3.0.0  # Previous version
```

### Backup and Recovery

**Backup configuration:**
```bash
cp adri-config.yaml adri-config.yaml.backup
```

**Backup custom standards:**
```bash
tar czf custom_standards_backup.tar.gz $ADRI_STANDARDS_PATH
```

### Performance Optimization

**1. Enable caching:**
```yaml
adri:
  protection:
    cache_enabled: true
    cache_duration: 3600  # 1 hour
```

**2. Optimize for large datasets:**
```python
@adri_protected(
    standard="large_data_standard",
    cache_duration=7200,  # 2 hours
    batch_size=10000  # Process in batches
)
def process_large_data(df):
    return df
```

**3. Memory management:**
```python
from adri.standards.loader import StandardsLoader

# Clear cache periodically
loader = StandardsLoader()
loader.clear_cache()
```

### Monitoring

**Enable audit logging:**
```yaml
adri:
  audit:
    enabled: true
    log_location: "/var/log/adri/audit.jsonl"
```

**Monitor performance:**
```python
import time
from adri.decorators import adri_protected

@adri_protected(standard="test_standard")
def monitored_function(df):
    start = time.time()
    # Your processing
    elapsed = time.time() - start
    print(f"Processing took {elapsed:.2f}s")
    return df
```

---

## Security Considerations

### Best Practices

1. **Use virtual environments** to isolate dependencies
2. **Regular updates** to get security patches
3. **Audit logging** for compliance tracking
4. **Input validation** for all data sources
5. **Least privilege** for file system access

### Security Scanning

```bash
# Install security tools
pip install bandit safety

# Scan for vulnerabilities
bandit -r adri/
safety check
```

---

## Support Matrix

| Python Version | ADRI Version | Support Status |
|---------------|--------------|----------------|
| 3.12          | 3.0.1        | ✅ Supported   |
| 3.11          | 3.0.1        | ✅ Supported   |
| 3.10          | 3.0.1        | ✅ Supported   |
| 3.9           | 2.x          | ⚠️ Legacy      |
| 3.8           | 2.x          | ❌ Unsupported |

---

*Deployment Guide for ADRI Validator v3.0.1*
