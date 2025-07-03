#!/bin/bash

# ADRI Validator Package Publishing Script
# Publishes adri-validator to PyPI with comprehensive validation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="adri-validator"
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PACKAGE_DIR/dist"
TEST_PYPI_URL="https://test.pypi.org/simple/"
PROD_PYPI_URL="https://pypi.org/simple/"

echo -e "${BLUE}🚀 ADRI Validator Package Publishing Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo "Package: $PACKAGE_NAME"
echo "Directory: $PACKAGE_DIR"
echo "Build Directory: $BUILD_DIR"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Parse command line arguments
ENVIRONMENT="test"  # Default to test PyPI
SKIP_TESTS=false
FORCE_PUBLISH=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            ENVIRONMENT="prod"
            shift
            ;;
        --test)
            ENVIRONMENT="test"
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE_PUBLISH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod, --production    Publish to production PyPI (default: test PyPI)"
            echo "  --test                  Publish to test PyPI (default)"
            echo "  --skip-tests           Skip running tests before publishing"
            echo "  --force                Force publish even if version exists"
            echo "  --dry-run              Show what would be done without actually doing it"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Publish to test PyPI with full validation"
            echo "  $0 --prod             # Publish to production PyPI"
            echo "  $0 --dry-run          # Show what would be published"
            echo "  $0 --skip-tests --force  # Quick publish without tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set PyPI URL based on environment
if [ "$ENVIRONMENT" = "prod" ]; then
    PYPI_URL="$PROD_PYPI_URL"
    PYPI_REPO="pypi"
    ENV_NAME="Production PyPI"
else
    PYPI_URL="$TEST_PYPI_URL"
    PYPI_REPO="testpypi"
    ENV_NAME="Test PyPI"
fi

echo "Target: $ENV_NAME"
echo "Repository: $PYPI_REPO"
echo ""

# Change to package directory
cd "$PACKAGE_DIR"

# Step 1: Validate environment
echo -e "${BLUE}📋 Step 1: Environment Validation${NC}"

# Check required tools
REQUIRED_TOOLS=("python" "pip")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if command_exists "$tool"; then
        print_status "$tool is available"
    else
        print_error "$tool is required but not installed"
        exit 1
    fi
done

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
print_status "Python version: $PYTHON_VERSION"

# Check if we're in a virtual environment (recommended)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_status "Virtual environment active: $VIRTUAL_ENV"
else
    print_warning "No virtual environment detected (recommended for publishing)"
fi

# Step 2: Install/upgrade publishing tools
echo -e "\n${BLUE}📦 Step 2: Publishing Tools Setup${NC}"

if [ "$DRY_RUN" = false ]; then
    pip install --upgrade pip setuptools wheel build twine
    print_status "Publishing tools updated"
else
    print_status "Would install/upgrade: pip setuptools wheel build twine"
fi

# Step 3: Validate package structure
echo -e "\n${BLUE}🔍 Step 3: Package Structure Validation${NC}"

# Check required files
REQUIRED_FILES=("setup.py" "pyproject.toml" "README.md" "LICENSE" "CHANGELOG.md")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status "$file exists"
    else
        print_error "$file is missing"
        exit 1
    fi
done

# Check package directory
if [ -d "adri" ]; then
    print_status "Package directory 'adri' exists"
else
    print_error "Package directory 'adri' not found"
    exit 1
fi

# Check version file
if [ -f "adri/version.py" ]; then
    VERSION=$(python -c "exec(open('adri/version.py').read()); print(__version__)")
    print_status "Package version: $VERSION"
else
    print_error "Version file 'adri/version.py' not found"
    exit 1
fi

# Step 4: Dependency validation
echo -e "\n${BLUE}🔗 Step 4: Dependency Validation${NC}"

# Check if adri-standards is available
if python -c "import standards" 2>/dev/null; then
    print_status "adri-standards dependency available"
else
    print_warning "adri-standards not found - may need to be published first"
    if [ "$FORCE_PUBLISH" = false ]; then
        echo "Consider publishing adri-standards first or use --force to continue"
        exit 1
    fi
fi

# Step 5: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    echo -e "\n${BLUE}🧪 Step 5: Test Suite Execution${NC}"
    
    if [ "$DRY_RUN" = false ]; then
        # Run package tests
        if [ -f "../test_adri_validator_package.py" ]; then
            print_status "Running validator package tests..."
            python ../test_adri_validator_package.py
            print_status "Package tests passed"
        else
            print_warning "Package test file not found, skipping tests"
        fi
        
        # Run integration tests if available
        if [ -f "../test_ecosystem_integration.py" ]; then
            print_status "Running ecosystem integration tests..."
            python ../test_ecosystem_integration.py
            print_status "Integration tests passed"
        fi
    else
        print_status "Would run test suite"
    fi
else
    print_warning "Skipping tests (--skip-tests specified)"
fi

# Step 6: Clean previous builds
echo -e "\n${BLUE}🧹 Step 6: Clean Previous Builds${NC}"

if [ "$DRY_RUN" = false ]; then
    # Remove old build artifacts
    rm -rf build/ dist/ *.egg-info/
    print_status "Cleaned build artifacts"
else
    print_status "Would clean: build/ dist/ *.egg-info/"
fi

# Step 7: Build package
echo -e "\n${BLUE}🔨 Step 7: Package Build${NC}"

if [ "$DRY_RUN" = false ]; then
    # Build source distribution and wheel
    python -m build
    print_status "Package built successfully"
    
    # List built files
    echo "Built files:"
    ls -la dist/
else
    print_status "Would build source distribution and wheel"
fi

# Step 8: Validate built package
echo -e "\n${BLUE}✅ Step 8: Package Validation${NC}"

if [ "$DRY_RUN" = false ]; then
    # Check package with twine
    twine check dist/*
    print_status "Package validation passed"
else
    print_status "Would validate built packages with twine"
fi

# Step 9: Check if version already exists (unless forced)
if [ "$FORCE_PUBLISH" = false ]; then
    echo -e "\n${BLUE}🔍 Step 9: Version Conflict Check${NC}"
    
    if [ "$DRY_RUN" = false ]; then
        # Try to install the specific version to see if it exists
        if pip install --dry-run --index-url "$PYPI_URL" "$PACKAGE_NAME==$VERSION" 2>/dev/null; then
            print_error "Version $VERSION already exists on $ENV_NAME"
            echo "Use --force to override or update the version number"
            exit 1
        else
            print_status "Version $VERSION is available for publishing"
        fi
    else
        print_status "Would check if version $VERSION exists on $ENV_NAME"
    fi
else
    print_warning "Skipping version conflict check (--force specified)"
fi

# Step 10: Update Release Registry
echo -e "\n${BLUE}📋 Step 10: Update Release Registry${NC}"

if [ "$DRY_RUN" = false ]; then
    echo "Updating ADRI Validator release registry..."
    
    # Update the release registry in adri-standards
    python scripts/update_release_registry.py --auto --type "$ENVIRONMENT" --description "Published to $ENV_NAME"
    
    if [ $? -eq 0 ]; then
        print_status "Release registry updated"
    else
        print_warning "Failed to update release registry (continuing with publish)"
    fi
else
    print_status "Would update release registry in adri-standards"
fi

# Step 11: Publish package
echo -e "\n${BLUE}🚀 Step 11: Package Publishing${NC}"

if [ "$DRY_RUN" = false ]; then
    echo "Publishing to $ENV_NAME..."
    echo "Repository: $PYPI_REPO"
    echo "Version: $VERSION"
    echo ""
    
    # Confirm publication for production
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo -e "${YELLOW}⚠️  You are about to publish to PRODUCTION PyPI!${NC}"
        echo "Package: $PACKAGE_NAME"
        echo "Version: $VERSION"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Publication cancelled"
            exit 0
        fi
    fi
    
    # Upload to PyPI
    twine upload --repository "$PYPI_REPO" dist/*
    print_status "Package published successfully!"
else
    print_status "Would publish to $ENV_NAME using repository $PYPI_REPO"
fi

# Step 12: Verify installation
echo -e "\n${BLUE}🔍 Step 12: Installation Verification${NC}"

if [ "$DRY_RUN" = false ]; then
    # Wait a moment for PyPI to process
    sleep 5
    
    # Try to install the published package
    echo "Verifying installation from $ENV_NAME..."
    pip install --index-url "$PYPI_URL" --upgrade "$PACKAGE_NAME==$VERSION"
    
    # Test import
    python -c "import adri; print(f'Successfully imported adri-validator v{adri.__version__}')"
    print_status "Installation verification passed"
else
    print_status "Would verify installation from $ENV_NAME"
fi

# Success summary
echo -e "\n${GREEN}🎉 Publication Complete!${NC}"
echo -e "${GREEN}========================${NC}"
echo "Package: $PACKAGE_NAME"
echo "Version: $VERSION"
echo "Environment: $ENV_NAME"
echo "Repository: $PYPI_REPO"

if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "Installation command:"
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo "  pip install $PACKAGE_NAME"
    else
        echo "  pip install --index-url $PYPI_URL $PACKAGE_NAME"
    fi
    
    echo ""
    echo "Usage:"
    echo "  from adri.decorators.guard import adri_protected"
    echo "  @adri_protected(data_param='data')"
    echo "  def your_function(data): ..."
else
    echo ""
    echo "This was a dry run - no actual publishing occurred"
fi

echo ""
print_status "ADRI Validator publishing completed successfully!"
