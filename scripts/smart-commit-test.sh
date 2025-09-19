#!/bin/bash
# Smart Commit Testing - Automatically determine testing requirements based on change size
# Minimizes CI failures while avoiding over-testing small changes

set -e

echo "🎯 Smart Commit Testing"
echo "======================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Analyze changes since last commit
analyze_changes() {
    local base_commit=${1:-HEAD~1}

    # Get change statistics
    local files_changed=$(git diff --name-only $base_commit | wc -l | tr -d ' ')
    local lines_added=$(git diff --numstat $base_commit | awk '{sum += $1} END {print sum+0}')
    local lines_deleted=$(git diff --numstat $base_commit | awk '{sum += $2} END {print sum+0}')
    local total_changes=$((lines_added + lines_deleted))

    # Analyze file types
    local python_files=$(git diff --name-only $base_commit | grep -c '\.py$' || echo 0)
    local config_files=$(git diff --name-only $base_commit | grep -c -E '\.(yml|yaml|toml|json)$' || echo 0)
    local doc_files=$(git diff --name-only $base_commit | grep -c -E '\.(md|tsx?|css)$' || echo 0)
    local workflow_files=$(git diff --name-only $base_commit | grep -c '\.github/workflows' || echo 0)

    # Check for critical path changes
    local critical_changes=0
    if git diff --name-only $base_commit | grep -qE '(src/adri|tests/|\.github/workflows|pyproject\.toml|\.pre-commit-config\.yaml)'; then
        critical_changes=1
    fi

    # Display analysis to stderr so it doesn't interfere with return value
    echo "📊 Change Analysis" >&2
    echo "---------------" >&2
    echo "Files changed: $files_changed" >&2
    echo "Lines added: $lines_added" >&2
    echo "Lines deleted: $lines_deleted" >&2
    echo "Total changes: $total_changes" >&2
    echo "" >&2
    echo "File type breakdown:" >&2
    echo "  Python files: $python_files" >&2
    echo "  Config files: $config_files" >&2
    echo "  Documentation: $doc_files" >&2
    echo "  Workflows: $workflow_files" >&2
    echo "  Critical paths: $critical_changes" >&2
    echo "" >&2

    # Return analysis data cleanly
    echo "$files_changed,$total_changes,$python_files,$config_files,$doc_files,$workflow_files,$critical_changes"
}

# Determine testing level based on change analysis
determine_testing_level() {
    local analysis="$1"
    IFS=',' read -r files_changed total_changes python_files config_files doc_files workflow_files critical_changes <<< "$analysis"

    # Define thresholds
    local SMALL_FILE_THRESHOLD=3
    local SMALL_CHANGE_THRESHOLD=50
    local MEDIUM_FILE_THRESHOLD=10
    local MEDIUM_CHANGE_THRESHOLD=200

    echo "🔍 Testing Level Analysis"
    echo "------------------------"

    # Critical changes always require full testing
    if [[ $critical_changes -eq 1 ]]; then
        echo -e "${RED}🚨 CRITICAL CHANGES DETECTED${NC}"
        echo "   Changes to core code, tests, or workflows"
        echo "   → FULL CI TESTING REQUIRED"
        return 3
    fi

    # Workflow changes always require full testing
    if [[ $workflow_files -gt 0 ]]; then
        echo -e "${RED}🔧 WORKFLOW CHANGES DETECTED${NC}"
        echo "   Changes to GitHub Actions workflows"
        echo "   → FULL CI TESTING REQUIRED"
        return 3
    fi

    # Large changes require full testing
    if [[ $files_changed -gt $MEDIUM_FILE_THRESHOLD || $total_changes -gt $MEDIUM_CHANGE_THRESHOLD ]]; then
        echo -e "${YELLOW}📈 LARGE CHANGES DETECTED${NC}"
        echo "   Files: $files_changed (threshold: $MEDIUM_FILE_THRESHOLD)"
        echo "   Lines: $total_changes (threshold: $MEDIUM_CHANGE_THRESHOLD)"
        echo "   → FULL CI TESTING REQUIRED"
        return 3
    fi

    # Medium changes with Python code require selective testing
    if [[ $python_files -gt 0 && ($files_changed -gt $SMALL_FILE_THRESHOLD || $total_changes -gt $SMALL_CHANGE_THRESHOLD) ]]; then
        echo -e "${BLUE}🐍 PYTHON CHANGES DETECTED${NC}"
        echo "   Python files: $python_files"
        echo "   Total changes: $total_changes"
        echo "   → SELECTIVE TESTING RECOMMENDED"
        return 2
    fi

    # Small documentation-only changes can use pre-commit only
    if [[ $doc_files -gt 0 && $python_files -eq 0 && $config_files -eq 0 ]]; then
        echo -e "${GREEN}📝 DOCUMENTATION-ONLY CHANGES${NC}"
        echo "   Doc files: $doc_files, Python: $python_files, Config: $config_files"
        echo "   → PRE-COMMIT HOOKS SUFFICIENT"
        return 1
    fi

    # Small changes can use pre-commit only
    if [[ $files_changed -le $SMALL_FILE_THRESHOLD && $total_changes -le $SMALL_CHANGE_THRESHOLD ]]; then
        echo -e "${GREEN}🔹 SMALL CHANGES DETECTED${NC}"
        echo "   Files: $files_changed (threshold: $SMALL_FILE_THRESHOLD)"
        echo "   Lines: $total_changes (threshold: $SMALL_CHANGE_THRESHOLD)"
        echo "   → PRE-COMMIT HOOKS SUFFICIENT"
        return 1
    fi

    # Default to selective testing for unclear cases
    echo -e "${BLUE}🤔 UNCLEAR CHANGE SCOPE${NC}"
    echo "   → SELECTIVE TESTING RECOMMENDED"
    return 2
}

# Main logic
main() {
    echo "Analyzing changes..."

    # Check if we have commits to analyze
    if ! git rev-parse HEAD~1 >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ No previous commit found - assuming large changes${NC}"
        echo "   → FULL CI TESTING REQUIRED"
        ./scripts/local-ci-test.sh
        exit $?
    fi

    # Analyze changes
    local analysis=$(analyze_changes)
    local testing_level=$(determine_testing_level "$analysis")

    echo ""
    echo "💡 Recommended Action"
    echo "===================="

    case $testing_level in
        1)
            echo -e "${GREEN}✅ MINIMAL TESTING SUFFICIENT${NC}"
            echo ""
            echo "🚀 You can safely commit and push:"
            echo "   git add ."
            echo "   git commit -m 'your message'"
            echo "   git push"
            echo ""
            echo "Pre-commit hooks will handle validation automatically."
            ;;
        2)
            echo -e "${BLUE}🔧 SELECTIVE TESTING RECOMMENDED${NC}"
            echo ""
            echo "🧪 Run targeted tests:"
            echo "   pre-commit run --all-files  # Quick formatting check"
            echo "   pytest tests/ -v            # Python tests only"
            echo "   cd docs && npm run build    # Docs build only"
            echo ""
            echo "Or run full CI if you prefer:"
            echo "   ./scripts/local-ci-test.sh"
            ;;
        3)
            echo -e "${RED}🚨 FULL CI TESTING REQUIRED${NC}"
            echo ""
            echo "Running comprehensive CI testing now..."
            echo ""
            ./scripts/local-ci-test.sh
            exit $?
            ;;
    esac
}

# Allow override with command line argument
if [[ "$1" == "--force-full" ]]; then
    echo "🔧 Forcing full CI testing..."
    ./scripts/local-ci-test.sh
    exit $?
elif [[ "$1" == "--analyze-only" ]]; then
    analysis=$(analyze_changes)
    testing_level=$(determine_testing_level "$analysis")
    exit 0
else
    main
fi
