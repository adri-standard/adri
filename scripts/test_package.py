#!/usr/bin/env python3
"""
ADRI Validator Package Testing Script

Comprehensive testing script for the adri-validator package before publishing.
Tests package structure, dependencies, functionality, and integration.

Usage:
    python scripts/test_package.py [--verbose] [--quick]
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class PackageTestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
        self.warnings_list = []
        self.start_time = time.time()
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
    
    def add_warning(self, test_name: str, warning: str):
        self.warnings += 1
        self.warnings_list.append(f"{test_name}: {warning}")
        print(f"⚠️  {test_name}: {warning}")
    
    def summary(self):
        duration = time.time() - self.start_time
        total = self.passed + self.failed
        
        print(f"\n{'='*70}")
        print(f"ADRI Validator Package Test Results")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f}s")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings_list:
            print(f"\n⚠️  Warnings ({len(self.warnings_list)}):")
            for warning in self.warnings_list:
                print(f"  - {warning}")
        
        return self.failed == 0

def run_command(cmd: List[str], cwd: str = None, timeout: int = 60) -> tuple:
    """Run a command and return (success, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def test_package_structure(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test package structure and required files"""
    print("\n🔍 Testing Package Structure...")
    
    # Required files
    required_files = [
        "setup.py",
        "pyproject.toml", 
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "adri/__init__.py",
        "adri/version.py"
    ]
    
    for file_path in required_files:
        full_path = package_dir / file_path
        if full_path.exists():
            result.add_pass(f"Required file: {file_path}")
        else:
            result.add_fail(f"Missing file: {file_path}", f"File not found: {full_path}")
    
    # Required directories
    required_dirs = [
        "adri",
        "adri/decorators",
        "adri/core", 
        "adri/analysis",
        "adri/config",
        "adri/cli",
        "scripts",
        "tests"
    ]
    
    for dir_path in required_dirs:
        full_path = package_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            result.add_pass(f"Required directory: {dir_path}")
        else:
            result.add_fail(f"Missing directory: {dir_path}", f"Directory not found: {full_path}")
    
    # Check key module files
    key_modules = [
        "adri/decorators/guard.py",
        "adri/core/assessor.py",
        "adri/core/protection.py",
        "adri/analysis/data_profiler.py",
        "adri/analysis/standard_generator.py",
        "adri/config/manager.py",
        "adri/config/loader.py",
        "adri/cli/commands.py"
    ]
    
    for module_path in key_modules:
        full_path = package_dir / module_path
        if full_path.exists():
            result.add_pass(f"Key module: {module_path}")
        else:
            result.add_fail(f"Missing module: {module_path}", f"Module not found: {full_path}")

def test_package_metadata(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test package metadata and configuration"""
    print("\n📋 Testing Package Metadata...")
    
    # Test version consistency
    try:
        # Get version from version.py
        version_file = package_dir / "adri" / "version.py"
        if version_file.exists():
            version_content = version_file.read_text()
            exec(version_content)
            version_py = locals().get('__version__')
            
            if version_py:
                result.add_pass(f"Version from version.py: {version_py}")
            else:
                result.add_fail("Version extraction", "__version__ not found in version.py")
        else:
            result.add_fail("Version file", "adri/version.py not found")
    
    except Exception as e:
        result.add_fail("Version parsing", str(e))
    
    # Test setup.py syntax
    setup_py = package_dir / "setup.py"
    if setup_py.exists():
        success, stdout, stderr = run_command([
            sys.executable, "-c", f"exec(open('{setup_py}').read())"
        ])
        if success:
            result.add_pass("setup.py syntax")
        elif "setuptools" in stderr:
            result.add_pass("setup.py syntax (setuptools not available)")
        else:
            result.add_fail("setup.py syntax", stderr)
    
    # Test pyproject.toml
    pyproject_toml = package_dir / "pyproject.toml"
    if pyproject_toml.exists():
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                result.add_warning("TOML parsing", "No TOML library available")
                return
        
        try:
            with open(pyproject_toml, 'rb') as f:
                config = tomllib.load(f)
            result.add_pass("pyproject.toml syntax")
            
            # Check project section
            if 'project' in config:
                project = config['project']
                
                # Check required fields
                required_fields = ['name', 'version', 'description', 'dependencies']
                for field in required_fields:
                    if field in project:
                        result.add_pass(f"pyproject.toml has {field}")
                    else:
                        result.add_fail(f"pyproject.toml missing {field}", f"Field '{field}' not found")
                
                # Check dependencies
                if 'dependencies' in project:
                    deps = project['dependencies']
                    has_standards = any('adri-standards' in dep for dep in deps)
                    if has_standards:
                        result.add_pass("adri-standards dependency found")
                    else:
                        result.add_fail("Dependencies", "adri-standards dependency not found")
            else:
                result.add_fail("pyproject.toml", "Missing [project] section")
                
        except Exception as e:
            result.add_fail("pyproject.toml parsing", str(e))

def test_imports_and_syntax(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test that all modules can be imported and have valid syntax"""
    print("\n🐍 Testing Imports and Syntax...")
    
    # Add package to path for testing
    sys.path.insert(0, str(package_dir))
    
    try:
        # Test main package import
        try:
            import adri
            result.add_pass("Main package import: adri")
        except ImportError as e:
            result.add_fail("Main package import", str(e))
        
        # Test key module imports
        key_imports = [
            ("adri.decorators.guard", "adri_protected"),
            ("adri.core.assessor", "DataQualityAssessor"),
            ("adri.core.protection", "DataProtectionEngine"),
            ("adri.analysis.data_profiler", "DataProfiler"),
            ("adri.analysis.standard_generator", "StandardGenerator"),
            ("adri.config.manager", "ConfigManager"),
            ("adri.config.loader", "ConfigLoader"),
            ("adri.cli.commands", "main")
        ]
        
        for module_name, class_name in key_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                result.add_pass(f"Import: {module_name}.{class_name}")
            except ImportError as e:
                result.add_fail(f"Import: {module_name}.{class_name}", str(e))
            except AttributeError as e:
                result.add_fail(f"Attribute: {module_name}.{class_name}", str(e))
        
        # Test decorator functionality
        try:
            from adri.decorators.guard import adri_protected
            
            @adri_protected(data_param="data")
            def test_function(data):
                return {"processed": True}
            
            result.add_pass("Decorator application")
        except Exception as e:
            result.add_fail("Decorator application", str(e))
    
    finally:
        # Remove from path
        if str(package_dir) in sys.path:
            sys.path.remove(str(package_dir))

def test_dependencies(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test package dependencies"""
    print("\n🔗 Testing Dependencies...")
    
    # Check if adri-standards is available
    try:
        import standards
        result.add_pass("adri-standards dependency available")
        
        # Test standards integration
        from standards.core import list_standards, load_standard
        standards_list = list_standards()
        if len(standards_list) > 0:
            result.add_pass(f"Standards available: {len(standards_list)} found")
        else:
            result.add_warning("Standards integration", "No standards found")
            
    except ImportError:
        result.add_warning("Dependencies", "adri-standards not available (may need to be installed)")
    
    # Check optional dependencies
    optional_deps = [
        ("pandas", "Data processing"),
        ("yaml", "YAML processing"),
        ("click", "CLI functionality")
    ]
    
    for dep_name, description in optional_deps:
        try:
            __import__(dep_name)
            result.add_pass(f"Optional dependency: {dep_name}")
        except ImportError:
            result.add_warning(f"Optional dependency: {dep_name}", f"{description} may not work")

def test_cli_functionality(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test CLI functionality"""
    print("\n💻 Testing CLI Functionality...")
    
    # Add package to path
    sys.path.insert(0, str(package_dir))
    
    try:
        # Test CLI import
        from adri.cli.commands import main
        result.add_pass("CLI main function import")
        
        # Test CLI with click (if available)
        try:
            import click
            from click.testing import CliRunner
            
            runner = CliRunner()
            cli = main()
            
            # Test help command
            help_result = runner.invoke(cli, ['--help'])
            if help_result.exit_code == 0:
                result.add_pass("CLI help command")
            else:
                result.add_fail("CLI help command", f"Exit code: {help_result.exit_code}")
            
        except ImportError:
            result.add_warning("CLI testing", "Click not available for CLI testing")
        except Exception as e:
            result.add_fail("CLI testing", str(e))
    
    except Exception as e:
        result.add_fail("CLI functionality", str(e))
    
    finally:
        if str(package_dir) in sys.path:
            sys.path.remove(str(package_dir))

def test_package_installation(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test package installation in a clean environment"""
    print("\n📦 Testing Package Installation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_venv"
        
        # Create virtual environment
        success, stdout, stderr = run_command([sys.executable, "-m", "venv", str(venv_path)])
        if not success:
            result.add_fail("Virtual environment creation", stderr)
            return
        result.add_pass("Virtual environment creation")
        
        # Determine python executable
        if os.name == 'nt':  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Install adri-standards first (if available)
        standards_path = package_dir.parent / "adri-standards"
        if standards_path.exists():
            success, stdout, stderr = run_command([str(pip_exe), "install", "-e", str(standards_path)])
            if success:
                result.add_pass("Standards dependency installation")
            else:
                result.add_warning("Standards dependency", "Could not install adri-standards")
        
        # Install the validator package
        success, stdout, stderr = run_command([str(pip_exe), "install", "-e", str(package_dir)])
        if success:
            result.add_pass("Package installation")
        else:
            result.add_fail("Package installation", stderr)
            return
        
        # Test import in clean environment
        success, stdout, stderr = run_command([
            str(python_exe), "-c", 
            "import adri; print(f'Successfully imported adri v{adri.__version__}')"
        ])
        if success:
            result.add_pass("Clean environment import")
        else:
            result.add_fail("Clean environment import", stderr)

def test_publishing_readiness(result: PackageTestResult, package_dir: Path, verbose: bool = False):
    """Test if package is ready for publishing"""
    print("\n🚀 Testing Publishing Readiness...")
    
    # Check if build tools are available
    try:
        import build
        result.add_pass("Build tool available")
    except ImportError:
        result.add_warning("Build tool", "python-build not available")
    
    try:
        import twine
        result.add_pass("Twine available")
    except ImportError:
        result.add_warning("Twine", "twine not available for package validation")
    
    # Test package building (if tools available)
    try:
        import build
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy package to temp directory
            temp_package = Path(temp_dir) / "package"
            shutil.copytree(package_dir, temp_package)
            
            # Build package
            success, stdout, stderr = run_command([
                sys.executable, "-m", "build", str(temp_package)
            ], timeout=120)
            
            if success:
                result.add_pass("Package build test")
                
                # Check built files
                dist_dir = temp_package / "dist"
                if dist_dir.exists():
                    built_files = list(dist_dir.glob("*"))
                    if len(built_files) >= 2:  # Should have .tar.gz and .whl
                        result.add_pass(f"Built files: {len(built_files)} artifacts")
                    else:
                        result.add_warning("Built files", f"Only {len(built_files)} artifacts built")
                else:
                    result.add_fail("Build output", "No dist directory created")
            else:
                result.add_fail("Package build test", stderr)
    
    except ImportError:
        result.add_warning("Build testing", "Build tools not available")
    except Exception as e:
        result.add_fail("Build testing", str(e))

def main():
    """Run all package tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ADRI Validator package before publishing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Skip slow tests")
    args = parser.parse_args()
    
    print("🧪 ADRI Validator Package Testing")
    print("=" * 50)
    
    # Get package directory
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent
    
    print(f"Package Directory: {package_dir}")
    print(f"Python Version: {sys.version}")
    print()
    
    result = PackageTestResult()
    
    # Run all tests
    test_package_structure(result, package_dir, args.verbose)
    test_package_metadata(result, package_dir, args.verbose)
    test_imports_and_syntax(result, package_dir, args.verbose)
    test_dependencies(result, package_dir, args.verbose)
    test_cli_functionality(result, package_dir, args.verbose)
    
    if not args.quick:
        test_package_installation(result, package_dir, args.verbose)
        test_publishing_readiness(result, package_dir, args.verbose)
    else:
        print("\n⚡ Skipping slow tests (--quick mode)")
    
    # Print summary and exit
    success = result.summary()
    
    if success:
        print("\n🎉 Package is ready for publishing!")
        print("Next steps:")
        print("  1. Run: ./scripts/publish_pypi.sh --dry-run")
        print("  2. Test publish: ./scripts/publish_pypi.sh --test")
        print("  3. Production publish: ./scripts/publish_pypi.sh --prod")
    else:
        print("\n❌ Package has issues that need to be resolved before publishing")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
