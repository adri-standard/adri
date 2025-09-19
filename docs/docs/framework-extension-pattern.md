---
sidebar_position: 7
---

# Framework Extension Pattern - Streamlined ADRI Examples

This document outlines the proven pattern for creating streamlined ADRI framework examples that focus on value demonstration rather than dependency management.

## Pattern Overview

**Transformation:** 700-900 line bloated examples → 100-line focused demonstrations

**Key Principle:** Separate setup concerns from value demonstration

## File Structure Pattern

```
tools/
  adri-setup.py                    # Universal setup tool
examples/
  utils/
    problem_demos.py               # Reusable GitHub issue scenarios
  [framework]-[use-case].py        # Streamlined 100-line examples
docs/
  setup-tool-guide.md             # Setup tool documentation
  framework-extension-pattern.md  # This pattern guide
```

## Implementation Steps

### Step 1: Research Framework GitHub Issues

**Goal:** Identify specific validation problems ADRI solves

**Process:**
1. Search framework GitHub repository for validation-related issues
2. Document specific issue numbers and descriptions
3. Categorize by impact type (conversation, function calls, data flow)
4. Quantify business impact for AI Agent Engineers

**Example - AutoGen Research:**
```
54+ documented validation issues:
• Issue #6819: "Conversational flow is not working as expected"
• Issue #5736: "Function Arguments as Pydantic Models fail"
• Issue #6123: "Internal Message Handling corruption"
Business Impact: Research collaboration workflows break
```

### Step 2: Add Framework to Setup Tool

**File:** `tools/adri-setup.py`

**Pattern:**
```python
FRAMEWORKS = {
    'framework_name': {
        'packages': ['adri', 'framework-package', 'openai'],
        'import_names': ['adri', 'framework_import', 'openai'],
        'api_keys': ['OPENAI_API_KEY'],  # or other required keys
        'description': 'Framework description for AI engineers'
    }
}
```

**Example - AutoGen:**
```python
'autogen': {
    'packages': ['adri', 'pyautogen', 'openai'],
    'import_names': ['adri', 'autogen', 'openai'],
    'api_keys': ['OPENAI_API_KEY'],
    'description': 'Microsoft AutoGen multi-agent conversations'
}
```

### Step 3: Create Problem Demonstration Data

**File:** `examples/utils/problem_demos.py`

**Pattern:**
```python
class FrameworkProblems:
    """Framework-specific problem scenarios based on documented GitHub issues."""

    # Issue #number: "Description"
    SCENARIO_GOOD = {
        # Valid data that should work normally
        "field1": "valid_value",
        "field2": ["valid", "list"],
        "field3": 42
    }

    SCENARIO_BAD = {
        # Bad data that causes the documented GitHub issue
        "field1": "",  # Empty value breaks processing
        "field2": "not_a_list",  # Wrong type causes failures
        "field3": -1  # Invalid value confuses framework
    }
```

**Integration Pattern:**
```python
def get_framework_problems(framework: str) -> Dict[str, Any]:
    problems = {
        'framework': {
            'scenario_name': {
                'good': FrameworkProblems.SCENARIO_GOOD,
                'bad': FrameworkProblems.SCENARIO_BAD,
                'github_issue': '#issue_number',
                'business_impact': 'Specific impact description'
            }
        }
    }
    return problems.get(framework, {})
```

### Step 4: Create Streamlined Example

**File:** `examples/[framework]-[use-case].py`

**Template Structure (~100 lines):**
```python
#!/usr/bin/env python3
"""
Framework + ADRI: Stop Use Case Failures in 30 Seconds

🚨 THE PROBLEM: Framework has X+ documented validation issues
   • Issue #number: "Description"
   • Issue #number: "Description"
   • Issue #number: "Description"
   • Business impact description

✨ THE SOLUTION: ADRI prevents X% of Framework failures
   • @adri_protected decorators validate data before processing
   • Complete audit trails for compliance
   • Works with any Framework workflow

🚀 SETUP: Run setup tool first, then this example:
   python tools/adri-setup.py --framework framework_name
   export API_KEY="your-key-here"
   python examples/framework-use-case.py

💰 Cost: ~$X.XX for full demonstration
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from adri.decorators.guard import adri_protected
from examples.utils.problem_demos import get_framework_problems

# Import framework with graceful fallback
try:
    import framework_module
    FRAMEWORK_AVAILABLE = True
except ImportError:
    print("❌ Framework not installed. Run: python tools/adri-setup.py --framework framework_name")
    FRAMEWORK_AVAILABLE = False

# Validate setup
if not os.getenv('API_KEY'):
    print("❌ API key required. Run setup tool for guidance:")
    print("   python tools/adri-setup.py --framework framework_name")
    exit(1)

if not FRAMEWORK_AVAILABLE:
    exit(1)

# Get real problem scenarios from GitHub issues
problems = get_framework_problems('framework_name')


class UseCaseAgent:
    """Production Framework agent with ADRI protection."""

    def __init__(self):
        """Initialize real Framework components."""
        # Real framework initialization here
        pass

    @adri_protected
    def primary_function(self, data):
        """
        Function description with ADRI protection.

        Prevents GitHub Issue #number: "Description"
        ADRI validates data before Framework processing.
        """
        print(f"🎯 Processing: data.get('key_field', 'N/A')")

        # Real framework processing here
        return {
            "result": "success",
            "processed": True
        }

    @adri_protected
    def secondary_function(self, data):
        """
        Function description with ADRI protection.

        Prevents GitHub Issue #number: "Description"
        """
        print(f"🔧 Executing: data.get('action', 'N/A')")

        # Real framework processing here
        return {"status": "completed"}


def main():
    """Demonstrate ADRI preventing real Framework GitHub issues."""

    print("🛡️  ADRI + Framework: Real GitHub Issue Prevention")
    print("=" * 55)
    print(f"🎯 Demonstrating protection against X+ documented Framework issues")
    print("   📋 Based on real GitHub issues from Framework repository")
    print("   ✅ ADRI blocks bad data before it breaks your agents")
    print()

    agent = UseCaseAgent()

    # Test scenarios for each GitHub issue
    for scenario_name, scenario_data in problems.items():
        print(f"📊 Test: scenario_name (GitHub scenario_data['github_issue'])")

        # Test good data
        try:
            result = getattr(agent, scenario_name.replace('_', ''))(scenario_data['good'])
            print("✅ Good data: Processing successful")
        except Exception as e:
            print(f"❌ Unexpected error: e")

        # Test bad data
        try:
            result = getattr(agent, scenario_name.replace('_', ''))(scenario_data['bad'])
            print("⚠️  Bad data allowed through (shouldn't happen)")
        except Exception:
            print(f"✅ ADRI blocked bad data - preventing GitHub scenario_data['github_issue']")

        print()

    print("=" * 55)
    print("🎉 ADRI Protection Complete!")
    print()
    print("📋 What ADRI Protected Against:")
    for scenario_name, scenario_data in problems.items():
        print(f"• Issue scenario_data['github_issue']: scenario_data['business_impact']")

    print()
    print(f"🚀 Next Steps for Framework Engineers:")
    print("• Add @adri_protected to your key functions")
    print(f"• Protect Framework initialization and data processing")
    print("• Customize data standards for your domain")
    print("• Enable audit logging for compliance")

    print()
    print("📖 Learn More:")
    print("• Setup tool: python tools/adri-setup.py --list")
    print("• Other frameworks: examples/langchain-*.py, examples/crewai-*.py")
    print("• Full guide: docs/ai-engineer-onboarding.md")


if __name__ == "__main__":
    main()
```

### Step 5: Update Documentation

**Files to Update:**
- `README.md` - Add framework to examples section
- `docs/setup-tool-guide.md` - Add to supported frameworks table
- Framework-specific documentation as needed

**README Pattern:**
```markdown
### 🤖 Framework → [`examples/framework-use-case.py`](examples/framework-use-case.py)
```python
@adri_protected
def primary_function(data):
    # Prevents GitHub #issue: "Description"
    # Prevents GitHub #issue: "Description"
```
**Setup:** `python tools/adri-setup.py --framework framework_name`
```

## Quality Checklist

Before releasing a new framework integration:

### ✅ Setup Tool Integration
- [ ] Framework added to `FRAMEWORKS` dict with correct packages
- [ ] Import names match actual Python imports
- [ ] API keys correctly specified
- [ ] Description is clear for AI Agent Engineers

### ✅ Problem Demonstration
- [ ] At least 3 real GitHub issues documented with specific numbers
- [ ] Good/bad data scenarios clearly show the problems
- [ ] Business impact clearly explained for target audience
- [ ] Data scenarios realistic for the framework's typical usage

### ✅ Example Implementation
- [ ] ~100 lines focused on value demonstration
- [ ] Real framework integration (not just mocks)
- [ ] Clear problem/solution narrative in docstring
- [ ] Graceful fallback when framework not installed
- [ ] Proper imports and path handling

### ✅ Value Proposition
- [ ] Specific GitHub issues cited in output
- [ ] Clear before/after demonstration
- [ ] Business impact clearly communicated
- [ ] Next steps actionable for framework engineers
- [ ] Cost estimate provided if applicable

### ✅ Documentation
- [ ] README updated with framework entry
- [ ] Setup tool guide updated
- [ ] Example tested end-to-end
- [ ] Clear setup and run instructions

## Success Metrics

A successful framework integration should achieve:

1. **30-Second Value:** AI Agent Engineer sees specific problems solved in 30 seconds
2. **Zero Friction:** One setup command handles all dependencies
3. **Real Problems:** Based on documented GitHub issues, not hypothetical scenarios
4. **Clear Next Steps:** Specific guidance for adopting ADRI in their framework

## Reusable Components

### Problem Research Template
```
Framework: Framework Name
GitHub Repository: URL
Search Terms: ["validation", "data quality", "input error", "parsing", "format"]
Issues Found: Number
Key Patterns:
• Pattern 1: Description
• Pattern 2: Description
Business Impact: Impact for AI Agent Engineers
```

### Testing Script Template
```bash
#!/bin/bash
# Test framework integration end-to-end

echo "Testing framework integration..."

# Test setup tool
python tools/adri-setup.py --framework framework_name --auto-install

# Test example without dependencies
python examples/framework-use-case.py

# Verify value proposition visible
if grep -q "GitHub Issue" examples/framework-use-case.py; then
    echo "✅ GitHub issues referenced"
else
    echo "❌ No GitHub issues found"
fi

echo "Framework integration test complete"
```

This pattern ensures consistent, high-quality framework integrations that immediately demonstrate ADRI's value to AI Agent Engineers from any framework background.
