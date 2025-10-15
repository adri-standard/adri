#!/bin/bash
# ADRI v5.0.0 Enterprise Repository Setup Automation
# Automates steps 2.2-2.3 of enterprise repository setup

set -e  # Exit on any error

echo "=================================================="
echo "ADRI v5.0.0 Enterprise Repository Setup"
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
TEMP_DIR="adri-enterprise-temp"
ENTERPRISE_REMOTE="git@github.com:Verodat/adri-enterprise.git"

# Function to print step headers
print_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking Prerequisites"

    # Check if git is installed
    if ! command -v git &> /dev/null; then
        echo -e "${RED}ERROR: git is not installed${NC}"
        echo "Please install git first"
        exit 1
    fi
    echo -e "${GREEN}✓ Git is installed${NC}"

    # Check if we're in the ADRI repository
    if [ ! -d .git ]; then
        echo -e "${RED}ERROR: Not in a git repository${NC}"
        echo "Please run this script from the root of the ADRI repository"
        exit 1
    fi
    echo -e "${GREEN}✓ Running in git repository${NC}"

    # Check if v5.0.0-pre-split tag exists
    if ! git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: Tag $TAG_NAME not found${NC}"
        echo "Please run scripts/create-rollback-point.sh first"
        exit 1
    fi
    echo -e "${GREEN}✓ Pre-split tag exists${NC}"

    # Check SSH access to GitHub
    echo "Checking GitHub SSH access..."
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✓ GitHub SSH authentication works${NC}"
    else
        echo -e "${YELLOW}⚠ GitHub SSH authentication may not be configured${NC}"
        echo "You may need to use HTTPS with personal access token instead"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to get workspace directory
get_workspace_dir() {
    print_step "Step 2.2: Clone Repository State"

    echo "Select workspace directory for cloning:"
    echo "1) Current directory's parent: $(dirname "$(pwd)")"
    echo "2) Home directory: $HOME"
    echo "3) Custom path"
    echo ""
    read -p "Enter choice (1-3): " -n 1 -r
    echo ""
    echo ""

    case $REPLY in
        1)
            WORKSPACE_DIR=$(dirname "$(pwd)")
            ;;
        2)
            WORKSPACE_DIR="$HOME"
            ;;
        3)
            read -p "Enter custom path: " WORKSPACE_DIR
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    # Expand tilde if present
    WORKSPACE_DIR="${WORKSPACE_DIR/#\~/$HOME}"

    # Create directory if it doesn't exist
    if [ ! -d "$WORKSPACE_DIR" ]; then
        mkdir -p "$WORKSPACE_DIR"
    fi

    echo "Workspace directory: $WORKSPACE_DIR"

    # Check if temp directory already exists
    if [ -d "$WORKSPACE_DIR/$TEMP_DIR" ]; then
        echo -e "${YELLOW}WARNING: Directory $TEMP_DIR already exists${NC}"
        read -p "Remove it and continue? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$WORKSPACE_DIR/$TEMP_DIR"
            echo "Removed existing directory"
        else
            echo "Aborted"
            exit 1
        fi
    fi
}

# Function to clone repository
clone_repository() {
    echo "Cloning repository..."

    # Get current repository URL
    CURRENT_REPO=$(git remote get-url origin)
    echo "Source repository: $CURRENT_REPO"

    # Clone the repository
    cd "$WORKSPACE_DIR"
    git clone "$CURRENT_REPO" "$TEMP_DIR"
    cd "$TEMP_DIR"

    echo -e "${GREEN}✓ Repository cloned${NC}"

    # Checkout pre-split tag
    echo ""
    echo "Checking out pre-split tag: $TAG_NAME"
    git checkout "$TAG_NAME"

    # Verify commit
    CURRENT_COMMIT=$(git rev-parse HEAD)
    echo "Current commit: $CURRENT_COMMIT"

    # Show commit details
    echo ""
    echo "Commit details:"
    git log -1 --oneline

    echo ""
    echo -e "${GREEN}✓ Checked out pre-split tag${NC}"
}

# Function to setup enterprise remote
setup_enterprise_remote() {
    print_step "Step 2.3: Setup Enterprise Remote"

    echo "Enterprise repository URL: $ENTERPRISE_REMOTE"
    echo ""
    echo -e "${YELLOW}NOTE: The enterprise repository must already exist on GitHub${NC}"
    echo "If you haven't created it yet:"
    echo "  1. Go to https://github.com/Verodat"
    echo "  2. Click 'New repository'"
    echo "  3. Name: adri-enterprise"
    echo "  4. Visibility: Private"
    echo "  5. Do NOT initialize with README"
    echo ""
    read -p "Has the enterprise repository been created? (y/N): " -n 1 -r
    echo ""
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please create the repository first, then run this script again"
        echo ""
        echo "Quick setup using GitHub CLI (if available):"
        echo "  gh repo create Verodat/adri-enterprise --private --confirm"
        echo ""
        exit 1
    fi

    # Add enterprise remote
    echo "Adding enterprise remote..."
    git remote add enterprise "$ENTERPRISE_REMOTE"

    # Verify remotes
    echo ""
    echo "Configured remotes:"
    git remote -v

    echo ""
    echo -e "${GREEN}✓ Enterprise remote configured${NC}"
}

# Function to push to enterprise
push_to_enterprise() {
    echo ""
    echo "Ready to push to enterprise repository"
    echo ""
    echo -e "${YELLOW}This will push:${NC}"
    echo "  - All branches"
    echo "  - All tags"
    echo "  - Complete commit history"
    echo ""
    read -p "Proceed with push? (y/N): " -n 1 -r
    echo ""
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi

    # Push all branches
    echo "Pushing all branches..."
    git push enterprise --all

    echo ""
    echo -e "${GREEN}✓ Branches pushed${NC}"

    # Push all tags
    echo ""
    echo "Pushing all tags..."
    git push enterprise --tags

    echo ""
    echo -e "${GREEN}✓ Tags pushed${NC}"

    # Verify remote
    echo ""
    echo "Verifying remote repository..."
    git ls-remote enterprise | head -10

    echo ""
    echo -e "${GREEN}✓ Push completed successfully${NC}"
}

# Function to display next steps
display_next_steps() {
    print_step "Setup Complete!"

    echo "The enterprise repository has been set up at:"
    echo "  $ENTERPRISE_REMOTE"
    echo ""
    echo "Temporary clone location:"
    echo "  $WORKSPACE_DIR/$TEMP_DIR"
    echo ""
    echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
    echo ""
    echo "1. Configure repository settings on GitHub:"
    echo "   - Branch protection rules"
    echo "   - Security settings"
    echo "   - Actions permissions"
    echo ""
    echo "2. Follow the complete guide:"
    echo "   - See: docs/enterprise-setup-guide.md"
    echo "   - Complete steps 2.4-2.6"
    echo ""
    echo "3. Verify CI pipeline:"
    echo "   - Go to: https://github.com/Verodat/adri-enterprise/actions"
    echo "   - Ensure all tests pass"
    echo ""
    echo "4. Clean up temporary directory (when done):"
    echo "   rm -rf $WORKSPACE_DIR/$TEMP_DIR"
    echo ""
    echo -e "${GREEN}✓ Enterprise repository setup automated steps complete${NC}"
    echo ""
}

# Main execution
main() {
    echo "This script automates steps 2.2-2.3 of the enterprise setup"
    echo ""
    echo "Prerequisites:"
    echo "  - GitHub access to Verodat organization"
    echo "  - Enterprise repository created on GitHub"
    echo "  - SSH authentication configured"
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo ""
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi

    check_prerequisites
    get_workspace_dir
    clone_repository
    setup_enterprise_remote
    push_to_enterprise
    display_next_steps
}

# Run main function
main
