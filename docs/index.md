# Agent Data Readiness Index

## The Industry's First Open Standard for Evaluating AI Agent Data Quality

Welcome to the Agent Data Readiness Index (ADRI) project – an open-source initiative to establish a standard framework for evaluating the quality of data used by agentic AI systems.

## Why This Matters

As AI agents move from experimental environments to making consequential decisions in production, the quality of data they interact with becomes critically important. Unlike traditional ML models, agents actively query and interact with data dynamically, making data reliability an even more crucial concern.

**The Problem**: Agentic systems are particularly vulnerable to "data blindness" – they often cannot tell when they're working with stale, incomplete, or inconsistent information. This leads to costly mistakes, security vulnerabilities, and compliance issues.

**Our Mission**: To create an open standard that helps AI engineers evaluate, communicate, and improve data readiness for agentic systems.

## What Is The Agent Data Readiness Index?

The ADRI is a diagnostic framework that evaluates five critical dimensions of data quality specifically for agentic AI systems:

1. **Validity** - Whether data adheres to required types, formats, and ranges
2. **Completeness** - Whether all expected data is present
3. **Freshness** - Whether data is current enough for the decision
4. **Consistency** - Whether data elements maintain logical relationships
5. **Plausibility** - Whether data values are reasonable based on context

Most importantly, the index focuses on whether these quality attributes are **explicitly communicated to agents** – addressing the "data blindness" problem that uniquely affects agentic systems.

## Getting Started

- **[Methodology](Methodology.md)**: Learn about our assessment approach and scoring system.
- **[Implementation Guide](Implementation-Guide.md)**: How to use ADRI in your organization.
- **[Community Catalog](datasets.md)**: Explore assessments of public datasets. <!-- Link to datasets page -->
- **[Contribute](CONTRIBUTING.md)**: Join our community and help improve the standard. <!-- Link to file within docs/ -->

## Project Status

This project is currently in active development. We welcome contributions from AI engineers, data scientists, and organizations working with agentic systems.

## About This Project

The Agent Data Readiness Index was initiated by [Verodat](https://verodat.ai) as an open-source community resource. As agentic AI becomes increasingly critical to business operations, we believe an open standard for data quality is essential for the entire ecosystem.

For more information about Verodat's commercial offerings that help solve agent data quality issues, visit [our website](https://verodat.ai).

## License

This project is available under the [MIT License](https://github.com/verodat/agent-data-readiness-index/blob/main/LICENSE). <!-- Absolute link to GitHub -->
