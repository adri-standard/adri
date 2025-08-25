#!/bin/bash

# ADRI Validator Local Testing Script
# This script runs all the same checks that GitHub Actions runs
# Use this before committing to catch issues early

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

# Track overall status
FAILED_CHECKS=()

# Function to run a check and track failures
run_check() {
    local check_name="$1"
    shift
    local command="$@"
    
    echo ""
    echo "Running: $check_name"
    echo "Command: $command"
    
    if eval $command; then
        print_status "$check_name passed"
    else
        print_error "$check_name failed"
        FAILED_CHECKS+=("$check_name")
        return 1
    fi
}

# Main testing sequence
print_header "ADRI Validator Local Testing"
echo "This will run all quality checks locally"
echo "Similar to what runs in GitHub Actions"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the adri-validator directory"
    exit 1
fi

# 1. Code Formatting Checks
print_header "Code Formatting Checks"

run_check "Black formatting" "black --check adri/ tests/" || true
run_check "isort import sorting" "isort --check-only adri/ tests/" || true

# 2. Code Quality Checks
print_header "Code Quality Checks"

run_check "Flake8 linting" "flake8 adri/ tests/" || true
run_check "MyPy type checking" "mypy adri/ tests/" || true

# 3. Security Checks
print_header "Security Checks"

run_check "Bandit security scan" "bandit -r adri/ -ll" || true

# Check if safety is installed
if command -v safety &> /dev/null; then
    run_check "Safety dependency check" "safety check --json" || true
else
    print_warning "Safety not installed, skipping dependency check"
    print_warning "Install with: pip install safety"
fi

# 4. Test Suite
print_header "Running Test Suite"

run_check "Pytest unit tests" "pytest tests/unit/ -v" || true
run_check "Pytest integration tests" "pytest tests/integration/ -v" || true

# 5. Test Coverage
print_header "Test Coverage Analysis"

if run_check "Coverage report" "pytest tests/ --cov=adri --cov-report=term-missing --cov-report=html" || true; then
    coverage_percent=$(coverage report | grep TOTAL | awk '{print $4}')
    echo "Overall coverage: $coverage_percent"
    
    # Check if coverage meets minimum threshold
    coverage_value=$(echo $coverage_percent | sed 's/%//')
    if (( $(echo "$coverage_value < 80" | bc -l) )); then
        print_warning "Coverage is below 80% threshold"
        FAILED_CHECKS+=("Coverage threshold")
    fi
fi

# 6. Documentation Checks
print_header "Documentation Checks"

# Check for missing docstrings
echo "Checking for missing docstrings..."
python -c "
import ast
import os
import sys

missing_docstrings = []

for root, dirs, files in os.walk('adri'):
    # Skip __pycache__ directories
    dirs[:] = [d for d in dirs if d != '__pycache__']
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            if not ast.get_docstring(node):
                                missing_docstrings.append(f'{filepath}:{node.lineno} - {node.name}')
                except SyntaxError:
                    pass

if missing_docstrings:
    print(f'Found {len(missing_docstrings)} missing docstrings')
    for item in missing_docstrings[:10]:  # Show first 10
        print(f'  - {item}')
    if len(missing_docstrings) > 10:
        print(f'  ... and {len(missing_docstrings) - 10} more')
else:
    print('All functions and classes have docstrings')
"

# 7. Pre-commit Hooks (if installed)
print_header "Pre-commit Hooks"

if [ -f ".pre-commit-config.yaml" ]; then
    if command -v pre-commit &> /dev/null; then
        run_check "Pre-commit hooks" "pre-commit run --all-files" || true
    else
        print_warning "pre-commit not installed"
        print_warning "Install with: pip install pre-commit"
        print_warning "Then run: pre-commit install"
    fi
else
    print_warning "No .pre-commit-config.yaml found"
fi

# 8. Check for common issues
print_header "Common Issues Check"

# Check for print statements (should use logging)
echo "Checking for print statements..."
if grep -r "print(" adri/ --include="*.py" | grep -v "# noqa" | grep -v "__str__" | grep -v "__repr__"; then
    print_warning "Found print statements - consider using logging instead"
else
    print_status "No print statements found"
fi

# Check for TODO comments
echo "Checking for TODO comments..."
todo_count=$(grep -r "TODO" adri/ tests/ --include="*.py" | wc -l)
if [ $todo_count -gt 0 ]; then
    print_warning "Found $todo_count TODO comments"
    grep -r "TODO" adri/ tests/ --include="*.py" | head -5
else
    print_status "No TODO comments found"
fi

# Final Summary
print_header "Test Summary"

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    print_status "All checks passed! ✨"
    echo ""
    echo "Your code is ready to commit!"
    echo "GitHub Actions should pass without issues."
    exit 0
else
    print_error "Some checks failed:"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  - $check"
    done
    echo ""
    echo "Please fix these issues before committing."
    echo "Run this script again after making fixes."
    exit 1
fi
