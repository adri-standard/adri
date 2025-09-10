# Enterprise Integration Tests

This directory contains tests for **optional enterprise features** that integrate with the Verodat platform.

## What are these tests?

These tests verify that ADRI's enterprise integration features work correctly when connecting to Verodat's data governance platform. They are **completely optional** and only relevant if you're using Verodat Enterprise.

## Do I need to run these tests?

**No** - if you're using ADRI as an open source data quality tool, you can safely ignore these tests.

**Yes** - if you're evaluating or using [Verodat Enterprise](https://verodat.com/adri-enterprise), these tests verify your integration is working.

## How to run these tests

```bash
# Run only enterprise tests (requires Verodat account)
pytest tests/enterprise/ -v

# Run all tests EXCEPT enterprise tests (default for open source users)
pytest tests/ -v --ignore=tests/enterprise/
```

## Enterprise Features Tested

- **Verodat Logger**: Centralized audit logging to Verodat platform
- **API Integration**: Data upload and synchronization with Verodat
- **Authentication**: API key validation and connection testing

## Need Verodat Enterprise?

Visit [verodat.com/adri-enterprise](https://verodat.com/adri-enterprise) to learn about enterprise-scale data governance features.

---

**Note**: All ADRI core functionality works perfectly without any enterprise features. These integrations are purely additive for organizations that need centralized data governance.
