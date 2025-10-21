#!/bin/bash

# VS Code Shell Integration Fix Script
# This script fixes the "Shell Integration Unavailable" issue in VS Code

echo "=== VS Code Terminal Shell Integration Fix ==="
echo ""

# Backup .zshrc if it exists
if [ -f ~/.zshrc ]; then
    echo "✓ Backing up ~/.zshrc to ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S)"
    cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S)
else
    echo "✓ Creating new ~/.zshrc file"
    touch ~/.zshrc
fi

# Check if VS Code shell integration is already present
if grep -q "vscode-server.*shellIntegration" ~/.zshrc 2>/dev/null; then
    echo "✓ VS Code shell integration already configured in ~/.zshrc"
else
    echo "✓ Adding VS Code shell integration to ~/.zshrc"
    cat >> ~/.zshrc << 'EOF'

# VS Code Shell Integration (added by fix script)
[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"
EOF
fi

echo ""
echo "=== Fix Applied Successfully ==="
echo ""
echo "Next steps:"
echo "1. Close all VS Code terminal instances"
echo "2. Press CMD+Shift+P and run: 'Developer: Reload Window'"
echo "3. Open a new terminal (CMD+Shift+\`)"
echo "4. The shell integration should now work!"
echo ""
echo "If issues persist:"
echo "- Press CMD+Shift+P → 'Update' to update VS Code"
echo "- Press CMD+Shift+P → 'Terminal: Select Default Profile' and ensure 'zsh' is selected"
echo ""
