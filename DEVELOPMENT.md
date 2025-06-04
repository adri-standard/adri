# ADRI Development Guide

## Current Architecture

### Template-Based Scoring System (v1.1.0)
As of the latest changes, ADRI uses a unified template-based scoring system:

- **All assessments use templates internally** - Even basic `assess_file()` calls use the default template
- **Weighted scoring** - Each dimension's rules have weights that sum to 20 points
- **Normalized scores** - Overall scores are normalized to 0-100 for consistency
- **Default template** - `general/default-v1.0.0` provides balanced general-purpose assessment

### Key Architecture Decisions

1. **Templates as the core abstraction**: Templates define what "good data" means for specific use cases
2. **Five dimensions**: Validity, Completeness, Freshness, Consistency, Plausibility
3. **Discovery vs Validation modes**: Discovery helps understand data, Validation checks compliance
4. **Metadata-driven approach**: Encouraging explicit data quality declarations

## Development Setup

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

Quick start:
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Active Development Areas

### Template System Enhancement
- Building out domain-specific templates
- Improving template discovery/matching
- Enhanced template validation

### Performance Optimization
- Template caching mechanisms
- Parallel rule execution
- Large dataset handling

### Integration Expansion
- Additional framework integrations
- Cloud platform connectors
- Real-time assessment capabilities

## Known Limitations

1. **Single dataset focus** - ADRI assesses individual datasets, not complex relationships
2. **Template weights** - Must manually ensure weights sum to 20 per dimension
3. **Metadata generation** - Currently creates JSON files, considering other formats

## Testing Philosophy

- Unit tests for all rule implementations
- Integration tests for template system
- Documentation tests to ensure examples work
- Performance benchmarks for large datasets

## Release Process

See [RELEASING.md](RELEASING.md) for the full process.

Key points:
- Semantic versioning (major.minor.patch)
- Update CHANGELOG.md before releases
- Test on TestPyPI before production release

## Resources

- **API Docs**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Template Guide**: [docs/UNDERSTANDING_TEMPLATES.md](docs/UNDERSTANDING_TEMPLATES.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Roadmap**: [docs/ROADMAP.md](docs/ROADMAP.md)

## Questions?

- GitHub Issues: Bug reports and feature requests
- Discussions: General questions and ideas
- Discord: Real-time chat (coming soon)
