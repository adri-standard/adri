# Implementation Plan

## Overview
Transform ADRI from a complex enterprise library structure into an AI Agent Engineer-friendly "try in 30 seconds" experience while preserving all advanced functionality.

The current 28+ root-level files create cognitive overload for AI engineers who just want to protect their agent workflows from bad data. This restructuring will prioritize immediate framework examples at the root level, hide development complexity in subdirectories, and provide a clear progression path from simple decorator usage to advanced enterprise features. The goal is to make ADRI feel like "copy this one line and you're protected" rather than requiring extensive setup and configuration.

## Types
Define new directory structure and file organization patterns for simplified AI engineer onboarding.

**New Root Structure Types:**
```
Root Level (AI Engineer Focused):
- README.md (streamlined 30-second start)
- langchain_example.py
- crewai_example.py
- autogen_example.py
- llamaindex_example.py
- haystack_example.py
- langgraph_example.py
- semantic_kernel_example.py
- basic_example.py
- QUICK_START.md

Framework Example Type:
- Standalone runnable files
- Zero external dependencies beyond pip install adri
- Complete working examples with sample data
- Clear comments explaining protection points

Hidden Complexity Type:
- /adri/ (core library - unchanged)
- /development/ (all dev tooling)
- /enterprise/ (advanced configs and docs)
- /testing/ (all test infrastructure)
```

**Configuration Types:**
```
Simple Config (embedded in examples):
- No external files required
- Sensible defaults built-in
- Optional customization through decorator params

Advanced Config (enterprise directory):
- Full YAML configuration files
- Complex environment setups
- Audit logging and governance features
```

## Files
Restructure project to prioritize AI engineer experience with framework examples at root level.

**New Files to Create:**
- `langchain_example.py` - Complete LangChain agent protection example
- `crewai_example.py` - CrewAI multi-agent protection example
- `autogen_example.py` - AutoGen conversation protection example
- `llamaindex_example.py` - LlamaIndex RAG protection example
- `haystack_example.py` - Haystack search pipeline protection example
- `langgraph_example.py` - LangGraph workflow protection example
- `semantic_kernel_example.py` - Semantic Kernel function protection example
- `basic_example.py` - Generic Python function protection example
- `QUICK_START.md` - 30-second getting started guide
- `development/README.md` - Guide for contributors and advanced users

**Files to Move:**
- `tests/` → `development/testing/`
- `scripts/` → `development/tools/`
- `docs/CONTRIBUTOR_DOCS/` → `development/docs/`
- `examples/` → `development/reference_examples/`
- `.flake8`, `.commitlintrc.json`, `.pre-commit-config.yaml` → `development/config/`
- `templates/` → `development/templates/`
- `adri-catalogue/` → `development/catalogue/`
- `AI-Development-docs/` → `development/ai-docs/`
- `subdir/` → `development/subdir/`
- `logs/` → `development/logs/`

**Files to Update:**
- `README.md` - Streamline to focus on 30-second experience with framework examples
- `pyproject.toml` - Update file exclusions for new structure
- `.gitignore` - Add development/ specific ignores
- `CONTRIBUTING.md` - Update with new development/ structure

**Files to Keep at Root:**
- `README.md` (updated)
- `LICENSE`
- `pyproject.toml` (updated)
- `setup.py`
- `VERSION.json`
- `CHANGELOG.md`
- `adri/` (core library)

## Functions
Create framework-specific example functions that demonstrate ADRI protection patterns.

**New Framework Example Functions:**
- `langchain_customer_service()` in `langchain_example.py`
  - File: `langchain_example.py`
  - Purpose: Show LangChain chain protection
  - Signature: `@adri_protected def langchain_customer_service(customer_data: dict) -> dict`

- `crewai_market_analysis()` in `crewai_example.py`
  - File: `crewai_example.py`
  - Purpose: Show CrewAI crew protection
  - Signature: `@adri_protected def crewai_market_analysis(market_data: dict) -> dict`

- `autogen_research_team()` in `autogen_example.py`
  - File: `autogen_example.py`
  - Purpose: Show AutoGen conversation protection
  - Signature: `@adri_protected def autogen_research_team(research_data: dict) -> dict`

- `llamaindex_rag_query()` in `llamaindex_example.py`
  - File: `llamaindex_example.py`
  - Purpose: Show LlamaIndex RAG protection
  - Signature: `@adri_protected def llamaindex_rag_query(query_data: dict) -> dict`

**Modified Functions:**
- Update `adri/cli/commands.py` → `development/tools/cli_commands.py`
  - Remove complex setup requirements for basic usage
  - Keep advanced CLI in development tools
  - Create simplified CLI entry points

**Example Function Pattern:**
```python
from adri.decorators.guard import adri_protected

@adri_protected
def framework_function(data):
    """
    Example of protecting [Framework] agents with ADRI.

    This function demonstrates:
    - Automatic data quality validation
    - Framework-specific integration patterns
    - Zero configuration required
    """
    # Mock framework integration
    return framework_specific_processing(data)
```

## Classes
Simplify class exposure and create example classes for common AI agent patterns.

**New Example Classes:**
- `CustomerServiceAgent` in `langchain_example.py`
  - File: `langchain_example.py`
  - Purpose: Complete LangChain customer service agent example
  - Key methods: `process_request()`, `generate_response()`
  - Inheritance: Uses LangChain base classes

- `MarketAnalysisCrew` in `crewai_example.py`
  - File: `crewai_example.py`
  - Purpose: Complete CrewAI market analysis crew example
  - Key methods: `analyze_market()`, `generate_insights()`
  - Inheritance: Uses CrewAI Crew class

- `ResearchTeam` in `autogen_example.py`
  - File: `autogen_example.py`
  - Purpose: Complete AutoGen research team example
  - Key methods: `conduct_research()`, `summarize_findings()`
  - Inheritance: Uses AutoGen agent classes

**Modified Classes:**
- Move complex configuration classes to `development/`
- Keep core `DataQualityAssessor`, `DataProtectionEngine` in `adri/core/`
- Simplify `adri/__init__.py` exports to focus on `adri_protected`

**Class Simplification Pattern:**
- Root examples: Focus on complete working agent classes
- Core library: Keep existing architecture unchanged
- Development: Move complex internal classes

## Dependencies
Maintain current lightweight dependency model while organizing development dependencies.

**No Changes to Core Dependencies:**
- Keep existing `adri` package dependencies minimal
- Pandas, PyYAML, Click remain core dependencies
- Framework dependencies remain optional

**Development Dependencies Organization:**
```python
# In pyproject.toml
[project.optional-dependencies]
dev = [
    # All current dev dependencies moved here
    "pytest>=7.0",
    "black>=23.0",
    # ... existing dev deps
]

frameworks = [
    # Optional framework dependencies for examples
    "langchain>=0.1.0",
    "crewai>=0.1.0",
    "pyautogen>=0.1.0",
    # ... other framework deps
]
```

**Example Dependencies:**
- Framework examples will include import fallbacks
- Mock implementations when frameworks not installed
- Clear installation instructions in each example

## Testing
Reorganize testing infrastructure into development directory while maintaining comprehensive coverage.

**Test File Reorganization:**
- Move `tests/` → `development/testing/`
- Keep all existing test functionality
- Update test discovery paths in CI/CD
- Maintain 90%+ coverage requirement

**New Test Categories:**
```
development/testing/
├── unit/           # Existing unit tests (moved)
├── integration/    # Existing integration tests (moved)
├── performance/    # Existing performance tests (moved)
├── examples/       # New: Test all root examples work
├── enterprise/     # Existing enterprise tests (moved)
└── fixtures/       # Existing test fixtures (moved)
```

**Example Testing Strategy:**
- Each root example must have corresponding test
- Tests verify examples run without framework dependencies
- CI/CD tests both with and without optional framework installs
- Smoke tests for 30-second experience validation

**Test Updates Required:**
- Update all import paths to reflect new structure
- Add example file execution tests
- Verify development/ structure in CI
- Test both simple and enterprise usage patterns

## Implementation Order
Phased approach to minimize disruption while enabling immediate AI engineer onboarding improvements.

**Phase 1: Create Root Examples (Priority 1)**
1. Create `basic_example.py` with generic protection pattern
2. Create `langchain_example.py` with complete LangChain integration
3. Create `crewai_example.py` with complete CrewAI integration
4. Create `autogen_example.py` with complete AutoGen integration
5. Create remaining framework examples (`llamaindex_`, `haystack_`, `langgraph_`, `semantic_kernel_`)
6. Create streamlined `QUICK_START.md`

**Phase 2: Reorganize Development Structure (Priority 2)**
7. Create `development/` directory structure
8. Move `tests/` → `development/testing/`
9. Move `scripts/` → `development/tools/`
10. Move `docs/CONTRIBUTOR_DOCS/` → `development/docs/`
11. Move development configs to `development/config/`

**Phase 3: Update Core Files (Priority 3)**
12. Update `README.md` to focus on 30-second framework examples
13. Update `pyproject.toml` file exclusions and structure
14. Update `.gitignore` for new development/ structure
15. Update `CONTRIBUTING.md` with new development workflow

**Phase 4: Clean Root Directory (Priority 4)**
16. Move remaining development artifacts to `development/`
17. Verify root contains only: examples, README, LICENSE, pyproject.toml, setup.py, VERSION.json, CHANGELOG.md, adri/
18. Test complete 30-second experience end-to-end
19. Update CI/CD for new structure

**Phase 5: Documentation and Communication (Priority 5)**
20. Update all documentation links and references
21. Create migration guide for existing users
22. Update GitHub README and description
23. Prepare announcement for community about simplified structure

**Validation Checkpoints:**
- After Phase 1: New user can copy example and be protected in 30 seconds
- After Phase 2: Development workflow remains fully functional
- After Phase 3: Package installation and core functionality unchanged
- After Phase 4: Root directory clean and intuitive for AI engineers
- After Phase 5: Community informed and documentation current

**Risk Mitigation:**
- Keep `adri/` core library completely unchanged
- Maintain backward compatibility for all public APIs
- Test package builds after each phase
- Verify existing user workflows remain functional
- Create rollback plan for each phase
