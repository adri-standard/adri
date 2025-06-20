# ADRI Examples

> **All Audiences**: Real-world examples of using ADRI for data quality assessment and agent protection

## Overview

This section provides practical examples of using ADRI across different use cases and audiences. Each example includes complete code, sample data, and step-by-step explanations.

## Quick Navigation

### 🎯 **By Audience**
- [AI Builders](#ai-builders) - Protect agents with quality gates
- [Data Providers](#data-providers) - Assess and improve data quality
- [Standard Contributors](#standard-contributors) - Extend ADRI functionality

### 🏭 **By Industry**
- [By Industry](#by-industry) - Industry-specific templates and patterns

### 🔧 **By Use Case**
- [Basic Assessment](#basic-assessment) - Simple quality checks
- [Advanced Patterns](#advanced-patterns) - Complex workflows
- [Integration Examples](#integration-examples) - Framework integration

---

## AI Builders

**Focus**: Protecting AI agents from bad data with quality gates and guards

### 🛡️ **Guard Implementation Examples**
- **[Basic Guard Setup →](ai-builders/basic-guard.md)** - Simple quality gate for any agent
- **[Framework Integration →](ai-builders/framework-integration.md)** - LangChain, CrewAI, DSPy examples
- **[Production Guards →](ai-builders/production-guards.md)** - Enterprise-ready quality gates

### 🤖 **Agent Protection Patterns**
- **[Invoice Processing Agent →](ai-builders/invoice-agent.md)** - Financial data validation
- **[Status Auditor Agent →](ai-builders/status-auditor.md)** - System monitoring with quality checks
- **[Customer Service Agent →](ai-builders/customer-service-agent.md)** - CRM data validation

### 📊 **Quality Monitoring**
- **[Real-time Monitoring →](ai-builders/real-time-monitoring.md)** - Track data quality over time
- **[Alert Systems →](ai-builders/alert-systems.md)** - Notify when quality drops
- **[Quality Dashboards →](ai-builders/quality-dashboards.md)** - Visualize agent data health

---

## Data Providers

**Focus**: Assessing and improving data quality to make it AI-ready

### 📈 **Assessment Examples**
- **[Basic Assessment →](data-providers/basic-assessment.md)** - Quick quality check
- **[Discovery Mode →](data-providers/discovery-mode.md)** - Explore data quality issues
- **[Validation Mode →](data-providers/validation-mode.md)** - Verify compliance with standards

### 🔧 **Improvement Strategies**
- **[Completeness Improvement →](data-providers/completeness-improvement.md)** - Fix missing data
- **[Validity Enhancement →](data-providers/validity-enhancement.md)** - Standardize formats
- **[Consistency Fixes →](data-providers/consistency-fixes.md)** - Resolve contradictions

### 📋 **Metadata and Documentation**
- **[Metadata Generation →](data-providers/metadata-generation.md)** - Auto-generate quality metadata
- **[Quality Documentation →](data-providers/quality-documentation.md)** - Document data characteristics
- **[Certification Process →](data-providers/certification-process.md)** - Prove AI-readiness

---

## Standard Contributors

**Focus**: Extending ADRI with custom rules, dimensions, and connectors

### 🔧 **Custom Rules**
- **[Business Email Rule →](standard-contributors/business-email-rule.md)** - Domain-specific validation
- **[Revenue Logic Rule →](standard-contributors/revenue-logic-rule.md)** - Business logic validation
- **[Duplicate Detection Rule →](standard-contributors/duplicate-detection-rule.md)** - Advanced deduplication

### 📐 **Custom Dimensions**
- **[Security Dimension →](standard-contributors/security-dimension.md)** - Data security assessment
- **[Privacy Dimension →](standard-contributors/privacy-dimension.md)** - Privacy compliance checking
- **[Performance Dimension →](standard-contributors/performance-dimension.md)** - Query performance impact

### 🔌 **Custom Connectors**
- **[MongoDB Connector →](standard-contributors/mongodb-connector.md)** - NoSQL database support
- **[API Connector →](standard-contributors/api-connector.md)** - REST API data sources
- **[Streaming Connector →](standard-contributors/streaming-connector.md)** - Real-time data streams

### 📋 **Template Development**
- **[Industry Template →](standard-contributors/industry-template.md)** - Create industry standards
- **[Template Testing →](standard-contributors/template-testing.md)** - Validate template compliance
- **[Template Documentation →](standard-contributors/template-documentation.md)** - Document template usage

---

## By Industry

**Focus**: Industry-specific examples and templates

### 🏥 **Healthcare**
- **[Patient Data Assessment →](by-industry/healthcare/patient-data.md)** - HIPAA-compliant quality checks
- **[Medical Records Template →](by-industry/healthcare/medical-records.md)** - Healthcare data standards
- **[Clinical Trial Data →](by-industry/healthcare/clinical-trials.md)** - Research data validation

### 💰 **Financial Services**
- **[Transaction Data →](by-industry/financial/transactions.md)** - Financial transaction validation
- **[Customer KYC Data →](by-industry/financial/kyc-data.md)** - Know Your Customer compliance
- **[Risk Assessment Data →](by-industry/financial/risk-assessment.md)** - Risk modeling data quality

### 🛒 **Retail & E-commerce**
- **[Product Catalog →](by-industry/retail/product-catalog.md)** - Product data standardization
- **[Customer Analytics →](by-industry/retail/customer-analytics.md)** - Customer behavior data
- **[Inventory Management →](by-industry/retail/inventory.md)** - Supply chain data quality

### 🚚 **Logistics & Supply Chain**
- **[Shipment Tracking →](by-industry/logistics/shipment-tracking.md)** - Logistics data validation
- **[Supplier Data →](by-industry/logistics/supplier-data.md)** - Vendor information quality
- **[Route Optimization →](by-industry/logistics/route-optimization.md)** - Transportation data

---

## Basic Assessment

**Quick Start Examples**: Simple quality checks for common scenarios

### 📊 **Single Dataset Assessment**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import DataSourceAssessor
from adri.connectors import FileConnector

# Quick assessment of any CSV file
connector = FileConnector("customer_data.csv")
assessor = DataSourceAssessor(connector)
result = assessor.assess()

print(f"Overall ADRI Score: {result.overall_score}/100")
for dimension, score in result.dimension_scores.items():
    print(f"{dimension}: {score}/20")
```

### 🎯 **Template-Based Assessment**
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri import DataSourceAssessor
from adri.templates import TemplateLoader

# Assess against industry standard
template = TemplateLoader.load("healthcare-patient-v1")
assessor = DataSourceAssessor(connector, template=template)
result = assessor.assess()

print(f"Compliance Score: {result.compliance_score}%")
```

### 🛡️ **Guard Protection**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=80)
def process_customer_data(data):
    # Your agent logic here - only runs if data quality >= 80
    return analyze_customer_behavior(data)

# Automatically protected from bad data
result = process_customer_data("customer_data.csv")
```

---

## Advanced Patterns

**Complex Workflows**: Enterprise-ready patterns and architectures

### 🏭 **Multi-Source Assessment**
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri import MultiSourceAssessor

# Assess multiple related datasets
assessor = MultiSourceAssessor([
    ("customers", "customers.csv"),
    ("orders", "orders.csv"),
    ("products", "products.csv")
])

results = assessor.assess_all()
for source, result in results.items():
    print(f"{source}: {result.overall_score}/100")
```

### 🔄 **Real-time Monitoring**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri.monitoring import QualityMonitor

# Monitor data quality in production
monitor = QualityMonitor(
    data_source="production_db",
    check_interval="5m",
    alert_threshold=70
)

monitor.start()  # Continuous quality monitoring
```

### 📈 **Quality Improvement Pipeline**
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri.improvement import QualityPipeline

# Automated quality improvement
pipeline = QualityPipeline([
    "fix_missing_values",
    "standardize_formats", 
    "validate_business_rules",
    "generate_metadata"
])

improved_data = pipeline.process("raw_data.csv")
```

---

## Integration Examples

**Framework Integration**: Using ADRI with popular AI frameworks

### 🦜 **LangChain Integration**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from langchain.agents import Agent
from adri.integrations.langchain import ADRIDataLoader

# LangChain agent with quality-assured data
loader = ADRIDataLoader(min_score=85)
agent = Agent(
    tools=[...],
    data_loader=loader
)

# Agent automatically gets high-quality data
response = agent.run("Analyze customer trends")
```

### 👥 **CrewAI Integration**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from crewai import Crew, Agent
from adri.integrations.crewai import ADRIDataValidator

# CrewAI with data quality validation
validator = ADRIDataValidator(template="customer-analytics-v1")

crew = Crew(
    agents=[...],
    data_validator=validator
)

# Crew only processes quality-assured data
result = crew.kickoff()
```

### 🧠 **DSPy Integration**
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
import dspy
from adri.integrations.dspy import ADRISignature

# DSPy with quality-aware signatures
class QualityAwareAnalysis(ADRISignature):
    data = dspy.InputField(min_adri_score=80)
    analysis = dspy.OutputField()

# Automatically validates input data quality
analyzer = dspy.Predict(QualityAwareAnalysis)
```

---

## Sample Data

All examples include sample datasets for testing:

### 📁 **Available Datasets**
- **Customer Data** (`customer_data.csv`) - Basic customer information
- **Transaction Data** (`transactions.csv`) - Financial transaction records
- **Product Catalog** (`products.csv`) - E-commerce product data
- **Patient Records** (`patients.csv`) - Healthcare data (anonymized)
- **Shipment Data** (`shipments.csv`) - Logistics tracking data

### 🔧 **Data Generation Tools**
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.testing import DataGenerator

# Generate test data for any template
generator = DataGenerator("healthcare-patient-v1")
test_data = generator.create_dataset(
    rows=1000,
    quality_level="high"  # high, medium, low
)
```

---

## Running Examples

### 📦 **Prerequisites**
```bash
# Install ADRI
pip install adri

# Clone examples repository
git clone https://github.com/adri-ai/adri.git
cd agent-data-readiness-index/docs/examples
```

### 🚀 **Quick Start**
```bash
# Run basic assessment example
python ai-builders/basic-guard.py

# Run data provider assessment
python data-providers/basic-assessment.py

# Run custom rule example
python standard-contributors/business-email-rule.py
```

### 🧪 **Testing Examples**
```bash
# Run all example tests
python -m pytest examples/

# Test specific audience examples
python -m pytest examples/ai-builders/
python -m pytest examples/data-providers/
python -m pytest examples/standard-contributors/
```

---

## Contributing Examples

### 📝 **Example Guidelines**
1. **Clear Purpose**: Each example solves a specific problem
2. **Complete Code**: Include all necessary imports and setup
3. **Sample Data**: Provide realistic test data
4. **Documentation**: Explain what the example demonstrates
5. **Testing**: Include test cases for the example

### 🎯 **Example Template**
```python
<!-- audience: ai-builders -->
"""
Example: [Brief Description]

Audience: [AI_BUILDER|DATA_PROVIDER|STANDARD_CONTRIBUTOR]
Use Case: [Specific problem this solves]
Complexity: [Basic|Intermediate|Advanced]

This example demonstrates how to [specific goal].
"""

# [AUDIENCE_TAG]
import adri
# ... rest of example code

if __name__ == "__main__":
    # Example execution
    pass
```

### 🤝 **Submitting Examples**
1. Create example following the template
2. Add to appropriate audience directory
3. Include sample data if needed
4. Add tests for the example
5. Update this index file
6. Submit pull request

---

## Next Steps

### 📚 **Learn More**
- **[AI Builders Guide →](../ai-builders/)** - Complete agent protection workflow
- **[Data Providers Guide →](../data-providers/)** - Comprehensive quality improvement
- **[Standard Contributors Guide →](../standard-contributors/)** - Extend ADRI functionality

### 🛠️ **Get Started**
- **[5-Minute Quickstart →](ai-builders/getting-started.md)** - Protect your first agent
- **[Data Assessment →](data-providers/getting-started.md)** - Check your data quality
- **[Contribution Setup →](standard-contributors/getting-started.md)** - Start contributing

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help
- **[Issue Tracker →](https://github.com/adri-ai/adri/issues)** - Report bugs

---

## Purpose & Test Coverage

**Why this file exists**: Provides organized access to practical ADRI examples across all audiences and use cases, enabling users to quickly find relevant implementation patterns.

**Key responsibilities**:
- Organize examples by audience and use case
- Provide clear navigation to relevant examples
- Include quick-start code snippets for common patterns
- Guide users to appropriate examples based on their needs
- Maintain comprehensive example catalog

**Test coverage**: All example code snippets tested with appropriate audience validation rules, ensuring examples work correctly for their intended audiences.
