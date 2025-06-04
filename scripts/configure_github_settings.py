#!/usr/bin/env python3
"""
GitHub Settings Configuration Helper for ADRI

This script opens the necessary GitHub settings pages and provides
step-by-step instructions for configuring the repository.
"""

import webbrowser
import time
import sys

REPO_URL = "https://github.com/adri-standard/adri"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def wait_for_user():
    """Wait for user to press Enter."""
    input("\nPress Enter when you've completed this step...")

def main():
    print_header("ADRI GitHub Repository Configuration Helper")
    
    print("This script will guide you through configuring your GitHub repository.")
    print("It will open the necessary pages in your browser.")
    print("\nMake sure you're logged into GitHub as an admin of the repository.")
    
    wait_for_user()
    
    # 1. Branch Protection
    print_header("Step 1: Configure Branch Protection")
    print("I'm opening the branch protection settings page.")
    print("\nPlease:")
    print("1. Click 'Add rule'")
    print("2. Branch name pattern: main")
    print("3. Check these options:")
    print("   ✓ Require a pull request before merging")
    print("     - Require approvals: 2")
    print("     - Dismiss stale pull request approvals")
    print("     - Require review from CODEOWNERS")
    print("   ✓ Require status checks to pass")
    print("     - Search and add: 'test'")
    print("     - Search and add: 'type-check'")
    print("     - Check: Require branches to be up to date")
    print("   ✓ Require conversation resolution")
    print("   ✓ Include administrators (you can disable later)")
    print("4. Click 'Create' at the bottom")
    
    webbrowser.open(f"{REPO_URL}/settings/branches")
    wait_for_user()
    
    # 2. Repository Description and Topics
    print_header("Step 2: Update Repository Info")
    print("I'm opening the general settings page.")
    print("\nPlease update:")
    print("1. Description: ADRI - Agent Data Readiness Index | Open standard enabling 99% AI agent reliability through universal data quality protocols")
    print("2. Website: https://adri-standard.github.io/adri/")
    print("3. Topics (click gear icon): data-quality, ai-agents, data-validation, python, open-standard, interoperability")
    print("4. Features:")
    print("   ✓ Issues (already enabled)")
    print("   ✓ Discussions")
    print("   ✓ Projects (optional)")
    print("5. Pull Requests section:")
    print("   ✓ Allow squash merging")
    print("   ✓ Allow merge commits")
    print("   ✓ Allow rebase merging")
    print("   ✓ Automatically delete head branches")
    
    webbrowser.open(f"{REPO_URL}/settings")
    wait_for_user()
    
    # 3. Security Settings
    print_header("Step 3: Configure Security")
    print("I'm opening the security settings page.")
    print("\nPlease enable:")
    print("1. ✓ Dependency graph")
    print("2. ✓ Dependabot alerts")
    print("3. ✓ Dependabot security updates")
    print("4. ✓ Secret scanning")
    
    webbrowser.open(f"{REPO_URL}/settings/security_analysis")
    wait_for_user()
    
    # 4. Code scanning
    print_header("Step 4: Set up Code Scanning")
    print("I'm opening the code scanning page.")
    print("\nPlease:")
    print("1. Click 'Set up code scanning'")
    print("2. Select 'CodeQL Analysis'")
    print("3. Use the default configuration")
    print("4. Click 'Enable CodeQL'")
    
    webbrowser.open(f"{REPO_URL}/settings/security/code-scanning")
    wait_for_user()
    
    # 5. Secrets (PyPI Token)
    print_header("Step 5: Add PyPI Token")
    print("I'm opening the secrets page.")
    print("\nTo add your PyPI token:")
    print("1. First, get your token from: https://pypi.org/manage/account/token/")
    print("2. Click 'New repository secret'")
    print("3. Name: PYPI_API_TOKEN")
    print("4. Value: (paste your PyPI token)")
    print("5. Click 'Add secret'")
    
    webbrowser.open(f"{REPO_URL}/settings/secrets/actions")
    wait_for_user()
    
    # 6. Pages
    print_header("Step 6: Configure GitHub Pages")
    print("I'm opening the Pages settings.")
    print("\nWhen you have a gh-pages branch:")
    print("1. Source: Deploy from a branch")
    print("2. Branch: gh-pages")
    print("3. Folder: / (root)")
    print("4. Click 'Save'")
    
    webbrowser.open(f"{REPO_URL}/settings/pages")
    wait_for_user()
    
    # 7. Create Release
    print_header("Step 7: Create v0.4.2 Release")
    print("I'm opening the releases page.")
    print("\nPlease:")
    print("1. Click 'Draft a new release'")
    print("2. Choose a tag: v0.4.2 (select existing)")
    print("3. Release title: v0.4.2")
    print("4. Describe this release:")
    print("   ### Fixed")
    print("   - Cleaned git repository history by removing accidentally committed virtual environment (venv/) files")
    print("   - Reduced repository size for faster cloning and better performance")
    print("5. Click 'Publish release'")
    print("\nThis will trigger automatic PyPI publishing!")
    
    webbrowser.open(f"{REPO_URL}/releases/new")
    wait_for_user()
    
    # Summary
    print_header("Configuration Complete!")
    print("✅ Branch protection configured")
    print("✅ Repository info updated")
    print("✅ Security features enabled")
    print("✅ PyPI secret added")
    print("✅ GitHub Pages configured")
    print("✅ Release created")
    print("\n🎉 Your repository is now properly configured for open source governance!")
    print("\nNext steps:")
    print("1. Monitor the Actions tab to ensure PyPI publishing succeeds")
    print("2. Check that branch protection is working on your next PR")
    print("3. Consider creating issue labels as listed in the governance checklist")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript cancelled by user.")
        sys.exit(1)
