# Changelog

All notable changes to ADRI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.1.0] - 2025-12-19

**verodat-adri v6.1.0 - Enterprise License Validation**

This release introduces mandatory license validation for the verodat-adri enterprise package. 
The package now requires a valid Verodat API key to function, ensuring enterprise features are 
only accessible to licensed users.

### Added

**License Validation System**
- New `adri_enterprise.license` module for API key validation
- `validate_license()` function for explicit license validation
- `is_license_valid()` function to check cached validation status
- `LicenseValidationError` exception for validation failures
- `LicenseInfo` dataclass with validation details (valid, account_id, username)
- Automatic validation on first decorator use (lazy validation)
- 24-hour validation cache to minimize API calls
- Environment variable support: `VERODAT_API_KEY` and `VERODAT_API_URL`

**Enterprise Decorator Enhancement**
- `@adri_protected` decorator now validates license on first use
- Clear error messages with guidance on obtaining API keys
- Graceful handling of network errors during validation

### Changed

- Package name: `verodat-adri` (enterprise) is now distinct from `adri` (open source)
- Package requires `VERODAT_API_KEY` environment variable to function
- Updated `__init__.py` to export license validation components
- Updated project URLs to point to Verodat/verodat-adri repository
- Enhanced package description to clarify enterprise licensing requirement

### Security

- API keys are validated against Verodat API endpoint (`/ai/key`)
- API key is passed via `Authorization: ApiKey {key}` header
- Validation results are cached to prevent unnecessary network calls
- Invalid or expired keys result in clear `LicenseValidationError`

### Migration Guide

To use verodat-adri v6.1.0+, you must:

1. **Obtain a Verodat API key** from your Verodat account settings
2. **Set the environment variable**:
   ```bash
   export VERODAT_API_KEY="your-api-key"
   ```
3. **Use the decorator as before** - validation happens automatically:
   ```python
   from adri_enterprise.decorator import adri_protected
   
   @adri_protected(contract="my_contract")
   def my_function(data):
       return process(data)
   ```

For open source features without licensing, use the `adri` package instead.

## [5.1.0] - 2025-10-21

**Documentation Improvements for Open-Source Adoption**

### Changed
- Enhanced documentation structure and clarity for better developer experience
- Improved getting started guides with clearer onboarding paths
- Optimized README for first-time users and quick adoption
- Refined code examples and usage patterns
- Updated architecture documentation for better understanding
- Streamlined contribution guidelines
- Enhanced API reference documentation

### Fixed
- Documentation consistency across all guides
- Code example accuracy and completeness
- Cross-reference links and navigation

## [5.0.1] - 2026-01-17

**Standards Library & Documentation Updates**

### Added
- 13 production-ready standards for common use cases (customer service, e-commerce, financial, healthcare, marketing)
- Framework integration standards (LangChain, CrewAI, LlamaIndex, AutoGen)
- Template standards for API responses, time series, and nested JSON
- Comprehensive test suite validating all standards

### Changed
- Improved README clarity and organization
- Enhanced documentation with better examples
- Updated contribution guidelines

### Fixed
- Documentation consistency improvements
- Code example updates

## [5.0.0] - 2025-10-17

**ADRI v5.0.0 - The missing data layer for AI agents**

Initial release of the open-source ADRI framework. Protect your AI agents from bad data with a single decorator.

### Features

**Core Protection**
- `@adri_protected` decorator for automatic data quality validation
- Five-dimension quality assessment (validity, completeness, consistency, accuracy, timeliness)
- Auto-generation of quality standards from your data
- Configurable protection modes: `raise`, `warn`, or `continue`
- Environment-based standard management (dev/prod separation)

**Framework Integration**
- Works with any Python function or AI framework
- Native support for LangChain, CrewAI, AutoGen, LlamaIndex, Haystack, Semantic Kernel
- Zero configuration required - add decorator and go

**CLI Tools**
- `adri setup` - Initialize ADRI in your project with guided setup
- `adri generate-standard` - Create quality standards from your data
- `adri assess` - Validate data quality against standards
- `adri list-standards` - View available quality standards
- `adri validate-standard` - Verify standard file correctness

**Developer Experience**
- 2-minute integration time
- Local logging for debugging and development
- YAML-based standards for transparency and version control
- Comprehensive documentation and examples
- Intelligent CI with docs-only detection

**Additional Features**
- Dimension-specific quality thresholds
- Auto-generation from sample data
- Configurable failure handling
- Assessment caching for performance
- Local JSONL logging

### Getting Started

```python
from adri import adri_protected

@adri_protected(standard="customer_data", data_param="data")
def process_customers(data):
    # Your agent logic here - now protected!
    return results
```

First run with good data → ADRI generates quality standard
Future runs → ADRI validates against that standard
Bad data → Blocked with detailed quality report

### Documentation

Complete documentation available in the repository:
- **QUICKSTART.md** - 2-minute integration guide
- **docs/GETTING_STARTED.md** - 10-minute detailed tutorial
- **docs/HOW_IT_WORKS.md** - Five quality dimensions explained
- **docs/FRAMEWORK_PATTERNS.md** - Framework-specific integration patterns
- **docs/CLI_REFERENCE.md** - Complete CLI command reference
- **docs/API_REFERENCE.md** - Full programmatic API documentation
- **docs/FAQ.md** - Common questions and answers
- **docs/ARCHITECTURE.md** - Technical architecture details

### Requirements

- Python 3.10+
- Works on Linux, macOS, and Windows

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to ADRI.

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
