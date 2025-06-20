# Code Example Audience Tagging System

This document explains the audience tagging system for code examples in ADRI documentation. By tagging code examples with their intended audience, we can ensure that examples are tested appropriately and that users see examples relevant to their needs.

## Audience Types

ADRI documentation serves three primary audiences:

1. **AI_BUILDER** 🤖 - Developers building AI applications and agents
2. **DATA_PROVIDER** 📊 - Teams that manage, prepare, and deliver data for AI systems
3. **STANDARD_CONTRIBUTOR** 🛠️ - Open source contributors and organizations improving ADRI

## Tagging Code Examples

To tag a code example for a specific audience, add a comment at the beginning of the code block:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import DataSourceAssessor

assessor = DataSourceAssessor("data.csv")
report = assessor.assess()
print(f"Overall score: {report.score}")
```

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
class CustomDimension(BaseDimension):
    """Implementation of a custom dimension for ADRI standard"""
    def __init__(self, name, weight=1.0):
        super().__init__(name, weight)
        self.rules = []
    
    def evaluate(self, data_source):
        # Implementation details
        pass
```

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri.connectors import FileConnector

class CustomConnector(FileConnector):
    """Custom connector for specialized data format"""
    def read(self):
        # Implementation details
        return dataframe
```

## Default Audience

If no audience tag is specified, the code example is assumed to be for the **AI_BUILDER** audience, which has the strictest validation requirements.

## Validation Rules by Audience

Each audience has different validation rules applied to their code examples:

### AI_BUILDER Audience

- **Strictest validation** - Code must be fully executable
- All imports must resolve
- No pseudo-code or placeholders allowed
- Examples must work with the current ADRI API

### STANDARD_CONTRIBUTOR Audience

- **Syntax validation** - Code must be syntactically valid Python
- Allows references to APIs that might not exist yet
- Permits certain development-related errors (ImportError, AttributeError, etc.)
- Ideal for showing how to extend ADRI with new components

### DATA_PROVIDER Audience

- **Interface validation** - Code must conform to ADRI interfaces
- Allows data-related errors (FileNotFoundError, ConnectionError, etc.)
- Focuses on showing how to implement data connectors and providers
- Uses mock implementations of ADRI interfaces for testing

## Testing Behavior

The documentation testing system applies different rules based on the audience tag:

1. **AI_BUILDER** examples are tested with the actual ADRI implementation and must pass without errors
2. **STANDARD_CONTRIBUTOR** examples are tested with mock implementations of core ADRI components
3. **DATA_PROVIDER** examples are tested with mock data sources and connectors

## When to Use Each Audience Tag

- Use **[AI_BUILDER]** for examples showing how to use ADRI in applications
- Use **[STANDARD_CONTRIBUTOR]** for examples showing how to extend or modify ADRI itself
- Use **[DATA_PROVIDER]** for examples showing how to implement data sources for ADRI

## Best Practices

1. Always tag code examples with the appropriate audience
2. Keep examples focused on the needs of the specific audience
3. For AGENT examples, ensure they work with the current ADRI API
4. For STANDARD examples, clearly indicate extension points
5. For SUPPLIER examples, focus on interface compliance

## Example: Multi-Audience Documentation

Some documentation may need to show examples for multiple audiences. In this case, clearly separate the examples and tag each appropriately:

```markdown
## Using Custom Data Sources

### For AI Builders

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import DataSourceAssessor
from custom_connector import MyCustomConnector

# Use a custom connector with ADRI
connector = MyCustomConnector("data.csv")
assessor = DataSourceAssessor(connector)
report = assessor.assess()
```

### For Data Providers

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri.connectors import BaseConnector

class MyCustomConnector(BaseConnector):
    def __init__(self, filepath):
        self.filepath = filepath
        
    def read(self):
        # Implementation details
        return dataframe
```
```

## Implementation Details

The audience tagging system is implemented in the documentation testing framework:

1. The `CodeExtractor` class detects audience tags in code blocks
2. The `TestCodeExamples` class applies different validation rules based on audience
3. Different mock implementations are provided for each audience

See `tests/documentation/utils/code_extractor.py` and `tests/documentation/test_code_examples.py` for implementation details.

## Visual Audience Indicators

Each audience is represented by a visual indicator in the documentation:

- **AI_BUILDER** 🤖 - Blue badge for developers building AI applications
- **DATA_PROVIDER** 📊 - Green badge for teams managing data
- **STANDARD_CONTRIBUTOR** 🛠️ - Purple badge for contributors improving ADRI

These visual indicators help users quickly identify content relevant to their role.

## Related Documentation

For HTML-based audience tagging in documentation (as opposed to code examples), see the [Audience Badges](audience_badges.md) guide. The audience badges system provides visual indicators for documentation sections and headings, complementing the code example tagging system described here.

The audience badges system uses the same audience types but implements them as HTML elements:

```html
<span class="audience-badge audience-badge-ai-builder"><span class="emoji">🤖</span> AI Builder</span>
```

And for headings:

```html
<h3 data-audience="AI_BUILDER">This heading is for AI Builders</h3>
```

See the [Audience Badges Example](../../examples/documentation/audience_badges_example.html) for a live demonstration.
