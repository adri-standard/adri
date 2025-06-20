#!/usr/bin/env python
"""
Example file demonstrating audience tagging for code examples in documentation.

This file contains examples of code blocks for each audience type:
- AI_BUILDER: Developers building AI applications and agents
- STANDARD_CONTRIBUTOR: Open source contributors and organizations improving ADRI
- DATA_PROVIDER: Teams that manage, prepare, and deliver data for AI systems

These examples can be copied and used as templates when writing documentation.
"""

def agent_example():
    """
    Example code for AI_BUILDER audience.
    
    ```python
    # [AI_BUILDER]
    from adri import DataSourceAssessor
    
    # Assess a CSV file
    assessor = DataSourceAssessor("customer_data.csv")
    report = assessor.assess()
    
    # Print the overall score
    print(f"Overall data quality score: {report.score}")
    
    # Check specific dimensions
    print(f"Completeness: {report.dimensions['completeness'].score}")
    print(f"Validity: {report.dimensions['validity'].score}")
    ```
    """
    pass


def standard_example():
    """
    Example code for STANDARD_CONTRIBUTOR audience.
    
    ```python
    # [STANDARD_CONTRIBUTOR]
    from adri.dimensions import BaseDimension
    from adri.rules import registry
    
    class CustomDimension(BaseDimension):
        """A custom dimension for specialized data quality assessment"""
        
        def __init__(self, name="custom", weight=1.0):
            super().__init__(name, weight)
            self.rules = []
        
        def evaluate(self, data_source):
            """Evaluate the dimension on a data source"""
            results = {}
            for rule in self.rules:
                result = rule.evaluate(data_source)
                results[rule.name] = result
            
            return self._calculate_score(results)
        
        def _calculate_score(self, results):
            """Calculate the dimension score from rule results"""
            if not results:
                return 1.0
                
            total = sum(result.score for result in results.values())
            return total / len(results)
    
    # Register the dimension
    registry.register_dimension("custom", CustomDimension)
    ```
    """
    pass


def supplier_example():
    """
    Example code for DATA_PROVIDER audience.
    
    ```python
    # [DATA_PROVIDER]
    from adri.connectors import BaseConnector
    import pandas as pd
    
    class CustomDataConnector(BaseConnector):
        """Custom connector for proprietary data format"""
        
        def __init__(self, filepath, **kwargs):
            self.filepath = filepath
            self.options = kwargs
            self._metadata = {
                "source_type": "custom_format",
                "last_updated": None,
                "record_count": 0,
                "fields": []
            }
        
        def read(self):
            """Read the data source and return as a pandas DataFrame"""
            # Implementation for reading custom format
            data = self._parse_custom_format()
            
            # Update metadata
            self._metadata["record_count"] = len(data)
            self._metadata["fields"] = list(data.columns)
            
            return data
        
        def _parse_custom_format(self):
            """Parse the custom format file"""
            # Implementation details for parsing
            # This is just a placeholder
            return pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["A", "B", "C"],
                "value": [10.5, 20.3, 15.7]
            })
        
        @property
        def metadata(self):
            """Return metadata about the data source"""
            return self._metadata
    ```
    """
    pass


def multi_audience_example():
    """
    Example showing how to document for multiple audiences.
    
    ## For AI Builders
    
    ```python
    # [AI_BUILDER]
    from adri import DataSourceAssessor
    from custom_connector import CustomDataConnector
    
    # Use a custom connector with ADRI
    connector = CustomDataConnector("data.custom")
    assessor = DataSourceAssessor(connector)
    report = assessor.assess()
    
    print(f"Data quality score: {report.score}")
    ```
    
    ## For Data Providers
    
    ```python
    # [DATA_PROVIDER]
    from adri.connectors import BaseConnector
    
    class CustomDataConnector(BaseConnector):
        def __init__(self, filepath):
            self.filepath = filepath
            
        def read(self):
            # Implementation details
            return dataframe
    ```
    
    ## For Standard Contributors
    
    ```python
    # [STANDARD_CONTRIBUTOR]
    from adri.connectors import registry
    
    # Register the custom connector
    registry.register_connector("custom", CustomDataConnector)
    ```
    """
    pass


def audience_badge_examples():
    """
    Example showing how to use audience badges in documentation.
    
    ## Inline Audience Badges
    
    ```html
    <!-- Inline audience badges -->
    <span class="audience-badge audience-badge-ai-builder"><span class="emoji">🤖</span> AI Builder</span>
    <span class="audience-badge audience-badge-data-provider"><span class="emoji">📊</span> Data Provider</span>
    <span class="audience-badge audience-badge-standard-contributor"><span class="emoji">🛠️</span> Standard Contributor</span>
    ```
    
    ## Audience-Specific Headings
    
    ```html
    <!-- Audience-specific headings -->
    <h3 data-audience="AI_BUILDER">This heading is for AI Builders</h3>
    <h3 data-audience="DATA_PROVIDER">This heading is for Data Providers</h3>
    <h3 data-audience="STANDARD_CONTRIBUTOR">This heading is for Standard Contributors</h3>
    ```
    
    ## Combined Example
    
    ```markdown
    # Data Quality Assessment
    
    <span class="audience-badge audience-badge-data-provider"><span class="emoji">📊</span> Data Provider</span>
    
    This section explains how to assess the quality of your data before making it available to AI systems.
    
    <h3 data-audience="DATA_PROVIDER">Implementing Data Validation</h3>
    
    Data Providers should implement the following validation checks...
    
    ```python
    # [DATA_PROVIDER]
    from adri import DataSourceAssessor
    
    assessor = DataSourceAssessor("customer_data.csv")
    report = assessor.assess()
    print(f"Data quality score: {report.score}")
    ```
    ```
    """
    pass


if __name__ == "__main__":
    print("This file contains example code blocks for documentation.")
    print("See the docstrings for examples of audience-tagged code blocks.")
