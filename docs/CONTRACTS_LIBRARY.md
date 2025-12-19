# ADRI Standards Library

**Community-driven catalog of reusable data quality standards**

The ADRI Standards Library provides a curated collection of production-ready standards for common business domains, AI frameworks, and generic data patterns. Browse, use, and contribute standards to accelerate your data quality implementation.

## 📚 Browse Standards

### Business Domains (`adri/contracts/domains/`)

Real-world business use case standards ready for production use.

#### Customer Service Standard
**File**: `customer_service_standard.yaml`
**Use Case**: Support ticket tracking, customer interaction data
**Quality Threshold**: 85%

Validates customer service interaction records including:
- Ticket identifiers and customer IDs
- Support categories and priorities
- Response time tracking (first response, resolution)
- Customer satisfaction scores
- Agent assignment and status workflow

```python
from adri import adri_protected

@adri_protected(contract="customer_service_standard")
def process_support_tickets(tickets_df):
    return tickets_df
```

#### E-commerce Order Standard
**File**: `ecommerce_order_standard.yaml`
**Use Case**: Order processing, fulfillment pipelines
**Quality Threshold**: 90%

Validates e-commerce order records including:
- Order and customer identifiers
- Financial calculations (subtotal, tax, shipping)
- Complete shipping address
- Payment method and status
- Order lifecycle tracking

```python
from adri import adri_protected

@adri_protected(contract="ecommerce_order_standard")
def process_orders(orders_df):
    return orders_df
```

#### Financial Transaction Standard
**File**: `financial_transaction_standard.yaml`
**Use Case**: Payment processing, accounting systems
**Quality Threshold**: 95%

Validates financial transaction records including:
- Transaction and account identifiers
- Amount, currency (ISO 4217), balance tracking
- Transaction type and status
- Merchant information
- Authorization codes and processing metrics

```python
from adri import adri_protected

@adri_protected(contract="financial_transaction_standard")
def process_transactions(txn_df):
    return txn_df
```

#### Healthcare Patient Standard
**File**: `healthcare_patient_standard.yaml`
**Use Case**: EHR systems, patient management
**Quality Threshold**: 92%

Validates healthcare patient records including:
- Patient and medical record identifiers
- Demographics and contact information
- Complete address details
- Medical information (blood type, physician)
- Insurance provider and policy details

**Note**: Validates structure only. Additional HIPAA compliance measures (encryption, access control) required separately.

```python
from adri import adri_protected

@adri_protected(contract="healthcare_patient_standard")
def process_patient_records(patients_df):
    return patients_df
```

#### Marketing Campaign Standard
**File**: `marketing_campaign_standard.yaml`
**Use Case**: Campaign management, ROI tracking
**Quality Threshold**: 85%

Validates marketing campaign performance data including:
- Campaign identifiers and date ranges
- Budget and spend tracking
- Performance metrics (impressions, clicks, conversions)
- Calculated KPIs (CTR, conversion rate, ROAS)
- Targeting information

```python
from adri import adri_protected

@adri_protected(contract="marketing_campaign_standard")
def analyze_campaigns(campaigns_df):
    return campaigns_df
```

---

### AI Frameworks (`adri/contracts/frameworks/`)

Framework-specific standards for popular AI agent and RAG systems.

#### LangChain Chain Input Standard
**File**: `langchain_chain_input_standard.yaml`
**Framework**: LangChain 0.1.x+
**Quality Threshold**: 80%

Validates LangChain chain input data including:
- Chain type and user input
- Model configuration (temperature, max_tokens)
- Context and session tracking
- Memory settings
- User and session identifiers

```python
from adri import adri_protected

@adri_protected(contract="langchain_chain_input_standard")
def process_chain_inputs(inputs_df):
    return inputs_df
```

#### CrewAI Task Context Standard
**File**: `crewai_task_context_standard.yaml`
**Framework**: CrewAI 0.1.x+
**Quality Threshold**: 85%

Validates CrewAI task context for multi-agent workflows including:
- Task and crew identifiers
- Task description and expected output
- Agent assignment and role
- Dependencies and context
- Execution status and tools

```python
from adri import adri_protected

@adri_protected(contract="crewai_task_context_standard")
def process_crew_tasks(tasks_df):
    return tasks_df
```

#### LlamaIndex Document Standard
**File**: `llamaindex_document_standard.yaml`
**Framework**: LlamaIndex 0.9.x+
**Quality Threshold**: 85%

Validates LlamaIndex document data for RAG pipelines including:
- Document identifiers and content
- Source and metadata
- Chunking configuration
- Embedding model details
- Retrieval metadata (keywords, category)

```python
from adri import adri_protected

@adri_protected(contract="llamaindex_document_standard")
def process_documents(docs_df):
    return docs_df
```

#### AutoGen Message Standard
**File**: `autogen_message_standard.yaml`
**Framework**: AutoGen 0.2.x+
**Quality Threshold**: 80%

Validates AutoGen agent message data including:
- Message and conversation identifiers
- Message role and content
- Sender/receiver agent information
- Function calling details
- Token usage tracking

```python
from adri import adri_protected

@adri_protected(contract="autogen_message_standard")
def process_messages(messages_df):
    return messages_df
```

---

### Generic Templates (`adri/contracts/templates/`)

Customizable templates for common data patterns.

#### API Response Template
**File**: `api_response_template.yaml`
**Use Case**: API monitoring, integration testing
**Quality Threshold**: 85%

Generic template for REST API response structures including:
- Request identification
- HTTP status codes
- Response timing
- Endpoint and method information
- Response data or error details

**Customization**: Add domain-specific fields, update valid values, adjust error codes.

```python
from adri import adri_protected

@adri_protected(contract="api_response_template")
def process_api_responses(responses_df):
    return responses_df
```

#### Time Series Template
**File**: `time_series_template.yaml`
**Use Case**: Sensor data, metrics, monitoring
**Quality Threshold**: 85%

Generic template for time series data including:
- Timestamp and metric identification
- Value and unit tracking
- Data source information
- Quality indicators (score, confidence, anomaly detection)
- Aggregation metadata

**Customization**: Add domain-specific metrics, define custom units, configure source types.

```python
from adri import adri_protected

@adri_protected(contract="time_series_template")
def process_time_series(metrics_df):
    return metrics_df
```

#### Key-Value Template
**File**: `key_value_template.yaml`
**Use Case**: Configuration data, feature flags, settings
**Quality Threshold**: 85%

Generic template for key-value pair configurations including:
- Key-value with type information
- Namespace and categorization
- Version tracking
- Access control levels
- Environment-specific settings

**Customization**: Define custom namespaces, add categories, configure access levels.

```python
from adri import adri_protected

@adri_protected(contract="key_value_template")
def process_config(config_df):
    return config_df
```

#### Nested JSON Template
**File**: `nested_json_template.yaml`
**Use Case**: Complex configurations, tree structures
**Quality Threshold**: 80%

Generic template for nested/hierarchical JSON data including:
- Hierarchical record identification
- Parent-child relationships
- Depth and path tracking
- Child count consistency
- Node data and validation status

**Customization**: Define custom record types, add depth limits, configure validation status values.

```python
from adri import adri_protected

@adri_protected(contract="nested_json_template")
def process_nested(nested_df):
    return nested_df
```

---

## 🚀 Quick Start

### Using a Catalog Standard

1. **Browse** the catalog above to find a relevant standard
2. **Import** ADRI and use the standard by name:

```python
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_service_standard")
def process_tickets(data):
    # Your processing logic here
    return data

# ADRI automatically validates data against the standard
tickets_df = pd.read_csv("tickets.csv")
validated_tickets = process_tickets(tickets_df)
```

3. **Review** assessment logs to see quality scores and issues

### Customizing a Template

1. **Copy** a template standard from `adri/contracts/templates/`
2. **Modify** field requirements for your use case
3. **Save** to your project's standards directory
4. **Use** your custom standard by name

```bash
# Copy template
cp adri/contracts/templates/api_response_template.yaml \
   ADRI/dev/contracts/my_api_standard.yaml

# Edit as needed
vim ADRI/dev/contracts/my_api_standard.yaml

# Use in code
@adri_protected(contract="my_api_standard")
def process_my_api_data(data):
    return data
```

---

## 🤝 Contributing Standards

The ADRI Standards Library thrives on community contributions. Share your standards to help others!

### Contribution Process

1. **Create** a new standard following v5.0.0 format:
   ```yaml
   standards:
     id: your_standard_id
     name: Your Standard Name
     version: 1.0.0
     authority: ADRI Standards Catalog
     description: What this standard validates

   record_identification:
     primary_key_fields:
       - id_field
     strategy: primary_key_with_fallback

   requirements:
     overall_minimum: 85.0
     field_requirements:
       # Define your fields here
   ```

2. **Test** your standard thoroughly (see testing requirements below)

3. **Submit** a pull request to the [ADRI repository](https://github.com/adri-standard/adri)

### Testing Requirements

All contributed standards must include:

1. **Sample data** demonstrating valid records
2. **Unit tests** validating the standard works
3. **Documentation** explaining use case and fields

Example test structure:
```python
def test_your_standard():
    """Test your contributed standard."""
    @adri_protected(contract="your_standard_name")
    def process_data(data):
        return data

    # Create sample data
    data = pd.DataFrame([{
        "field1": "value1",
        "field2": 123,
        # ... all required fields
    }])

    result = process_data(data)
    assert result is not None
```

### Contribution Guidelines

**Good Candidates for Standards Library**:
- ✅ Common business domains (retail, healthcare, finance)
- ✅ Popular AI frameworks (LangChain, CrewAI, LlamaIndex)
- ✅ Generic patterns (event logs, audit trails, user activity)
- ✅ Industry-specific formats (HL7, FHIR, financial standards)

**Keep Out**:
- ❌ Company-specific internal standards
- ❌ Standards with proprietary/confidential fields
- ❌ Overly narrow use cases (single-app standards)

**Quality Checklist**:
- [ ] Clear, descriptive standard name and ID
- [ ] Complete field documentation (descriptions, types, constraints)
- [ ] Appropriate quality threshold (85-95% for production)
- [ ] Example usage code in metadata
- [ ] All tests passing
- [ ] No SQL reserved words in field names

---

## 📖 Standard Format Reference

### Required Sections

All standards must include these sections:

```yaml
standards:
  id: unique_identifier
  name: Human Readable Name
  version: 1.0.0
  authority: ADRI Standards Catalog
  description: What this validates

record_identification:
  primary_key_fields: [id_field]
  strategy: primary_key_with_fallback

requirements:
  overall_minimum: 85.0
  field_requirements:
    field_name:
      type: string|integer|float|boolean|date
      nullable: true|false
      description: Field purpose

  dimension_requirements:
    validity:
      minimum_score: 20.0
      weight: 1.0
    completeness:
      minimum_score: 20.0
      weight: 1.0
    consistency:
      minimum_score: 20.0
      weight: 1.0
    freshness:
      minimum_score: 15.0
      weight: 1.0
    plausibility:
      minimum_score: 15.0
      weight: 1.0

metadata:
  purpose: Why this standard exists
  usage: How to use it
  created_by: ADRI Standards Catalog
  created_date: YYYY-MM-DD
  tags: [tag1, tag2]
```

### Field Validation Rules

Common field validation patterns:

```yaml
# String with pattern
field_name:
  type: string
  nullable: false
  pattern: '^PREFIX-\d{6}$'
  description: ID with PREFIX-######

# Enum values
status:
  type: string
  nullable: false
  valid_values: [Active, Inactive, Pending]

# Numeric range
score:
  type: float
  nullable: false
  min_value: 0.0
  max_value: 100.0

# Date format
date_field:
  type: string
  nullable: false
  pattern: '^\d{4}-\d{2}-\d{2}$'
```

---

## 🔍 Discovery and SEO

Standards in the catalog are optimized for discovery:

**Search Engine Visibility**:
- Standards are GitHub-indexed for search discovery
- Tags enable category-based search
- Clear naming conventions for findability

**Example Searches**:
- "customer service data standard" → finds `customer_service_standard.yaml`
- "langchain validation" → finds `langchain_chain_input_standard.yaml`
- "financial transaction quality" → finds `financial_transaction_standard.yaml`

---

## 📊 Statistics

**Current Library Size**:
- **5** Domain Standards (business use cases)
- **4** Framework Standards (AI/ML frameworks)
- **4** Template Standards (generic patterns)
- **13** Total Standards

**Test Coverage**: 29 passing tests validating all standards

**Community**:
- Standards are open source (Apache 2.0)
- Community contributions welcome
- Used in production by ADRI users worldwide

---

## 🆘 Support

**Questions?**
- [GitHub Discussions](https://github.com/adri-standard/adri/discussions)
- [Issue Tracker](https://github.com/adri-standard/adri/issues)

**Want to Contribute?**
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines
- Start with template standards for easier contribution
- Join the community to discuss new standards

---

## 📄 License

All standards in the ADRI Standards Library are licensed under Apache 2.0.
See [LICENSE](../LICENSE) for full details.
