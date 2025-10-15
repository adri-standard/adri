#!/bin/bash
# ADRI v5.0.0 Rollback Restoration Script
# Restores repository to pre-split state from Git tag or file backup

set -e  # Exit on any error

echo "=================================================="
echo "ADRI v5.0.0 Rollback Restoration"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TAG_NAME="v5.0.0-pre-split"
BACKUP_DIR="backup/pre-split"

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}ERROR: Not in a git repository${NC}"
    echo "Please run this script from the root of the ADRI repository"
    exit 1
fi

# Function to check for uncommitted changes
check_uncommitted_changes() {
    if ! git diff-index --quiet HEAD --; then
        echo -e "${RED}ERROR: You have uncommitted changes${NC}"
        echo ""
        echo "Uncommitted changes:"
        git status --short
        echo ""
        echo "Please commit or stash your changes before restoring"
        echo "Or use: git stash"
        exit 1
    fi
}

# Function to restore from Git tag
restore_from_tag() {
    echo -e "${BLUE}Restoring from Git tag: $TAG_NAME${NC}"
    echo ""

    # Check if tag exists
    if ! git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Tag $TAG_NAME not found${NC}"
        echo "Cannot restore from Git tag."
        return 1
    fi

    # Get current state
    CURRENT_COMMIT=$(git rev-parse HEAD)
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    TAG_COMMIT=$(git rev-parse "$TAG_NAME")

    echo "Current state:"
    echo "  Branch: $CURRENT_BRANCH"
    echo "  Commit: $CURRENT_COMMIT"
    echo ""
    echo "Tag state:"
    echo "  Tag: $TAG_NAME"
    echo "  Commit: $TAG_COMMIT"
    echo ""

    if [ "$CURRENT_COMMIT" = "$TAG_COMMIT" ]; then
        echo -e "${GREEN}Already at rollback point!${NC}"
        echo "No restoration needed."
        return 0
    fi

    echo -e "${YELLOW}WARNING: This will reset your repository to the pre-split state${NC}"
    echo "All changes after commit $TAG_COMMIT will be lost!"
    echo ""
    read -p "Are you sure you want to continue? (yes/NO): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Aborted."
        return 1
    fi

    # Perform hard reset to tag
    echo "Performing hard reset to $TAG_NAME..."
    git reset --hard "$TAG_NAME"

    echo -e "${GREEN}✓ Repository restored from Git tag${NC}"
    echo ""
    echo "Current state:"
    git log -1 --oneline

    return 0
}

# Function to restore from file backup
restore_from_backup() {
    echo -e "${BLUE}Restoring from file backup: $BACKUP_DIR${NC}"
    echo ""

    # Check if backup exists
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}ERROR: Backup directory not found: $BACKUP_DIR${NC}"
        echo "Cannot restore from file backup."
        return 1
    fi

    # Check for metadata file
    METADATA_FILE="$BACKUP_DIR/rollback-metadata.json"
    if [ ! -f "$METADATA_FILE" ]; then
        echo -e "${YELLOW}WARNING: Metadata file not found${NC}"
        echo "Proceeding with file restoration anyway..."
    else
        echo "Backup metadata:"
        cat "$METADATA_FILE"
        echo ""
    fi

    # Count files to restore
    FILE_COUNT=0
    while IFS= read -r -d '' file; do
        ((FILE_COUNT++))
    done < <(find "$BACKUP_DIR" -type f -name "*.py" -o -name "*.toml" -o -name "*.md" -print0)

    echo "Found $FILE_COUNT files to restore"
    echo ""

    echo -e "${YELLOW}WARNING: This will overwrite current files with backup versions${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/NO): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Aborted."
        return 1
    fi

    # Restore files
    echo "Restoring files..."
    RESTORED_COUNT=0

    # Find all backed up files and restore them
    while IFS= read -r -d '' backup_file; do
        # Get relative path from backup directory
        relative_path="${backup_file#$BACKUP_DIR/}"

        # Skip metadata and file list
        if [[ "$relative_path" == "rollback-metadata.json" ]] || [[ "$relative_path" == "file-list.txt" ]]; then
            continue
        fi

        # Create directory if needed
        target_dir=$(dirname "$relative_path")
        if [ ! -d "$target_dir" ]; then
            mkdir -p "$target_dir"
        fi

        # Copy file
        cp "$backup_file" "$relative_path"
        echo "  ✓ Restored: $relative_path"
        ((RESTORED_COUNT++))
    done < <(find "$BACKUP_DIR" -type f -print0)

    echo ""
    echo -e "${GREEN}✓ Restored $RESTORED_COUNT files from backup${NC}"

    return 0
}

# Main menu
echo "Select restoration method:"
echo ""
echo "1) Restore from Git tag (recommended)"
echo "   - Resets entire repository to pre-split commit"
echo "   - Clean and complete restoration"
echo "   - Requires: Git tag $TAG_NAME exists"
echo ""
echo "2) Restore from file backup"
echo "   - Restores only backed up files"
echo "   - Preserves other changes"
echo "   - Requires: Backup directory $BACKUP_DIR exists"
echo ""
echo "3) Show backup information only"
echo ""
echo "4) Exit"
echo ""
read -p "Enter your choice (1-4): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        check_uncommitted_changes
        if restore_from_tag; then
            echo ""
            echo "=================================================="
            echo -e "${GREEN}Restoration from Git Tag Complete!${NC}"
            echo "=================================================="
            echo ""
            echo "Your repository has been restored to the pre-split state."
            echo ""
            echo "Next steps:"
            echo "1. Verify files are correct: git status"
            echo "2. Run tests: pytest"
            echo "3. If everything looks good, you can continue working"
            echo ""
        else
            echo -e "${RED}Restoration failed${NC}"
            exit 1
        fi
        ;;
    2)
        check_uncommitted_changes
        if restore_from_backup; then
            echo ""
            echo "=================================================="
            echo -e "${GREEN}Restoration from File Backup Complete!${NC}"
            echo "=================================================="
            echo ""
            echo "Backed up files have been restored."
            echo ""
            echo "Next steps:"
            echo "1. Review changes: git status"
            echo "2. Test functionality: pytest"
            echo "3. Commit restored files: git add . && git commit -m 'Restore from backup'"
            echo ""
        else
            echo -e "${RED}Restoration failed${NC}"
            exit 1
        fi
        ;;
    3)
        echo -e "${BLUE}Backup Information:${NC}"
        echo ""

        # Check Git tag
        if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Git tag exists: $TAG_NAME${NC}"
            echo "  Commit: $(git rev-parse "$TAG_NAME")"
            echo "  Date: $(git log -1 --format=%ai "$TAG_NAME")"
            echo ""
            echo "  Tag message:"
            git tag -n10 "$TAG_NAME" | sed 's/^/    /'
            echo ""
        else
            echo -e "${RED}✗ Git tag not found: $TAG_NAME${NC}"
            echo ""
        fi

        # Check file backup
        if [ -d "$BACKUP_DIR" ]; then
            echo -e "${GREEN}✓ File backup exists: $BACKUP_DIR${NC}"

            if [ -f "$BACKUP_DIR/rollback-metadata.json" ]; then
                echo ""
                echo "  Backup metadata:"
                cat "$BACKUP_DIR/rollback-metadata.json" | sed 's/^/    /'
                echo ""
            fi

            if [ -f "$BACKUP_DIR/file-list.txt" ]; then
                FILE_COUNT=$(wc -l < "$BACKUP_DIR/file-list.txt")
                echo "  Files backed up: $FILE_COUNT"
                echo ""
                echo "  Backed up files:"
                head -n 20 "$BACKUP_DIR/file-list.txt" | sed 's/^/    /'
                if [ $FILE_COUNT -gt 20 ]; then
                    echo "    ... and $((FILE_COUNT - 20)) more files"
                fi
            fi
        else
            echo -e "${RED}✗ File backup not found: $BACKUP_DIR${NC}"
        fi
        echo ""
        ;;
    4)
        echo "Exiting without restoration."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
