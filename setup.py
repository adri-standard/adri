#!/usr/bin/env python
"""
Setup script for the ADRI package.

This is used by the TestPyPI publishing script to build the package.
It reads configuration from pyproject.toml.
"""

import re
import os
from setuptools import setup, find_packages

# Read version from version.py
with open(os.path.join('adri', 'version.py'), 'r') as f:
    version_file = f.read()
    version_match = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", version_file)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in adri/version.py")

# Read long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="adri",
    version=version,
    description="Agent Data Readiness Index",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ADRI Team",
    author_email="adri@example.com",
    url="https://github.com/example/adri",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "adri": ["templates/*.html"],
    },
    entry_points={
        "console_scripts": [
            "adri=adri.cli:main",
        ],
    },
)
