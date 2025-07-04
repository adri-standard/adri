#!/bin/bash

# ADRI Validator Development Environment Setup
# This script sets up the complete development environment with all quality tools

set -e  # Exit on any error

echo "🚀 Setting up ADRI Validator development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the adri-validator root directory."
    exit 1
fi

print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

print_success "Python version $python_version is compatible"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode with all dependencies
print_status "Installing ADRI Validator in development mode..."
pip install -e ".[dev]"

# Install additional development tools
print_status "Installing additional development tools..."
pip install pre-commit pytest-benchmark memory-profiler psutil

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
pre-commit install

print_success "Pre-commit hooks installed"

# Run initial quality checks
print_status "Running initial quality checks..."

echo "🎨 Checking code formatting..."
if black --check adri/ tests/ 2>/dev/null; then
    print_success "Code formatting is correct"
else
    print_warning "Code formatting issues found. Run 'black adri/ tests/' to fix."
fi

echo "📦 Checking import sorting..."
if isort --check-only adri/ tests/ 2>/dev/null; then
    print_success "Import sorting is correct"
else
    print_warning "Import sorting issues found. Run 'isort adri/ tests/' to fix."
fi

echo "🔍 Running linting checks..."
if flake8 adri/ tests/ 2>/dev/null; then
    print_success "No linting issues found"
else
    print_warning "Linting issues found. Check output above."
fi

echo "🔬 Running type checking..."
if mypy adri/ --ignore-missing-imports 2>/dev/null; then
    print_success "Type checking passed"
else
    print_warning "Type checking issues found. Check output above."
fi

# Run security checks
print_status "Running security checks..."

echo "🔒 Running Bandit security scan..."
if bandit -r adri/ -q 2>/dev/null; then
    print_success "No security issues found"
else
    print_warning "Security issues found. Run 'bandit -r adri/' for details."
fi

echo "🛡️ Running Safety vulnerability check..."
if safety check 2>/dev/null; then
    print_success "No known vulnerabilities found"
else
    print_warning "Vulnerabilities found. Check output above."
fi

# Run tests
print_status "Running test suite..."
if pytest tests/unit/ -v --tb=short 2>/dev/null; then
    print_success "All tests passed"
else
    print_warning "Some tests failed. Run 'pytest tests/unit/ -v' for details."
fi

# Create useful aliases and commands file
print_status "Creating development commands reference..."
cat > dev-commands.md << 'EOF'
# ADRI Validator Development Commands

## Quality Checks
```bash
# Format code
black adri/ tests/

# Sort imports
isort adri/ tests/

# Lint code
flake8 adri/ tests/

# Type checking
mypy adri/

# Security scan
bandit -r adri/
safety check

# All quality checks
black adri/ tests/ && isort adri/ tests/ && flake8 adri/ tests/ && mypy adri/
```

## Testing
```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=adri --cov-report=html

# Run integration tests
pytest tests/integration/ -v

# Run performance benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Run all tests
pytest tests/ -v
```

## Pre-commit
```bash
# Run pre-commit on all files
pre-commit run --all-files

# Update pre-commit hooks
pre-commit autoupdate

# Skip pre-commit for a commit
git commit -m "message" --no-verify
```

## Package Building
```bash
# Build package
python -m build

# Check package
twine check dist/*

# Install locally
pip install -e .
```

## Development Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run quality checks: `black . && isort . && flake8 . && mypy adri/`
4. Run tests: `pytest tests/ -v`
5. Commit changes: `git commit -m "feat: your feature"`
6. Push and create PR: `git push origin feature/your-feature`
EOF

print_success "Development commands reference created: dev-commands.md"

# Create .env file for development
if [ ! -f ".env" ]; then
    print_status "Creating .env file for development..."
    cat > .env << 'EOF'
# ADRI Validator Development Environment Variables

# Development mode
ADRI_ENV=development

# Logging level
ADRI_LOG_LEVEL=DEBUG

# Test data directory
ADRI_TEST_DATA_DIR=./test_data

# Coverage settings
COVERAGE_PROCESS_START=.coveragerc
EOF
    print_success ".env file created"
else
    print_warning ".env file already exists"
fi

# Summary
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ Virtual environment created and activated"
echo "  ✅ All development dependencies installed"
echo "  ✅ Pre-commit hooks configured"
echo "  ✅ Quality tools ready"
echo "  ✅ Security scanners installed"
echo "  ✅ Development commands reference created"
echo ""
echo "🚀 Next steps:"
echo "  1. Review dev-commands.md for common development tasks"
echo "  2. Run 'source venv/bin/activate' to activate the environment"
echo "  3. Start developing with confidence!"
echo ""
echo "💡 Tip: Run 'pre-commit run --all-files' to check all files before committing"
echo ""
print_success "Happy coding! 🚀"
