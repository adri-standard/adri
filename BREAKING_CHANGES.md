# ADRI v6.0.0 Breaking Changes Migration Guide

## Overview

ADRI v6.0.0 introduces a major terminology migration from "standard" to "contract" across the entire framework. This positions ADRI as executable data contracts aligned with modern data architecture patterns (Data Mesh, Data Fabric, DataOps).

**Migration Timeline**: This is a one-time breaking change with NO backward compatibility.

## Breaking Changes Summary

### 1. API Parameter Rename

**OLD (v5.x)**:
```python
@adri_protected(standard="customer_data", data_param="data")
def process_customers(data):
    return results
```

**NEW (v6.0.0)**:
```python
@adri_protected(contract="customer_data", data_param="data")
def process_customers(data):
    return results
```

### 2. Directory Structure Changes

**OLD Structure**:
```
ADRI/
├── dev/
│   └── standards/       # Development contract files
├── prod/
│   └── standards/       # Production contract files
└── tutorials/
    └── customer_service_standard/
```

**NEW Structure**:
```
ADRI/
├── dev/
│   └── contracts/       # Development contract files
├── prod/
│   └── contracts/       # Production contract files
└── tutorials/
    └── customer_service_contract/
```

### 3. File Extension Changes

**OLD**: `*_standard.yaml`
**NEW**: `*_contract.yaml`

Examples:
- `customer_data_standard.yaml` → `customer_data_contract.yaml`
- `adri_execution_standard.yaml` → `adri_execution_contract.yaml`

### 4. Module Path Changes

**OLD Imports**:
```python
from adri.standards import StandardParser, StandardValidator
from adri.analysis import StandardGenerator
from adri.config.loader import resolve_standard_path
from adri.validator.loaders import load_standard
```

**NEW Imports**:
```python
from adri.contracts import ContractsParser, ContractValidator
from adri.analysis import ContractGenerator
from adri.config.loader import resolve_contract_path
from adri.validator.loaders import load_contract
```

### 5. CLI Command Changes

| Old Command | New Command |
|------------|-------------|
| `adri generate-standard <data>` | `adri generate-contract <data>` |
| `adri list-standards` | `adri list-contracts` |
| `adri show-standard <name>` | `adri show-contract <name>` |
| `adri validate-standard <file>` | `adri validate-contract <file>` |

### 6. Configuration File Changes

**OLD (adri-config.yaml)**:
```yaml
environments:
  development:
    paths:
      standards: ./ADRI/dev/standards
```

**NEW (adri-config.yaml)**:
```yaml
environments:
  development:
    paths:
      contracts: ./ADRI/dev/contracts
```

### 7. Environment Variable Changes

| Old Variable | New Variable |
|-------------|--------------|
| `ADRI_STANDARDS_DIR` | `ADRI_CONTRACTS_DIR` |

## Migration Steps

### Step 1: Update Code (5-10 minutes)

**Find and replace in your codebase**:

1. **API calls**: `standard=` → `contract=`
2. **Imports**: `adri.standards` → `adri.contracts`  
3. **Class names**: `StandardGenerator` → `ContractGenerator`
4. **Functions**: `load_standard()` → `load_contract()`

**Automated migration**:
```bash
# Update decorator usage
find . -name "*.py" -exec sed -i 's/@adri_protected(standard=/@adri_protected(contract=/g' {} \;

# Update imports
find . -name "*.py" -exec sed -i 's/from adri\.standards/from adri.contracts/g' {} \;
```

### Step 2: Rename Contract Files (2-5 minutes)

**Rename your contract YAML files**:
```bash
cd ADRI/dev/standards
for f in *_standard.yaml; do 
  mv "$f" "${f/_standard/_contract}"
done
```

### Step 3: Update Directory Structure (1 minute)

**Rename directories**:
```bash
mv ADRI/dev/standards ADRI/dev/contracts
mv ADRI/prod/standards ADRI/prod/contracts  # if you have prod
mv examples/standards examples/contracts     # if you have examples
```

### Step 4: Update Configuration (1 minute)

**Edit `ADRI/config.yaml`** or `adri-config.yaml`:
```yaml
# Change:
paths:
  standards: ./ADRI/dev/standards

# To:
paths:
  contracts: ./ADRI/dev/contracts
```

### Step 5: Update Environment Variables (if used)

```bash
# OLD
export ADRI_STANDARDS_DIR=./ADRI/dev/standards

# NEW  
export ADRI_CONTRACTS_DIR=./ADRI/dev/contracts
```

### Step 6: Test Your Migration

```bash
# Install updated ADRI
pip install --upgrade adri

# Test import
python -c "from adri import adri_protected; print('✓ Import works')"

# Test your functions
python your_agent_script.py
```

## Common Migration Issues

### Issue 1: Missing 'standard' parameter error

**Error**:
```
TypeError: adri_protected() got an unexpected keyword argument 'standard'
```

**Solution**: Change `standard=` to `contract=` in your decorator usage.

### Issue 2: Module not found error

**Error**:
```
ImportError: cannot import name 'StandardGenerator' from 'adri.standards'
```

**Solution**: 
- Change `from adri.standards` to `from adri.contracts`
- Change `StandardGenerator` to `ContractGenerator`

### Issue 3: Contract file not found

**Error**:
```
FileNotFoundError: Contract file not found at: ./ADRI/dev/contracts/customer_data.yaml
```

**Solution**: Ensure you've renamed both:
1. The directory: `standards/` → `contracts/`
2. The file: `*_standard.yaml` → `*_contract.yaml`

### Issue 4: Config path errors

**Error**:
```
KeyError: 'standards'
```

**Solution**: Update your `adri-config.yaml` to use `contracts:` instead of `standards:` in paths.

## Why This Change?

### Strategic Positioning

ADRI v6.0 positions the framework as **executable data contracts**, aligning with:

- **Data Mesh**: Domain-owned contracts with decentralized data ownership
- **Data Fabric**: Unified contract enforcement across data landscape
- **DataOps**: Automated quality gates in data pipelines

### Competitive Differentiation

"Contract" terminology differentiates ADRI from generic validation libraries:

- **Pydantic**: Type validation (schemas)
- **Great Expectations**: Data testing (expectations)
- **Pandera**: DataFrame validation (schemas)
- **ADRI**: Data contracts (executable + SLAs + governance)

### Industry Alignment

Modern data architectures increasingly use "contract" terminology:
- Data contracts define producer-consumer agreements
- Contracts include both schema AND quality SLAs
- Contracts are executable and enforceable
- Contracts align with microservices/API contract patterns

## Rollback (Not Recommended)

If you absolutely need to rollback to v5.x:

```bash
pip install adri==5.1.0
```

Note: v5.x will receive critical security patches only. New features are v6.0+.

## Support

- **Documentation**: https://docs.adri.dev
- **GitHub Issues**: https://github.com/adri-standard/adri/issues
- **Migration Help**: Create issue with `migration` label

## Checklist

Use this checklist to verify your migration:

- [ ] Updated all `standard=` to `contract=` in decorator calls
- [ ] Renamed `*_standard.yaml` files to `*_contract.yaml`
- [ ] Moved files from `standards/` to `contracts/` directories
- [ ] Updated `adri-config.yaml` paths
- [ ] Updated environment variables (if used)
- [ ] Updated imports from `adri.standards` to `adri.contracts`
- [ ] Updated class names (StandardGenerator → ContractGenerator)
- [ ] Ran tests to verify migration
- [ ] Updated CI/CD pipelines (if applicable)
- [ ] Updated documentation/README files

## Timeline

- **v5.1.0** (Current): Last version with "standard" terminology
- **v6.0.0** (This release): Complete contract terminology migration
- **v6.1.0+** (Future): New features on contract foundation

## Questions?

Ref: https://github.com/adri-standard/adri/discussions for migration questions.
