# Document Processing Agent Example

> **AI Builders**: Protect document processing agents with ADRI

## Overview

Example implementation of ADRI guards for a document processing AI agent.

## Scenario

A document processing agent handles:
- Invoice processing and extraction
- Contract analysis and review
- Compliance document validation
- Metadata extraction and classification

## Data Quality Requirements

### Document Metadata
- **Completeness**: 85%+ (file type, size, creation date)
- **Validity**: 98%+ (file integrity, format compliance)
- **Consistency**: 90%+ (naming conventions, structure)

### Extracted Content
- **Completeness**: 90%+ (key fields extracted)
- **Validity**: 95%+ (data format compliance)
- **Plausibility**: 85%+ (reasonable value ranges)

## Implementation

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import Guard, Assessor

# Configure guard for document processing
guard = Guard(
    name="document_processing_guard",
    thresholds={
        'completeness': 0.85,
        'validity': 0.95,
        'consistency': 0.90,
        'plausibility': 0.85
    }
)

# Assess document quality before processing
@guard.protect
def process_document(document_path):
    document_data = extract_document_metadata(document_path)
    
    # Guard validates document quality
    # Ensures reliable processing
    
    return extract_and_classify(document_data)
```

## Next Steps

- [Customer Service Example](customer-service.md)
- [Financial Analysis Example](financial-analysis.md)
- [Implementation Guide](ai-builders/implementing-guards.md)
