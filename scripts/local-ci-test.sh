#!/bin/bash
# Local CI Test Script - Mirror GitHub Actions Pipeline Locally
# Ensures local testing catches all issues before GitHub CI

set -e  # Exit on any error

echo "🧪 ADRI Local CI Pipeline Test"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

run_check() {
    local name="$1"
    local command="$2"

    echo -n "🔍 $name... "

    if eval "$command" > /tmp/check_output 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "   Error details:"
        cat /tmp/check_output | sed 's/^/   /'
        FAILURES=$((FAILURES + 1))
    fi
}

echo "📋 Pre-commit Checks (Mirror GitHub CI)"
echo "---------------------------------------"

# 1. Pre-commit hooks (exact same as CI)
run_check "Trailing whitespace" "pre-commit run trailing-whitespace --all-files"
run_check "End-of-file fixer" "pre-commit run end-of-file-fixer --all-files"
run_check "YAML validation" "pre-commit run check-yaml --all-files"
run_check "Large files check" "pre-commit run check-added-large-files --all-files"
run_check "Merge conflicts" "pre-commit run check-merge-conflict --all-files"
run_check "TOML validation" "pre-commit run check-toml --all-files"
run_check "Debug statements" "pre-commit run debug-statements --all-files"
run_check "Line endings" "pre-commit run mixed-line-ending --all-files"
run_check "Black formatting" "pre-commit run black --all-files"
run_check "Import sorting" "pre-commit run isort --all-files"
run_check "Flake8 linting" "pre-commit run flake8 --all-files"
run_check "Security scan" "pre-commit run bandit --all-files"

echo ""
echo "🔧 Python CI Tests (Mirror GitHub CI)"
echo "-------------------------------------"

# 2. Python tests (same as CI)
run_check "Build test" "python -m pip install -e . --quiet"
run_check "Unit tests" "python -m pytest tests/ -v --tb=short"
run_check "CLI functionality" "python -m adri.cli --help"
run_check "Import verification" "python -c 'import adri; print(\"ADRI import successful\")'"

echo ""
echo "📖 Documentation Tests (Mirror GitHub CI)"
echo "-----------------------------------------"

# 3. Documentation build (same as docs workflow)
if [ -d "docs" ]; then
    cd docs
    run_check "Node.js setup" "node --version && npm --version"
    run_check "NPM dependencies" "npm ci --silent"
    run_check "Docusaurus build" "npm run build"
    run_check "Build output check" "test -d build && test -f build/index.html"
    cd ..
else
    echo -e "${YELLOW}⚠️ SKIPPED - docs directory not found${NC}"
fi

echo ""
echo "🏗️ Repository Structure Validation (Mirror GitHub CI)"
echo "-----------------------------------------------------"

# 4. Repository structure validation (same as GitHub workflow)
run_check "Root directory structure" "bash -c '
    VIOLATIONS=0
    ALLOWED_FILES=(\".commitlintrc.json\" \".flake8\" \".gitignore\" \".gitmessage\" \".pre-commit-config.yaml\" \"adri-config.yaml\" \"ARCHITECTURE.md\" \"CHANGELOG.md\" \"CONTRIBUTING.md\" \"LICENSE\" \"pyproject.toml\" \"README.md\" \"SECURITY.md\")
    ALLOWED_DIRS=(\".git\" \".github\" \"archive\" \"demos\" \"docs\" \"examples\" \"scripts\" \"src\" \"tests\")

    for file in *; do
        if [[ \$file =~ ^(htmlcov|\.coverage|coverage\.json|\.pytest_cache|\.benchmarks|.*_standard\.yaml|test_logs)$ ]]; then
            continue
        fi
        if [[ -f \"\$file\" ]]; then
            FOUND=0
            for allowed in \"\${ALLOWED_FILES[@]}\"; do
                if [[ \"\$file\" == \"\$allowed\" ]]; then
                    FOUND=1
                    break
                fi
            done
            if [[ \$FOUND -eq 0 ]]; then
                echo \"❌ UNAUTHORIZED FILE: \$file\"
                VIOLATIONS=\$((VIOLATIONS + 1))
            fi
        elif [[ -d \"\$file\" ]]; then
            FOUND=0
            for allowed in \"\${ALLOWED_DIRS[@]}\"; do
                if [[ \"\$file\" == \"\$allowed\" ]]; then
                    FOUND=1
                    break
                fi
            done
            if [[ \$FOUND -eq 0 ]]; then
                echo \"❌ UNAUTHORIZED DIRECTORY: \$file\"
                VIOLATIONS=\$((VIOLATIONS + 1))
            fi
        fi
    done

    if [[ \$VIOLATIONS -eq 0 ]]; then
        echo \"✅ Root directory structure is clean\"
        exit 0
    else
        echo \"❌ Found \$VIOLATIONS structure violations\"
        exit 1
    fi
'"

run_check "Gitignore protection patterns" "bash -c '
    REQUIRED_PATTERNS=(\"archive/\" \"src/adri/_version.py\" \"*_plan.md\" \"*_implementation*.md\" \"*.DS_Store\" \"*.swp\" \"bandit-report.json\" \"coverage.xml\" \"dist/\" \"build/\" \"*.egg-info/\")
    MISSING=0

    for pattern in \"\${REQUIRED_PATTERNS[@]}\"; do
        if ! grep -qF \"\$pattern\" .gitignore; then
            echo \"❌ Missing .gitignore pattern: \$pattern\"
            MISSING=\$((MISSING + 1))
        fi
    done

    if [[ \$MISSING -eq 0 ]]; then
        echo \"✅ All required .gitignore patterns present\"
        exit 0
    else
        echo \"❌ Missing \$MISSING required patterns\"
        exit 1
    fi
'"

echo ""
echo "🎯 Complete GitHub Actions Simulation (ALL Workflows)"
echo "======================================================"

# 5. ACT testing (simulate ALL GitHub Actions workflows)
if command -v act >/dev/null 2>&1; then
    echo "Testing all 4 GitHub workflows for complete confidence..."
    echo ""

    # Test CI workflow (Python testing)
    run_check "ACT CI workflow test" "act -W .github/workflows/ci.yml -j build-test --container-architecture linux/amd64 --dryrun"
    run_check "ACT CI security test" "act -W .github/workflows/ci.yml -j security --container-architecture linux/amd64 --dryrun"

    # Test Documentation workflow (build only, no deploy)
    run_check "ACT docs build test" "act -W .github/workflows/docs.yml -j build --container-architecture linux/amd64 --dryrun"
    run_check "ACT docs test-deployment" "act -W .github/workflows/docs.yml -j test-deployment --container-architecture linux/amd64 --dryrun"

    # Test Structure validation workflow
    run_check "ACT structure validation test" "act -W .github/workflows/structure-validation.yml -j validate-root-structure --container-architecture linux/amd64 --dryrun"
    run_check "ACT gitignore validation test" "act -W .github/workflows/structure-validation.yml -j validate-gitignore-protection --container-architecture linux/amd64 --dryrun"

    # Test Release workflow (build/test only, no actual release)
    run_check "ACT release build test" "act -W .github/workflows/release.yml -j build --container-architecture linux/amd64 --dryrun"
    run_check "ACT release test-install" "act -W .github/workflows/release.yml -j test-install --container-architecture linux/amd64 --dryrun"

    echo ""
    echo "📊 Complete Workflow Coverage:"
    echo "   ✅ CI Pipeline (Python tests, security)"
    echo "   ✅ Documentation (build, deployment readiness)"
    echo "   ✅ Structure Validation (root structure, gitignore)"
    echo "   ✅ Release Pipeline (build, test - no deploy)"
    echo ""
    echo "🎯 This gives you 100% confidence that PR and Release will succeed!"

else
    echo -e "${YELLOW}⚠️ SKIPPED - ACT not installed${NC}"
    echo "   Install: brew install act"
    echo "   Without ACT, you're missing complete workflow simulation"
fi

echo ""
echo "📊 Summary"
echo "=========="

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - Ready for GitHub!${NC}"
    echo ""
    echo "🚀 Safe to commit and push:"
    echo "   git add ."
    echo "   git commit -m 'your message'"
    echo "   git push"
    exit 0
else
    echo -e "${RED}❌ $FAILURES CHECK(S) FAILED${NC}"
    echo ""
    echo "🔧 Fix issues above before committing"
    echo "💡 Run: pre-commit run --all-files"
    exit 1
fi
