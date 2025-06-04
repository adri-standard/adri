# ADRI Project Index

This document provides a comprehensive overview of all files and directories in the ADRI project, explaining their purpose and role.

## 📁 Root Directory Files

| File | Purpose |
|------|---------|
| **README.md** | Main project introduction with standards-first positioning |
| **LICENSE** | MIT License file |
| **GOVERNANCE.md** | Open governance model and community structure |
| **CHARTER.md** | Mission, vision, and core values of ADRI as a standard |
| **pyproject.toml** | Python project configuration and package metadata |
| **requirements-dev.txt** | Development dependencies |
| **MANIFEST.in** | Specifies additional files to include in package distribution |
| **Makefile** | Common development tasks (test, build, clean, etc.) |
| **.gitignore** | Git ignore patterns |
| **.dockerignore** | Docker ignore patterns |
| **mypy.ini** | MyPy type checking configuration |
| **.coverage** | Test coverage data file |

### 📋 Process & Guidelines

| File | Purpose |
|------|---------|
| **CHANGELOG.md** | Version history and release notes |
| **RELEASING.md** | Release process documentation |
| **VERSIONS.md** | Version policy and semantic versioning guide |
| **CONTRIBUTING.md** | Contribution guidelines for developers |
| **CODE_OF_CONDUCT.md** | Community code of conduct |
| **SECURITY.md** | Security policy and vulnerability reporting |
| **PROJECT_INDEX.md** | This file - comprehensive project file index |

### 🧹 Project Management

| File | Purpose |
|------|---------|
| **CLEANUP_SUMMARY.md** | Record of project cleanup activities |
| **REMOVE_WIKI_INSTRUCTIONS.md** | Instructions for wiki migration |
| **ADRI_AI_ENGINEER_REVIEW.md** | AI engineering review documentation |
| **test_template_matcher.py** | Template matcher test script |

### 📁 Generated/Output Files

| File | Purpose |
|------|---------|
| **inventory_demo.*.json** | Demo inventory assessment output files |
| **crm_audit_demo.*.json** | Demo CRM audit assessment output files |
| **crm_audit_report.html** | Generated CRM audit HTML report |
| **crm_audit_business_report.txt** | Generated CRM business report |
| **test_*.html** | Generated test report files |
| **test_customer_data.report.json** | Test customer data report |

## 📁 adri/ - Core Package

### Core Modules

| File | Purpose |
|------|---------|
| **\_\_init\_\_.py** | Package initialization, exports main APIs |
| **\_\_main\_\_.py** | CLI entry point when running as module |
| **assessor.py** | Main DataSourceAssessor class |
| **assessment_modes.py** | Assessment modes implementation |
| **cli.py** | Command-line interface implementation |
| **interactive.py** | Interactive mode functionality |
| **report.py** | AssessmentReport class and reporting logic |
| **version.py** | Version information |

### 📁 adri/config/

| File | Purpose |
|------|---------|
| **config.py** | Configuration management system |
| **defaults.py** | Default configuration values |
| **example_config.yaml** | Example configuration file |
| **show_custom_config.py** | Utility to display custom configurations |

### 📁 adri/connectors/

| File | Purpose |
|------|---------|
| **base.py** | Abstract base connector class |
| **file.py** | File-based data source connector (CSV, JSON, etc.) |
| **database.py** | Database connector implementation |
| **api.py** | API endpoint connector |
| **registry.py** | Connector registry and discovery |

### 📁 adri/dimensions/

| File | Purpose |
|------|---------|
| **base.py** | Abstract base dimension class |
| **validity.py** | Validity dimension implementation |
| **completeness.py** | Completeness dimension implementation |
| **freshness.py** | Freshness dimension implementation |
| **consistency.py** | Consistency dimension implementation |
| **plausibility.py** | Plausibility dimension implementation |
| **business_validity.py** | Business-specific validity dimension |
| **business_completeness.py** | Business-specific completeness dimension |
| **business_freshness.py** | Business-specific freshness dimension |
| **business_consistency.py** | Business-specific consistency dimension |
| **business_plausibility.py** | Business-specific plausibility dimension |
| **registry.py** | Dimension registry |

### 📁 adri/rules/

| File | Purpose |
|------|---------|
| **base.py** | Abstract DiagnosticRule base class |
| **validity.py** | Validity-related rules |
| **completeness.py** | Completeness-related rules |
| **freshness.py** | Freshness-related rules |
| **consistency.py** | Consistency-related rules |
| **plausibility.py** | Plausibility-related rules |
| **registry.py** | Rule registry and discovery |
| **demo.py** | Demonstration rules |
| **example_evaluation.py** | Example rule evaluations |
| **expiration_rule.py** | Data expiration checking rule |
| **README.md** | Rules subsystem documentation |
| **rule_grid.md** | Rule coverage matrix |

### 📁 adri/templates/

| File | Purpose |
|------|---------|
| **base.py** | Abstract template base class |
| **evaluation.py** | Template evaluation logic |
| **exceptions.py** | Template-specific exceptions |
| **loader.py** | Template loading and parsing |
| **registry.py** | Template registry |
| **yaml_template.py** | YAML template implementation |
| **matcher.py** | Template matching implementation |
| **guard.py** | Template validation and fallback mechanisms |
| **report_template.html** | HTML report template |
| **TEMPLATE_STATUS.md** | Template system status |
| **catalog/** | Production-ready template library |
| **development/** | Test-driven template development workspace |

### 📁 adri/integrations/

| File | Purpose |
|------|---------|
| **guard.py** | Base guard implementation and @adri_guarded decorator |
| **langchain/** | LangChain framework integration |
| **crewai/** | CrewAI framework integration |
| **dspy/** | DSPy framework integration |

### 📁 adri/utils/

| File | Purpose |
|------|---------|
| **inference.py** | Data type and schema inference utilities |
| **metadata_generator.py** | Automatic metadata generation |
| **validators.py** | Common validation functions |

## 📁 docs/ - Documentation

### 🎯 Core Documentation

| File | Purpose |
|------|---------|
| **index.md** | Documentation home page |
| **VISION.md** | Core vision and strategic direction (hybrid approach) |
| **VISION_IN_ACTION.md** | Concrete examples of the vision |
| **GET_STARTED.md** | Quick start guide |
| **ROADMAP.md** | Future development plans |
| **ROADMAP_V1.1.md** | Detailed v1.1 roadmap with priority rules |
| **FAQ.md** | Frequently asked questions |
| **QUICKSTART.md** | 5-minute quickstart tutorial |

### 📚 Concept Documentation

| File | Purpose |
|------|---------|
| **UNDERSTANDING_DIMENSIONS.md** | Overview of the five data quality dimensions |
| **validity_dimension.md** | Detailed validity dimension documentation |
| **completeness_dimension.md** | Detailed completeness dimension documentation |
| **freshness_dimension.md** | Detailed freshness dimension documentation |
| **consistency_rules.md** | Consistency rules documentation |
| **plausibility_dimension.md** | Detailed plausibility dimension documentation |
| **plausibility_rules.md** | Plausibility rules documentation |
| **Methodology.md** | ADRI methodology explanation |
| **implementation_guide.md** | Step-by-step implementation guide |
| **UNDERSTANDING_TEMPLATES.md** | Guide to template system and authoring |
| **TEMPLATE_TDD_GUIDE.md** | Test-driven development guide for templates |
| **CONTRIBUTING_TEMPLATES.md** | Template contribution guidelines |

### 🔧 Technical Documentation

| File | Purpose |
|------|---------|
| **API_REFERENCE.md** | Complete API documentation |
| **IMPLEMENTING_GUARDS.md** | Guide to implementing data quality guards |
| **INTEGRATIONS.md** | Framework integration guides |
| **EXTENDING.md** | How to extend ADRI |
| **CUSTOM_RULES_GUIDE.md** | Comprehensive guide for creating custom rules |
| **ENHANCING_DATA_SOURCES.md** | Adding metadata to data sources |
| **TESTING.md** | Testing guide and strategy |
| **ASSESSMENT_MODES.md** | Assessment modes documentation |
| **RULE_TESTING_ARCHITECTURE.md** | Rule testing architecture guide |
| **TEMPLATE_GUARD.md** | Template guard documentation |

### 💼 Use Cases

| File | Purpose |
|------|---------|
| **USE_CASE_AI_STATUS_AUDITOR.md** | AI status auditor implementation |
| **USE_CASE_INVOICE_PAYMENT_AGENT.md** | Invoice payment agent example |

### 🛠️ Development Documentation

| File | Purpose |
|------|---------|
| **DEVELOPER.md** | Developer setup guide |
| **architecture.md** | System architecture documentation |
| **architecture.mmd** | Architecture Mermaid diagram source |
| **architecture.png** | Architecture diagram image |
| **components.md** | Component descriptions |
| **datasets.md** | Example datasets catalog |
| **PROJECT_STRUCTURE.md** | Repository structure guide |

### 📝 Internal Documentation

| File | Purpose |
|------|---------|
| **DOCUMENTATION_ALIGNMENT.md** | Documentation standards |
| **PROGRESSIVE_ENGAGEMENT_STRATEGY.md** | User engagement strategy |
| **STYLE_GUIDE.md** | Documentation style guide |
| **GITHUB_PAGES.md** | GitHub Pages deployment guide |
| **test-deployment.md** | Test deployment instructions |
| **DOCUMENT_PURPOSE_ANALYSIS.md** | Analysis of documentation purposes |
| **CLAIMS_TRACKER.md** | Tracker for claims made across documentation |
| **DISCOVERY_AND_VALIDATION.md** | Discovery and validation process documentation |
| **PROVENANCE_SPECIFICATION.md** | Data provenance specification |

### 📁 docs/test_coverage/

| File | Purpose |
|------|---------|
| **README.md** | Test coverage documentation overview |
| **TEST_COVERAGE_TRACKING.md** | Comprehensive test coverage tracking |
| **\*\_test_coverage.md** | Individual test coverage documents for each feature |

### 📁 docs/data/

| File | Purpose |
|------|---------|
| **benchmark.json** | Performance benchmark data |

### 📁 docs/diagrams/

Contains Mermaid diagram source files and generated images for documentation.

### 📁 docs/evidence/

Contains evidence files supporting claims and documentation.

## 📁 config/

| File | Purpose |
|------|---------|
| **mkdocs.yml** | MkDocs site configuration |
| **site_config.yml** | Additional site configuration |

## 📁 examples/

| File | Purpose |
|------|---------|
| **README.md** | Examples overview and index |
| **01_basic_assessment.py** | Basic data assessment example |
| **02_requirements_as_code.py** | Data requirements as code |
| **03_data_team_contract.py** | Team data quality contracts |
| **04_multi_source.py** | Multi-source assessment |
| **05_production_guard.py** | Production guard implementation |
| **06_metadata_generation.py** | Automatic metadata generation |
| **07_status_auditor_demo.py** | Status auditor demonstration |
| **08_template_compliance.py** | Template compliance checking |
| **09_agent_view_pattern.py** | Agent view pattern example |
| **10_template_discovery_demo.py** | Template discovery demonstration |
| **template_guard_demo.py** | Template guard demonstration |
| **data/** | Example data files |
| **custom_rules/** | Custom rule examples and test data |
| **integrations/** | Framework-specific examples |
| **interactive/** | Interactive mode examples |
| **legacy/** | Legacy examples (deprecated) |
| **plausibility/** | Plausibility checking examples |
| **web_demo/** | Web demonstration |

### 📁 examples/custom_rules/

| File | Purpose |
|------|---------|
| **README.md** | Quick start guide for custom rules |
| **business_email_rule.py** | Example rule validating business emails |
| **duplicate_detection_rule.py** | Example rule detecting duplicate records |
| **revenue_logic_rule.py** | Example rule validating revenue calculations |
| **test_data/** | Sample CSV files for testing custom rules |

## 📁 tests/

| File | Purpose |
|------|---------|
| **conftest.py** | Pytest configuration and fixtures |
| **unit/** | Unit tests organized by module |
| **integration/** | Integration tests |
| **infrastructure/** | Infrastructure tests |
| **documentation/** | Documentation tests |
| **fixtures/** | Test fixtures and data |
| **data/** | Test data files |
| **datasets/** | Test datasets |
| **plans/** | Test execution plans |
| **results/** | Test result storage |
| **claims/** | Claims verification tests |

## 📁 scripts/

| File | Purpose |
|------|---------|
| **publish_pypi.sh** | PyPI publishing script |
| **run_financial_market_assessment.py** | Financial market assessment demo |
| **verify_version.py** | Version verification utility |
| **template_tdd_runner.py** | Test-driven template development runner |

## 📁 notebooks/

| File | Purpose |
|------|---------|
| **01_adri_guard_tutorial.ipynb** | ADRI guard tutorial notebook |
| **02_langchain_integration_tutorial.ipynb** | LangChain integration tutorial |

## 📁 quickstart/

| File | Purpose |
|------|---------|
| **README.md** | Quickstart guide |
| **quickstart.py** | Main quickstart script |
| **see_it.py** | Visual demonstration |
| **try_it.py** | Interactive tryout |
| **minimal_adri/** | Minimal ADRI example |
| **outputs/** | Sample outputs |
| **samples/** | Sample data files |

## 🎯 Key Entry Points

1. **For Users**: Start with `README.md` → `docs/GET_STARTED.md`
2. **For Developers**: `docs/DEVELOPER.md` → `docs/architecture.md`
3. **For Contributors**: `CONTRIBUTING.md` → `docs/EXTENDING.md`
4. **For Examples**: `examples/README.md` → specific example files

## 📊 File Categories

- **📚 Documentation**: All `.md` files in `docs/`
- **🐍 Source Code**: All `.py` files in `adri/`
- **🧪 Tests**: All files in `tests/`
- **📝 Examples**: All files in `examples/`
- **⚙️ Configuration**: `pyproject.toml`, `mkdocs.yml`, etc.
- **📋 Process**: `CONTRIBUTING.md`, `RELEASING.md`, etc.

---

*Last Updated: 2025-06-03*
