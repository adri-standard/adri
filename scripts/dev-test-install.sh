#!/bin/bash
# ADRI Developer Testing Script
# Creates isolated environment for testing local ADRI build

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_NAME="adri_dev_test"
VENV_PATH=".dev-testing/${VENV_NAME}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLE_DATA_DIR="${PROJECT_ROOT}/demos"

echo "🚀 ADRI Developer Testing Environment"
echo "====================================="
echo ""
echo "This script creates an isolated environment for testing your local ADRI build."
echo "Perfect for the edit-code-test-immediately workflow you need!"
echo ""

# Function to create virtual environment
create_test_environment() {
    echo "🏗️  Creating test environment..."

    # Create .dev-testing directory if it doesn't exist
    mkdir -p .dev-testing

    # Remove existing environment if it exists
    if [ -d "$VENV_PATH" ]; then
        echo "   Removing existing environment..."
        rm -rf "$VENV_PATH"
    fi

    # Create new virtual environment
    echo "   Creating virtual environment: $VENV_NAME"
    python3 -m venv "$VENV_PATH"

    echo -e "${GREEN}✅ Virtual environment created${NC}"
}

# Function to install package in editable mode
install_package_editable() {
    echo ""
    echo "📦 Installing ADRI in editable mode..."

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Upgrade pip first
    echo "   Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1

    # Install package in editable mode with dev dependencies
    echo "   Installing ADRI package (editable mode)..."
    cd "$PROJECT_ROOT"
    pip install -e ".[dev]" > /dev/null 2>&1

    echo -e "${GREEN}✅ ADRI installed in editable mode${NC}"
    echo "   Any changes to src/adri/ will be immediately available!"
}

# Function to verify installation
verify_installation() {
    echo ""
    echo "🔍 Verifying installation..."

    # Test CLI availability
    if command -v adri >/dev/null 2>&1; then
        VERSION=$(adri --version 2>/dev/null || echo "unknown")
        echo -e "   ${GREEN}✅ CLI available: adri${NC} (${VERSION})"
    else
        echo -e "   ${RED}❌ CLI not available${NC}"
        return 1
    fi

    # Test Python import
    if python -c "import adri; print('✅ Python import successful')" 2>/dev/null; then
        echo -e "   ${GREEN}✅ Python import working${NC}"
    else
        echo -e "   ${RED}❌ Python import failed${NC}"
        return 1
    fi

    # Test decorator import (key functionality)
    if python -c "from adri import adri_protected; print('✅ Decorator import successful')" 2>/dev/null; then
        echo -e "   ${GREEN}✅ Decorator import working${NC}"
    else
        echo -e "   ${RED}❌ Decorator import failed${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Installation verified successfully${NC}"
}

# Function to show available demo data
show_demo_data() {
    echo ""
    echo "📊 Available Demo Data (from demos/ directory):"

    if [ -d "$SAMPLE_DATA_DIR" ]; then
        echo "   Data files:"
        find "$SAMPLE_DATA_DIR" -name "*.csv" -o -name "*.json" -o -name "*.parquet" 2>/dev/null | head -5 | sed 's/^/     📄 /'

        echo "   Standard files:"
        find "$SAMPLE_DATA_DIR" -name "*.yaml" -o -name "*.yml" 2>/dev/null | head -5 | sed 's/^/     📋 /'
    else
        echo -e "   ${YELLOW}ℹ️  No demos/ directory found${NC}"
        echo "   You can use any CSV files from your Desktop or other locations"
    fi
}

# Function to run quick functionality test
run_quick_test() {
    echo ""
    echo "🧪 Running quick functionality test..."

    # Test help command
    if adri --help > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Help command works${NC}"
    else
        echo -e "   ${RED}❌ Help command failed${NC}"
        return 1
    fi

    # Test list-standards command
    if adri list-standards > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ List standards command works${NC}"
    else
        echo -e "   ${YELLOW}⚠️  List standards command had issues (may be expected)${NC}"
    fi

    echo -e "${GREEN}✅ Quick test completed${NC}"
}

# Function to start interactive session
start_interactive_session() {
    echo ""
    echo "🎯 Starting Interactive Testing Session"
    echo "======================================="
    echo ""
    echo -e "${BLUE}Your ADRI development environment is ready!${NC}"
    echo ""
    echo "Available commands to try:"
    echo "  🎓 adri guide                     # Interactive tutorial (recommended for first-time users!)"
    echo "  📋 adri --help                    # Show all available commands"
    echo "  📋 adri --version                 # Show version (your local build)"
    echo "  📋 adri list-standards             # List available standards"
    echo "  📋 adri setup                     # Setup ADRI project (try in ~/Desktop)"
    echo "  📋 adri generate-standard data.csv # Generate standard from your data"
    echo "  📋 adri assess data.csv --standard std.yaml # Test data quality"
    echo ""
    echo "💡 Tips:"
    echo "  • You can cd to ~/Desktop or anywhere and use ADRI commands"
    echo "  • Edit code in src/adri/ - changes are immediately available!"
    echo "  • Use 'exit' to leave this testing environment"
    echo ""
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    echo -e "${YELLOW}Python environment: $VENV_PATH${NC}"
    echo ""

    # Launch interactive bash session with the virtual environment activated
    exec bash --rcfile <(echo "
        source '$VENV_PATH/bin/activate'
        PS1='(adri-dev) \u@\h:\w$ '
        echo 'ADRI Development Environment Active - Happy Testing! 🚀'
        echo 'Type \"adri --help\" to see available commands'
        echo ''
    ")
}

# Function to show cleanup instructions
show_cleanup_info() {
    echo ""
    echo "🧹 Cleanup Information"
    echo "======================"
    echo ""
    echo "When you're done testing:"
    echo "  🗑️  Remove test environment: rm -rf .dev-testing/"
    echo "  📁 Test environment location: $PROJECT_ROOT/.dev-testing/"
    echo ""
    echo "Note: This script creates isolated environments that don't affect your system Python!"
}

# Main execution flow
main() {
    # Check if we're in the right directory (should have pyproject.toml)
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ Error: pyproject.toml not found${NC}"
        echo "   Please run this script from the ADRI project root directory"
        echo "   Expected to find: pyproject.toml"
        exit 1
    fi

    # Check Python version
    if ! python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
        echo -e "${RED}❌ Error: Python 3.10+ required${NC}"
        echo "   Current Python: $(python3 --version)"
        exit 1
    fi

    # Create and setup environment
    create_test_environment
    install_package_editable
    verify_installation
    show_demo_data
    run_quick_test
    show_cleanup_info

    # Start interactive session
    start_interactive_session
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "ADRI Developer Testing Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --cleanup      Remove test environment and exit"
        echo ""
        echo "This script creates an isolated Python environment with your"
        echo "local ADRI build installed in editable mode for development testing."
        exit 0
        ;;
    --cleanup)
        echo "🧹 Cleaning up test environment..."
        rm -rf .dev-testing/
        echo -e "${GREEN}✅ Test environment removed${NC}"
        exit 0
        ;;
    "")
        # No arguments - run main function
        main
        ;;
    *)
        echo -e "${RED}❌ Unknown argument: $1${NC}"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
