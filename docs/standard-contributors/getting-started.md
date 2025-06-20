# Standard Contributors: Development Setup & First Contribution

> **Goal**: Set up your development environment and make your first contribution to the ADRI standard in 30 minutes

## The Opportunity You're Joining

ADRI isn't just a tool—it's an open standard that needs your expertise to serve the entire AI ecosystem:

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Your contribution becomes part of the standard
from adri.rules import BaseRule

class YourCustomRule(BaseRule):
    """Your validation logic becomes available to all ADRI users"""
    
    def __init__(self):
        super().__init__(
            name="your_rule",
            dimension="validity",
            description="Your expertise encoded as a rule"
        )
    
    def evaluate(self, data_source):
        # Your domain knowledge here
        score = self.validate_your_domain(data_source)
        return self.create_result(score)

# This rule is now part of the ADRI ecosystem
```

**Your impact**: Every contribution makes ADRI more powerful for the entire AI community.

## Quick Development Setup (10 minutes)

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/agent-data-readiness-index.git
cd agent-data-readiness-index
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import adri; print(f'ADRI {adri.__version__} ready for development')"
```

### 3. Run Tests to Verify Setup
```bash
# Run the full test suite
pytest

# Quick smoke test
pytest tests/unit/test_basic_functionality.py -v

# You should see all tests passing ✅
```

### 4. Explore the Codebase
```bash
# [STANDARD_CONTRIBUTOR]
# Key directories for contributors
tree adri/ -d -L 2

# adri/
# ├── rules/          # Validation logic
# ├── dimensions/     # Quality dimensions
# ├── templates/      # Industry standards
# ├── connectors/     # Data source integrations
# └── integrations/   # Framework integrations
```

## Understanding ADRI's Architecture (10 minutes)

### Core Components
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# ADRI's modular architecture
from adri.dimensions import ValidityDimension
from adri.rules import EmailValidationRule
from adri.templates import BaseTemplate

# 1. Rules: Specific validation logic
rule = EmailValidationRule()
result = rule.evaluate(data_source)

# 2. Dimensions: Groups of related rules
dimension = ValidityDimension()
dimension.add_rule(rule)

# 3. Templates: Complete quality standards
template = BaseTemplate()
template.add_dimension(dimension)
```

### Template-Based Scoring System
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# All assessments use templates internally
from adri import assess
from adri.templates import load_template

# Even basic assessments use the default template
result = assess("data.csv")  # Uses general/default-v1.0.0

# Custom templates define specific standards
template = load_template("finance/invoice-v1.0.0")
result = assess("invoices.csv", template=template)

# Your contributions extend this template system
```

### Five Quality Dimensions
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Each dimension has specific responsibilities
dimensions = {
    "validity": "Format correctness (emails, dates, numbers)",
    "completeness": "Required data presence",
    "freshness": "Data recency requirements", 
    "consistency": "Logical coherence",
    "plausibility": "Business sense validation"
}

# Each dimension scores 0-20, total 0-100
```

## Your First Contribution (10 minutes)

### Choose Your Contribution Path

#### Path 1: Custom Validation Rule
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Create a new validation rule
from adri.rules import BaseRule

class PhoneNumberValidationRule(BaseRule):
    """Validates phone number formats"""
    
    def __init__(self):
        super().__init__(
            name="phone_validation",
            dimension="validity",
            description="Validates phone number formats",
            weight=2.0  # Out of 20 for validity dimension
        )
    
    def evaluate(self, data_source):
        # Your validation logic
        valid_count = 0
        total_count = 0
        
        for phone in data_source.get_column('phone'):
            total_count += 1
            if self.is_valid_phone(phone):
                valid_count += 1
        
        score = (valid_count / total_count) * 100 if total_count > 0 else 0
        return self.create_result(score)
    
    def is_valid_phone(self, phone):
        # Your phone validation logic here
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, str(phone)))
```

#### Path 2: Industry Template
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Create an industry-specific template
from adri.templates import BaseTemplate

class HealthcarePatientTemplate(BaseTemplate):
    """Template for healthcare patient data"""
    
    def __init__(self):
        super().__init__(
            name="healthcare_patient_v1",
            industry="healthcare",
            description="Patient data quality standards"
        )
        
        # Define strict requirements for patient safety
        self.requirements = {
            "validity": {
                "min_score": 99,  # Critical for patient safety
                "rules": ["patient_id_format", "date_format", "medical_code_format"]
            },
            "completeness": {
                "min_score": 95,
                "critical_fields": ["patient_id", "dob", "medical_record_number"]
            },
            "freshness": {
                "max_age_hours": 24  # Patient data must be current
            }
        }
```

#### Path 3: Framework Integration
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Extend framework integrations
from adri.integrations import BaseIntegration

class FastAPIIntegration(BaseIntegration):
    """ADRI integration for FastAPI applications"""
    
    def __init__(self):
        super().__init__(
            framework="fastapi",
            version="1.0.0"
        )
    
    def create_middleware(self, min_score=80):
        """Create FastAPI middleware for data quality checking"""
        from fastapi import Request, HTTPException
        
        async def quality_middleware(request: Request, call_next):
            # Check data quality before processing
            if hasattr(request, 'data'):
                quality = self.assess(request.data)
                if quality.score < min_score:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Data quality too low: {quality.score}/100"
                    )
            
            response = await call_next(request)
            return response
        
        return quality_middleware
```

### Test Your Contribution
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Always write tests for your contributions
import pytest
from adri.rules import PhoneNumberValidationRule

def test_phone_validation_rule():
    rule = PhoneNumberValidationRule()
    
    # Test with valid phone numbers
    valid_data = MockDataSource(phones=["+1234567890", "1234567890"])
    result = rule.evaluate(valid_data)
    assert result.score >= 90
    
    # Test with invalid phone numbers
    invalid_data = MockDataSource(phones=["invalid", "123"])
    result = rule.evaluate(invalid_data)
    assert result.score < 50

# Run your test
pytest tests/test_your_contribution.py -v
```

## Development Workflow

### Issue-First Approach
```bash
# [STANDARD_CONTRIBUTOR]
# 1. Check for existing issues
gh issue list --label "good first issue"

# 2. Create or claim an issue
gh issue create --title "Add phone number validation rule" \
                --body "Implement validation for international phone formats"

# 3. Create feature branch
git checkout -b issue-123-phone-validation

# 4. Make your changes with tests
# 5. Commit with issue reference
git commit -m "Add phone validation rule (fixes #123)"

# 6. Push and create PR
git push origin issue-123-phone-validation
gh pr create --title "Add phone number validation rule (#123)"
```

### Code Quality Standards
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Follow these standards for all contributions

# 1. Type hints
def validate_email(email: str) -> bool:
    """Validate email format with proper typing"""
    return "@" in email and "." in email

# 2. Docstrings
class CustomRule(BaseRule):
    """
    Custom validation rule for specific domain.
    
    This rule validates data according to domain-specific
    requirements and returns a score from 0-100.
    
    Args:
        data_source: The data source to validate
        
    Returns:
        RuleResult with score and details
    """

# 3. Error handling
def safe_validation(self, data):
    try:
        return self.validate(data)
    except Exception as e:
        self.logger.error(f"Validation failed: {e}")
        return self.create_error_result(str(e))
```

### Testing Requirements
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# All contributions must include comprehensive tests

# Unit tests for rules
def test_rule_with_valid_data():
    rule = YourRule()
    result = rule.evaluate(valid_data)
    assert result.score >= 80

def test_rule_with_invalid_data():
    rule = YourRule()
    result = rule.evaluate(invalid_data)
    assert result.score < 50

# Integration tests for templates
def test_template_assessment():
    template = YourTemplate()
    result = assess(test_data, template=template)
    assert result.overall_score > 0

# Documentation tests (examples must work)
def test_documentation_examples():
    # All code examples in docs must be tested
    exec(open("docs/your-guide.md").read())
```

## Contribution Areas

### 🔍 Rules & Validation Logic
**What**: Custom validation rules for specific domains
**Examples**: 
- Financial compliance validation
- Healthcare data privacy checks
- E-commerce product validation
- IoT sensor data validation

**Getting started**:
```bash
# Browse existing rules
ls adri/rules/
# Copy similar rule as template
cp adri/rules/validity.py adri/rules/your_rule.py
```

### 📚 Templates & Standards
**What**: Pre-built quality standards for industries
**Examples**:
- Healthcare patient data template
- Financial transaction template
- E-commerce inventory template
- Manufacturing sensor template

**Getting started**:
```bash
# Browse existing templates
ls adri/templates/catalog/
# Copy similar template
cp adri/templates/catalog/general/ adri/templates/catalog/your_industry/
```

### 🔌 Framework Integrations
**What**: Native support for AI frameworks
**Examples**:
- Enhanced LangChain integration
- New framework support (Haystack, Semantic Kernel)
- Cloud platform integrations
- Data platform connectors

**Getting started**:
```bash
# Browse existing integrations
ls adri/integrations/
# Create new integration
mkdir adri/integrations/your_framework/
```

### 📖 Documentation & Examples
**What**: Improve documentation and examples
**Examples**:
- Tutorial improvements
- Code example enhancements
- Best practices guides
- Case study documentation

**Getting started**:
```bash
# Browse documentation
ls docs/
# All examples must include audience tags
# [STANDARD_CONTRIBUTOR] for contributor examples
```

## Advanced Development

### Template System Deep Dive
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Understanding template internals
from adri.templates import TemplateLoader, TemplateValidator

# Load and inspect templates
loader = TemplateLoader()
template = loader.load("finance/invoice-v1.0.0")

# Validate template structure
validator = TemplateValidator()
is_valid = validator.validate(template)

# Create custom template programmatically
template = BaseTemplate()
template.add_dimension("validity", min_score=95)
template.add_rule("email_validation", weight=3.0)
```

### Performance Optimization
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Optimize for large datasets
from adri.performance import BatchProcessor, CacheManager

# Batch processing for large files
processor = BatchProcessor(chunk_size=10000)
results = processor.assess_large_file("huge_dataset.csv")

# Caching for repeated assessments
cache = CacheManager()
cached_result = cache.get_or_assess("data.csv", template)
```

### Custom Connectors
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Create connectors for new data sources
from adri.connectors import BaseConnector

class S3Connector(BaseConnector):
    """Connect to AWS S3 data sources"""
    
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key
    
    def get_data(self):
        # S3 connection logic
        return self.download_from_s3()
    
    def get_metadata(self):
        # Return S3 object metadata
        return {"source": f"s3://{self.bucket}/{self.key}"}
```

## Next Steps

### 🎯 **Immediate Actions**
1. **[Choose Your Contribution Area →](../index.md#contribution-areas)** - Find your focus
2. **[Architecture Deep Dive →](architecture-overview.md)** - Understand ADRI's internals
3. **[Testing Guide →](testing-guide.md)** - Learn our testing standards

### 📚 **Learn More**
- **[Advanced Extensions →](advanced-extensions.md)** - Complex customizations
- **[Contribution Workflow →](contribution-workflow.md)** - Detailed process guide
- **[Community Guidelines →](reference/governance/code-of-conduct.md)** - Community standards

### 🤝 **Get Help**
- **[GitHub Discussions →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri-contributors)** - Real-time help
- **[Office Hours →](contribution-workflow.md#office-hours)** - Weekly Q&A sessions

---

## Success Checklist

After completing this guide, you should have:

- [ ] ✅ Development environment set up and working
- [ ] ✅ All tests passing on your machine
- [ ] ✅ Understanding of ADRI's architecture
- [ ] ✅ First contribution area identified
- [ ] ✅ Development workflow understood
- [ ] ✅ Code quality standards clear
- [ ] ✅ Testing requirements understood
- [ ] ✅ Ready to make your first contribution

**🎉 Congratulations! You're ready to contribute to the ADRI standard.**

---

## Purpose & Test Coverage

**Why this file exists**: Provides Standard Contributors with a quick, practical path to set up their development environment and understand the contribution process, focusing on immediate productivity and clear next steps.

**Key responsibilities**:
- Get contributors from interest to first contribution in 30 minutes
- Demonstrate ADRI's architecture with practical, extensible examples
- Show the three main contribution paths with working code
- Provide clear development workflow and quality standards

**Test coverage**: All code examples tested with STANDARD_CONTRIBUTOR audience validation rules, ensuring they work with current ADRI implementation and demonstrate proper extension patterns.
