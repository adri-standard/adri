# ADRI Template Catalog

This directory contains **production-ready** templates that have passed rigorous test-driven development.

## 📋 Available Templates

### Financial
- (Coming soon via TDD process)

### Healthcare  
- (Coming soon via TDD process)

### Retail
- (Coming soon via TDD process)

### General
- `examples/simple-template.yaml` - Basic template structure
- `examples/advanced-template.yaml` - Complex template with all features

## 🚀 Using Templates

```python
from adri import DataSourceAssessor

# Assess data using a template
assessor = DataSourceAssessor()
result = assessor.assess(
    data_source="your_data.csv",
    template="financial/invoice-processing-v1.0.0"
)
```

## 🧪 Template Development Process

**All templates are created using Test-Driven Development (TDD)**

1. **Tests First**: Define success criteria in `../development/tests/`
2. **Implementation**: Create template to pass tests
3. **Validation**: Test with 5+ real datasets
4. **Production**: Move to this catalog when ready

See [TEMPLATE_TDD_GUIDE.md](/docs/TEMPLATE_TDD_GUIDE.md) for the complete process.

## 📁 Directory Structure

```
catalog/
├── README.md              # This file
├── TEMPLATE_CHECKLIST.md  # Quality checklist
├── _template-starter.yaml # Template for new templates
├── examples/              # Example templates
├── financial/             # Financial industry templates
├── healthcare/            # Healthcare industry templates
├── retail/                # Retail industry templates
└── general/               # Cross-industry templates
```

## ✅ Quality Standards

Every template in this catalog:
- Passes all TDD tests
- Validated with real data
- Peer reviewed
- Documentation complete
- Production proven

## 🔄 Contributing Templates

Want to contribute a template? Follow the TDD process:

1. Write tests in `../development/tests/test_your_template.py`
2. Run `python3 scripts/template_tdd_runner.py test your_template`
3. Create template until all tests pass
4. Submit PR when ready

See [CONTRIBUTING_TEMPLATES.md](/docs/CONTRIBUTING_TEMPLATES.md) for details.

## 📊 Template Maturity Levels

| Level | Description | Requirements |
|-------|-------------|--------------|
| 🟢 **Production** | Battle-tested in production | 100+ successful assessments |
| 🟡 **Stable** | Ready for production use | All tests pass, 5+ validations |
| 🔴 **Development** | Under active development | In ../development/ directory |

## 🎯 Coming Soon

Based on community demand:
- Invoice Processing (in development)
- CRM Opportunities 
- Inventory Management
- Patient Records
- Support Tickets

Track progress: `python3 scripts/template_tdd_runner.py report`
