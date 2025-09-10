#!/usr/bin/env python3
"""
ADRI Universal Setup Tool - Framework Environment Management

This tool handles dependency installation and environment setup for ADRI framework examples,
keeping the examples themselves focused on demonstrating value, not managing dependencies.

Usage:
    python tools/adri-setup.py --framework autogen
    python tools/adri-setup.py --framework langchain  
    python tools/adri-setup.py --framework crewai
    python tools/adri-setup.py --framework all

Features:
    • Automated dependency installation for any framework
    • Environment validation and troubleshooting
    • API key setup guidance
    • Virtual environment management
    • Platform-specific installation instructions
"""

import sys
import os
import subprocess
import platform
import argparse
import json
from pathlib import Path


class FrameworkSetup:
    """Handles setup for specific AI frameworks with ADRI."""
    
    FRAMEWORKS = {
        'autogen': {
            'packages': ['adri', 'pyautogen', 'openai'],
            'import_names': ['adri', 'autogen', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'Microsoft AutoGen multi-agent conversations'
        },
        'langchain': {
            'packages': ['adri', 'langchain', 'openai'],
            'import_names': ['adri', 'langchain', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'LangChain agent chains and workflows'
        },
        'crewai': {
            'packages': ['adri', 'crewai', 'openai'],
            'import_names': ['adri', 'crewai', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'CrewAI multi-agent crew coordination'
        },
        'llamaindex': {
            'packages': ['adri', 'llama-index', 'openai'],
            'import_names': ['adri', 'llama_index', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'LlamaIndex RAG and document processing'
        },
        'haystack': {
            'packages': ['adri', 'haystack-ai', 'openai'],
            'import_names': ['adri', 'haystack', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'Haystack search and NLP pipelines'
        },
        'langgraph': {
            'packages': ['adri', 'langgraph', 'openai'],
            'import_names': ['adri', 'langgraph', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'LangGraph workflow automation'
        },
        'semantic_kernel': {
            'packages': ['adri', 'semantic-kernel', 'openai'],
            'import_names': ['adri', 'semantic_kernel', 'openai'],
            'api_keys': ['OPENAI_API_KEY'],
            'description': 'Microsoft Semantic Kernel AI orchestration'
        }
    }

    def __init__(self):
        self.system = platform.system().lower()
        
    def get_pip_guidance(self):
        """Get platform-specific pip installation guidance."""
        if self.system == "darwin":  # macOS
            return """🍎 macOS pip installation:
   python -m ensurepip --upgrade
   brew install python  # If using Homebrew"""
        elif self.system == "linux":
            return """🐧 Linux pip installation:
   sudo apt install python3-pip     # Ubuntu/Debian
   sudo dnf install python3-pip     # Fedora"""
        elif self.system == "windows":
            return """🪟 Windows pip installation:
   py -m ensurepip --upgrade
   Reinstall Python from python.org with "Add to PATH" checked"""
        else:
            return """📦 General pip installation:
   python -m ensurepip --upgrade"""

    def check_python_environment(self):
        """Check Python and pip availability."""
        print("🔍 Checking Python Environment...")
        print("=" * 50)
        
        # Check Python version
        python_version = sys.version.split()[0]
        print(f"🐍 Python: {python_version}")
        
        # Check virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if in_venv:
            print("🌐 Virtual environment: ACTIVE")
        else:
            print("⚠️  Virtual environment: NOT DETECTED")
            print("💡 Recommendation: Use virtual environment to avoid conflicts")
            if self.system == "windows":
                print("   python -m venv adri_env && adri_env\\Scripts\\activate")
            else:
                print("   python -m venv adri_env && source adri_env/bin/activate")
        
        # Check pip
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                pip_version = result.stdout.strip()
                print(f"📦 {pip_version}")
                return True
            else:
                print("❌ pip: not responding properly")
                print("🔧 PIP INSTALLATION REQUIRED:")
                print(self.get_pip_guidance())
                return False
        except Exception as e:
            print(f"❌ pip: {str(e)}")
            print("🔧 PIP INSTALLATION REQUIRED:")
            print(self.get_pip_guidance())
            return False

    def validate_framework_imports(self, framework):
        """Test if framework packages can be imported."""
        if framework not in self.FRAMEWORKS:
            print(f"❌ Unknown framework: {framework}")
            return False
            
        config = self.FRAMEWORKS[framework]
        print(f"\n🔍 Testing {framework} imports...")
        
        success = True
        for import_name in config['import_names']:
            try:
                __import__(import_name)
                print(f"✅ {import_name}")
            except ImportError:
                print(f"❌ {import_name}")
                success = False
                
        return success

    def install_framework(self, framework, auto_confirm=False):
        """Install packages for a specific framework."""
        if framework not in self.FRAMEWORKS:
            print(f"❌ Unknown framework: {framework}")
            return False
            
        config = self.FRAMEWORKS[framework]
        packages = config['packages']
        
        print(f"\n📦 Installing {framework} dependencies...")
        print(f"🎯 Framework: {config['description']}")
        print(f"📝 Packages: {', '.join(packages)}")
        
        if not auto_confirm:
            try:
                confirm = input(f"\nInstall {framework} packages? [y/N]: ").lower().strip()
                if confirm != 'y':
                    print("❌ Installation cancelled")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Installation cancelled")
                return False
        
        try:
            print(f"🔄 Installing: {' '.join(packages)}")
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print("✅ Installation completed!")
            
            # Test imports immediately
            if self.validate_framework_imports(framework):
                print(f"🎉 {framework} ready for use!")
                return True
            else:
                print(f"⚠️  {framework} packages installed but imports failed")
                print("💡 Try restarting your Python environment")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False

    def check_api_keys(self, framework):
        """Check if required API keys are configured."""
        if framework not in self.FRAMEWORKS:
            return False
            
        config = self.FRAMEWORKS[framework]
        api_keys = config.get('api_keys', [])
        
        if not api_keys:
            return True
            
        print(f"\n🔑 Checking API keys for {framework}...")
        
        all_present = True
        for key in api_keys:
            value = os.getenv(key)
            if value:
                print(f"✅ {key}: configured")
                # Basic validation for OpenAI keys
                if key == 'OPENAI_API_KEY':
                    if not value.startswith(('sk-', 'sk-proj-')):
                        print(f"⚠️  {key}: format may be invalid (should start with 'sk-')")
                    elif len(value) < 20:
                        print(f"⚠️  {key}: seems too short")
            else:
                print(f"❌ {key}: not set")
                all_present = False
                
        if not all_present:
            print("\n🔧 API Key Setup Instructions:")
            for key in api_keys:
                if not os.getenv(key):
                    if key == 'OPENAI_API_KEY':
                        print(f"   export {key}='your-key-here'")
                        print("   📖 Get key: https://platform.openai.com/api-keys")
                        print("   💰 Cost estimate per example: ~$0.10")
                        
        return all_present

    def setup_framework(self, framework, auto_install=False):
        """Complete setup process for a framework."""
        print(f"🚀 Setting up ADRI + {framework.title()}")
        print("=" * 60)
        
        # Check environment
        if not self.check_python_environment():
            return False
            
        # Check if already installed
        if self.validate_framework_imports(framework):
            print(f"\n✅ {framework} packages already installed!")
        else:
            if not self.install_framework(framework, auto_install):
                return False
                
        # Check API keys
        if not self.check_api_keys(framework):
            print(f"\n⚠️  {framework} packages installed but API keys needed")
            print("🎯 You can run examples once API keys are configured")
            
        print(f"\n🎉 {framework} setup complete!")
        print(f"\n🚀 Next steps:")
        print(f"   python examples/{framework}-*.py")
        print("   📖 See example-specific README for usage details")
        
        return True


def main():
    """Main setup tool entry point."""
    parser = argparse.ArgumentParser(
        description="ADRI Universal Setup Tool - Install dependencies for AI framework examples"
    )
    parser.add_argument(
        '--framework', 
        choices=list(FrameworkSetup.FRAMEWORKS.keys()) + ['all'],
        required=True,
        help='Framework to set up (or "all" for all frameworks)'
    )
    parser.add_argument(
        '--auto-install', 
        action='store_true',
        help='Automatically install without confirmation prompts'
    )
    parser.add_argument(
        '--list',
        action='store_true', 
        help='List available frameworks and exit'
    )
    
    args = parser.parse_args()
    
    setup = FrameworkSetup()
    
    if args.list:
        print("🔧 Available ADRI Framework Integrations:")
        print("=" * 50)
        for name, config in setup.FRAMEWORKS.items():
            print(f"📦 {name:<15} - {config['description']}")
        return
        
    if args.framework == 'all':
        print("🚀 Setting up ALL ADRI framework integrations...")
        success_count = 0
        for framework in setup.FRAMEWORKS:
            print(f"\n{'='*60}")
            if setup.setup_framework(framework, args.auto_install):
                success_count += 1
                
        print(f"\n🎉 Setup complete! {success_count}/{len(setup.FRAMEWORKS)} frameworks ready")
    else:
        setup.setup_framework(args.framework, args.auto_install)


if __name__ == "__main__":
    main()
