#!/bin/bash

# Local Windows Testing with ACT
# Run this to replicate Windows CI issues locally before pushing

echo "🔍 Setting up local Windows testing with ACT..."

# Check if ACT is installed
if ! command -v act &> /dev/null; then
    echo "❌ ACT is not installed. Please install it first:"
    echo "   macOS: brew install act"
    echo "   Other: https://github.com/nektos/act#installation"
    exit 1
fi

echo "✅ ACT is available"

# Create ACT configuration for Windows testing
cat > .actrc << 'EOF'
# ACT Configuration for Windows Testing
-P windows-latest=ghcr.io/catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
--artifact-server-path /tmp/artifacts
EOF

echo "✅ Created .actrc configuration"

# Create a focused Windows test workflow for local testing
cat > .github/workflows/test-windows-local.yml << 'EOF'
name: Windows Local Test

on:
  workflow_dispatch:

jobs:
  test-windows:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.11']  # Focus on 3.11 for local testing

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,test]

    - name: Run Windows-specific failing tests
      run: |
        python -c "import os; os.makedirs('tests/coverage', exist_ok=True)"

        # Run the specific failing tests to replicate issues
        echo "🧪 Running Windows temp directory cleanup tests..."
        pytest tests/integration/test_generate_standard_enriched.py::test_generate_standard_enriched_and_training_pass_guarantee -v

        echo "🧪 Running Windows config path tests..."
        pytest tests/test_config_loader.py::TestConfigLoaderIntegration::test_config_file_discovery_workflow -v
        pytest tests/test_config_loader.py::TestConfigLoaderEdgeCases::test_config_file_discovery_in_deep_directories -v

        echo "🧪 Running Windows logging path tests..."
        pytest tests/test_logging_local.py::TestLocalLoggingEdgeCases::test_legacy_config_compatibility -v
        pytest tests/unit/logging/test_local_comprehensive.py::TestLocalLoggingComprehensive::test_invalid_log_directory_handling -v

        echo "🧪 Running end-to-end workflow tests..."
        pytest tests/integration/test_end_to_end_workflows.py -v --tb=short
EOF

echo "✅ Created focused Windows test workflow"

# Create a test script to run specific failing tests
cat > run-failing-tests.py << 'EOF'
#!/usr/bin/env python3
"""
Local test runner for Windows-specific failing tests
"""
import subprocess
import sys

FAILING_TESTS = [
    "tests/integration/test_generate_standard_enriched.py::test_generate_standard_enriched_and_training_pass_guarantee",
    "tests/test_config_loader.py::TestConfigLoaderIntegration::test_config_file_discovery_workflow",
    "tests/test_config_loader.py::TestConfigLoaderEdgeCases::test_config_file_discovery_in_deep_directories",
    "tests/test_logging_local.py::TestLocalLoggingEdgeCases::test_legacy_config_compatibility",
    "tests/unit/logging/test_local_comprehensive.py::TestLocalLoggingComprehensive::test_invalid_log_directory_handling",
    # Add a few end-to-end tests that are failing
    "tests/integration/test_end_to_end_workflows.py::TestEndToEndWorkflows::test_new_user_complete_workflow",
]

def run_tests():
    """Run the failing tests locally"""
    print("🧪 Running Windows-specific failing tests locally...")

    for test in FAILING_TESTS:
        print(f"\n🔍 Testing: {test}")
        result = subprocess.run([
            "python", "-m", "pytest", test, "-v", "--tb=short"
        ], capture_output=False)

        if result.returncode != 0:
            print(f"❌ FAILED: {test}")
        else:
            print(f"✅ PASSED: {test}")

    print("\n✅ Local test run completed")

if __name__ == "__main__":
    run_tests()
EOF

chmod +x run-failing-tests.py

echo "✅ Created local test runner"

# Instructions for user
cat << 'EOF'

🚀 Windows Testing Setup Complete!

To test Windows issues locally:

1. **Run ACT with Windows simulation:**
   act -W .github/workflows/test-windows-local.yml

2. **Run failing tests locally (easier for development):**
   python run-failing-tests.py

3. **Run specific test categories:**
   # Temp directory cleanup issues
   pytest tests/integration/test_generate_standard_enriched.py -v

   # Path handling issues
   pytest tests/test_config_loader.py -k "discovery" -v

   # Logging path issues
   pytest tests/test_logging_local.py -k "legacy_config" -v

4. **Debug specific issues:**
   # Run with more verbose output
   pytest tests/integration/test_generate_standard_enriched.py::test_generate_standard_enriched_and_training_pass_guarantee -v -s --tb=long

🔧 Next Steps:
1. Fix the temp directory cleanup issues (most critical)
2. Fix Windows path handling in config tests
3. Fix logging path separator issues
4. Test locally before pushing to avoid CI cycles

EOF

echo "🎯 Ready to start local Windows testing!"
