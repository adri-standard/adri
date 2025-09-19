#!/bin/bash
# Interactive Pre-Commit Testing - Choose your testing level
# Simple, user-controlled approach for reliable development

set -e

echo "🧪 ADRI Pre-Commit Testing"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Choose your testing level:"
echo ""
echo -e "${GREEN}1) 🚀 Quick Test (~30 seconds)${NC}"
echo "   - Pre-commit hooks (formatting, linting)"
echo "   - Basic validation only"
echo "   - Good for: small changes, doc updates"
echo ""
echo -e "${BLUE}2) 🔬 Full CI Test (~3-5 minutes)${NC}"
echo "   - Everything above PLUS"
echo "   - Complete Python test suite"
echo "   - Documentation builds"
echo "   - GitHub Actions workflow simulation"
echo "   - Good for: major changes, before important PRs"
echo ""

while true; do
    read -p "Enter choice (1 or 2): " choice
    case $choice in
        1)
            echo ""
            echo -e "${GREEN}🚀 Running Quick Test...${NC}"
            echo "========================================"
            echo ""

            echo "📋 Pre-commit Hooks"
            echo "-------------------"
            echo "🔍 Running: pre-commit run --all-files"
            echo ""

            # Run pre-commit hooks
            if pre-commit run --all-files; then
                echo -e "${GREEN}✅ All pre-commit hooks passed${NC}"
            else
                # Check if files were auto-fixed
                if [[ -n $(git status --porcelain) ]]; then
                    echo -e "${YELLOW}ℹ️  Pre-commit auto-fixed formatting issues${NC}"
                    echo "Modified files:"
                    git status --porcelain | sed 's/^/   /'
                    echo ""
                    echo -e "${GREEN}✅ Auto-fixes applied - you're good to commit!${NC}"
                else
                    echo -e "${RED}❌ Pre-commit hooks failed with real errors${NC}"
                    echo ""
                    echo "🔧 Fix the errors above, then run this script again"
                    exit 1
                fi
            fi

            echo ""
            echo "🎉 Quick Test Complete!"
            echo "======================"
            echo -e "${GREEN}✅ Ready to commit!${NC}"
            echo ""
            echo "🚀 Safe to commit and push:"
            echo "   git add ."
            echo "   git commit -m 'your message'"
            echo "   git push"
            break
            ;;
        2)
            echo ""
            echo -e "${BLUE}🔬 Running Full CI Test...${NC}"
            echo "========================================"
            echo ""

            # Run the comprehensive CI script
            ./scripts/local-ci-test.sh
            break
            ;;
        *)
            echo "Please enter 1 or 2"
            ;;
    esac
done
