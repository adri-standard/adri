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
