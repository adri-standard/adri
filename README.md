# ADRI - Stop AI Agents Breaking on Bad Data

**Prevent 80% of production agent failures with one decorator**

## 10-Second Setup

```bash
pip install adri
```

```python
from adri.decorators.guard import adri_protected

@adri_protected
def your_agent_function(data):
    # Your existing code - now protected!
    return result
```

**That's it.** Your AI agents are now protected from bad data.

## What You Get

✅ **Zero Configuration** - Works immediately with built-in standards  
✅ **Framework Agnostic** - Protects any Python function  
✅ **Offline First** - No external dependencies or API keys  
✅ **Sub-millisecond** - Intelligent caching for performance  

## Protection in Action

### ✅ Good Data (Protection Allows)
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
```

### ❌ Bad Data (Protection Blocks)
```
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 67.3/100 (Required: 80.0/100)

🔧 Fix This:
   • customer_id: Should be integer, got string
   • email: Invalid email format
   • age: Value -5 is outside valid range (18-120)
```

## Real Examples

```python
# Customer service agent
@adri_protected
def process_customer_request(customer_data):
    response = generate_support_response(customer_data)
    return response

# Financial analysis
@adri_protected(min_score=95)  # Extra strict
def analyze_loan_application(application_data):
    risk_assessment = calculate_risk(application_data)
    return risk_assessment

# Any Python function
@adri_protected
def my_function(data):
    return process_data(data)
```

## Next Steps

- **[Quick Start Guide](QUICK_START.md)** - Comprehensive examples for all frameworks
- **[Framework Examples](DETAILED_EXAMPLES.md)** - LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **[CLI Tools](QUICK_START.md#cli-tools)** - `adri assess`, `adri generate-standard`, etc.

## Support

- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Community support

---

**MIT License** - Use freely in any project. See [LICENSE](LICENSE) for details.
