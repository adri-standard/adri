# ADRI Framework Examples Testing

This directory contains comprehensive testing for all ADRI framework examples, providing both free smoke tests and paid live integration tests.

## 🎯 Purpose

Test real framework integrations with ADRI protection to ensure:
- Examples work with actual OpenAI API calls
- ADRI decorators are properly implemented
- Framework integrations are production-ready
- Bad data is correctly blocked by ADRI

## 🏗️ Structure

```
tests/examples/
├── test_runner.py           # Interactive test runner
├── utils/                   # Testing utilities
│   ├── api_key_manager.py   # Secure API key handling
│   └── cost_controls.py     # Cost limiting & tracking
├── smoke_tests/             # FREE tests (no API calls)
│   ├── test_imports.py      # Import validation
│   └── test_decorators.py   # Decorator validation
└── integration_tests/       # PAID tests (real API calls)
    └── test_*_live.py       # Live framework tests
```

## 🆓 Smoke Tests (FREE)

Fast, free validation with no API calls:

- **Import Tests**: Verify all examples can be imported
- **Structure Tests**: Check file structure and shebangs
- **Decorator Tests**: Validate `@adri_protected` usage
- **README Tests**: Ensure documentation completeness

```bash
# Run all smoke tests
python tests/examples/test_runner.py --smoke

# Run specific framework
python tests/examples/test_runner.py --smoke --framework langchain
```

## 🔥 Live Integration Tests (PAID)

Real API tests with cost controls:

- **Real Framework Execution**: Actual LangChain, CrewAI, etc.
- **OpenAI Integration**: Real API calls with live responses
- **ADRI Protection**: Validate blocking of bad data
- **Error Handling**: Test graceful failure modes

```bash
# Run all live tests (prompts for API key)
python tests/examples/test_runner.py --live

# Run specific framework
python tests/examples/test_runner.py --live --framework crewai
```

## 💰 Cost Controls

Built-in protection against runaway costs:

- **Max Calls**: 5 API calls per framework, 35 total
- **Cost Limit**: $0.50 maximum per test run
- **Rate Limiting**: 1 second between API calls
- **Real-time Tracking**: Cost summary after each run

## 🔑 API Key Management

Secure handling of OpenAI API keys:

- **Interactive Prompts**: Never stored in code
- **Cost Warnings**: Clear cost information upfront
- **Confirmation Required**: Explicit consent for charges
- **Environment Detection**: Uses `OPENAI_API_KEY` if available

## 🚀 Quick Start

### 1. Interactive Mode (Recommended)

```bash
python tests/examples/test_runner.py
```

This launches an interactive menu where you can:
- Choose between free smoke tests or paid live tests
- Select specific frameworks or test all
- View cost estimates before proceeding
- Get real-time progress updates

### 2. Command Line Mode

```bash
# Free smoke tests only
python tests/examples/test_runner.py --smoke

# Live tests with API key prompt
python tests/examples/test_runner.py --live

# Test specific framework
python tests/examples/test_runner.py --live --framework langchain

# Show testing information
python tests/examples/test_runner.py --info
```

### 3. Direct pytest (Advanced)

```bash
# Run smoke tests directly
pytest tests/examples/smoke_tests/ -v

# Run live tests (requires OPENAI_API_KEY set)
export OPENAI_API_KEY=your_key_here
pytest tests/examples/integration_tests/ -v -s
```

## 📋 Framework Coverage

The testing framework covers all ADRI examples:

| Framework | Smoke Tests | Live Tests | Features Tested |
|-----------|-------------|------------|-----------------|
| **LangChain** | ✅ | ✅ | Customer service, QA pipeline, conversation chains |
| **CrewAI** | ✅ | 🚧 | Market analysis, research workflows, agent collaboration |
| **AutoGen** | ✅ | 🚧 | Multi-agent conversations, code review, group chat |
| **Haystack** | ✅ | 🚧 | Document search, QA pipelines, knowledge management |
| **LlamaIndex** | ✅ | 🚧 | Document processing, query engines, RAG systems |
| **LangGraph** | ✅ | 🚧 | State graphs, workflow automation, decision trees |
| **Semantic Kernel** | ✅ | 🚧 | AI functions, planning, memory operations |

## 🛡️ Safety Features

Multiple layers of protection:

- **API Key Security**: Never logged or stored
- **Cost Confirmation**: Explicit user consent required
- **Rate Limiting**: Prevents API flooding
- **Interrupt Protection**: Safe Ctrl+C handling
- **Error Recovery**: Graceful failure handling
- **Separate Test Suite**: Isolated from main tests

## 📊 Example Output

### Smoke Test Run
```
🆓 Running Smoke Tests (FREE)
========================================
🔍 Testing frameworks: langchain, crewai, autogen
⚡ Running tests...

test_imports.py::TestFrameworkImports::test_langchain_example_imports PASSED
test_imports.py::TestFrameworkImports::test_crewai_example_imports PASSED
test_decorators.py::TestADRIDecorators::test_langchain_example_has_decorators PASSED

✅ All smoke tests passed!
```

### Live Test Run
```
🔥 Running Live Integration Tests (PAID)
=============================================
💰 Estimated cost: $0.15
🎯 Testing frameworks: langchain
⚡ Running live tests...

test_langchain_live.py::TestLangChainLive::test_customer_service_good PASSED
✅ LangChain customer service test passed
   Customer: CUST001
   Response: I'd be happy to help you with your recent order...

💰 API USAGE COST SUMMARY
==================================================
📞 Total calls: 3/35
✅ Successful: 3
💵 Total cost: $0.045
💰 Remaining budget: $0.455
```

## 🔧 Configuration

Customize testing behavior by modifying:

- `utils/cost_controls.py`: Adjust cost limits and rate limiting
- `utils/api_key_manager.py`: Modify security prompts
- `test_runner.py`: Change framework list or menu options

## 🐛 Troubleshooting

### Common Issues

**"OPENAI_API_KEY environment variable required"**
- Solution: Set your API key or use interactive mode

**"Cost limit reached"**
- Solution: Reset cost controller or increase limits in configuration

**"Module import failed"**
- Solution: Check framework dependencies are installed

**"Syntax error in example"**
- Solution: Verify example files are valid Python

### Getting Help

1. **View Test Information**: `python tests/examples/test_runner.py --info`
2. **Run in Verbose Mode**: Add `-v` flag to pytest commands
3. **Check Example Structure**: Run smoke tests first
4. **Verify API Key**: Test with a simple OpenAI call outside ADRI

## 📈 Adding New Tests

### Adding a New Framework Test

1. **Create Live Test File**: `tests/examples/integration_tests/test_newframework_live.py`
2. **Follow Template**: Copy structure from `test_langchain_live.py`
3. **Add to Runner**: Update framework list in `test_runner.py`
4. **Update Documentation**: Add to framework coverage table

### Adding New Test Cases

1. **Import the Example**: Use `importlib.util` pattern
2. **Check Cost Limits**: Use `cost_controller.can_make_call()`
3. **Record API Calls**: Use `cost_controller.record_call()`
4. **Test ADRI Protection**: Include bad data test cases

## 🎓 Best Practices

- **Start with Smoke Tests**: Always run free tests first
- **Monitor Costs**: Check cost summary after live tests
- **Test Incrementally**: Use single framework testing during development
- **Document Changes**: Update README when adding new features
- **Safety First**: Never commit API keys or skip cost controls

## 📝 License

This testing framework is part of the ADRI project and follows the same MIT license.
