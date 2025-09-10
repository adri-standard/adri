"""
Dependency Testing Module for ADRI Framework Examples

This module contains comprehensive tests for the dependency validation system
implemented across all ADRI framework examples.

Test Categories:
- Mock-based dependency checking tests
- Virtual environment detection validation
- Interactive installation flow simulation
- Dependency-specific error scenarios
- Cross-framework dependency consistency
"""

# Framework dependency mappings for testing
FRAMEWORK_DEPENDENCIES = {
    "langchain": ["adri", "langchain", "langchain-openai", "openai"],
    "crewai": ["adri", "crewai", "langchain", "openai"],
    "autogen": ["adri", "pyautogen", "openai"],
    "llamaindex": ["adri", "llama-index", "openai"],
    "haystack": ["adri", "haystack-ai", "openai"],
    "langgraph": ["adri", "langgraph", "langchain-openai", "openai"],
    "semantic_kernel": ["adri", "semantic-kernel", "openai"],
}

# Test scenarios for dependency validation
DEPENDENCY_TEST_SCENARIOS = [
    {
        "name": "all_dependencies_missing",
        "description": "Test behavior when all dependencies are missing",
        "missing_packages": "all",
    },
    {
        "name": "only_adri_missing",
        "description": "Test behavior when only ADRI is missing",
        "missing_packages": ["adri"],
    },
    {
        "name": "only_framework_missing",
        "description": "Test behavior when only framework package is missing",
        "missing_packages": "framework_only",
    },
    {
        "name": "only_openai_missing",
        "description": "Test behavior when only OpenAI is missing",
        "missing_packages": ["openai"],
    },
    {
        "name": "partial_dependencies_missing",
        "description": "Test behavior with partial dependencies missing",
        "missing_packages": "partial",
    },
]

# Virtual environment test scenarios
VENV_TEST_SCENARIOS = [
    {
        "name": "venv_detected",
        "description": "Test when virtual environment is properly detected",
        "venv_active": True,
        "expected_message": "Virtual environment: DETECTED",
    },
    {
        "name": "venv_not_detected",
        "description": "Test when no virtual environment is detected",
        "venv_active": False,
        "expected_message": "Virtual environment: NOT DETECTED",
    },
]

# Interactive installation test scenarios
INSTALLATION_TEST_SCENARIOS = [
    {
        "name": "user_accepts_installation",
        "description": "Test when user accepts automatic installation",
        "user_input": "y",
        "expected_behavior": "install_packages",
    },
    {
        "name": "user_declines_installation",
        "description": "Test when user declines automatic installation",
        "user_input": "n",
        "expected_behavior": "show_manual_commands",
    },
    {
        "name": "user_requests_commands",
        "description": "Test when user requests to see installation commands",
        "user_input": "s",
        "expected_behavior": "show_commands_only",
    },
    {
        "name": "invalid_user_input",
        "description": "Test behavior with invalid user input",
        "user_input": "x",
        "expected_behavior": "reprompt_user",
    },
]

# Error handling test scenarios
ERROR_HANDLING_SCENARIOS = [
    {
        "name": "installation_failure",
        "description": "Test behavior when pip installation fails",
        "error_type": "subprocess.CalledProcessError",
        "expected_behavior": "graceful_fallback",
    },
    {
        "name": "non_interactive_environment",
        "description": "Test behavior in non-interactive environments",
        "error_type": "EOFError",
        "expected_behavior": "show_manual_instructions",
    },
    {
        "name": "permission_error",
        "description": "Test behavior when installation lacks permissions",
        "error_type": "PermissionError",
        "expected_behavior": "suggest_venv",
    },
]
