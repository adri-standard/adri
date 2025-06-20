# ADRI v1.1 Roadmap (ARCHIVED)

> **⚠️ ARCHIVED DOCUMENT**: This roadmap was created in January 2024 for the originally planned v1.1 release. The project has since evolved differently, and is currently at v0.2.0b1 as of June 2025. Please refer to [ROADMAP.md](ROADMAP.md) for the current project roadmap.

---

## Original v1.1 Plan (Historical Reference)

### Overview

ADRI v1.0 was planned to ship with a comprehensive set of pre-built rules covering 80% of common data quality needs. Version 1.1 was intended to expand this coverage with specialized rules requested by the community.

### Original Timeline

**Target Release**: Q2 2024 (3-4 months after v1.0)

### High Priority Rules (Originally Planned)

These rules addressed the most common gaps identified:

1. **DuplicateDetectionRule** (Consistency)
   - Identify duplicate records based on configurable key fields
   - Exact and fuzzy matching capabilities
   
2. **UniqueKeyRule** (Validity)
   - Ensure specified fields contain unique values
   - Single and composite key validation

3. **DomainValueRule** (Plausibility)
   - Validate fields against domain-specific value sets
   - Dynamic domain loading from external sources

### What Actually Happened

The project took a different direction:

1. **Template-First Approach**: Instead of focusing on individual rules, ADRI evolved to use a template-based system where rules are defined within industry-specific templates.

2. **Simpler Architecture**: Rather than the complex rule system originally envisioned, ADRI now uses dimension assessors with template-configurable rules.

3. **Current Focus**: The project is currently focused on:
   - Stabilizing the core assessment framework
   - Building a comprehensive template library
   - Improving the assessment modes (Discovery/Validation)
   - Enhancing framework integrations

### Lessons Learned

1. **Simplicity Wins**: The template-based approach is easier to understand and use
2. **Community Templates**: Industry-specific templates are more valuable than generic rules
3. **Assessment Modes**: Discovery vs Validation modes address real user needs better

### Current Development

For the actual current roadmap and development priorities, please see:
- [ROADMAP.md](ROADMAP.md) - Current project roadmap
- [GitHub Issues](https://github.com/adri-ai/adri/issues) - Active development tasks
- [Release Notes](CHANGELOG.md) - What's actually been delivered

---

*Original Document Date: January 2024*  
*Archive Date: June 2025*  
*Archive Reason: Project evolved in a different direction than originally planned*
