#!/bin/bash
# ADRI PyPI Publishing Script
# Usage: ./scripts/publish_pypi.sh [--test]
# Add --test flag to publish to TestPyPI instead of production PyPI

set -e  # Exit on any error

# Check if running from project root
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must run from project root (where pyproject.toml is located)"
    exit 1
fi

# Parse arguments
USE_TESTPYPI=0
for arg in "$@"; do
    if [ "$arg" == "--test" ]; then
        USE_TESTPYPI=1
    fi
done

# Extract version from pyproject.toml
VERSION=$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2)

if [ -z "$VERSION" ]; then
    echo "Error: Couldn't extract version from pyproject.toml"
    exit 1
fi

echo "======================= ADRI PyPI PUBLISHER ======================="
echo "Preparing to publish ADRI version $VERSION"
echo "=================================================================="

# Check if version tag exists
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "✓ Git tag v$VERSION exists"
else
    echo "Error: Git tag v$VERSION doesn't exist!"
    echo "Please create a tag with: git tag v$VERSION && git push origin v$VERSION"
    exit 1
fi

# Verify clean working directory
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory not clean. Please commit or stash changes."
    exit 1
fi

# Verify the tag matches current commit
TAG_COMMIT=$(git rev-list -n 1 "v$VERSION")
HEAD_COMMIT=$(git rev-parse HEAD)
if [ "$TAG_COMMIT" != "$HEAD_COMMIT" ]; then
    echo "Error: Tag v$VERSION points to a different commit"
    echo "Please checkout the tagged commit or update your tag"
    exit 1
fi

# Check version in package
echo "Verifying version in Python package..."
PACKAGE_VERSION=$(python -c "import adri; print(adri.__version__)")
if [ "$PACKAGE_VERSION" != "$VERSION" ]; then
    echo "Error: Version mismatch!"
    echo "pyproject.toml: $VERSION"
    echo "adri.__version__: $PACKAGE_VERSION"
    exit 1
fi

# Check CHANGELOG.md
if ! grep -q "$VERSION" CHANGELOG.md; then
    echo "Warning: Version $VERSION not found in CHANGELOG.md"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Install build requirements
echo "Installing build requirements..."
pip install --upgrade pip build twine

# Build package
echo "Building distribution packages..."
python -m build

# Check the built packages with twine
echo "Checking packages with twine..."
twine check dist/*

# Upload to TestPyPI if requested
if [ $USE_TESTPYPI -eq 1 ]; then
    echo "Uploading to TestPyPI..."
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
    
    echo "Testing installation from TestPyPI..."
    # Create temporary venv to test installation
    python -m venv .venv_test
    source .venv_test/bin/activate
    pip install --index-url https://test.pypi.org/simple/ --no-deps adri==$VERSION
    
    # Verify installed version
    TEST_VERSION=$(python -c "import adri; print(adri.__version__)")
    if [ "$TEST_VERSION" != "$VERSION" ]; then
        echo "Error: Installed version mismatch from TestPyPI!"
        deactivate
        rm -rf .venv_test
        exit 1
    fi
    
    # Test basic functionality
    python -c "import adri; print('ADRI package imports successfully')"
    
    # Clean up test venv
    deactivate
    rm -rf .venv_test
    
    echo "TestPyPI installation verified successfully!"
    
    read -p "Proceed with uploading to production PyPI? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted upload to production PyPI"
        exit 0
    fi
fi

# Upload to PyPI
echo "Uploading to PyPI..."
twine upload dist/*

echo "=================================================================="
echo "ADRI $VERSION successfully published to PyPI!"
echo "Verify at: https://pypi.org/project/adri/$VERSION/"
echo "=================================================================="

# Create GitHub release if not exists
if ! curl --silent --fail "https://api.github.com/repos/verodat/agent-data-readiness-index/releases/tags/v$VERSION" > /dev/null; then
    echo "Consider creating a GitHub release for v$VERSION"
    echo "Visit: https://github.com/verodat/agent-data-readiness-index/releases/new?tag=v$VERSION"
fi

# Update documentation if needed
echo "Don't forget to update documentation and version compatibility matrix!"
