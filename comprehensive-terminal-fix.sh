#!/bin/bash

echo "=== VS Code Terminal Comprehensive Fix ==="
echo ""

# Function to add line to file if not present
add_if_missing() {
    local file="$1"
    local content="$2"
    local marker="$3"

    if grep -q "$marker" "$file" 2>/dev/null; then
        echo "✓ Already configured: $marker"
    else
        echo "$content" >> "$file"
        echo "✓ Added: $marker"
    fi
}

# 1. Backup .zshrc
echo "Step 1: Backing up shell configuration..."
if [ -f ~/.zshrc ]; then
    cp ~/.zshrc ~/.zshrc.backup.comprehensive.$(date +%Y%m%d_%H%M%S)
    echo "✓ Backed up ~/.zshrc"
else
    touch ~/.zshrc
    echo "✓ Created new ~/.zshrc"
fi
echo ""

# 2. Add VS Code shell integration
echo "Step 2: Configuring VS Code shell integration..."
cat >> ~/.zshrc << 'EOF'

# === VS Code Shell Integration (Comprehensive Fix) ===
# This enables proper terminal integration with VS Code
if [[ "$TERM_PROGRAM" == "vscode" ]]; then
    # Source the shell integration script
    VSCODE_SHELL_INTEGRATION=$(code --locate-shell-integration-path zsh 2>/dev/null)
    if [[ -n "$VSCODE_SHELL_INTEGRATION" ]] && [[ -f "$VSCODE_SHELL_INTEGRATION" ]]; then
        . "$VSCODE_SHELL_INTEGRATION"
    fi
fi
# === End VS Code Integration ===
EOF
echo "✓ Added VS Code shell integration"
echo ""

# 3. Create VS Code settings if needed
echo "Step 3: Checking VS Code settings..."
VSCODE_SETTINGS="$HOME/Library/Application Support/Code/User/settings.json"
VSCODE_SETTINGS_DIR=$(dirname "$VSCODE_SETTINGS")

if [ ! -d "$VSCODE_SETTINGS_DIR" ]; then
    mkdir -p "$VSCODE_SETTINGS_DIR"
    echo "✓ Created VS Code settings directory"
fi

if [ ! -f "$VSCODE_SETTINGS" ]; then
    cat > "$VSCODE_SETTINGS" << 'EOF'
{
    "terminal.integrated.shellIntegration.enabled": true,
    "terminal.integrated.defaultProfile.osx": "zsh"
}
EOF
    echo "✓ Created VS Code settings with terminal integration enabled"
else
    echo "✓ VS Code settings file exists"
fi
echo ""

# 4. Source the new configuration
echo "Step 4: Testing shell configuration..."
source ~/.zshrc
echo "✓ Sourced updated .zshrc"
echo ""

echo "=== Fix Complete ==="
echo ""
echo "IMPORTANT - You MUST do these steps manually:"
echo ""
echo "1. QUIT VS Code completely (CMD+Q or Code → Quit)"
echo "2. Wait 3 seconds"
echo "3. Open VS Code again"
echo "4. Open a new terminal (CMD+Shift+\`)"
echo "5. Run: echo 'Test successful!'"
echo ""
echo "If you still see 'Shell Integration Unavailable':"
echo "- Press CMD+Shift+P"
echo "- Type: 'Terminal: Select Default Profile'"
echo "- Select 'zsh'"
echo "- Close all terminals and open a new one"
echo ""
echo "Alternative manual fix:"
echo "1. Press CMD+, to open Settings"
echo "2. Search for 'shell integration'"
echo "3. Enable 'Terminal › Integrated › Shell Integration: Enabled'"
echo "4. Restart VS Code"
echo ""
