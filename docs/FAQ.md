# Frequently Asked Questions

## General Questions

### What is the Agent Data Readiness Index?
The Agent Data Readiness Index (ADRI) is an open-source framework for evaluating how well data sources communicate their quality attributes to AI agents. It focuses on addressing the "data blindness" problem that uniquely affects agentic AI systems.

### How is this different from other data quality tools?
Most data quality tools focus on measuring and improving the intrinsic quality of data. ADRI specifically focuses on whether quality attributes are explicitly communicated to agents in a way they can understand and act upon. This addresses the unique challenge of agentic systems that make dynamic decisions based on data.

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
Yes, ADRI is actively maintained by Verodat and the open-source community.

### Can I use ADRI commercially?
Yes, ADRI is available under the permissive MIT License, allowing commercial use.

### How can we get support for implementing ADRI?
- **Community Support:** Use the GitHub repository's Issues and Discussions sections.
- **Commercial Support:** For consulting, training, or enterprise features, contact Verodat.
