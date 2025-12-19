# ADRI Feature Marker System

## Overview

The ADRI Feature Marker System enables sustainable management of the relationship between the enterprise codebase (verodat-adri) and the open source codebase (adri). It uses inline code markers to explicitly label feature scope, which are then parsed to generate a human-readable governance registry.

**Key Benefits:**
- Work primarily in enterprise repo with full functionality
- Clear markers identify what code belongs where
- Auto-generated registry provides review checkpoint
- Automated sync to open source repo
- Dependency tracking prevents broken extractions
- No manual tracking required

## Quick Start

### 1. Add Markers to Your Code

```python
# @ADRI_FEATURE[schema_validation, scope=OPEN_SOURCE, deps=[core_validator]]
# Description: Auto-fix field name case mismatches
def validate_schema(data, contract_spec):
    """Schema validation with auto-fix."""
    # Your code here
    pass
# @ADRI_FEATURE_END[schema_validation]
```

### 2. Generate Registry

```bash
python scripts/generate_feature_registry.py
```

### 3. Review Changes

```bash
git diff FEATURE_REGISTRY.md
```

Look for lines like:
```diff
+ | new_feature | Description | file.py | ✅ ACTIVE | deps |
```

### 4. Commit Together

```bash
git add FEATURE_REGISTRY.md src/yourfile.py
git commit -m "feat: add new feature with markers"
```

## Marker Syntax

### Basic Marker

```python
# @ADRI_FEATURE[feature_name, scope=SCOPE_TYPE]
# Description: What this feature does
# Your code here
# @ADRI_FEATURE_END[feature_name]
```

### With Dependencies

```python
# @ADRI_FEATURE[advanced_feature, scope=OPEN_SOURCE, deps=[core_feature, helper_feature]]
# Description: Advanced functionality built on core features
# Your code here
# @ADRI_FEATURE_END[advanced_feature]
```

### With Status

```python
# @ADRI_FEATURE[experimental_feature, scope=OPEN_SOURCE, status=EXPERIMENTAL]
# Description: New feature under development
# Your code here
# @ADRI_FEATURE_END[experimental_feature]
```

## Feature Scopes

### OPEN_SOURCE
Code that belongs in the open source repository.
- Core ADRI functionality
- CLI commands
- Analysis tools
- Contract management
- Basic validation

**Example:**
```python
# @ADRI_FEATURE[cli_assess, scope=OPEN_SOURCE]
# Description: CLI assess command for running assessments
def assess_command(args):
    pass
# @ADRI_FEATURE_END[cli_assess]
```

### ENTERPRISE
Code that stays in the enterprise repository only.
- Verodat API integrations
- License validation
- Enterprise authentication
- Remote logging to proprietary services
- Commercial features

**Example:**
```python
# @ADRI_FEATURE[verodat_api_logging, scope=ENTERPRISE, deps=[auth_license]]
# Description: Upload assessment results to Verodat API
def send_to_verodat(data, api_key):
    pass
# @ADRI_FEATURE_END[verodat_api_logging]
```

### SHARED
Core functionality used by both repositories.
- Validation engine core
- Configuration system
- Common utilities
- Data structures

**Example:**
```python
# @ADRI_FEATURE[core_validator, scope=SHARED]
# Description: Core validation engine logic
class ValidationEngine:
    pass
# @ADRI_FEATURE_END[core_validator]
```

## Feature Naming Conventions

### Use Domain Prefixes

Organize features by domain using prefixes:

- `core_*` - Core shared functionality (SHARED)
- `cli_*` - Command-line interface (OPEN_SOURCE)
- `api_*` - API integrations (ENTERPRISE)
- `auth_*` - Authentication (ENTERPRISE)
- `validator_*` - Validation (OPEN_SOURCE)
- `logging_*` - Logging systems (SHARED)
- `contracts_*` - Contracts (OPEN_SOURCE)
- `analysis_*` - Analysis (OPEN_SOURCE)
- `decorator_*` - Decorators (OPEN_SOURCE)
- `config_*` - Configuration (SHARED)

### Good Names

✅ `validator_schema_auto_fix` - Clear, descriptive, domain prefix
✅ `cli_assess_command` - Clear purpose
✅ `api_verodat_upload` - Clear integration
✅ `logging_local_file` - Specific implementation

### Bad Names

❌ `stuff` - Too vague
❌ `function1` - Non-descriptive
❌ `temp_fix` - Temporary marker
❌ `v2_validator` - Version in name

## Marker Syntax by Language

### Python

```python
# @ADRI_FEATURE[feature_name, scope=OPEN_SOURCE]
# Description: Feature description
def my_function():
    pass
# @ADRI_FEATURE_END[feature_name]
```

### YAML

```yaml
# @ADRI_FEATURE[config_defaults, scope=SHARED]
# Description: Default configuration structure
settings:
  key: value
# @ADRI_FEATURE_END[config_defaults]
```

### Markdown

```markdown
<!-- @ADRI_FEATURE[open_source_docs, scope=OPEN_SOURCE] -->
<!-- Description: User-facing documentation -->

## Documentation Content

...

<!-- @ADRI_FEATURE_END[open_source_docs] -->
```

### Shell Scripts

```bash
# @ADRI_FEATURE[deployment_script, scope=ENTERPRISE]
# Description: Deployment automation
#!/bin/bash
echo "Deploying..."
# @ADRI_FEATURE_END[deployment_script]
```

## Working with Dependencies

### Declaring Dependencies

When a feature depends on other features, declare them:

```python
# @ADRI_FEATURE[advanced_validator, scope=OPEN_SOURCE, deps=[core_validator, schema_parser]]
# Description: Advanced validation built on core validator
def advanced_validate(data):
    # Uses core_validator and schema_parser
    pass
# @ADRI_FEATURE_END[advanced_validator]
```

### Dependency Rules

1. **Dependencies must exist** - Referenced features must be marked somewhere in the codebase
2. **No circular dependencies** - Features cannot depend on each other in a cycle
3. **Scope compatibility** - OPEN_SOURCE features cannot depend on ENTERPRISE features
4. **Extraction order** - Dependencies are extracted before dependents during sync

### Scope Compatibility Matrix

| Feature Scope | Can Depend On |
|--------------|---------------|
| OPEN_SOURCE | OPEN_SOURCE, SHARED |
| ENTERPRISE | OPEN_SOURCE, SHARED, ENTERPRISE |
| SHARED | SHARED only |

## Workflow

### Daily Development

1. **Write code** with markers as you go
2. **Run generator** before committing: `python scripts/generate_feature_registry.py`
3. **Review registry diff** in git to verify scope decisions
4. **Commit code + registry** together

### Reviewing Registry Changes

When reviewing `FEATURE_REGISTRY.md` in a PR or commit:

```diff
+ | new_api_feature | Verodat integration | api.py | ✅ ACTIVE | auth_system |
```

Ask yourself:
- Is the scope correct? (Should this be ENTERPRISE?)
- Is the description clear?
- Are dependencies appropriate?
- Does this align with project goals?

### Syncing to Open Source

Once features are mature and marked:

```bash
# Preview what will be synced
python scripts/sync_to_opensource.py --dry-run

# Perform actual sync
python scripts/sync_to_opensource.py

# Creates branch and PR in upstream repo
```

## Validation

### Run Validation

```bash
python scripts/validate_markers.py
```

### What Gets Validated

- **Syntax** - Markers are well-formed
- **Pairing** - Every START has a matching END
- **Dependencies** - All referenced features exist
- **Naming** - Follows conventions
- **Descriptions** - Not placeholders or too short
- **Scope compatibility** - Dependencies respect scope rules

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python scripts/validate_markers.py
if [ $? -ne 0 ]; then
    echo "Marker validation failed. Fix errors before committing."
    exit 1
fi
```

## Tools Reference

### generate_feature_registry.py

Generates `FEATURE_REGISTRY.md` from markers.

**Usage:**
```bash
python scripts/generate_feature_registry.py
```

**Output:**
- `FEATURE_REGISTRY.md` - Human-readable registry

### validate_markers.py

Validates all markers in codebase.

**Usage:**
```bash
python scripts/validate_markers.py
```

**Exit Codes:**
- `0` - All validations passed
- `1` - Validation errors found

### sync_to_opensource.py

Syncs OPEN_SOURCE and SHARED features to upstream repo.

**Usage:**
```bash
# Dry run (preview only)
python scripts/sync_to_opensource.py --dry-run

# Actual sync
python scripts/sync_to_opensource.py
```

## Configuration

Edit `.adri-markers.yaml` to configure:

```yaml
scan:
  include_patterns:
    - "src/**/*.py"
  exclude_patterns:
    - "tests/**"

feature_naming:
  domain_prefixes:
    - core_
    - cli_
  scope_defaults:
    core_: SHARED
    cli_: OPEN_SOURCE

sync:
  upstream_repo: ../adri
  default_branch: main
  create_pr: true
```

## Best Practices

### 1. Mark New Code Immediately

Add markers as you write code, not later:

✅ **Good:**
```python
# Write feature with marker from the start
# @ADRI_FEATURE[new_feature, scope=OPEN_SOURCE]
# Description: New validation rule
def new_validation_rule():
    pass
# @ADRI_FEATURE_END[new_feature]
```

❌ **Bad:**
```python
# Write code first, mark later (easy to forget)
def new_validation_rule():
    pass
```

### 2. Use Descriptive Names

✅ **Good:** `validator_field_type_check`
❌ **Bad:** `check1`

### 3. Write Clear Descriptions

✅ **Good:** "Validates field types match contract specifications"
❌ **Bad:** "validation stuff"

### 4. Review Registry Diffs

Always check `FEATURE_REGISTRY.md` changes before committing:

```bash
git diff FEATURE_REGISTRY.md
```

### 5. Keep Markers Updated

If you refactor code, update or move markers:

```python
# If you split a feature, update markers
# @ADRI_FEATURE[feature_part_a, scope=OPEN_SOURCE]
# Description: First part of refactored feature
def part_a():
    pass
# @ADRI_FEATURE_END[feature_part_a]

# @ADRI_FEATURE[feature_part_b, scope=OPEN_SOURCE, deps=[feature_part_a]]
# Description: Second part of refactored feature
def part_b():
    pass
# @ADRI_FEATURE_END[feature_part_b]
```

### 6. Don't Nest Markers

❌ **Bad:**
```python
# @ADRI_FEATURE[outer, scope=OPEN_SOURCE]
# Description: Outer feature
def outer():
    # @ADRI_FEATURE[inner, scope=OPEN_SOURCE]  # ERROR: Nested!
    # Description: Inner feature
    def inner():
        pass
    # @ADRI_FEATURE_END[inner]
# @ADRI_FEATURE_END[outer]
```

✅ **Good:**
```python
# @ADRI_FEATURE[outer, scope=OPEN_SOURCE]
# Description: Outer feature
def outer():
    def inner():
        pass
# @ADRI_FEATURE_END[outer]
```

## Troubleshooting

### Error: "Unclosed marker"

**Problem:** Started a marker but didn't close it.

```python
# @ADRI_FEATURE[my_feature, scope=OPEN_SOURCE]
# Description: My feature
def my_function():
    pass
# Missing: @ADRI_FEATURE_END[my_feature]
```

**Solution:** Add the END marker:
```python
# @ADRI_FEATURE_END[my_feature]
```

### Error: "Mismatched markers"

**Problem:** END marker doesn't match START marker.

```python
# @ADRI_FEATURE[feature_a, scope=OPEN_SOURCE]
# Description: Feature A
def my_function():
    pass
# @ADRI_FEATURE_END[feature_b]  # Wrong name!
```

**Solution:** Match the names:
```python
# @ADRI_FEATURE_END[feature_a]
```

### Error: "Unknown dependency"

**Problem:** Referenced a feature that doesn't exist.

```python
# @ADRI_FEATURE[my_feature, scope=OPEN_SOURCE, deps=[nonexistent_feature]]
```

**Solution:** Either create the dependency or remove the reference.

### Error: "Circular dependency"

**Problem:** Features depend on each other in a cycle.

```python
# Feature A depends on B
# @ADRI_FEATURE[feature_a, scope=OPEN_SOURCE, deps=[feature_b]]

# Feature B depends on A (circular!)
# @ADRI_FEATURE[feature_b, scope=OPEN_SOURCE, deps=[feature_a]]
```

**Solution:** Refactor to remove circular dependency.

## FAQ

### Q: Do I need to mark every function?

**A:** No. Mark logical features that make sense to track independently. A feature might span multiple functions or just one.

### Q: Can I have multiple features in one file?

**A:** Yes, definitely. Large files often contain multiple features.

### Q: What if I'm not sure about the scope?

**A:** Start with your best guess. The registry review process will help identify issues. When in doubt:
- Core functionality → SHARED
- User-facing features → OPEN_SOURCE
- Commercial/proprietary → ENTERPRISE

### Q: Can I change a feature's scope later?

**A:** Yes. Edit the marker, regenerate the registry, and review the diff. The change will be visible in version control.

### Q: How often should I regenerate the registry?

**A:** Before every commit that modifies marked code or adds new markers.

### Q: What if validation fails?

**A:** Fix the errors reported by `validate_markers.py` before committing. The errors will guide you to the problems.

## Examples

### Example 1: CLI Command (OPEN_SOURCE)

```python
# @ADRI_FEATURE[cli_assess_command, scope=OPEN_SOURCE, deps=[core_validator]]
# Description: Command-line interface for running assessments
def assess_command(args):
    """Run assessment from CLI."""
    validator = create_validator(args.contract)
    result = validator.assess(args.data)
    print_results(result)
# @ADRI_FEATURE_END[cli_assess_command]
```

### Example 2: Verodat Integration (ENTERPRISE)

```python
# @ADRI_FEATURE[api_verodat_upload, scope=ENTERPRISE, deps=[auth_license]]
# Description: Upload assessment results to Verodat platform
def upload_to_verodat(assessment_data, api_key):
    """Send assessment to Verodat for storage and analysis."""
    if not verify_license(api_key):
        raise AuthenticationError("Invalid license key")
    
    response = requests.post(VERODAT_API_URL, json=assessment_data)
    return response.json()
# @ADRI_FEATURE_END[api_verodat_upload]
```

### Example 3: Shared Core (SHARED)

```python
# @ADRI_FEATURE[core_validator_engine, scope=SHARED]
# Description: Core validation engine used by both enterprise and open source
class ValidationEngine:
    """Core validation logic."""
    
    def __init__(self, contract):
        self.contract = contract
    
    def validate(self, data):
        """Run validation rules."""
        return self._run_rules(data)
# @ADRI_FEATURE_END[core_validator_engine]
```

## Getting Help

If you have questions about the marker system:

1. Read this documentation
2. Check `FEATURE_REGISTRY.md` for examples
3. Run `python scripts/validate_markers.py` for guidance
4. Review `marker_system_implementation_plan.md` for technical details

## Summary

The marker system enables:
- ✅ Clear separation between enterprise and open source code
- ✅ Automated governance through registry reviews
- ✅ Safe, automated syncing to open source repo
- ✅ Dependency tracking and validation
- ✅ Easy collaboration and code review

Start marking your code today to establish sustainable open source/enterprise management!
