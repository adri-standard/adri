# Frequently Asked Questions

Common questions about ADRI answered.

## Table of Contents

1. [What is ADRI?](#what-is-adri)
2. [Why use ADRI?](#why-use-adri)
3. [How does auto-generation work?](#how-does-auto-generation-work)
4. [What's the difference between block and warn modes?](#whats-the-difference-between-block-and-warn-modes)
5. [Can I customize standards?](#can-i-customize-standards)
6. [What frameworks does ADRI work with?](#what-frameworks-does-adri-work-with)
7. [Why is ADRI open source?](#why-is-adri-open-source)
8. [What's the difference between ADRI and ADRI Enterprise?](#whats-the-difference-between-adri-and-adri-enterprise)
9. [How do I contribute?](#how-do-i-contribute)
10. [Performance Questions](#performance-questions)
11. [Troubleshooting](#troubleshooting)

## What is ADRI?

**ADRI** (Agent Data Readiness Index) is the missing data layer for AI agents.

It's an open-source Python framework that protects AI agent workflows from bad data by automatically validating data quality. With a single decorator, ADRI:

- Auto-generates quality standards from good data
- Validates data across 5 dimensions (validity, completeness, consistency, accuracy, timeliness)
- Blocks or warns on quality failures
- Logs insights locally for debugging

**Key insight**: AI agents are powerful but fragile. One malformed field or missing value can crash your entire workflow. ADRI learns what good data looks like and enforces it automatically.

## Why use ADRI?

### Problem: Data Quality is the #1 Agent Killer

Traditional approaches to data validation are tedious and error-prone:
- Writing dozens of `if` statements
- Manually checking every field type
- Hoping you caught all edge cases
- Debugging mysterious agent failures

### Solution: One Decorator, Complete Protection

```python
@adri_protected(contract="data", data_param="data")
def process_customers(data):
    return results
```

**Benefits:**
1. **2-minute integration** - Add decorator, done
2. **Zero configuration** - Auto-learns from your data
3. **Framework agnostic** - Works with any Python function
4. **Developer-friendly** - Local logging, clear errors
5. **Production-ready** - Block bad data before it causes issues

## How does auto-generation work?

ADRI's auto-generation is magic that works like this:

### First Run with Good Data

```python
@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    return analyze(customers)

# Run with clean data
good_data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user@example.com", ...],
    "age": [25, 30, 35]
})

process_customers(good_data)  # ✅ Generates standard
```

### What ADRI Learns

ADRI analyzes your data and learns:

1. **Field names**: `id`, `email`, `age`
2. **Data types**: integer, string, integer
3. **Patterns**: Email format for `email` field
4. **Ranges**: Age between 25-35 (with buffer)
5. **Required fields**: All fields present = all required

### Standard Generation

Creates `ADRI/dev/contracts/process_customers_customers_standard.yaml`:

```yaml
standard:
  name: "process_customers_customers"
  version: "1.0.0"

  fields:
    id:
      type: integer
      required: true
      min_value: 1

    email:
      type: string
      required: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

    age:
      type: integer
      required: true
      min_value: 0
      max_value: 120
```

### Future Runs

All subsequent runs validate against this standard:

```python
bad_data = pd.DataFrame({
    "id": [None, 2, 3],  # Missing ID
    "email": ["invalid", ...],  # Bad email
    "age": [-5, 30, 35]  # Negative age
})

process_customers(bad_data)  # ❌ Raises exception
```

**Customize it**: Edit the YAML to tighten/loosen rules as needed.

## What's the difference between block and warn modes?

ADRI offers two guard modes:

### Block Mode (Default)

**Behavior**: Raises exception on quality failure

```python
@adri_protected(contract="data", data_param="data", on_failure="raise")
def strict_function(data):
    return results  # Won't execute if data is bad
```

**Use when:**
- Production environments
- Data quality is critical
- Bad data would cause errors
- You want to fail fast

**Output:**
```python
DataQualityException: Data quality too low (67.3/100, required: 80.0/100)
- Validity: 3 invalid types
- Completeness: 2 missing fields
```

### Warn Mode

**Behavior**: Logs warning, continues execution

```python
@adri_protected(contract="data", data_param="data", on_failure="warn")
def lenient_function(data):
    return results  # Executes even with bad data
```

**Use when:**
- Development and testing
- You want visibility without disruption
- Quality issues are acceptable
- Graceful degradation preferred

**Output:**
```
⚠️  WARNING: Data quality low (67.3/100)
⚠️  Executing despite quality issues (warn mode)
```

### Choosing the Right Mode

```python
import os

# Environment-based mode selection
MODE = "warn" if os.getenv("ENV") == "dev" else "block"

@adri_protected(data_param="data", mode=MODE)
def flexible_function(data):
    return results
```

## Can I customize standards?

**Yes!** Standards are human-readable YAML files you can edit.

### Location

Generated standards are saved to:
```
ADRI/dev/contracts/your_function_data_standard.yaml
```

### Customization Examples

**1. Tighten age range:**
```yaml
age:
  type: integer
  min_value: 18  # Was: 0
  max_value: 100  # Was: 120
```

**2. Add email validation:**
```yaml
email:
  type: string
  required: true
  pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  max_length: 255  # Added
```

**3. Add timeliness check:**
```yaml
signup_date:
  type: date
  required: true
  max_age_days: 365  # Must be within last year
```

**4. Add cross-field validation:**
```yaml
rules:
  - name: "End after start"
    expression: "end_date > start_date"
    severity: "critical"
```

### Version Standards

Bump version when making changes:

```yaml
standard:
  name: "customer_data"
  version: "2.0.0"  # Was: 1.0.0
  changelog:
    - "2.0.0: Added email max_length"
    - "1.0.0: Initial version"
```

## What frameworks does ADRI work with?

**All of them.** ADRI is framework-agnostic.

### Officially Tested

- ✅ LangChain
- ✅ LangGraph
- ✅ CrewAI
- ✅ AutoGen
- ✅ LlamaIndex
- ✅ Haystack
- ✅ Semantic Kernel
- ✅ Generic Python functions

### How It Works

ADRI protects **Python functions**, not frameworks:

```python
# Works with ANY framework
@adri_protected(contract="data", data_param="data")
def your_function(data):
    return framework_specific_logic(data)
```

### Examples

See [Framework Patterns](FRAMEWORK_PATTERNS.md) for integration patterns, or [examples/](../examples/) for working code.

## How does ADRI compare to alternatives?

ADRI is **purpose-built for AI agent data quality**. Here's how it compares to other validation tools:

### vs. Pydantic

**Pydantic**: Type validation and serialization for Python objects

```python
# Pydantic approach
from pydantic import BaseModel, EmailStr

class Customer(BaseModel):
    id: int
    email: EmailStr
    age: int

# Must define schema manually
# Must convert your data to Pydantic models
# No quality scoring or dimensions
```

**ADRI**: Automatic data contract generation and enforcement

```python
# ADRI approach
@adri_protected(contract="customer_data")
def process(data):
    return results

# Auto-learns schema from data
# Works with DataFrames, dicts, lists
# Five-dimensional quality scoring
```

**When to use Pydantic**: API request/response validation, configuration parsing  
**When to use ADRI**: AI agent data quality, batch data validation, quality scoring

**Can use both**: Pydantic for API layer, ADRI for agent data layer

### vs. Great Expectations

**Great Expectations**: Data quality testing framework

```python
# Great Expectations approach
import great_expectations as gx

# Must manually define expectations
suite = gx.ExpectationSuite("customers")
suite.add_expectation(gx.expectations.ExpectColumnToExist("id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique("id"))
# ... 20+ more expectations to define manually

# Run validation
results = context.run_validation(batch, suite)
```

**ADRI**: Auto-generated contracts with decorator pattern

```python
# ADRI approach
@adri_protected(contract="customers")
def process(data):
    return results

# Auto-generates all expectations from good data
# One decorator vs 20+ manual expectations
# Integrated quality scoring
```

**When to use Great Expectations**: Data pipeline testing, explicit expectations, Databricks/Spark workflows  
**When to use ADRI**: AI agent protection, auto-generated contracts, Python function validation

**Key difference**: Great Expectations requires manual expectation definition, ADRI auto-generates from data

### vs. Pandera

**Pandera**: DataFrame schema validation

```python
# Pandera approach
import pandera as pa

# Must manually define schema
schema = pa.DataFrameSchema({
    "id": pa.Column(int, nullable=False, unique=True),
    "email": pa.Column(str, pa.Check.str_matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")),
    "age": pa.Column(int, pa.Check.in_range(0, 120))
})

# Validate
validated_df = schema.validate(df)
```

**ADRI**: Contract-based validation with quality dimensions

```python
# ADRI approach
@adri_protected(contract="customers")
def process(data):
    return results

# Auto-learns schema + patterns + ranges
# Five-dimensional quality scoring
# Built-in audit logging
```

**When to use Pandera**: DataFrame-specific validation, statistical testing, data science workflows  
**When to use ADRI**: AI agents, quality scoring across dimensions, auto-generation

**Key difference**: Pandera focuses on DataFrames and statistical checks, ADRI focuses on agent data readiness and contracts

### vs. Cerberus / Marshmallow

**Cerberus/Marshmallow**: Dict/object validation

```python
# Cerberus/Marshmallow approach
schema = {
    'id': {'type': 'integer', 'required': True},
    'email': {'type': 'string', 'regex': '^[\w\.-]+@[\w\.-]+\.\w+$'}
}

# Must manually define every rule
# No quality scoring
# No auto-generation
```

**ADRI**: Data contract with automatic rule inference

**When to use Cerberus/Marshmallow**: Form validation, API input validation, configuration validation  
**When to use ADRI**: AI agent data, batch validation, quality assessment

### vs. JSON Schema

**JSON Schema**: JSON structure validation

**When to use JSON Schema**: API specification, JSON document validation  
**When to use ADRI**: AI agent data quality, multi-dimensional scoring, auto-generation

### Why ADRI is Different

**ADRI's Unique Value Proposition**:

1. **AI Agent Focus**: Built specifically for LLM/agent workflows where data quality is critical
2. **Data Contract Framing**: Aligns with modern data architecture (Data Mesh, Data Fabric)
3. **Auto-Generation**: Learns from your data vs manual schema definition
4. **Holistic Quality**: Five dimensions vs just schema validation
5. **Decorator Pattern**: Non-invasive integration vs validation logic throughout code
6. **Quality Scoring**: Quantitative scores (0-100) vs binary pass/fail
7. **Audit Trail**: Built-in logging for debugging and compliance
8. **Schema Validation**: Detects field name mismatches with auto-fix suggestions

### When to Use What

**Choose ADRI when:**
- ✅ Building AI agent workflows
- ✅ Need data quality scoring (not just pass/fail)
- ✅ Want auto-generated validation from good data
- ✅ Need data contract enforcement
- ✅ Working with batch data for agents
- ✅ Need audit trails for debugging

**Choose Pydantic when:**
- ✅ Validating API requests/responses
- ✅ Need serialization/deserialization
- ✅ Working with strongly-typed Python objects
- ✅ Configuration file parsing

**Choose Great Expectations when:**
- ✅ Testing data pipelines in Spark/Databricks
- ✅ Need explicit, documented expectations
- ✅ Pipeline quality monitoring
- ✅ Team prefers test-driven data development

**Choose Pandera when:**
- ✅ Working exclusively with DataFrames
- ✅ Need statistical hypothesis testing
- ✅ Data science/ML validation
- ✅ Prefer schema-as-code approach

**Can use together**: Many teams use Pydantic for APIs + ADRI for agent data + Great Expectations for pipelines

### The Data Contract Advantage

**What makes ADRI special** is positioning validation as **data contracts**:

- **Not just validation**: Executable agreements between data producers and consumers
- **Industry alignment**: Data Mesh, Data Fabric concepts
- **Business language**: "Contract" resonates with stakeholders vs "schema validation"
- **Modern architecture**: Fits naturally into contract-first data platforms

This framing makes ADRI relevant beyond just AI agents - it's the contract enforcement layer for modern data systems.

## Why is ADRI open source?

ADRI is open source because **data quality is a fundamental challenge** that the entire AI agent community should solve together.

### Our Philosophy

**Data quality is infrastructure, not competitive advantage.** Just like:
- **HTTP** is open (everyone benefits)
- **PostgreSQL** is open (database foundation)
- **Linux** is open (operating system base)

**ADRI should be open** (data quality foundation).

### Why Open Source Benefits You

1. **No vendor lock-in** - Use ADRI without contracts or negotiations
2. **Community-driven** - Improvements from engineers solving real problems
3. **Transparent** - See exactly how validation works
4. **Customizable** - Fork and modify for your specific needs
5. **Free** - No licensing fees, ever

### Why Open Source Benefits Everyone

1. **Standards adoption** - Open standards become industry standards
2. **Framework integration** - All frameworks can adopt ADRI
3. **Collective intelligence** - Best practices emerge from community
4. **Faster innovation** - More contributors = faster improvements

### The Business Model

Open source ADRI is **free forever**. We offer **ADRI Enterprise** for organizations that need:
- Advanced features (data lineage, compliance reporting)
- Enterprise support (SLA, dedicated team)
- Managed services (hosted validation, monitoring)

**Think**: Redis (open) vs Redis Enterprise, or Postgres (open) vs managed Postgres services.

### Our Commitment

- ✅ Core ADRI will always be free and open source
- ✅ No features removed to push Enterprise
- ✅ Community contributions always welcome
- ✅ Transparent roadmap and development

## What's the difference between ADRI and ADRI Enterprise?

ADRI offers two editions:

### ADRI (Open Source) - Free Forever

**Core Features:**
- ✅ `@adri_protected` decorator
- ✅ Auto-generation of standards
- ✅ Five-dimensional quality validation
- ✅ Block and warn modes
- ✅ Local logging
- ✅ CLI tools
- ✅ Framework integrations
- ✅ Community support

**Perfect for:**
- Individual developers
- Startups and small teams
- Development and testing
- Open source projects
- Learning and experimentation

### ADRI Enterprise - For Organizations

**Everything in Open Source, plus:**

**Advanced Features:**
- 📊 Data lineage tracking
- 🔐 Compliance reporting (SOC2, GDPR, etc.)
- 🔄 Replay engine for debugging
- 📈 Real-time monitoring dashboards
- 🎯 Custom validation rules engine
- 🔗 Integration with data platforms

**Enterprise Support:**
- 📞 Priority support with SLA
- 👥 Dedicated customer success team
- 🎓 Training and onboarding
- 📋 Professional services
- 🏢 Custom development

**Managed Services:**
- ☁️ Hosted validation service
- 📡 Centralized logging
- 👀 Multi-tenant management
- 🔐 Enterprise security features

**Perfect for:**
- Large enterprises
- Regulated industries (finance, healthcare)
- Production deployments at scale
- Teams needing guaranteed uptime
- Organizations requiring compliance

### Comparison Table

| Feature | Open Source | Enterprise |
|---------|-------------|------------|
| Core validation | ✅ | ✅ |
| Auto-generation | ✅ | ✅ |
| Local logging | ✅ | ✅ |
| CLI tools | ✅ | ✅ |
| Framework support | ✅ | ✅ |
| Data lineage | ❌ | ✅ |
| Compliance reporting | ❌ | ✅ |
| Replay engine | ❌ | ✅ |
| Priority support | ❌ | ✅ |
| SLA guarantees | ❌ | ✅ |
| Managed hosting | ❌ | ✅ |
| Custom development | ❌ | ✅ |

### Migration Path

Start with open source, upgrade when you need enterprise features:

1. **Start**: Use open source ADRI
2. **Grow**: Scale with open source
3. **Upgrade**: Move to Enterprise when you need advanced features
4. **Same code**: No code changes needed

## How do I contribute?

We welcome contributions! Here's how:

### Quick Start

1. **Star the repo**: [github.com/adri-standard/adri](https://github.com/adri-standard/adri)
2. **Read**: [CONTRIBUTING.md](../CONTRIBUTING.md)
3. **Join**: [GitHub Discussions](https://github.com/adri-standard/adri/discussions)

### Ways to Contribute

**Code:**
- Fix bugs
- Add features
- Improve performance
- Write tests

**Documentation:**
- Fix typos
- Add examples
- Improve guides
- Translate docs

**Community:**
- Answer questions
- Share use cases
- Write blog posts
- Give talks

**Testing:**
- Report bugs
- Test releases
- Provide feedback
- Share edge cases

### Development Setup

```bash
# Clone the repo
git clone https://github.com/adri-standard/adri.git
cd adri

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
flake8 adri/
black adri/
```

### Contribution Guidelines

- Follow the [Code of Conduct](../CODE_OF_CONDUCT.md)
- Write tests for new features
- Update documentation
- Keep commits atomic and clear
- Be respectful and constructive

## Performance Questions

### How fast is ADRI?

**Very fast.** Validation adds minimal overhead:

- **Simple datasets (<1K rows)**: <10ms overhead
- **Medium datasets (1K-100K rows)**: 10-100ms overhead
- **Large datasets (100K+ rows)**: 100ms-1s overhead

### Does ADRI slow down my agents?

**Barely.** For most use cases, ADRI's validation is negligible compared to:
- LLM API calls (100ms-10s)
- Database queries (10ms-1s)
- Network requests (50ms-5s)

**Example:**
```
Without ADRI: 2.5s total
With ADRI: 2.52s total (+20ms, or +0.8%)
```

### Can I disable ADRI in production?

You can, but **you shouldn't**. ADRI is designed for production use.

If you must:
```python
import os

# Skip validation in specific environments
SKIP_VALIDATION = os.getenv("SKIP_ADRI") == "true"

if not SKIP_VALIDATION:
    @adri_protected(contract="data", data_param="data")
    def process(data):
        return results
```

### How does ADRI handle large datasets?

ADRI samples large datasets for validation:

- **Sampling strategy**: Representative sampling
- **Default sample size**: 10,000 rows
- **Configurable**: Adjust sample size in config

```yaml
# ADRI/config.yaml
validation:
  sample_size: 5000  # For faster validation
  # sample_size: null  # Validate all rows
```

## Troubleshooting

### "Standard not found"

**Problem**: ADRI can't find the standard file.

**Solution**:
```bash
# Run once with good data to generate standard
python your_script.py

# Or generate manually
adri generate-standard good_data.csv --name your_standard
```

### "Quality score too low"

**Problem**: Data doesn't meet quality threshold.

**Solutions**:
1. **Fix the data** (recommended):
   ```bash
   # Check detailed report
   adri assess data.csv --standard my_standard --show-details
   ```

2. **Lower threshold** (if appropriate):
   ```python
   @adri_protected(data_param="data", min_score=70.0)
   ```

3. **Use warn mode** (for development):
   ```python
   @adri_protected(contract="data", data_param="data", on_failure="warn")
   ```

### "Import error"

**Problem**: Can't import ADRI.

**Solution**:
```bash
# Reinstall
pip install --upgrade adri

# Check installation
python -c "import adri; print(adri.__version__)"
```

### "Standard keeps regenerating"

**Problem**: Standard regenerates on every run.

**Cause**: Standard file not being saved or found.

**Solution**:
```bash
# Check if standard exists
ls ADRI/dev/contracts/

# Specify standard explicitly
@adri_protected(data_param="data", standard="my_standard")
```

### "Performance is slow"

**Problem**: Validation takes too long.

**Solutions**:
1. **Enable sampling**:
   ```yaml
   # ADRI/config.yaml
   validation:
     sample_size: 5000
   ```

2. **Cache standards**:
   ```python
   # Standards are cached by default
   # Ensure you're not regenerating on every run
   ```

3. **Profile your code**:
   ```bash
   python -m cProfile -s time your_script.py
   ```

## Still Have Questions?

- **Issues**: [GitHub Issues](https://github.com/adri-standard/adri/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adri-standard/adri/discussions)
- **Documentation**: [Full Documentation](https://github.com/adri-standard/adri)

---

**Can't find your question?** [Open a discussion](https://github.com/adri-standard/adri/discussions/new) and we'll help!
