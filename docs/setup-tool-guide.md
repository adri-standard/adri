# ADRI Setup Tool Guide - Framework Environment Management

The ADRI Universal Setup Tool (`tools/adri-setup.py`) handles dependency installation and environment setup for all AI framework examples, keeping the examples themselves focused on demonstrating value rather than managing dependencies.

## Design Philosophy

**Problem:** Previous examples were 700-900 lines each, with setup code obscuring ADRI's value proposition.

**Solution:** Separate setup concerns from value demonstration:
- **Setup Tool:** Handles all dependency management and environment validation
- **Examples:** Focus on showing real GitHub issues prevented by ADRI
- **Clear Path:** Setup → Run → See Value → Adopt

## Quick Usage

```bash
# List available frameworks
python tools/adri-setup.py --framework autogen --list

# Setup a specific framework
python tools/adri-setup.py --framework autogen

# Setup all frameworks at once
python tools/adri-setup.py --framework all --auto-install

# Run the streamlined example
python examples/autogen-research-collaboration.py
```

## Supported Frameworks

| Framework | Description | Example File |
|-----------|-------------|--------------|
| `autogen` | Microsoft AutoGen multi-agent conversations | `examples/autogen-research-collaboration.py` |
| `langchain` | LangChain agent chains and workflows | `examples/langchain-customer-service.py` |
| `crewai` | CrewAI multi-agent crew coordination | `examples/crewai-business-analysis.py` |
| `llamaindex` | LlamaIndex RAG and document processing | `examples/llamaindex-document-processing.py` |
| `haystack` | Haystack search and NLP pipelines | `examples/haystack-knowledge-management.py` |
| `langgraph` | LangGraph workflow automation | `examples/langgraph-workflow-automation.py` |
| `semantic_kernel` | Microsoft Semantic Kernel AI orchestration | `examples/semantic-kernel-ai-orchestration.py` |

## Setup Tool Features

### Environment Validation
- ✅ Python version compatibility check
- ✅ Virtual environment detection and recommendations
- ✅ pip availability and version validation
- ✅ Platform-specific installation guidance (macOS, Linux, Windows)

### Dependency Management
- ✅ Framework-specific package installation
- ✅ Import validation after installation
- ✅ Automatic dependency resolution
- ✅ Graceful error handling with actionable guidance

### API Key Configuration
- ✅ OpenAI API key detection and validation
- ✅ Key format validation (starts with 'sk-' or 'sk-proj-')
- ✅ Setup guidance with cost estimates
- ✅ Direct links to API key management

## Example Flow - AutoGen

### 1. Setup Environment
```bash
python tools/adri-setup.py --framework autogen
```

**Output:**
```
🚀 Setting up ADRI + Autogen
============================================================
🔍 Checking Python Environment...
🐍 Python: 3.11.5
🌐 Virtual environment: ACTIVE
📦 pip 23.2.1

📦 Installing autogen dependencies...
🎯 Framework: Microsoft AutoGen multi-agent conversations
📝 Packages: adri, pyautogen, openai

Install autogen packages? [y/N]: y
🔄 Installing: adri pyautogen openai
✅ Installation completed!

🔍 Testing autogen imports...
✅ adri
✅ autogen
✅ openai

🔑 Checking API keys for autogen...
❌ OPENAI_API_KEY: not set

🔧 API Key Setup Instructions:
   export OPENAI_API_KEY='your-key-here'
   📖 Get key: https://platform.openai.com/api-keys
   💰 Cost estimate per example: ~$0.10

🎉 autogen setup complete!
```

### 2. Configure API Key
```bash
export OPENAI_API_KEY="your-key-here"
```

### 3. Run Example
```bash
python examples/autogen-research-collaboration.py
```

**Output:**
```
🛡️  ADRI + AutoGen: Real GitHub Issue Prevention
=======================================================
🎯 Demonstrating protection against 54+ documented AutoGen issues
   📋 Based on real GitHub issues from AutoGen repository
   ✅ ADRI blocks bad data before it breaks your agents
   📊 Complete audit trails for research compliance

📊 Test 1: Conversation Flow Protection (GitHub #6819)
🔬 Starting: AI in Healthcare Research
   👥 Participants: researcher, data_analyst, report_writer
   🎯 Expected rounds: 5
✅ Good conversation data: Research collaboration started successfully
✅ ADRI blocked bad conversation data - preventing GitHub #6819

📊 Test 2: Function Call Protection (GitHub #5736)
🔧 Calling: analyze_research_data
   📊 Analysis: sentiment_analysis
   📝 Sample size: 1000
✅ Good function data: Research tool executed successfully
✅ ADRI blocked bad function data - preventing GitHub #5736

📊 Test 3: Message Handling Protection (GitHub #6123)
📨 Message from researcher to data_analyst
   📋 Type: research_request
   📎 Attachments: 1
✅ Good message data: Agent communication successful
✅ ADRI blocked bad message data - preventing GitHub #6123

=======================================================
🎉 ADRI Protection Complete!

📋 What ADRI Protected Against:
• Issue #6819: Conversation flow breakdowns
• Issue #5736: Function argument validation failures
• Issue #6123: Message handling corruption
• Plus 51+ other documented AutoGen validation issues

🚀 Next Steps for AutoGen Engineers:
• Add @adri_protected to your conversation functions
• Protect group chat initialization and agent messaging
• Customize data standards for your research domain
• Enable audit logging for research compliance
```

## Architecture Benefits

### For AI Agent Engineers
- **Immediate Value:** See specific GitHub issues prevented in 30 seconds
- **No Setup Friction:** One command handles all dependencies
- **Clear Next Steps:** Specific guidance for their framework
- **Real Problems:** Based on 1,998+ documented GitHub issues

### For Framework Adoption
- **Universal Pattern:** Same setup flow works for all frameworks
- **Scalable:** Easy to add new frameworks
- **Maintainable:** Setup logic separated from demonstration logic
- **Testable:** Each component can be tested independently

## Troubleshooting

### Common Issues

**Import Errors After Installation:**
```bash
# Solution: Restart Python environment
# Exit current session and restart terminal
python examples/autogen-research-collaboration.py
```

**Virtual Environment Recommended:**
```bash
# Create clean environment
python -m venv adri_env
source adri_env/bin/activate  # Linux/Mac
# OR
adri_env\Scripts\activate     # Windows

# Re-run setup
python tools/adri-setup.py --framework autogen
```

**API Key Issues:**
```bash
# Validate key format
echo $OPENAI_API_KEY  # Should start with 'sk-'

# Test key validity
python -c "import openai; client = openai.OpenAI(); print(client.models.list().data[0].id)"
```

### Advanced Usage

**Non-Interactive Installation:**
```bash
python tools/adri-setup.py --framework autogen --auto-install
```

**Setup Multiple Frameworks:**
```bash
python tools/adri-setup.py --framework all --auto-install
```

**Development Mode:**
```bash
# Install with development dependencies
pip install -e .[dev]
python tools/adri-setup.py --framework autogen
```

## Extending to New Frameworks

To add a new framework to the setup tool:

1. **Add Framework Configuration** in `tools/adri-setup.py`:
```python
FRAMEWORKS = {
    'new_framework': {
        'packages': ['adri', 'new-framework', 'openai'],
        'import_names': ['adri', 'new_framework', 'openai'],
        'api_keys': ['OPENAI_API_KEY'],
        'description': 'New Framework description'
    }
}
```

2. **Create Problem Scenarios** in `examples/utils/problem_demos.py`:
```python
class NewFrameworkProblems:
    PROBLEM_SCENARIO_GOOD = {...}
    PROBLEM_SCENARIO_BAD = {...}
```

3. **Create Streamlined Example** in `examples/new-framework-*.py`:
```python
@adri_protected
def framework_function(data):
    # Prevents GitHub Issue #XYZ: Specific problem
    return framework_processing(data)
```

4. **Update README** with new framework entry and setup instructions.

This architecture ensures consistent setup experience across all AI frameworks while keeping examples focused on demonstrating ADRI's value proposition.
