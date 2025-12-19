#!/bin/bash
# ADRI v5.0.0 Pre-Split Rollback Point Creation Script
# Creates Git tag and backup before splitting codebase into open-source and enterprise

set -e  # Exit on any error

echo "=================================================="
echo "ADRI v5.0.0 Pre-Split Rollback Point Creation"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TAG_NAME="v5.0.0-pre-split"
BACKUP_DIR="backup/pre-split"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}ERROR: Not in a git repository${NC}"
    echo "Please run this script from the root of the ADRI repository"
    exit 1
fi

# Check for uncommitted changes
echo "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}WARNING: You have uncommitted changes${NC}"
    echo "Please commit or stash your changes before creating a rollback point"
    echo ""
    echo "Uncommitted changes:"
    git status --short
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Get current commit SHA
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo ""
echo "Current repository state:"
echo "  Branch: $CURRENT_BRANCH"
echo "  Commit: $CURRENT_COMMIT"
echo ""

# Check if tag already exists
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: Tag $TAG_NAME already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing tag..."
        git tag -d "$TAG_NAME"
    else
        echo "Aborted."
        exit 1
    fi
fi

# Create backup directory
echo "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup critical files
echo "Backing up critical files..."
CRITICAL_FILES=(
    "src/adri/logging/reasoning.py"
    "src/adri/logging/workflow.py"
    "src/adri/logging/enterprise.py"
    "src/adri/guard/reasoning_mode.py"
    "src/adri/__init__.py"
    "src/adri/logging/__init__.py"
    "src/adri/validator/engine.py"
    "src/adri/logging/local.py"
    "pyproject.toml"
    "README.md"
    "ARCHITECTURE.md"
    "CHANGELOG.md"
)

BACKUP_COUNT=0
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Create directory structure in backup
        backup_path="$BACKUP_DIR/$file"
        mkdir -p "$(dirname "$backup_path")"
        cp "$file" "$backup_path"
        echo "  ✓ Backed up: $file"
        ((BACKUP_COUNT++))
    else
        echo -e "  ${YELLOW}⚠ Skipped (not found): $file${NC}"
    fi
done

echo "Backed up $BACKUP_COUNT files to $BACKUP_DIR"

# Create rollback metadata file
METADATA_FILE="$BACKUP_DIR/rollback-metadata.json"
echo "Creating rollback metadata..."
cat > "$METADATA_FILE" << EOF
{
  "tag_name": "$TAG_NAME",
  "commit_sha": "$CURRENT_COMMIT",
  "branch": "$CURRENT_BRANCH",
  "timestamp": "$TIMESTAMP",
  "python_version": "$(python --version 2>&1)",
  "git_remote": "$(git remote get-url origin 2>/dev/null || echo 'N/A')",
  "files_backed_up": $BACKUP_COUNT,
  "created_by": "$USER",
  "hostname": "$(hostname)"
}
EOF
echo "  ✓ Metadata saved to: $METADATA_FILE"

# Create the Git tag
echo ""
echo "Creating Git tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "Pre-split rollback point for ADRI v5.0.0 open-source/enterprise split

This tag marks the last commit before splitting the ADRI codebase into:
- adri (open-source) v5.0.0
- adri-enterprise (private fork) v5.0.0

Backup created: $TIMESTAMP
Commit: $CURRENT_COMMIT
Files backed up: $BACKUP_COUNT files in $BACKUP_DIR

To restore from this point, use:
  bash scripts/restore-from-rollback.sh
"

echo -e "${GREEN}✓ Git tag created successfully${NC}"

# Verify tag was created
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Tag verification successful${NC}"
else
    echo -e "${RED}ERROR: Tag verification failed${NC}"
    exit 1
fi

# Create backup verification file
echo ""
echo "Creating backup verification file..."
find "$BACKUP_DIR" -type f > "$BACKUP_DIR/file-list.txt"
echo "  ✓ File list saved to: $BACKUP_DIR/file-list.txt"

# Final summary
echo ""
echo "=================================================="
echo -e "${GREEN}Rollback Point Created Successfully!${NC}"
echo "=================================================="
echo ""
echo "Summary:"
echo "  Tag name: $TAG_NAME"
echo "  Commit SHA: $CURRENT_COMMIT"
echo "  Branch: $CURRENT_BRANCH"
echo "  Files backed up: $BACKUP_COUNT"
echo "  Backup location: $BACKUP_DIR"
echo "  Timestamp: $TIMESTAMP"
echo ""
echo "To view the tag:"
echo "  git show $TAG_NAME"
echo ""
echo "To restore from this point:"
echo "  bash scripts/restore-from-rollback.sh"
echo ""
echo "To push the tag to remote (optional):"
echo "  git push origin $TAG_NAME"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC} Keep this tag and backup until the v5.0.0 split is complete"
echo "           and verified. Do not delete or modify them."
echo ""
