# Frequently Asked Questions

## General Questions

### What is the Agent Data Readiness Index?
The Agent Data Readiness Index (ADRI) is an open-source framework for evaluating how well data sources communicate their quality attributes to AI agents. It focuses on addressing the "data blindness" problem that uniquely affects agentic AI systems.

### Why is it called an "Index"?
The name "Agent Data Readiness Index" was carefully chosen to reflect the framework's core positioning as a **measurement tool** rather than a certification or guard system. Like a thermometer measures temperature, ADRI provides consistent, transparent measurement of data reliability that different agents can interpret based on their specific needs.

The "Index" terminology signals that:
- It's a standardized measurement scale (0-100)
- Different agents can set different thresholds based on their requirements (e.g., a financial trading agent might need 95+ while a content recommendation agent might work fine with 70)
- It provides objective measurement rather than subjective judgment
- All stakeholders use the same "thermometer" to measure and communicate about data reliability

This positioning enables:
- **Engineers** to say: "Set ADRI threshold to 85"
- **Data Suppliers** to say: "Our data has ADRI score of 92"
- **Organizations** to say: "Require ADRI > 80 for production"

The primary requirement is that the standards are known and consistent, allowing each use case to determine what level of data reliability is appropriate for their specific needs.

### How is this different from other data quality tools?
Most data quality tools focus on measuring and improving the intrinsic quality of data. ADRI specifically focuses on whether quality attributes are explicitly communicated to agents in a way they can understand and act upon. This addresses the unique challenge of agentic systems that make dynamic decisions based on data.

### Is ADRI a protocol or a tool?

ADRI is both - it's a **protocol for data-agent communication** AND **tools to implement that protocol**.

**The Protocol**: ADRI defines a standardized way for data sources to communicate their reliability characteristics to AI agents through companion metadata files. This creates a common language between data providers and AI systems.

**The Tools**: ADRI provides assessment frameworks, scoring mechanisms, and guard functions to evaluate data quality and verify protocol compliance.

Think of it like HTTP:
- HTTP is a protocol for how web servers and browsers communicate
- Web servers and browsers are tools that implement the protocol
- Similarly, ADRI defines how data sources communicate quality to agents, plus provides tools to enable this communication

This dual nature is what enables the vision of source-agnostic AI workflows - any data source that "speaks ADRI" can work with any agent that "understands ADRI."

## The Gap ADRI Fills

### What specific problem does ADRI solve that other tools don't?

ADRI addresses the **"last-mile data quality problem"** for AI agents - the critical gap between having "good data" and having "agent-ready data."

**The Gap Illustrated:**
```
Traditional Pipeline:
Data Source → [Great Expectations] → Clean Data → ❌ AI Agent Crashes

With ADRI:
Data Source → [Great Expectations] → Clean Data → [ADRI Guard] → ✅ Safe Agent Execution
```

Traditional data quality tools ensure data is technically correct. ADRI ensures data is **safe and understandable for autonomous agents** to consume.

### Why can't I just use Great Expectations/Deequ/Soda for my agents?

These tools excel at data validation but miss critical agent-specific concerns:

| Traditional Tools | ADRI |
|---|---|
| "Email field is valid format" | "Email field is valid AND agent knows how fresh it is" |
| "No nulls in customer_id" | "No nulls AND agent understands what missing data means" |
| "Prices are within range" | "Prices are plausible AND agent can verify when they were last updated" |
| Alert humans about issues | Prevent agents from acting on bad data |

**Real Example:**
- **Great Expectations**: "✅ All inventory counts are positive integers"
- **ADRI**: "❌ Inventory data is 72 hours old - unsafe for ordering decisions"

Your agent would happily process the "valid" data and order $127,000 of unnecessary inventory.

### What about ML monitoring tools like Evidently or WhyLabs?

ML monitoring tools are **reactive** - they tell you what went wrong after deployment. ADRI is **preventive** - it stops agents from consuming bad data in the first place.

```python
# ML Monitoring Approach
agent.process(data)  # Executes regardless
monitor.alert("Data drift detected!")  # Too late, damage done

# ADRI Approach
@adri_guard(min_score=80)
def agent_process(data):  # Never executes if data quality < 80
    return agent.process(data)
```

### Why not just build custom validation?

Many teams do, but this approach doesn't scale:

**Custom Validation Problems:**
- Every team reinvents the wheel
- No standard way to communicate requirements
- Hard to maintain across multiple agents
- No common language between data and AI teams

**ADRI Solution:**
- Standardized framework and scoring
- Reusable templates (e.g., "Production-v1.0.0")
- Common vocabulary for all stakeholders
- Maintained by community

### What about agent observability tools like LangSmith?

Agent observability tools monitor **agent behavior**, not **input data quality**. They're complementary:

```
Data → [ADRI: Prevent bad data] → Agent → [LangSmith: Monitor behavior] → Output
        ↑                                    ↑
        Preventive                           Reactive
```

### How does ADRI fit into the modern AI stack?

ADRI fills a critical gap in the AI infrastructure stack:

**Current Stack (with gap):**
1. Data Infrastructure (Snowflake, Databricks)
2. Data Quality (Great Expectations, Monte Carlo)
3. **❌ GAP: Agent-specific data readiness**
4. Agent Frameworks (LangChain, CrewAI)
5. Agent Monitoring (LangSmith, Helicone)

**Complete Stack (with ADRI):**
1. Data Infrastructure
2. Data Quality
3. **✅ ADRI: Agent Data Readiness**
4. Agent Frameworks
5. Agent Monitoring

### What makes ADRI uniquely suited for agents?

ADRI is built specifically for how agents fail:

**Agent-Specific Features:**
1. **Five dimensions chosen for agent reliability** - not general data quality
2. **Guard decorators** - Prevent execution, don't just alert
3. **Freshness as first-class citizen** - Critical for agent decisions
4. **Plausibility checks** - Agents can't use common sense
5. **Contract-based approach** - Enables source-agnostic agent development

### Can you show me a concrete before/after scenario?

**Before ADRI:**
```python
# Monday: Deploy customer service agent
result = agent.analyze_customer_data(data)
# Works great in testing!

# Tuesday: Production disaster
result = agent.analyze_customer_data(data)
# Agent sends apology emails to all customers because 
# data included test accounts with "complaint" status
# Cost: Brand damage, customer confusion
```

**After ADRI:**
```python
@adri_guard(min_score=85)
def analyze_customer_data(data):
    return agent.analyze_customer_data(data)

# ADRI Output: "Score 67/100 - Plausibility check failed: 
# 95% of customers marked as 'complaint' status (expected < 5%)"
# Result: Agent blocked, crisis averted
```

### Who should use ADRI?
ADRI is designed for AI engineers, ML operations teams, and data engineers who are building or deploying agentic AI systems, especially in enterprise or regulated environments. It's particularly valuable for teams that have experienced reliability issues with their agents or are facing governance challenges.

### Is this only for large enterprises?
No. While ADRI addresses challenges that are often most acute in enterprise environments, the framework is valuable for any team building agentic systems where reliability matters. The open-source toolkit can be used by organizations of all sizes.

## Technical Questions

### What data sources can ADRI evaluate?
ADRI is designed to be extensible. Built-in connectors support:
- Files (CSV, JSON)
- Databases (via SQLAlchemy - requires `adri[database]`)
- APIs (via basic HTTP requests - requires `adri[api]`)

The framework allows adding connectors for other sources like document repositories, knowledge bases, vector stores, internal tools, etc.

### Does ADRI require access to my actual data?
ADRI primarily analyzes metadata and structural properties of your data sources. While having sample data improves the assessment accuracy for some dimensions (like Plausibility), the tool doesn't necessarily need access to sensitive row-level information to provide valuable insights, especially for dimensions like Freshness or Validity based on schema/metadata. Connector implementations determine the exact access needed.

### How long does an assessment take?
This varies based on the data source size, complexity, and the specific connector implementation. A basic assessment of a file or API metadata might be quick (minutes), while assessing a large database table requiring data sampling could take longer.

### Can I customize the assessment criteria?
Yes, ADRI is designed to be customizable. You can:
- Select which dimensions to assess.
- Adjust the weightings of different dimensions in configuration.
- Define custom thresholds for scoring bands.
- Add custom checks specific to your domain via scripts.

*(Note: For contributing results to the public Community Catalog, adherence to the standard methodology and scoring is expected.)*

## Multi-Dataset Questions

### Can ADRI assess relationships between multiple datasets?
**A**: No, ADRI focuses exclusively on individual dataset quality. This is by design - it allows us to create universal standards that work across industries. For multi-dataset validation, use ADRI to ensure each dataset meets quality standards, then use your data platform to validate relationships.

### Why doesn't ADRI support data model assessment?
**A**: Data models are highly specific to each organization's business logic. While a "customer" dataset looks similar everywhere, how customers relate to orders, products, and support tickets varies greatly. ADRI standardizes what's universal (dataset quality) while leaving what's unique (business relationships) to your data platform.

### How do I ensure quality across related datasets?
**A**: Use ADRI to certify each dataset independently:
1. Assess `customers.csv` → Must meet `customer-master-v2.0`
2. Assess `orders.csv` → Must meet `transaction-v1.0`
3. Use your data platform to validate that all `orders.customer_id` exist in `customers.id`

### What if my use case requires multi-table validation?
**A**: Consider these approaches:
1. **Denormalization**: Create a joined view and assess the combined dataset
2. **Sequential Assessment**: Assess each table and implement relationship checks separately
3. **Platform Integration**: Use enterprise platforms that support ADRI standards for individual datasets while adding relationship validation

### How can I assess quality for agent workflows that need data from multiple tables?
**A**: Use the "Agent View" pattern - create a denormalized view combining the data your agent needs, then assess that view with a custom template:

**Example: Customer 360 Agent View**
```sql
-- Create a denormalized view for your agent
CREATE VIEW customer_360_agent_view AS
SELECT 
    c.customer_id,
    c.name,
    c.email,
    c.lifetime_value,
    COUNT(o.order_id) as total_orders,
    MAX(o.order_date) as last_order_date,
    AVG(o.order_total) as avg_order_value,
    COUNT(t.ticket_id) as support_tickets,
    AVG(t.satisfaction_score) as avg_satisfaction
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN tickets t ON c.customer_id = t.customer_id
GROUP BY c.customer_id;
```

Then create a custom template for this specific view:
```yaml
# customer-360-agent-view-v1.0.yaml
template:
  id: "customer-360-agent-view"
  name: "Customer 360 Agent View"
  description: "Quality standards for denormalized customer agent view"
  
requirements:
  dimension_requirements:
    completeness:
      minimum_score: 18
      critical_fields:
        - customer_id
        - email
        - lifetime_value
        - last_order_date
```

This approach provides:
- ✅ Full control over what data the agent sees
- ✅ Single dataset for ADRI to assess
- ✅ Custom quality rules for your specific use case
- ✅ Performance optimization (pre-joined data)

### How does ADRI integrate with existing agent frameworks?
ADRI provides integration adapters for popular agent frameworks like LangChain, DSPy, and CrewAI. These allow agents to invoke ADRI assessments or use ADRI scores to make decisions (e.g., refusing to act on low-quality data). See the Integrations documentation for details.

## Methodology Questions

### Why are there five dimensions?
The five dimensions (Validity, Completeness, Freshness, Consistency, and Plausibility) represent critical aspects of data quality identified through research and practice as highly impactful for agent performance and reliability. They cover structural correctness, presence of data, timeliness, logical coherence, and reasonableness.

### How was the scoring system developed?
The scoring system prioritizes the explicit communication of quality signals to agents. It was developed based on:
- Analysis of common agent failure modes related to data issues.
- Consultation with AI practitioners.
- Data quality management best practices.
- Community feedback.

The scoring aims to quantify the risk of "agent blindness" for each dimension. It is expected to evolve with community input.

### How often should we reassess our data sources?
We recommend reassessing:
- After significant changes to data sources or infrastructure.
- When deploying new agent capabilities relying on the data.
- Periodically (e.g., quarterly) for critical data sources.
- Annually for all assessed sources as part of data governance.

### Are some dimensions more important than others?
The relative importance depends heavily on the agent's task and the potential impact of failures. For financial trading agents, Freshness might be paramount. For medical diagnosis agents, Consistency and Validity might be critical. ADRI allows customizing dimension weights in the assessment configuration to reflect these use-case-specific priorities.

## Project and Community

### How can I contribute to ADRI?
See our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details. We welcome contributions to the methodology, code (tool, connectors, dimensions, integrations), documentation, examples, and especially assessments for the public dataset catalog.

### Is ADRI maintained actively?
Yes, ADRI is actively maintained by the open-source community.

### Can I use ADRI commercially?
Yes, ADRI is available under the permissive MIT License, allowing commercial use.

### How can we get support for implementing ADRI?
- **Community Support:** Use the GitHub repository's Issues and Discussions sections.
- **Documentation:** Comprehensive guides available in the documentation within this repository.

## Assessment Modes and Metadata

### What happens if I don't have metadata files?

**Great news!** ADRI follows a "facilitation, not enforcement" philosophy. When you assess data without metadata:

1. **Discovery Mode activates automatically** - Analyzes your actual data quality
2. **Metadata is generated for you** - Creates all five dimension metadata files
3. **Scoring is fair** - Based on intrinsic data quality, NOT metadata presence
4. **No penalties** - You get a quality score of (e.g.) 74/100, not 8/100

**Example:**
```bash
$ adri assess --source customer_data.csv

Overall Score: 74/100 (based on actual quality)
✅ Generated 5 metadata files to help agents understand your data:
  - customer_data.validity.json
  - customer_data.completeness.json
  - customer_data.freshness.json
  - customer_data.consistency.json
  - customer_data.plausibility.json
```

### Why does ADRI generate metadata instead of penalizing its absence?

This aligns with ADRI's vision as a communication protocol between data and agents:
- **Traditional approach**: "Your data fails because it lacks documentation"
- **ADRI approach**: "Here's your quality score AND the documentation agents need"

The generated metadata provides the ADRI protocol layer that enables agent communication, turning a potential failure into a helpful starting point.

### What's the difference between Discovery and Validation modes?

| Mode | Purpose | When Used | Scoring Basis |
|------|---------|-----------|---------------|
| **Discovery** | Analyze & help | No metadata exists | Intrinsic data quality |
| **Validation** | Verify claims | ADRI metadata exists | Compliance with declarations |

Both modes serve different purposes in the data quality journey:
- Start with Discovery to understand and document
- Use Validation to ensure ongoing compliance

## Growing with ADRI

### Do I need to use templates from the start?
No! ADRI is designed with progressive complexity. Most users start with simple assessments:
```python
assessor = DataSourceAssessor()
report = assessor.assess_file("data.csv")
```

Templates are an optional feature for teams that need standardized quality requirements across projects.

### What is the ADRI contract layer?
For advanced users, ADRI can serve as a contract layer between data suppliers and AI engineers. This enables:
- AI engineers to specify data requirements (e.g., "requires ADRI Production-v1.0.0")
- Data suppliers to certify their data meets specific ADRI standards
- Agent workflows that work with any data source meeting the requirements

This is an enterprise feature for organizations building source-agnostic AI solutions. [Learn more in our Vision document](./VISION.md#the-adri-contract-decoupling-data-sources-from-agent-workflows).

### How does ADRI help with team organization?
ADRI helps clarify responsibilities:
- **AI Engineers**: Focus on agent logic and specify ADRI requirements
- **Data Engineers**: Ensure data sources meet ADRI compliance
- **IT Systems**: Provide infrastructure for ADRI-compliant data

This division of labor becomes more important as organizations scale their AI initiatives.

### Can ADRI help us productize AI solutions faster?
Yes! By standardizing data quality requirements through ADRI:
- Prototype-to-production cycles are faster
- Integration complexity is reduced
- AI solutions can be deployed across different data sources without modification
- Business integration becomes more straightforward

This is particularly valuable for AI teams looking to scale their solutions across an enterprise.

## Purpose & Test Coverage

**Why this file exists**: Provides answers to common questions about ADRI, addressing conceptual understanding, technical implementation, and practical usage concerns from various stakeholders.

**Key responsibilities**:
- Clarify ADRI's unique value proposition vs other tools
- Explain technical and architectural decisions
- Address common implementation questions
- Guide progressive adoption and scaling
- Answer multi-dataset and integration queries

**Test coverage**: This document's claims and features are verified by tests documented in [FAQ_test_coverage.md](./test_coverage/FAQ_test_coverage.md)
