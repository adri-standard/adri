#!/usr/bin/env python3
"""
Utility functions for enhanced dependency validation in ADRI examples.

Provides robust pip installation validation and API key verification
to improve setup reliability for AI engineers.
"""

import os
import platform
import subprocess
import sys


def validate_pip_installation():
    """
    Check if pip is available and working.

    Returns:
        tuple: (bool, str) - (is_available, message)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            pip_version = result.stdout.strip()
            return True, f"pip available: {pip_version}"
        else:
            return False, "pip module not responding properly"
    except FileNotFoundError:
        return False, "Python executable not found"
    except subprocess.TimeoutExpired:
        return False, "pip check timed out (>10s)"
    except Exception as e:
        return False, f"pip validation failed: {str(e)}"


def get_pip_installation_guidance():
    """
    Get platform-specific pip installation guidance.

    Returns:
        str: Installation instructions for current platform
    """
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return """🍎 macOS pip installation options:
   1. python -m ensurepip --upgrade
   2. brew install python  # If using Homebrew
   3. Download Python from python.org (includes pip)"""

    elif system == "linux":
        # Try to detect Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read().lower()
                if "ubuntu" in os_info or "debian" in os_info:
                    return """🐧 Ubuntu/Debian pip installation:
   sudo apt update && sudo apt install python3-pip"""
                elif "fedora" in os_info or "rhel" in os_info or "centos" in os_info:
                    return """🐧 Fedora/RHEL/CentOS pip installation:
   sudo dnf install python3-pip  # Fedora
   sudo yum install python3-pip  # RHEL/CentOS"""
                elif "arch" in os_info:
                    return """🐧 Arch Linux pip installation:
   sudo pacman -S python-pip"""
        except:
            pass

        return """🐧 Linux pip installation:
   sudo apt install python3-pip     # Ubuntu/Debian
   sudo dnf install python3-pip     # Fedora
   sudo yum install python3-pip     # RHEL/CentOS"""

    elif system == "windows":
        return """🪟 Windows pip installation options:
   1. py -m ensurepip --upgrade
   2. Reinstall Python from python.org with "Add to PATH" checked
   3. Use Microsoft Store Python installation"""

    else:
        return """📦 General pip installation:
   python -m ensurepip --upgrade
   OR download Python from python.org"""


def validate_openai_api_key(api_key=None):
    """
    Test if OpenAI API key is valid with minimal cost.

    Args:
        api_key (str, optional): API key to test. If None, uses OPENAI_API_KEY env var.

    Returns:
        tuple: (bool, str) - (is_valid, message)
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return False, "No API key provided"

    # Basic format validation
    if not api_key.startswith(("sk-", "sk-proj-")):
        return False, "API key format invalid (should start with 'sk-' or 'sk-proj-')"

    if len(api_key) < 20:
        return False, "API key too short (should be 40+ characters)"

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        # Use cheapest possible test - list models (free operation)
        response = client.models.list()

        # Verify we got a reasonable response
        if hasattr(response, "data") and len(response.data) > 0:
            return True, "API key valid and working"
        else:
            return False, "API key accepted but unexpected response"

    except ImportError:
        return False, "OpenAI package not installed"
    except openai.AuthenticationError:
        return False, "Invalid API key (authentication failed)"
    except openai.RateLimitError:
        return True, "API key valid (rate limited but working)"
    except openai.APIConnectionError:
        return False, "Network connection failed (check internet)"
    except openai.PermissionDeniedError:
        return False, "API key valid but lacks required permissions"
    except openai.APITimeoutError:
        return False, "OpenAI API timeout (try again later)"
    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg:
            return False, "Invalid API key"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network connection failed"
        else:
            return False, f"API validation failed: {str(e)}"


def detect_conda_environment():
    """
    Detect if running in a conda environment.

    Returns:
        tuple: (bool, str) - (is_conda, environment_info)
    """
    # Check for conda environment variables
    conda_env = os.getenv("CONDA_DEFAULT_ENV")
    conda_prefix = os.getenv("CONDA_PREFIX")

    if conda_env and conda_prefix:
        return True, f"Conda environment: {conda_env}"
    elif conda_prefix:
        env_name = os.path.basename(conda_prefix)
        return True, f"Conda environment: {env_name}"
    elif "conda" in sys.executable.lower():
        return True, "Conda environment detected"
    else:
        return False, "Not in conda environment"


def get_python_environment_info():
    """
    Get comprehensive Python environment information.

    Returns:
        dict: Environment details
    """
    # Check virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    # Check conda environment
    is_conda, conda_info = detect_conda_environment()

    return {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "virtual_env": in_venv,
        "conda_env": is_conda,
        "conda_info": conda_info if is_conda else None,
        "platform": platform.platform(),
        "system": platform.system(),
    }


def enhanced_dependency_check_header(framework_name, dependencies):
    """
    Print enhanced dependency check header with environment info.

    Args:
        framework_name (str): Name of the framework being checked
        dependencies (list): List of dependency names
    """
    print(f"🔍 Checking {framework_name} Example Dependencies...")
    print("=" * 60)

    # Show environment information
    env_info = get_python_environment_info()
    print(f"🐍 Python: {env_info['python_version']}")

    if env_info["virtual_env"]:
        print("🌐 Virtual environment: ACTIVE")
    elif env_info["conda_env"]:
        print(f"🅰️  {env_info['conda_info']}")
    else:
        print("⚠️  Virtual environment: NOT DETECTED")
        print("💡 Recommendation: Use a virtual environment to avoid conflicts")
        if env_info["system"] == "Windows":
            print("   python -m venv adri_env && adri_env\\Scripts\\activate")
        else:
            print("   python -m venv adri_env && source adri_env/bin/activate")
        print()

    # Validate pip first
    pip_available, pip_message = validate_pip_installation()
    if pip_available:
        print(f"📦 {pip_message}")
    else:
        print(f"❌ pip: {pip_message}")
        print()
        print("🔧 PIP INSTALLATION REQUIRED:")
        print(get_pip_installation_guidance())
        print()
        return False

    print()
    return True
