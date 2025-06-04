# Extending ADRI

This guide explains how to extend the Agent Data Readiness Index (ADRI) framework with new dimensions and connectors.

## Architecture Overview

ADRI uses a registry-based architecture that makes it easy to add new components:

- **Dimensions**: Assessors that evaluate specific aspects of data quality
- **Connectors**: Interfaces to different data sources (files, databases, APIs, etc.)

Each type of component has:
1. A base class that defines the interface
2. A registry that manages registered implementations
3. A decorator for easy registration

## Adding a New Dimension

To add a new dimension assessor:

1. Create a new Python file in the `adri/dimensions` directory
2. Import the base class and registration decorator
3. Define your dimension class and use the decorator to register it
4. Implement the required methods

### Example

```python
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

## Adding a New Connector

To add a new data source connector:

1. Create a new Python file in the `adri/connectors` directory
2. Import the base class and registration decorator
3. Define your connector class and use the decorator to register it
4. Implement all the required methods from the base class

### Example

```python
# adri/connectors/my_connector.py
import logging
from typing import Dict, List, Any, Optional

from . import BaseConnector, register_connector

logger = logging.getLogger(__name__)


@register_connector(
    name="my_connector",
    description="Connector for my custom data source"
)
class MyConnector(BaseConnector):
    """
    Connector for my custom data source.
    
    Detailed description of the connector and the data source it interfaces with.
    """
    
    def __init__(self, connection_string, **kwargs):
        """
        Initialize the connector.
        
        Args:
            connection_string: Connection string for the data source
            **kwargs: Additional configuration options
        """
        self.connection_string = connection_string
        self.config = kwargs
        
        # Initialize connection to the data source
        self._connect()
        
    def _connect(self):
        """Establish connection to the data source."""
        # Your connection logic here
        pass
        
    def get_name(self) -> str:
        """Get the name of this data source."""
        return f"My Data Source ({self.connection_string})"
    
    def get_type(self) -> str:
        """Get the type of this data source."""
        return "my-connector"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data source."""
        return {
            "connection": self.connection_string,
            # Other metadata
        }
    
    # Implement all other required methods from BaseConnector
    # ...
```

## Using Custom Components

Once you've added your custom components, they will be automatically registered and available for use:

```python
from adri import DataSourceAssessor

# The custom dimension will be included automatically
assessor = DataSourceAssessor()

# Use a custom connector
report = assessor.assess_with_connector("my_connector", "connection-string", option1=value1)
```

## Best Practices

1. **Follow the Pattern**: Look at existing dimensions and connectors for guidance
2. **Document Thoroughly**: Include detailed docstrings and comments
3. **Use Logging**: Log important information at appropriate levels
4. **Handle Errors Gracefully**: Catch and handle exceptions appropriately
5. **Test Your Components**: Write unit tests for your custom components

## Creating Custom Templates

Templates define quality standards and requirements that data sources should meet. They are particularly useful for industry-specific compliance or organizational standards.

### Template Structure

Templates are written in YAML and define:
- Overall score requirements
- Per-dimension score requirements  
- Required rules that must pass
- Metadata about the template

### Example Template

```yaml
# templates/my-standard-v1.0.0.yaml
name: "My Organization Standard"
version: "1.0.0"
description: "Quality requirements for production data sources"
author: "Data Team"
created: "2024-01-01"

requirements:
  overall_score: 70  # Minimum overall score required
  
  dimensions:
    validity:
      min_score: 14  # Minimum score for validity dimension
      required_rules:
        - "no_invalid_types"
        - "format_consistency"
    
    completeness:
      min_score: 14
      required_rules:
        - "no_missing_required_fields"
    
    freshness:
      min_score: 12
    
    consistency:
      min_score: 12
    
    plausibility:
      min_score: 12

metadata:
  industry: "general"
  compliance_frameworks: ["ISO-27001"]
  certification_eligible: true
```

### Using Templates

```python
from adri import DataSourceAssessor
from adri.templates import load_template

# Load template from file
template = load_template("templates/my-standard-v1.0.0.yaml")

# Or from the built-in catalog
template = load_template("general/production-v1.0.0")

# Assess against template
assessor = DataSourceAssessor()
report = assessor.assess_with_template("data.csv", template)

# Check compliance
if report.template_evaluations[0].is_compliant:
    print("Data source meets all requirements!")
else:
    print("Gaps found:")
    for gap in report.template_evaluations[0].gaps:
        print(f"- {gap.message} (Severity: {gap.severity})")
```

### Built-in Template Catalog

ADRI includes pre-built templates for common use cases:

- `general/production-v1.0.0` - General production data requirements
- `financial/basel-iii-v1.0.0` - Basel III compliance requirements
- More templates coming soon for healthcare, retail, and AI/ML use cases

## Advanced: Entry Points

For third-party packages that want to extend ADRI, you can use setuptools entry points:

```python
# In setup.py or pyproject.toml
entry_points={
    'adri.dimensions': [
        'my_dimension = my_package.dimensions:MyDimensionAssessor',
    ],
    'adri.connectors': [
        'my_connector = my_package.connectors:MyConnector',
    ],
}
```

This allows your components to be discovered and registered automatically when your package is installed.

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive guidance for developers who want to extend ADRI with custom dimensions, connectors, or templates to meet specific organizational or industry needs.

**Key responsibilities**:
- Explain ADRI's extensible architecture and registry pattern
- Guide creation of custom dimension assessors
- Document how to add new data source connectors
- Show template creation for custom quality standards
- Demonstrate integration via setuptools entry points

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [EXTENDING_test_coverage.md](./test_coverage/EXTENDING_test_coverage.md)
