"""
ADRI - Agent Data Readiness Index.

Open source data quality standard for AI agents.
"""

from setuptools import find_packages, setup

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from version file
version = "1.0.0"

setup(
    name="adri-validator",
    version=version,
    author="Thomas Russell",
    author_email="adri@verodat.com",
    description="AI Data Reliability Intelligence - Comprehensive data quality assessment and validation framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adri-standard/adri",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.20.0",
        "pyyaml>=6.0",
        "jsonschema>=4.0",
        "click>=8.0",
        "rich>=12.0",
        "cachetools>=5.0",
        "psutil>=5.8",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-mock>=3.0",
            "pytest-benchmark>=4.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=5.0",
            "mypy>=1.0",
            "pre-commit>=2.0",
        ],
        "performance": [
            "numba>=0.56",
            "polars>=0.15",
            "pyarrow>=10.0",
        ],
        "monitoring": [
            "prometheus-client>=0.15",
            "structlog>=22.0",
        ],
    },
    include_package_data=True,
    package_data={
        "adri": ["**/*.yaml", "**/*.yml"],
        "tests": ["**/*.py", "**/*.yaml", "**/*.csv"],
    },
    entry_points={
        "console_scripts": [
            "adri=adri.cli.commands:main",
            "adri-protect=adri.cli.commands:protect",
            "adri-profile=adri.cli.commands:profile",
            "adri-generate=adri.cli.commands:generate",
        ],
    },
    keywords=[
        "ai",
        "agents",
        "data-quality",
        "validation",
        "protection",
        "adri",
    ],
    license="MIT",
    zip_safe=False,
    options={
        "bdist_wheel": {
            "universal": False,
        }
    },
)
