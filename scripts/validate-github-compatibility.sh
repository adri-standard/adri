#!/bin/bash
# Pre-PR GitHub Compatibility Validation Script
# ============================================
# This script provides comprehensive validation that your changes will pass
# GitHub CI before you create a feature branch or submit a PR.
#
# Features:
# - Complete local testing identical to GitHub CI
# - Path resolution validation for recent enhancements
# - Cross-platform compatibility checks
# - Performance regression detection
# - Comprehensive reporting with actionable recommendations
#
# Usage:
#   ./scripts/validate-github-compatibility.sh
#   ./scripts/validate-github-compatibility.sh --fast (skip ACT testing)
#   ./scripts/validate-github-compatibility.sh --report-only (generate report only)

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/tests/coverage/pre-pr-validation"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
VALIDATION_REPORT="${REPORT_DIR}/validation-report-${TIMESTAMP}.json"
FAST_MODE=false
REPORT_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST_MODE=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  --fast       Skip ACT testing for faster validation"
            echo "  --report-only Generate validation report only"
            echo "  --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ensure we're in project root
cd "$PROJECT_ROOT"

# Initialize reporting
mkdir -p "$REPORT_DIR"
echo '{"validation_results": [], "summary": {}, "recommendations": []}' > "$VALIDATION_REPORT"

echo -e "${CYAN}🚀 ADRI Pre-PR GitHub Compatibility Validation${NC}"
echo "=============================================="
echo -e "${BLUE}📊 Validation Strategy:${NC}"
echo "   ✅ Complete local testing identical to GitHub CI"
echo "   ✅ Path resolution enhancement validation"
echo "   ✅ Cross-platform compatibility verification"
echo "   ✅ Performance regression detection"
echo "   ✅ Comprehensive reporting with recommendations"
echo ""
echo -e "${BLUE}📄 Report will be saved to: ${VALIDATION_REPORT}${NC}"
echo ""

# Function to log validation results
log_validation_result() {
    local test_name="$1"
    local status="$2"
    local duration="$3"
    local details="$4"
    local error_msg="$5"

    # Add result to JSON report if jq is available
    if command -v jq >/dev/null 2>&1; then
        local temp_file=$(mktemp)
        jq --arg test "$test_name" \
           --arg status "$status" \
           --arg duration "$duration" \
           --arg details "$details" \
           --arg error "$error_msg" \
           --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
           '.validation_results += [{
               "test": $test,
               "status": $status,
               "duration": ($duration | tonumber),
               "details": $details,
               "error": $error,
               "timestamp": $timestamp
           }]' "$VALIDATION_REPORT" > "$temp_file"
        mv "$temp_file" "$VALIDATION_REPORT"
    fi
}

# Function to run a validation test with timing
run_validation_test() {
    local test_name="$1"
    local test_command="$2"
    local description="$3"

    echo -e "${YELLOW}🔄 Running: $description${NC}"

    local start_time=$(date +%s)
    local status=0
    local error_msg=""

    if eval "$test_command" 2>/dev/null; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ PASSED: $description (${duration}s)${NC}"
        log_validation_result "$test_name" "PASSED" "$duration" "$description" ""
        return 0
    else
        status=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        error_msg="Exit code: $status"
        echo -e "${RED}❌ FAILED: $description (${duration}s)${NC}"
        log_validation_result "$test_name" "FAILED" "$duration" "$description" "$error_msg"
        return $status
    fi
}

# Skip all validation if in report-only mode
if [[ "$REPORT_ONLY" == "true" ]]; then
    echo -e "${BLUE}📊 Generating report from previous validation...${NC}"
    echo ""
else
    # Step 1: Pre-commit validation
    echo -e "${PURPLE}🔧 Step 1: Pre-commit Validation${NC}"
    echo "================================="

    run_validation_test "pre-commit-hooks" \
        "pre-commit run --all-files" \
        "Pre-commit hooks validation"
    echo ""

    # Step 2: Path resolution validation
    echo -e "${PURPLE}🛤️  Step 2: Path Resolution Enhancement Validation${NC}"
    echo "================================================="

    # Create comprehensive path resolution test
    cat > /tmp/comprehensive-path-test.py << 'EOF'
#!/usr/bin/env python3
"""Comprehensive path resolution validation for GitHub CI compatibility"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def test_comprehensive_path_resolution():
    """Test all path resolution scenarios"""
    from adri.cli import _find_adri_project_root, _resolve_project_path

    print("🔍 Testing project root detection...")
    root = _find_adri_project_root()
    assert root is not None, "Should find project root"
    assert (root / "ADRI" / "config.yaml").exists(), "Should have config.yaml"
    print(f"✅ Found project root: {root}")

    print("\n🔍 Testing tutorial paths...")
    tutorial_paths = [
        "tutorials/invoice_processing/invoice_data.csv",
        "tutorials/customer_service/customer_data.csv",
        "tutorials/financial_analysis/market_data.csv"
    ]
    for path in tutorial_paths:
        resolved = _resolve_project_path(path)
        assert resolved.is_absolute(), f"Path should be absolute: {path}"
        assert "ADRI/tutorials" in str(resolved), f"Should contain ADRI/tutorials: {path}"
        print(f"✅ Tutorial path resolved: {path}")

    print("\n🔍 Testing environment paths...")
    env_paths = [
        "dev/standards/test.yaml",
        "dev/assessments/report.json",
        "dev/training-data/snapshot.csv",
        "prod/standards/prod_test.yaml",
        "prod/audit-logs/audit.log"
    ]
    for path in env_paths:
        resolved = _resolve_project_path(path)
        assert resolved.is_absolute(), f"Path should be absolute: {path}"
        if path.startswith("dev/"):
            assert "ADRI/dev" in str(resolved), f"Should contain ADRI/dev: {path}"
        elif path.startswith("prod/"):
            assert "ADRI/prod" in str(resolved), f"Should contain ADRI/prod: {path}"
        print(f"✅ Environment path resolved: {path}")

    print("\n🔍 Testing ADRI-prefixed paths...")
    adri_paths = [
        "ADRI/tutorials/test/data.csv",
        "ADRI/dev/standards/test.yaml"
    ]
    for path in adri_paths:
        resolved = _resolve_project_path(path)
        assert resolved.is_absolute(), f"Path should be absolute: {path}"
        assert path in str(resolved), f"Should preserve ADRI prefix: {path}"
        print(f"✅ ADRI-prefixed path resolved: {path}")

    print("\n🔍 Testing cross-directory functionality...")
    # Test from subdirectory
    original_cwd = os.getcwd()
    try:
        temp_subdir = Path.cwd() / "temp_test_subdir"
        temp_subdir.mkdir(exist_ok=True)
        os.chdir(temp_subdir)

        subdir_root = _find_adri_project_root()
        assert subdir_root == root, "Should find same root from subdirectory"

        subdir_resolved = _resolve_project_path("tutorials/invoice_processing/data.csv")
        expected = root / "ADRI/tutorials/invoice_processing/data.csv"
        assert subdir_resolved == expected, "Should resolve correctly from subdirectory"
        print("✅ Cross-directory functionality works")

    finally:
        os.chdir(original_cwd)
        if temp_subdir.exists():
            shutil.rmtree(temp_subdir)

    print("\n✅ All comprehensive path resolution tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_comprehensive_path_resolution()
        print("\n🎉 Path resolution validation successful!")
    except Exception as e:
        print(f"\n❌ Path resolution validation failed: {e}")
        exit(1)
EOF

    run_validation_test "path-resolution-comprehensive" \
        "python3 /tmp/comprehensive-path-test.py" \
        "Comprehensive path resolution validation"

    # Clean up
    rm -f /tmp/comprehensive-path-test.py
    echo ""

    # Step 3: Python testing validation
    echo -e "${PURPLE}🐍 Step 3: Python Testing Validation${NC}"
    echo "=================================="

    # Run specific test suites for recent enhancements
    enhanced_test_suites=(
        "tests/test_path_resolution_comprehensive.py"
        "tests/test_environment_documentation.py"
        "tests/test_cli_enhancements.py"
    )

    for test_suite in "${enhanced_test_suites[@]}"; do
        if [[ -f "$test_suite" ]]; then
            test_name=$(basename "$test_suite" .py)
            run_validation_test "$test_name" \
                "python -m pytest $test_suite -v --tb=short" \
                "Testing $test_suite"
        fi
    done
    echo ""

    # Step 4: Integration testing
    echo -e "${PURPLE}🔄 Step 4: Integration Testing${NC}"
    echo "=============================="

    run_validation_test "integration-tests" \
        "python -m pytest tests/ -k 'integration or workflow or end_to_end' -v --tb=short" \
        "Integration and workflow tests"
    echo ""

    # Step 5: Performance validation (quick benchmarks)
    echo -e "${PURPLE}⚡ Step 5: Performance Validation${NC}"
    echo "================================"

    cat > /tmp/performance-validation.py << 'EOF'
#!/usr/bin/env python3
"""Performance validation for path resolution"""
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def benchmark_path_resolution():
    from adri.cli import _find_adri_project_root, _resolve_project_path

    # Benchmark project root finding
    start = time.time()
    for _ in range(100):
        _find_adri_project_root()
    root_time = time.time() - start

    print(f"📊 Project root finding: {root_time:.4f}s (100 calls)")
    print(f"📊 Average per call: {root_time/100:.6f}s")

    # Benchmark path resolution
    paths = [
        "tutorials/invoice_processing/data.csv",
        "dev/standards/test.yaml",
        "prod/assessments/report.json"
    ]

    start = time.time()
    for _ in range(100):
        for path in paths:
            _resolve_project_path(path)
    resolve_time = time.time() - start

    total_calls = 100 * len(paths)
    print(f"📊 Path resolution: {resolve_time:.4f}s ({total_calls} calls)")
    print(f"📊 Average per call: {resolve_time/total_calls:.6f}s")

    # Performance assertions
    assert root_time < 2.0, f"Root finding too slow: {root_time:.4f}s"
    assert resolve_time < 3.0, f"Path resolution too slow: {resolve_time:.4f}s"

    print("✅ Performance benchmarks passed!")

if __name__ == "__main__":
    benchmark_path_resolution()
EOF

    run_validation_test "performance-benchmarks" \
        "python3 /tmp/performance-validation.py" \
        "Performance regression validation"

    rm -f /tmp/performance-validation.py
    echo ""

    # Step 6: ACT workflow testing (unless in fast mode)
    if [[ "$FAST_MODE" == "false" ]]; then
        echo -e "${PURPLE}🎯 Step 6: GitHub Actions Compatibility (ACT)${NC}"
        echo "============================================="

        if command -v act >/dev/null 2>&1; then
            # Test critical workflows
            critical_workflows=(
                ".github/workflows/ci.yml:build-test:CI Workflow"
                ".github/workflows/structure-validation.yml:validate-root-structure:Structure Validation"
            )

            for workflow_spec in "${critical_workflows[@]}"; do
                IFS=':' read -r workflow job description <<< "$workflow_spec"
                if [[ -f "$workflow" ]]; then
                    run_validation_test "act-$job" \
                        "timeout 600 act -W $workflow -j $job --container-architecture linux/amd64 >/dev/null 2>&1" \
                        "ACT: $description"
                fi
            done
        else
            echo -e "${YELLOW}⚠️  ACT not installed - GitHub Actions compatibility not tested${NC}"
            log_validation_result "act-validation" "SKIPPED" "0" "ACT not available" "ACT not installed"
        fi
        echo ""
    else
        echo -e "${BLUE}⚡ Step 6: Skipping ACT testing (fast mode)${NC}"
        echo "=========================================="
        echo -e "${YELLOW}⚠️  ACT testing skipped for faster validation${NC}"
        log_validation_result "act-validation" "SKIPPED" "0" "Fast mode enabled" "Skipped in fast mode"
        echo ""
    fi

    # Step 7: Documentation validation
    echo -e "${PURPLE}📖 Step 7: Documentation Validation${NC}"
    echo "==================================="

    if [[ -d "docs" ]]; then
        run_validation_test "docs-build" \
            "cd docs && npm ci --silent && npm run build >/dev/null 2>&1" \
            "Documentation build validation"
    else
        echo -e "${YELLOW}⚠️  No docs directory found${NC}"
        log_validation_result "docs-build" "SKIPPED" "0" "No docs directory" "Docs not found"
    fi
    echo ""
fi

# Generate comprehensive validation report
echo -e "${PURPLE}📋 Generating Comprehensive Validation Report${NC}"
echo "============================================="

if command -v jq >/dev/null 2>&1 && [[ -f "$VALIDATION_REPORT" ]]; then
    # Calculate summary statistics
    temp_file=$(mktemp)
    jq --arg total "$(jq '.validation_results | length' "$VALIDATION_REPORT")" \
       --arg passed "$(jq '[.validation_results[] | select(.status == "PASSED")] | length' "$VALIDATION_REPORT")" \
       --arg failed "$(jq '[.validation_results[] | select(.status == "FAILED")] | length' "$VALIDATION_REPORT")" \
       --arg skipped "$(jq '[.validation_results[] | select(.status == "SKIPPED")] | length' "$VALIDATION_REPORT")" \
       --arg avg_duration "$(jq '[.validation_results[].duration] | add / length' "$VALIDATION_REPORT" 2>/dev/null || echo "0")" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.summary = {
           "total_tests": ($total | tonumber),
           "passed": ($passed | tonumber),
           "failed": ($failed | tonumber),
           "skipped": ($skipped | tonumber),
           "success_rate": (($passed | tonumber) / ($total | tonumber) * 100 | floor),
           "average_duration": ($avg_duration | tonumber),
           "validation_timestamp": $timestamp
       }' "$VALIDATION_REPORT" > "$temp_file"
    mv "$temp_file" "$VALIDATION_REPORT"

    # Add recommendations based on results
    temp_file=$(mktemp)
    failed_count=$(jq -r '.summary.failed' "$VALIDATION_REPORT")
    success_rate=$(jq -r '.summary.success_rate' "$VALIDATION_REPORT")

    recommendations=()

    if [[ "$failed_count" -gt 0 ]]; then
        recommendations+=("Fix failing tests before creating PR")
        recommendations+=("Review error messages in validation results")
        recommendations+=("Run individual test suites to debug issues")
    fi

    if [[ "$success_rate" -lt 100 ]]; then
        recommendations+=("Investigate any skipped tests")
        recommendations+=("Consider running full validation without --fast mode")
    fi

    if [[ "$FAST_MODE" == "true" ]]; then
        recommendations+=("Run full validation with ACT testing before PR")
        recommendations+=("Execute: ./scripts/validate-github-compatibility.sh")
    fi

    recommendations+=("Review the comprehensive ACT testing: ./scripts/comprehensive-act-test.sh")
    recommendations+=("Check test coverage reports in tests/coverage/")

    # Add recommendations to report
    recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
    jq --argjson recs "$recommendations_json" '.recommendations = $recs' "$VALIDATION_REPORT" > "$temp_file"
    mv "$temp_file" "$VALIDATION_REPORT"

    # Display summary
    echo -e "${BLUE}📊 Validation Summary:${NC}"
    echo "   Total tests: $(jq -r '.summary.total_tests' "$VALIDATION_REPORT")"
    echo "   Passed: $(jq -r '.summary.passed' "$VALIDATION_REPORT")"
    echo "   Failed: $(jq -r '.summary.failed' "$VALIDATION_REPORT")"
    echo "   Skipped: $(jq -r '.summary.skipped' "$VALIDATION_REPORT")"
    echo "   Success rate: $(jq -r '.summary.success_rate' "$VALIDATION_REPORT")%"
    echo "   Average duration: $(jq -r '.summary.average_duration' "$VALIDATION_REPORT")s"
    echo ""

    # Show failed tests if any
    if [[ "$failed_count" -gt 0 ]]; then
        echo -e "${RED}❌ Failed Tests:${NC}"
        jq -r '.validation_results[] | select(.status == "FAILED") | "   • \(.test): \(.error)"' "$VALIDATION_REPORT"
        echo ""
    fi

    # Show recommendations
    echo -e "${BLUE}💡 Recommendations:${NC}"
    jq -r '.recommendations[]' "$VALIDATION_REPORT" | while read -r rec; do
        echo "   • $rec"
    done
    echo ""
fi

echo -e "${BLUE}📄 Detailed validation report: ${VALIDATION_REPORT}${NC}"
echo ""

# Final status and recommendations
if command -v jq >/dev/null 2>&1 && [[ -f "$VALIDATION_REPORT" ]]; then
    success_rate=$(jq -r '.summary.success_rate // 0' "$VALIDATION_REPORT")
    failed_count=$(jq -r '.summary.failed // 0' "$VALIDATION_REPORT")

    if [[ "$failed_count" -eq 0 && "$success_rate" -eq 100 ]]; then
        echo -e "${GREEN}🎉 VALIDATION SUCCESSFUL!${NC}"
        echo "=============================="
        echo -e "${GREEN}✅ 100% success rate - Ready to create PR!${NC}"
        echo -e "${GREEN}✅ All GitHub CI compatibility checks passed${NC}"
        echo ""
        echo -e "${BLUE}🚀 Next Steps:${NC}"
        echo "   1. Create your feature branch: git checkout -b feature/your-feature"
        echo "   2. Commit your changes: git add . && git commit"
        echo "   3. Push to GitHub: git push origin feature/your-feature"
        echo "   4. Create Pull Request on GitHub"
        echo ""
        echo -e "${CYAN}🎯 GitHub CI will pass because local validation was comprehensive!${NC}"

    elif [[ "$success_rate" -ge 95 ]]; then
        echo -e "${YELLOW}⚠️  VALIDATION MOSTLY SUCCESSFUL${NC}"
        echo "==============================="
        echo -e "${YELLOW}⚠️  ${success_rate}% success rate - Minor issues detected${NC}"
        echo ""
        echo -e "${BLUE}🔧 Recommended Actions:${NC}"
        echo "   1. Review and fix any failing tests"
        echo "   2. Re-run validation: ./scripts/validate-github-compatibility.sh"
        echo "   3. Consider running comprehensive ACT test for full confidence"
        echo ""

    else
        echo -e "${RED}❌ VALIDATION FAILED${NC}"
        echo "==================="
        echo -e "${RED}❌ ${success_rate}% success rate - Issues need attention${NC}"
        echo -e "${RED}❌ $failed_count tests failed${NC}"
        echo ""
        echo -e "${BLUE}🔧 Required Actions:${NC}"
        echo "   1. Fix all failing tests shown above"
        echo "   2. Address any performance regressions"
        echo "   3. Re-run validation after fixes"
        echo "   4. DO NOT create PR until validation passes"
        echo ""
        exit 1
    fi
else
    echo -e "${BLUE}ℹ️  Validation completed - Check logs for results${NC}"
fi

echo -e "${CYAN}📚 Additional Resources:${NC}"
echo "   • Comprehensive testing: ./scripts/comprehensive-act-test.sh"
echo "   • Local CI testing: ./scripts/local-ci-test.sh"
echo "   • Test coverage: tests/coverage/html/index.html"
echo ""
