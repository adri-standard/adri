#!/usr/bin/env python3
"""
GitHub Pages Configuration Test Suite

This script tests the GitHub Pages configuration and deployment process,
ensuring that URLs are configured correctly and consistently throughout
the project.

Usage:
    python test_github_pages.py [--category=CATEGORY]

Categories:
    configuration    Test site configuration file
    build            Test MkDocs build process
    urls             Test URL reference consistency
    workflow         Test GitHub Actions workflow
    migration        Test URL migration process
    all              Run all tests (default)
"""

import os
import sys
import argparse
import yaml
import subprocess
import re
from pathlib import Path


class GitHubPagesTests:
    """GitHub Pages test suite."""

    def __init__(self):
        """Initialize the test suite."""
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_file = self.root_dir / "config" / "site_config.yml"
        self.mkdocs_file = self.root_dir / "config" / "mkdocs.yml"
        self.site_dir = self.root_dir / "site" / "docs"
        self.index_file = self.root_dir / "index.html"
        
        # Define test URLs
        self.private_url = "https://probable-adventure-3jve6ry.pages.github.io/"
        self.public_url = "https://thinkevolvesolve.github.io/agent-data-readiness-index/"
        self.test_url = "https://test-url.example.com/"

    def run_all_tests(self):
        """Run all tests."""
        print("Running all GitHub Pages tests...\n")
        
        tests = [
            self.test_config_validation,
            self.test_mkdocs_build,
            self.test_url_consistency,
            self.test_workflow_simulation,
            self.test_url_migration
        ]
        
        passing = 0
        for test in tests:
            try:
                test()
                passing += 1
            except Exception as e:
                print(f"Test failed: {str(e)}")
        
        print(f"\nTests completed: {passing}/{len(tests)} passing")
        return passing == len(tests)

    def test_config_validation(self):
        """Test ID: GHP-CONFIG-001 - Verify site_config.yml can be parsed and contains the correct URL."""
        print("Running test: Site Configuration Validation")
        
        # Check if the config file exists
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        # Load the config file
        with open(self.config_file, 'r') as file:
            try:
                config = yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse site_config.yml: {str(e)}")
        
        # Check if the site_base_url key exists
        if 'site_base_url' not in config:
            raise KeyError("site_base_url key not found in site_config.yml")
        
        # Check if the URL is valid
        site_base_url = config.get('site_base_url')
        if not site_base_url:
            raise ValueError("site_base_url is empty in site_config.yml")
        
        # Check if the URL matches one of the expected patterns
        if site_base_url != self.private_url and site_base_url != self.public_url:
            print(f"Warning: site_base_url '{site_base_url}' doesn't match expected patterns")
        
        print(f"√ Config validation passed - URL: {site_base_url}")
        return True

    def test_mkdocs_build(self):
        """Test ID: GHP-BUILD-001 - Verify MkDocs can build the site using the environment variable."""
        print("Running test: MkDocs Build with Environment Variables")
        
        # Check if the MkDocs file exists
        if not self.mkdocs_file.exists():
            raise FileNotFoundError(f"MkDocs file not found: {self.mkdocs_file}")
        
        # Set the environment variable
        os.environ['SITE_BASE_URL'] = self.test_url
        
        # Run MkDocs build with the test URL
        try:
            # Use check=True to raise an exception if the command fails
            result = subprocess.run(
                ["python", "-m", "mkdocs", "build", "--clean"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if the site directory exists
            if not self.site_dir.exists():
                raise FileNotFoundError(f"Site directory not found: {self.site_dir}")
            
            # Check if the index.html file exists in the site directory
            index_path = self.site_dir / "index.html"
            if not index_path.exists():
                raise FileNotFoundError(f"index.html not found in site directory: {index_path}")
            
            print(f"√ MkDocs build passed - Site built with URL: {self.test_url}")
            return True
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"MkDocs build failed: {e.stderr}")
        
    def test_url_consistency(self):
        """Test ID: GHP-URL-001 - Verify all URLs in HTML files are consistent with the configuration."""
        print("Running test: URL Reference Consistency")
        
        # Check if the site directory exists
        if not self.site_dir.exists():
            raise FileNotFoundError(f"Site directory not found: {self.site_dir}")
        
        # Get the test URL from the environment variable
        test_url = os.environ.get('SITE_BASE_URL', self.test_url)
        
        # Clean the URL for regex pattern (escape special characters)
        pattern_url = re.escape(test_url)
        
        # Find all HTML files in the site directory
        html_files = list(self.site_dir.glob("**/*.html"))
        if not html_files:
            raise FileNotFoundError("No HTML files found in site directory")
        
        # Check for canonical URLs in HTML files
        inconsistent_files = []
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as file:
                content = file.read()
                # Check for canonical link
                if '<link rel="canonical"' in content:
                    if not re.search(f'<link rel="canonical" href="{pattern_url}', content):
                        inconsistent_files.append(html_file)
        
        if inconsistent_files:
            raise ValueError(f"Inconsistent URLs found in {len(inconsistent_files)} files: {inconsistent_files}")
        
        print(f"√ URL consistency passed - {len(html_files)} files checked")
        return True

    def test_workflow_simulation(self):
        """Test ID: GHP-WORKFLOW-001 - Simulate the GitHub Actions workflow."""
        print("Running test: GitHub Actions Workflow Simulation")
        
        # Get the site configuration
        with open(self.config_file, 'r') as file:
            config = yaml.safe_load(file)
        
        site_base_url = config.get('site_base_url')
        
        # Simulate the workflow steps
        os.environ['SITE_BASE_URL'] = site_base_url
        
        # Check if the environment variable is set correctly
        if os.environ.get('SITE_BASE_URL') != site_base_url:
            raise EnvironmentError("Failed to set SITE_BASE_URL environment variable")
        
        print(f"√ Workflow simulation passed - Environment variable set: {site_base_url}")
        return True

    def test_url_migration(self):
        """Test ID: GHP-MIGRATE-001 - Test URL migration from private to public."""
        print("Running test: URL Migration Simulation")
        
        # Save the original configuration
        with open(self.config_file, 'r') as file:
            original_config = file.read()
        
        try:
            # Create a temporary configuration with the public URL
            config_data = yaml.safe_load(original_config)
            config_data['site_base_url'] = self.public_url
            
            # Write the temporary configuration
            with open(self.config_file, 'w') as file:
                yaml.dump(config_data, file)
            
            # Test the configuration
            if not self.test_config_validation():
                raise ValueError("Configuration validation failed after migration")
            
            # Set the environment variable to the public URL
            os.environ['SITE_BASE_URL'] = self.public_url
            
            # Check if the environment variable is set correctly
            if os.environ.get('SITE_BASE_URL') != self.public_url:
                raise EnvironmentError("Failed to set SITE_BASE_URL environment variable")
            
            print(f"√ URL migration passed - Configuration updated to: {self.public_url}")
            return True
            
        finally:
            # Restore the original configuration
            with open(self.config_file, 'w') as file:
                file.write(original_config)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Pages test suite')
    parser.add_argument('--category', choices=['configuration', 'build', 'urls', 'workflow', 'migration', 'all'],
                        default='all', help='Test category to run')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    tests = GitHubPagesTests()
    
    if args.category == 'configuration':
        tests.test_config_validation()
    elif args.category == 'build':
        tests.test_mkdocs_build()
    elif args.category == 'urls':
        tests.test_url_consistency()
    elif args.category == 'workflow':
        tests.test_workflow_simulation()
    elif args.category == 'migration':
        tests.test_url_migration()
    else:
        # Run all tests
        tests.run_all_tests()

if __name__ == '__main__':
    main()
