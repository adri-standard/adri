# ADRI Developer Guide

This guide is intended for developers who want to contribute to the Agent Data Readiness Index (ADRI) project or build extensions and integrations.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Type Checking](#type-checking)
- [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip or conda for package management

### Setting Up Your Development Environment

1. **Clone the repository**

   ```bash
   git clone https://github.com/adri-ai/adri.git
   cd agent-data-readiness-index
   ```

2. **Create a virtual environment**

   ```bash
   # Using venv
   python -m venv venv
   
   # Activate the environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install the package in development mode**

   ```bash
   # Install the package with all optional dependencies
   pip install -e ".[all]"
   
   # Or install with specific optional dependencies
   pip install -e ".[langchain,dspy]"
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

## Project Structure

The ADRI project follows a modular architecture with clear extension points:

```
adri/
├── __init__.py           # Main package initialization
├── assessor.py           # Core assessment logic
├── cli.py                # Command-line interface
├── interactive.py        # Interactive CLI mode
├── report.py             # Report generation
├── connectors/           # Data source connectors
│   ├── __init__.py
│   ├── base.py           # Base connector interface
│   ├── file.py           # File connector implementation
│   └── registry.py       # Connector registry
├── dimensions/           # Assessment dimensions
│   ├── __init__.py
│   ├── base.py           # Base dimension interface
│   ├── completeness.py   # Completeness dimension
│   ├── consistency.py    # Consistency dimension
│   ├── freshness.py      # Freshness dimension
│   ├── plausibility.py   # Plausibility dimension
│   ├── validity.py       # Validity dimension
│   └── registry.py       # Dimension registry
├── integrations/         # Framework integrations
│   ├── __init__.py
│   ├── guard.py          # ADRI guard decorator
│   ├── langchain/        # LangChain integration
│   ├── dspy/             # DSPy integration
│   └── crewai/           # CrewAI integration
├── templates/            # Report templates
└── utils/                # Utility functions
```

### Key Extension Points

- **Dimensions**: Add new assessment dimensions by extending `BaseDimensionAssessor`
- **Connectors**: Add support for new data sources by extending `BaseConnector`
- **Integrations**: Add integrations with new frameworks in the `integrations` directory

## Development Workflow

### Adding a New Dimension

1. Create a new file in the `adri/dimensions` directory
2. Import the base class and registration decorator
3. Define your dimension class and use the decorator to register it
4. Implement the required methods

Example:

```python
<!-- audience: ai-builders -->
# adri/dimensions/my_dimension.py
import logging
from typing import Dict, List, Tuple, Any, Optional

from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension

logger = logging.getLogger(__name__)


@register_dimension(
    name="my_dimension",
    description="Description of what this dimension evaluates"
)
class MyDimensionAssessor(BaseDimensionAssessor):
    """
    Assessor for the My Dimension.
    
    Detailed description of what this dimension evaluates and why it matters.
    """
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing my_dimension for {connector.get_name()}")
        
        findings = []
        recommendations = []
        score_components = {}
        
        # Your assessment logic here
        # ...
        
        # Calculate overall score (0-20)
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        logger.info(f"My dimension assessment complete. Score: {score}")
        return score, findings, recommendations
```

### Adding a New Connector

1. Create a new file in the `adri/connectors` directory
2. Import the base class and registration decorator
3. Define your connector class and use the decorator to register it
4. Implement all the required methods from the base class

See [EXTENDING.md](EXTENDING.md) for more detailed instructions.

### Adding a New Integration

1. Create a new directory in the `adri/integrations` directory
2. Create an `__init__.py` file to expose the public API
3. Implement the integration with graceful handling of missing dependencies
4. Create example scripts in the `examples` directory

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/test_dimensions.py

# Run tests with coverage
pytest --cov=adri
```

### Writing Tests

- Place tests in the `tests` directory
- Follow the same structure as the main package
- Use descriptive test names
- Include tests for both success and failure cases
- Mock external dependencies

Example:

```python
<!-- audience: ai-builders -->
# tests/dimensions/test_my_dimension.py
import pytest
from unittest.mock import MagicMock

from adri.dimensions import DimensionRegistry
from adri.dimensions.my_dimension import MyDimensionAssessor


def test_my_dimension_registration():
    """Test that MyDimensionAssessor is properly registered."""
    assert "my_dimension" in DimensionRegistry.list_dimensions()
    dimension_class = DimensionRegistry.get_dimension("my_dimension")
    assert dimension_class == MyDimensionAssessor


def test_my_dimension_assessment():
    """Test that MyDimensionAssessor correctly assesses a data source."""
    # Create a mock connector
    connector = MagicMock()
    connector.get_name.return_value = "test_connector"
    
    # Create the assessor
    assessor = MyDimensionAssessor()
    
    # Run the assessment
    score, findings, recommendations = assessor.assess(connector)
    
    # Check the results
    assert 0 <= score <= 20
    assert isinstance(findings, list)
    assert isinstance(recommendations, list)
```

## Documentation

### Docstrings

Use Google-style docstrings for all public classes and methods:

```python
<!-- audience: ai-builders -->
def function(arg1: str, arg2: int = 10) -> bool:
    """
    Short description of the function.
    
    Longer description explaining the function's behavior,
    use cases, and any important details.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2, defaults to 10
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: When arg1 is empty
        TypeError: When arg2 is not an integer
        
    Example:
        ```python
        # Import required modules
        import re
        from typing import Optional
        
        # Call the function with different arguments
        result1 = function("example", 5)
        result2 = function("test", 10)
        
        # Use the results
        if result1 and result2:
            print("Both calls succeeded")
        ```
    """
    if not arg1:
        raise ValueError("arg1 cannot be empty")
    if not isinstance(arg2, int):
        raise TypeError("arg2 must be an integer")
    return True  # Example implementation
```

### Building Documentation

We use Sphinx for generating documentation:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build the documentation
cd docs
make html
```

## Type Checking

We use mypy for static type checking:

```bash
# Run type checking
mypy adri

# Run type checking with specific options
mypy --disallow-untyped-defs --disallow-incomplete-defs adri
```

## Contributing Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and type checking
5. Update documentation if necessary
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

We follow PEP 8 and use Black for code formatting:

```bash
# Format code
black adri

# Check code style
flake8 adri
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add new dimension for data lineage
fix: correct calculation in freshness dimension
docs: update README with new examples
test: add tests for consistency dimension
refactor: simplify connector registry
```

## Additional Resources

- [EXTENDING.md](EXTENDING.md): Detailed guide on extending ADRI
- [INTEGRATIONS.md](INTEGRATIONS.md): Guide on using ADRI integrations

---

## Maintainer Workflows

### Updating the Community Dataset Catalog

The Community Dataset Catalog displayed on the documentation site is powered by the `docs/data/benchmark.json` file. This file is generated by aggregating validated community submissions from the `assessed_datasets/` directory.

**Process:**

1.  **Review Submission PR:** When a contributor submits a Pull Request adding a new dataset assessment (typically a `report.json` and `metadata.yaml` file within a subdirectory of `assessed_datasets/`), review the submission according to the guidelines in `CONTRIBUTING.md`. Check for:
    *   Completeness of metadata.
    *   Validity of the JSON report structure.
    *   Plausibility of the assessment scores and findings.
    *   Relevance of the dataset to the community.
2.  **Merge Valid PR:** If the submission is valid, merge the Pull Request.
3.  **Update Local Repository:** Ensure your local repository clone is up-to-date with the `main` branch.
    ```bash
    git checkout main
    git pull origin main
    ```
4.  **Run Update Script:** Execute the catalog update script from the project root directory. Ensure your virtual environment with documentation dependencies (`pip install -e ".[docs]"`) is active.
    ```bash
    python scripts/update_catalog.py
    ```
    This script will scan `assessed_datasets/`, parse new/updated assessments, recalculate summary statistics, and overwrite `docs/data/benchmark.json`.
5.  **Review Changes:** Check the changes made to `docs/data/benchmark.json` using `git diff docs/data/benchmark.json`. Verify that the new dataset is included and the summary statistics look reasonable.
6.  **Commit Changes:** Commit the updated `benchmark.json` file.
    ```bash
    git add docs/data/benchmark.json
    git commit -m "chore: update community dataset catalog"
    ```
7.  **Push Changes:** Push the commit to the `main` branch.
    ```bash
    git push origin main
    ```
8.  **Verify Site:** After the push, the GitHub Pages site should automatically rebuild (if deployment is configured). Check the live site to ensure the Community Catalog section reflects the updated data.

**Frequency:** This process is automated with GitHub Actions and runs automatically whenever changes are made to the `assessed_datasets/` directory or weekly on Mondays at noon UTC. It can also be manually triggered from the Actions tab in GitHub.

### Automated Deployment and Updates

The project utilizes GitHub Actions for automating several key processes:

1. **Documentation Deployment:** The MkDocs documentation site is automatically built and deployed to GitHub Pages whenever changes are made to the documentation content, Python source files, or Markdown files.
   - Workflow file: `.github/workflows/docs.yml`
   - Trigger: Push to `main` branch affecting docs content, markdown files, or direct manual trigger
   - Output: Site deployed to GitHub Pages from the `./site` directory

2. **Community Catalog Updates:** The community dataset catalog is automatically updated whenever new assessments are added to the `assessed_datasets/` directory.
   - Workflow file: `.github/workflows/update-catalog.yml`
   - Trigger: Push to `main` branch affecting the `assessed_datasets/` directory, weekly on Mondays, or direct manual trigger
   - Action: Runs `scripts/update_catalog.py` and auto-commits changes to `docs/data/benchmark.json`

3. **Tests and Type Checking:** Automated tests and type checking are performed on pull requests and commits to ensure code quality.
   - Workflow files: `.github/workflows/tests.yml` and `.github/workflows/type-check.yml`
   - Trigger: Push to `main` branch or pull requests

**Manual Trigger:** Any of these workflows can be manually triggered from the "Actions" tab in the GitHub repository if needed.

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive technical documentation for developers contributing to ADRI, including setup instructions, architecture details, and development workflows.

**Key responsibilities**:
- Guide development environment setup
- Document project architecture and extension points
- Explain development workflows for new features
- Define testing and documentation standards
- Detail maintainer workflows and automation

**Test coverage**: This document's examples, workflows, and technical specifications should be verified by tests documented in [DEVELOPER_test_coverage.md](test_coverage/DEVELOPER_test_coverage.md)
