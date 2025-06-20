# Community Dataset Catalog

The ADRI Community Dataset Catalog showcases real-world implementations of the Agent Data Readiness Index across various industries and use cases. This living catalog demonstrates how organizations are using ADRI to ensure their data is ready for AI agent consumption.

## 📊 Featured Assessments

### Coming Soon
We're actively collecting community submissions to showcase diverse ADRI implementations. The catalog will feature:

- **Industry Examples**: Financial services, healthcare, retail, manufacturing
- **Use Case Diversity**: Customer data, transaction records, IoT sensor data, inventory systems
- **Score Distributions**: Real-world score patterns and improvement journeys
- **Template Applications**: How organizations use and customize ADRI templates

## 🤝 How to Contribute

Want to share your ADRI assessment? Here's how:

1. **Run Your Assessment**
   ```bash
   adri assess your-data.csv --output report.json
   ```

2. **Anonymize If Needed**
   Remove any sensitive information while preserving the assessment value

3. **Submit via GitHub**
   - Fork the repository
   - Add your assessment to `assessed_datasets/`
   - Create a pull request

4. **Include Context**
   - Industry/domain
   - Data type description
   - Use case overview
   - Lessons learned

## 📈 Benchmark Insights

As the catalog grows, we'll provide:

- **Industry Benchmarks**: Average scores by sector
- **Dimension Analysis**: Common strengths and challenges
- **Improvement Patterns**: How organizations raise their scores
- **Template Effectiveness**: Which templates work best for different use cases

## 🎯 Why Share Your Assessment?

- **Help Others**: Your experience guides the community
- **Set Standards**: Contribute to industry benchmarks
- **Get Recognition**: Featured assessments with attribution
- **Improve Together**: Learn from similar implementations

## 📚 Example Categories

### Financial Services
- Transaction data readiness
- Customer master data quality
- Risk assessment data preparation
- Regulatory reporting datasets

### Healthcare
- Patient record completeness
- Clinical trial data validation
- Insurance claims processing
- Medical device telemetry

### Retail & E-commerce
- Inventory management data
- Customer behavior analytics
- Supply chain visibility
- Product catalog quality

### Manufacturing
- IoT sensor data streams
- Quality control metrics
- Production planning data
- Maintenance records

## 🔗 Resources

- [How to Run Assessments](GET_STARTED.md)
- [Understanding ADRI Scores](UNDERSTANDING_DIMENSIONS.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Template Library](UNDERSTANDING_TEMPLATES.md)

---

*The Community Dataset Catalog is a collaborative effort. Every contribution helps establish better data standards for AI agent development.*

## Purpose & Test Coverage

**Why this file exists**: Provides a catalog of community-submitted dataset assessments to showcase real-world ADRI implementations and results.

**Key responsibilities**:
- Catalog community dataset assessments
- Show diverse use cases and industries
- Provide benchmarks and comparisons
- Foster community engagement
- Demonstrate ADRI adoption

**Test coverage**: This document's features should be verified by tests documented in [datasets_test_coverage.md](test_coverage/datasets_test_coverage.md)
