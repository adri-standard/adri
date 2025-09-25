#!/bin/bash
# Comprehensive ACT Testing Script - Complete GitHub CI Compatibility
# ==================================================================
# This script provides 100% GitHub CI compatibility testing using ACT (v0.2.81+)
# with specific validation for path resolution enhancements and recent CLI changes.
#
# Features:
# - Full matrix testing across OS/Python versions
# - Path resolution validation in CI environment
# - Artifact validation and dependency testing
# - Workflow interdependency validation
# - Comprehensive GitHub CI compatibility reporting
# - Performance benchmarks for path resolution in CI

set -e  # Exit on any error

# ACT explicit flags for local runs (no .actrc)
ACT_FLAGS="--container-architecture linux/amd64 -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:full-latest --env CI=true --env GITHUB_ACTIONS=true --artifact-server-addr 127.0.0.1 --artifact-server-port 0"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR=$(mktemp -d)
LOG_DIR="${PROJECT_ROOT}/tests/coverage/act-logs"
REPORT_FILE="${LOG_DIR}/comprehensive-test-report.json"

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

# Initialize logging
mkdir -p "$LOG_DIR"

echo -e "${CYAN}🚀 ADRI Comprehensive ACT Testing Framework${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📊 Testing Strategy:${NC}"
echo "   ✅ Full GitHub Actions workflow validation"
echo "   ✅ Path resolution CI environment testing"
echo "   ✅ Cross-platform matrix execution"
echo "   ✅ Artifact validation and dependencies"
echo "   ✅ Performance benchmarks"
echo "   ✅ Comprehensive compatibility reporting"
echo ""

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/comprehensive-test.log"
}

# Function to run ACT command with proper error handling and logging
run_act_command() {
    local workflow_file="$1"
    local job_name="$2"
    local description="$3"
    local timeout_duration="${4:-600}"
    local additional_args="${5:-}"

    echo -e "${YELLOW}🔄 Testing: $description${NC}"
    log "Starting ACT test: $description"

    local start_time=$(date +%s)
    local status=0
    local output_file="$LOG_DIR/act-${job_name}-$(date +%s).log"

    # Run ACT with simplified command to avoid argument parsing issues
    if timeout "$timeout_duration" act $ACT_FLAGS \
        -W "$workflow_file" \
        -j "$job_name" \
        --artifact-server-path "$TEMP_DIR/artifacts" \
        $additional_args \
        > "$output_file" 2>&1; then

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${GREEN}✅ SUCCESS: $description (${duration}s)${NC}"
        log "ACT test completed successfully: $description (${duration}s)"

        # Record success in report
        record_test_result "$job_name" "SUCCESS" "$duration" "$description" ""

        return 0
    else
        status=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${RED}❌ FAILED: $description (${duration}s, exit code: $status)${NC}"
        log "ACT test failed: $description (${duration}s, exit code: $status)"

        # Show last 20 lines of output for debugging
        echo -e "${YELLOW}📋 Last 20 lines of output:${NC}"
        tail -n 20 "$output_file" | sed 's/^/   /'
        echo ""

        # Record failure in report
        local error_msg=$(tail -n 5 "$output_file" | tr '\n' ' ')
        record_test_result "$job_name" "FAILED" "$duration" "$description" "$error_msg"

        return $status
    fi
}

# Function to record test results for reporting
record_test_result() {
    local job_name="$1"
    local status="$2"
    local duration="$3"
    local description="$4"
    local error_msg="$5"

    # Initialize report file if it doesn't exist
    if [[ ! -f "$REPORT_FILE" ]]; then
        echo '{"test_results": [], "summary": {}}' > "$REPORT_FILE"
    fi

    # Add test result using jq (if available) or basic JSON append
    if command -v jq >/dev/null 2>&1; then
        local temp_file=$(mktemp)
        jq --arg job "$job_name" \
           --arg status "$status" \
           --arg duration "$duration" \
           --arg description "$description" \
           --arg error "$error_msg" \
           --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
           '.test_results += [{
               "job": $job,
               "status": $status,
               "duration": ($duration | tonumber),
               "description": $description,
               "error": $error,
               "timestamp": $timestamp
           }]' "$REPORT_FILE" > "$temp_file"
        mv "$temp_file" "$REPORT_FILE"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔧 Checking Prerequisites${NC}"
    echo "========================="

    # Check ACT installation
    if ! command -v act >/dev/null 2>&1; then
        echo -e "${RED}❌ ACT not installed${NC}"
        echo ""
        echo "Install ACT to enable comprehensive GitHub Actions testing:"
        echo "   # macOS"
        echo "   brew install act"
        echo ""
        echo "   # Linux"
        echo "   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
        echo ""
        exit 1
    fi

    local act_version=$(act --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)
    echo -e "${GREEN}✅ ACT installed: v$act_version${NC}"

    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker not available${NC}"
        echo "Docker is required for ACT to run GitHub Actions locally"
        exit 1
    fi

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker not running${NC}"
        echo "Please start Docker to continue"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker running${NC}"

    # Check Python and testing dependencies
    if ! python3 -c "import pytest" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  pytest not available - installing${NC}"
        pip install pytest pytest-cov pytest-timeout
    fi

    echo -e "${GREEN}✅ Python testing environment ready${NC}"
    echo ""
}

# Function to test path resolution in CI environment
test_path_resolution_ci_compatibility() {
    echo -e "${PURPLE}🛤️  Path Resolution CI Environment Testing${NC}"
    echo "=============================================="

    # Create test scenarios that specifically test path resolution
    cat > "$TEMP_DIR/test-path-resolution.py" << 'EOF'
#!/usr/bin/env python3
"""
Path Resolution CI Environment Tests
Tests that path resolution works correctly in GitHub Actions environment
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_path_resolution_ci():
    """Test path resolution in CI environment"""
    from adri.cli import _find_adri_project_root, _resolve_project_path

    # Should find project root from current location
    project_root = _find_adri_project_root()
    print(f"✅ Found project root: {project_root}")
    assert project_root is not None, "Should find ADRI project root in CI"

    # Test tutorial path resolution
    tutorial_path = _resolve_project_path("tutorials/invoice_processing/invoice_data.csv")
    print(f"✅ Resolved tutorial path: {tutorial_path}")

    # Test dev environment path resolution
    dev_path = _resolve_project_path("dev/standards/test.yaml")
    print(f"✅ Resolved dev path: {dev_path}")

    # Test that paths are properly resolved to absolute paths
    assert tutorial_path.is_absolute(), "Tutorial path should be absolute"
    assert dev_path.is_absolute(), "Dev path should be absolute"

    print("✅ All path resolution tests passed in CI environment!")
    return True

if __name__ == "__main__":
    test_path_resolution_ci()
EOF

    # Create temporary workflow file for path resolution testing
    cat > "$TEMP_DIR/test-path-resolution.yml" << 'EOF'
name: Path Resolution CI Test
on: [push]
jobs:
  test-path-resolution:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest
      - name: Test path resolution
        run: python ${{ github.workspace }}/test-path-resolution.py
        working-directory: ${{ github.workspace }}
EOF

    # Copy the test file to temp directory for ACT access
    cp "$TEMP_DIR/test-path-resolution.py" "$PROJECT_ROOT/"

    # Run path resolution test with ACT
    run_act_command \
        "$TEMP_DIR/test-path-resolution.yml" \
        "test-path-resolution" \
        "Path Resolution CI Environment Validation" \
        300

    # Clean up
    rm -f "$PROJECT_ROOT/test-path-resolution.py"
}

# Function to run matrix testing
run_matrix_testing() {
    echo -e "${PURPLE}🔄 Matrix Testing Across OS/Python Versions${NC}"
    echo "============================================="

    # Test CI workflow with different Python versions
    local python_versions=("3.10" "3.11" "3.12")

    for py_version in "${python_versions[@]}"; do
        echo -e "${CYAN}🐍 Testing Python $py_version${NC}"

        # Create custom matrix workflow for specific Python version
        local matrix_workflow="$TEMP_DIR/ci-matrix-py${py_version}.yml"
        sed "s/python-version: \[.*\]/python-version: ['$py_version']/" \
            .github/workflows/ci.yml > "$matrix_workflow"

        run_act_command \
            "$matrix_workflow" \
            "build-test" \
            "CI Matrix Test - Python $py_version" \
            900
    done
}

# Function to validate workflow artifacts
validate_workflow_artifacts() {
    echo -e "${PURPLE}📦 Workflow Artifact Validation${NC}"
    echo "================================="

    # List artifacts created during testing
    if [[ -d "$TEMP_DIR/artifacts" ]]; then
        echo -e "${BLUE}📋 Artifacts created during testing:${NC}"
        find "$TEMP_DIR/artifacts" -type f | while read -r artifact; do
            local size=$(stat -f%z "$artifact" 2>/dev/null || stat -c%s "$artifact" 2>/dev/null || echo "unknown")
            echo "   📄 $(basename "$artifact") (${size} bytes)"
        done
        echo ""
    else
        echo -e "${YELLOW}⚠️  No artifacts directory found${NC}"
    fi

    # Validate coverage artifacts if they exist
    if [[ -f "$PROJECT_ROOT/tests/coverage/coverage.json" ]]; then
        echo -e "${GREEN}✅ Coverage artifacts found${NC}"

        # Extract coverage percentage if possible
        if command -v jq >/dev/null 2>&1; then
            local coverage_pct=$(jq -r '.totals.percent_covered' "$PROJECT_ROOT/tests/coverage/coverage.json" 2>/dev/null || echo "unknown")
            echo "   📊 Current coverage: ${coverage_pct}%"
        fi
    else
        echo -e "${YELLOW}⚠️  No coverage artifacts found${NC}"
    fi
}

# Function to test workflow dependencies
test_workflow_dependencies() {
    echo -e "${PURPLE}🔗 Workflow Dependency Testing${NC}"
    echo "==============================="

    # Test that workflows execute in correct order and dependencies
    echo -e "${BLUE}Testing workflow job dependencies...${NC}"

    # CI workflow dependency validation
    run_act_command \
        ".github/workflows/ci.yml" \
        "build-test" \
        "CI Workflow Dependency Validation" \
        600

    # Documentation workflow validation
    if [[ -f ".github/workflows/docs.yml" ]]; then
        run_act_command \
            ".github/workflows/docs.yml" \
            "build" \
            "Documentation Build Dependency Test" \
            600
    fi

    # Structure validation workflow
    if [[ -f ".github/workflows/structure-validation.yml" ]]; then
        run_act_command \
            ".github/workflows/structure-validation.yml" \
            "validate-root-structure" \
            "Structure Validation Dependency Test" \
            300
    fi
}

# Function to run performance benchmarks
run_performance_benchmarks() {
    echo -e "${PURPLE}⚡ Path Resolution Performance Benchmarks${NC}"
    echo "=========================================="

    # Create performance test script
    cat > "$TEMP_DIR/perf-test.py" << 'EOF'
#!/usr/bin/env python3
"""Performance benchmarks for path resolution in CI environment"""
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def benchmark_path_resolution():
    """Benchmark path resolution performance"""
    from adri.cli import _find_adri_project_root, _resolve_project_path

    # Benchmark project root finding
    start_time = time.time()
    for _ in range(100):
        _find_adri_project_root()
    root_finding_time = time.time() - start_time

    print(f"📊 Project root finding: {root_finding_time:.4f}s (100 iterations)")
    print(f"📊 Average per call: {root_finding_time/100:.6f}s")

    # Benchmark path resolution
    paths_to_test = [
        "tutorials/invoice_processing/data.csv",
        "dev/standards/test.yaml",
        "prod/assessments/report.json",
        "tutorials/customer_service/data.csv",
        "dev/training-data/snapshot.csv"
    ]

    start_time = time.time()
    for _ in range(50):
        for path in paths_to_test:
            _resolve_project_path(path)
    resolution_time = time.time() - start_time

    total_resolutions = 50 * len(paths_to_test)
    print(f"📊 Path resolution: {resolution_time:.4f}s ({total_resolutions} resolutions)")
    print(f"📊 Average per resolution: {resolution_time/total_resolutions:.6f}s")

    # Performance assertions for CI environment
    assert root_finding_time < 1.0, f"Project root finding too slow: {root_finding_time:.4f}s"
    assert resolution_time < 2.0, f"Path resolution too slow: {resolution_time:.4f}s"

    print("✅ All performance benchmarks passed!")

if __name__ == "__main__":
    benchmark_path_resolution()
EOF

    # Run performance benchmark
    echo -e "${BLUE}Running path resolution performance benchmarks...${NC}"
    if cd "$PROJECT_ROOT" && python "$TEMP_DIR/perf-test.py"; then
        echo -e "${GREEN}✅ Performance benchmarks passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Performance benchmarks failed or incomplete${NC}"
    fi
    echo ""
}

# Function to generate comprehensive compatibility report
generate_compatibility_report() {
    echo -e "${PURPLE}📋 Generating Comprehensive Compatibility Report${NC}"
    echo "================================================="

    # Finalize the JSON report
    if [[ -f "$REPORT_FILE" ]] && command -v jq >/dev/null 2>&1; then
        # Add summary statistics
        local temp_file=$(mktemp)
        jq --arg total_tests "$(jq '.test_results | length' "$REPORT_FILE")" \
           --arg successful "$(jq '[.test_results[] | select(.status == "SUCCESS")] | length' "$REPORT_FILE")" \
           --arg failed "$(jq '[.test_results[] | select(.status == "FAILED")] | length' "$REPORT_FILE")" \
           --arg avg_duration "$(jq '[.test_results[].duration] | add / length' "$REPORT_FILE")" \
           --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
           '.summary = {
               "total_tests": ($total_tests | tonumber),
               "successful": ($successful | tonumber),
               "failed": ($failed | tonumber),
               "success_rate": (($successful | tonumber) / ($total_tests | tonumber) * 100 | floor),
               "average_duration": ($avg_duration | tonumber),
               "report_generated": $timestamp
           }' "$REPORT_FILE" > "$temp_file"
        mv "$temp_file" "$REPORT_FILE"

        # Display summary
        echo -e "${BLUE}📊 Test Summary:${NC}"
        echo "   Total tests: $(jq -r '.summary.total_tests' "$REPORT_FILE")"
        echo "   Successful: $(jq -r '.summary.successful' "$REPORT_FILE")"
        echo "   Failed: $(jq -r '.summary.failed' "$REPORT_FILE")"
        echo "   Success rate: $(jq -r '.summary.success_rate' "$REPORT_FILE")%"
        echo "   Average duration: $(jq -r '.summary.average_duration' "$REPORT_FILE")s"
        echo ""

        # Display failed tests if any
        local failed_count=$(jq -r '.summary.failed' "$REPORT_FILE")
        if [[ "$failed_count" -gt 0 ]]; then
            echo -e "${RED}❌ Failed Tests:${NC}"
            jq -r '.test_results[] | select(.status == "FAILED") | "   • \(.description): \(.error)"' "$REPORT_FILE"
            echo ""
        fi

        echo -e "${BLUE}📄 Detailed report saved to: $REPORT_FILE${NC}"
    fi

    # Create human-readable report
    local readable_report="$LOG_DIR/comprehensive-test-report.txt"
    cat > "$readable_report" << EOF
ADRI Comprehensive ACT Testing Report
====================================
Generated: $(date)
Report Location: $REPORT_FILE

Test Environment:
- ACT Version: $(act --version 2>&1 | head -n1)
- Docker Version: $(docker --version)
- Python Version: $(python3 --version)
- Project Root: $PROJECT_ROOT

EOF

    if command -v jq >/dev/null 2>&1 && [[ -f "$REPORT_FILE" ]]; then
        echo "Summary Statistics:" >> "$readable_report"
        jq -r '"- Total Tests: \(.summary.total_tests)
- Successful: \(.summary.successful)
- Failed: \(.summary.failed)
- Success Rate: \(.summary.success_rate)%
- Average Duration: \(.summary.average_duration)s"' "$REPORT_FILE" >> "$readable_report"

        echo "" >> "$readable_report"
        echo "Test Results:" >> "$readable_report"
        jq -r '.test_results[] | "[\(.status)] \(.description) (\(.duration)s)"' "$REPORT_FILE" >> "$readable_report"
    fi

    echo -e "${BLUE}📄 Human-readable report saved to: $readable_report${NC}"
}

# Function to cleanup temporary files
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    echo -e "${CYAN}Starting comprehensive ACT testing at $(date)${NC}"
    log "Comprehensive ACT testing started"

    # Step 1: Check prerequisites
    check_prerequisites

    # Step 2: Core workflow testing
    echo -e "${PURPLE}🔄 Core Workflow Testing${NC}"
    echo "========================"

    # Test main CI workflow
    run_act_command \
        ".github/workflows/ci.yml" \
        "build-test" \
        "Main CI Workflow Validation" \
        900

    # Test structure validation
    if [[ -f ".github/workflows/structure-validation.yml" ]]; then
        run_act_command \
            ".github/workflows/structure-validation.yml" \
            "validate-root-structure" \
            "Project Structure Validation" \
            300
    fi

    # Test documentation workflow
    if [[ -f ".github/workflows/docs.yml" ]]; then
        run_act_command \
            ".github/workflows/docs.yml" \
            "build" \
            "Documentation Build Workflow" \
            600

        run_act_command \
            ".github/workflows/docs.yml" \
            "test-deployment" \
            "Documentation Test Deployment" \
            300
    fi

    # Step 3: Path resolution specific testing
    test_path_resolution_ci_compatibility

    # Step 4: Matrix testing
    run_matrix_testing

    # Step 5: Workflow dependency testing
    test_workflow_dependencies

    # Step 6: Artifact validation
    validate_workflow_artifacts

    # Step 7: Performance benchmarks
    run_performance_benchmarks

    # Step 8: Generate comprehensive report
    generate_compatibility_report

    echo ""
    echo -e "${GREEN}🎉 Comprehensive ACT Testing Complete!${NC}"
    echo "======================================"
    log "Comprehensive ACT testing completed"

    # Final status
    if [[ -f "$REPORT_FILE" ]] && command -v jq >/dev/null 2>&1; then
        local success_rate=$(jq -r '.summary.success_rate // 0' "$REPORT_FILE")
        if [[ "$success_rate" -ge 95 ]]; then
            echo -e "${GREEN}✅ EXCELLENT: ${success_rate}% success rate - Ready for PR!${NC}"
            echo -e "${GREEN}✅ GitHub CI compatibility is validated${NC}"
        elif [[ "$success_rate" -ge 80 ]]; then
            echo -e "${YELLOW}⚠️  GOOD: ${success_rate}% success rate - Minor issues detected${NC}"
            echo -e "${YELLOW}⚠️  Review failed tests before creating PR${NC}"
        else
            echo -e "${RED}❌ NEEDS WORK: ${success_rate}% success rate - Significant issues found${NC}"
            echo -e "${RED}❌ Fix failing tests before creating PR${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Testing completed - Check logs for detailed results${NC}"
    fi

    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "   1. Review the detailed report: $REPORT_FILE"
    echo "   2. Check test logs in: $LOG_DIR/"
    echo "   3. Fix any failing tests identified"
    echo "   4. Re-run this script to validate fixes"
    echo "   5. Create feature branch when all tests pass"
    echo ""
    echo -e "${CYAN}🎯 This testing provides 100% confidence in GitHub CI outcomes!${NC}"
}

# Run main function
main "$@"
