"""
Mock Project Fixtures for ADRI Testing.

Provides reusable fixtures for creating consistent ADRI project structures
across different test modules. These fixtures support cross-directory testing
scenarios and ensure comprehensive validation of path resolution functionality.

Fixtures include:
- Simple ADRI project structures
- Complex multi-directory projects
- Projects with various environment configurations
- Projects with sample data for different use cases
"""

import tempfile
import shutil
from pathlib import Path
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class ProjectStructure:
    """Defines the structure of a mock ADRI project."""
    directories: List[str]
    files: Dict[str, str]  # path -> content
    config: Dict[str, Any]
    name: str
    description: str


class MockProjectFixtures:
    """Factory for creating mock ADRI project fixtures."""

    @staticmethod
    def simple_adri_project() -> ProjectStructure:
        """Create a simple ADRI project with basic structure."""
        directories = [
            "ADRI/tutorials/invoice_processing",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
        ]

        files = {
            "ADRI/tutorials/invoice_processing/invoice_data.csv":
                "invoice_id,amount,status\nINV-001,1250.00,paid\nINV-002,875.50,pending",
            "ADRI/tutorials/invoice_processing/test_invoice_data.csv":
                "invoice_id,amount,status\nINV-101,1350.00,paid\nINV-102,,925.50"
        }

        config = {
            "adri": {
                "project_name": "simple_test_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                            "audit_logs": "ADRI/dev/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/dev/audit-logs",
                            "log_prefix": "adri",
                            "log_level": "INFO",
                            "include_data_samples": True,
                            "max_log_size_mb": 100,
                        }
                    }
                }
            }
        }

        return ProjectStructure(
            directories=directories,
            files=files,
            config=config,
            name="simple_adri_project",
            description="Basic ADRI project with invoice processing tutorial"
        )

    @staticmethod
    def complex_multi_directory_project() -> ProjectStructure:
        """Create a complex ADRI project with multiple directories and use cases."""
        directories = [
            "ADRI/tutorials/invoice_processing",
            "ADRI/tutorials/customer_service",
            "ADRI/tutorials/financial_analysis",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
            "ADRI/prod/contracts",
            "ADRI/prod/assessments",
            "ADRI/prod/training-data",
            "ADRI/prod/audit-logs",
            "docs/src/components",
            "docs/api",
            "src/utils",
            "src/components",
            "tests/integration",
            "tests/unit",
            "scripts/deployment",
            "scripts/data-processing",
            "config/environments",
        ]

        files = {
            # Tutorial data files
            "ADRI/tutorials/invoice_processing/invoice_data.csv":
                "invoice_id,customer_id,amount,date,status,payment_method\n"
                "INV-001,CUST-101,1250.00,2024-01-15,paid,credit_card\n"
                "INV-002,CUST-102,875.50,2024-01-16,paid,bank_transfer",

            "ADRI/tutorials/customer_service/customer_data.csv":
                "customer_id,name,email,phone,status\n"
                "CUST-001,John Doe,john@example.com,555-0101,active\n"
                "CUST-002,Jane Smith,jane@example.com,555-0102,active",

            "ADRI/tutorials/financial_analysis/market_data.csv":
                "date,symbol,price,volume,market_cap\n"
                "2024-01-15,TECH,125.50,1000000,12550000000\n"
                "2024-01-16,TECH,127.25,1200000,12725000000",

            # Sample standards
            "ADRI/dev/contracts/invoice_standard.yaml": yaml.dump({
                "contracts": {
                    "id": "invoice_standard",
                    "name": "Invoice Data Standard",
                    "version": "1.0.0"
                },
                "requirements": {
                    "overall_minimum": 75.0
                }
            }),

            # Documentation files
            "docs/README.md": "# Project Documentation",
            "docs/api/endpoints.md": "# API Endpoints",

            # Configuration files
            "config/environments/dev.yaml": "environment: development",
            "config/environments/prod.yaml": "environment: production",
        }

        config = {
            "adri": {
                "project_name": "complex_multi_directory_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                            "audit_logs": "ADRI/dev/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/dev/audit-logs",
                            "log_prefix": "adri",
                            "log_level": "DEBUG",
                            "include_data_samples": True,
                            "max_log_size_mb": 100,
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "ADRI/prod/contracts",
                            "assessments": "ADRI/prod/assessments",
                            "training_data": "ADRI/prod/training-data",
                            "audit_logs": "ADRI/prod/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/prod/audit-logs",
                            "log_prefix": "adri",
                            "log_level": "INFO",
                            "include_data_samples": True,
                            "max_log_size_mb": 100,
                        }
                    }
                }
            }
        }

        return ProjectStructure(
            directories=directories,
            files=files,
            config=config,
            name="complex_multi_directory_project",
            description="Complex ADRI project with multiple tutorials and environments"
        )

    @staticmethod
    def deep_nested_project() -> ProjectStructure:
        """Create a project with deeply nested directory structure for performance testing."""
        directories = ["ADRI"]

        # Create deep nesting (10 levels)
        nested_path = "very/deeply/nested/directory/structure/for/testing/path/resolution/performance"
        directories.append(nested_path)

        # Add ADRI structure
        adri_dirs = [
            "ADRI/tutorials/deep_nesting_test",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
        ]
        directories.extend(adri_dirs)

        files = {
            "ADRI/tutorials/deep_nesting_test/data.csv": "id,value\n1,test\n2,data",
            f"{nested_path}/test_file.txt": "This file is deeply nested for testing path resolution performance.",
        }

        config = {
            "adri": {
                "project_name": "deep_nested_test_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                            "audit_logs": "ADRI/dev/audit-logs",
                        }
                    }
                }
            }
        }

        return ProjectStructure(
            directories=directories,
            files=files,
            config=config,
            name="deep_nested_project",
            description="Project with deeply nested structure for performance testing"
        )

    @staticmethod
    def enterprise_project() -> ProjectStructure:
        """Create an enterprise-style ADRI project with comprehensive structure."""
        directories = [
            # Core ADRI structure
            "ADRI/tutorials/invoice_processing",
            "ADRI/tutorials/customer_management",
            "ADRI/tutorials/financial_reporting",
            "ADRI/tutorials/compliance_monitoring",
            "ADRI/dev/contracts",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/dev/audit-logs",
            "ADRI/staging/standards",
            "ADRI/staging/assessments",
            "ADRI/staging/training-data",
            "ADRI/staging/audit-logs",
            "ADRI/prod/contracts",
            "ADRI/prod/assessments",
            "ADRI/prod/training-data",
            "ADRI/prod/audit-logs",

            # Enterprise application structure
            "src/main/java/com/enterprise/adri",
            "src/main/resources/config",
            "src/test/java/com/enterprise/adri",
            "infrastructure/kubernetes/dev",
            "infrastructure/kubernetes/staging",
            "infrastructure/kubernetes/prod",
            "infrastructure/terraform/modules",
            "docs/architecture",
            "docs/user-guides",
            "docs/api-reference",
            "scripts/ci-cd",
            "scripts/data-migration",
            "config/environments/dev",
            "config/environments/staging",
            "config/environments/prod",
        ]

        files = {
            # Enterprise tutorial data
            "ADRI/tutorials/invoice_processing/enterprise_invoice_data.csv":
                "invoice_id,vendor_id,amount,currency,date,status,department,cost_center\n"
                "INV-2024-001,VEND-001,15750.00,USD,2024-01-15,paid,IT,CC-001\n"
                "INV-2024-002,VEND-002,8925.50,EUR,2024-01-16,pending,HR,CC-002",

            "ADRI/tutorials/customer_management/customer_data.csv":
                "customer_id,company_name,contact_email,industry,tier,annual_value\n"
                "CUST-ENT-001,TechCorp Inc,contact@techcorp.com,Technology,Enterprise,1250000\n"
                "CUST-ENT-002,FinanceGlobal LLC,admin@financeglobal.com,Finance,Premium,875000",

            # Enterprise standards
            "ADRI/prod/contracts/enterprise_invoice_standard.yaml": yaml.dump({
                "contracts": {
                    "id": "enterprise_invoice_standard",
                    "name": "Enterprise Invoice Data Quality Standard",
                    "version": "2.1.0",
                    "authority": "Enterprise Data Governance"
                },
                "requirements": {
                    "overall_minimum": 95.0,
                    "dimension_requirements": {
                        "validity": {"minimum_score": 18.0},
                        "completeness": {"minimum_score": 19.0},
                        "consistency": {"minimum_score": 18.0},
                        "freshness": {"minimum_score": 20.0},
                        "plausibility": {"minimum_score": 20.0}
                    }
                }
            }),

            # Configuration files
            "config/environments/dev/database.yaml": "host: dev-db.enterprise.com",
            "config/environments/staging/database.yaml": "host: staging-db.enterprise.com",
            "config/environments/prod/database.yaml": "host: prod-db.enterprise.com",

            # Documentation
            "docs/architecture/data-quality-framework.md": "# Enterprise Data Quality Framework",
            "docs/user-guides/getting-started.md": "# Getting Started with Enterprise ADRI",
        }

        config = {
            "adri": {
                "project_name": "enterprise_data_quality_platform",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "ADRI/dev/contracts",
                            "assessments": "ADRI/dev/assessments",
                            "training_data": "ADRI/dev/training-data",
                            "audit_logs": "ADRI/dev/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/dev/audit-logs",
                            "log_prefix": "adri-dev",
                            "log_level": "DEBUG",
                            "include_data_samples": True,
                            "max_log_size_mb": 50,
                        }
                    },
                    "staging": {
                        "paths": {
                            "contracts": "ADRI/staging/standards",
                            "assessments": "ADRI/staging/assessments",
                            "training_data": "ADRI/staging/training-data",
                            "audit_logs": "ADRI/staging/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/staging/audit-logs",
                            "log_prefix": "adri-staging",
                            "log_level": "INFO",
                            "include_data_samples": True,
                            "max_log_size_mb": 100,
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "ADRI/prod/contracts",
                            "assessments": "ADRI/prod/assessments",
                            "training_data": "ADRI/prod/training-data",
                            "audit_logs": "ADRI/prod/audit-logs",
                        },
                        "audit": {
                            "enabled": True,
                            "log_dir": "ADRI/prod/audit-logs",
                            "log_prefix": "adri-prod",
                            "log_level": "WARN",
                            "include_data_samples": False,  # Security requirement
                            "max_log_size_mb": 200,
                        }
                    }
                }
            }
        }

        return ProjectStructure(
            directories=directories,
            files=files,
            config=config,
            name="enterprise_project",
            description="Enterprise ADRI project with comprehensive governance structure"
        )


class ProjectFixtureManager:
    """Manages the creation and cleanup of mock project fixtures."""

    def __init__(self):
        self.temp_dirs = []

    def create_project(self, project_structure: ProjectStructure) -> Path:
        """Create a mock project from a ProjectStructure definition."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"{project_structure.name}_")
        self.temp_dirs.append(temp_dir)
        project_root = Path(temp_dir)

        # Create directory structure
        for directory in project_structure.directories:
            (project_root / directory).mkdir(parents=True, exist_ok=True)

        # Create files
        for file_path, content in project_structure.files.items():
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Create config.yaml
        config_path = project_root / "ADRI" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(project_structure.config, f, default_flow_style=False)

        return project_root

    def cleanup_all(self):
        """Clean up all created temporary directories."""
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup_all()


@contextmanager
def mock_project_context(project_structure: ProjectStructure, change_to_directory: Optional[str] = None):
    """
    Context manager for creating and cleaning up a mock project.

    Args:
        project_structure: The ProjectStructure to create
        change_to_directory: Optional subdirectory to change to (relative to project root)

    Yields:
        Path to the project root directory
    """
    import os

    manager = ProjectFixtureManager()
    original_cwd = os.getcwd()

    try:
        project_root = manager.create_project(project_structure)

        if change_to_directory:
            target_dir = project_root / change_to_directory
            target_dir.mkdir(parents=True, exist_ok=True)
            os.chdir(target_dir)
        else:
            os.chdir(project_root)

        yield project_root

    finally:
        os.chdir(original_cwd)
        manager.cleanup_all()


# Convenience functions for common fixtures
def create_simple_project() -> Path:
    """Create a simple ADRI project and return the path."""
    manager = ProjectFixtureManager()
    return manager.create_project(MockProjectFixtures.simple_adri_project())


def create_complex_project() -> Path:
    """Create a complex ADRI project and return the path."""
    manager = ProjectFixtureManager()
    return manager.create_project(MockProjectFixtures.complex_multi_directory_project())


def create_enterprise_project() -> Path:
    """Create an enterprise ADRI project and return the path."""
    manager = ProjectFixtureManager()
    return manager.create_project(MockProjectFixtures.enterprise_project())


# Test data generators
class TestDataGenerator:
    """Generates test data for various ADRI use cases."""

    @staticmethod
    def generate_invoice_data(num_records: int = 100, include_quality_issues: bool = False) -> str:
        """Generate CSV data for invoice processing tests."""
        import random
        from datetime import datetime, timedelta

        headers = "invoice_id,customer_id,amount,date,status,payment_method"
        rows = [headers]

        statuses = ["paid", "pending", "overdue", "cancelled"]
        payment_methods = ["credit_card", "bank_transfer", "cash", "check"]

        for i in range(1, num_records + 1):
            invoice_id = f"INV-{i:04d}"
            customer_id = f"CUST-{random.randint(101, 999)}"
            amount = round(random.uniform(100, 5000), 2)
            date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
            status = random.choice(statuses)
            payment_method = random.choice(payment_methods)

            # Introduce quality issues if requested
            if include_quality_issues and random.random() < 0.1:  # 10% chance of issues
                if random.random() < 0.3:
                    customer_id = ""  # Missing customer
                elif random.random() < 0.3:
                    amount = -abs(amount)  # Negative amount
                elif random.random() < 0.3:
                    date = "invalid_date"  # Invalid date
                else:
                    status = "INVALID_STATUS"  # Invalid status

            rows.append(f"{invoice_id},{customer_id},{amount},{date},{status},{payment_method}")

        return "\n".join(rows)

    @staticmethod
    def generate_customer_data(num_records: int = 50, include_quality_issues: bool = False) -> str:
        """Generate CSV data for customer management tests."""
        import random

        headers = "customer_id,company_name,contact_email,industry,tier,annual_value"
        rows = [headers]

        industries = ["Technology", "Finance", "Healthcare", "Manufacturing", "Retail"]
        tiers = ["Enterprise", "Premium", "Standard", "Basic"]

        for i in range(1, num_records + 1):
            customer_id = f"CUST-ENT-{i:03d}"
            company_name = f"Company {i} Inc"
            contact_email = f"contact{i}@company{i}.com"
            industry = random.choice(industries)
            tier = random.choice(tiers)
            annual_value = random.randint(10000, 2000000)

            # Introduce quality issues if requested
            if include_quality_issues and random.random() < 0.15:  # 15% chance of issues
                if random.random() < 0.4:
                    contact_email = "invalid-email"  # Invalid email
                elif random.random() < 0.4:
                    annual_value = -annual_value  # Negative value
                else:
                    tier = "UNKNOWN_TIER"  # Invalid tier

            rows.append(f"{customer_id},{company_name},{contact_email},{industry},{tier},{annual_value}")

        return "\n".join(rows)

    @staticmethod
    def generate_financial_data(num_records: int = 200, include_quality_issues: bool = False) -> str:
        """Generate CSV data for financial analysis tests."""
        import random
        from datetime import datetime, timedelta

        headers = "date,symbol,price,volume,market_cap,sector"
        rows = [headers]

        symbols = ["TECH", "BANK", "HEALTH", "ENERGY", "RETAIL"]
        sectors = ["Technology", "Financial", "Healthcare", "Energy", "Consumer"]

        for i in range(num_records):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            symbol = random.choice(symbols)
            price = round(random.uniform(50, 500), 2)
            volume = random.randint(100000, 10000000)
            market_cap = int(price * volume * random.uniform(0.8, 1.2))
            sector = random.choice(sectors)

            # Introduce quality issues if requested
            if include_quality_issues and random.random() < 0.08:  # 8% chance of issues
                if random.random() < 0.3:
                    price = 0  # Zero price
                elif random.random() < 0.3:
                    volume = -volume  # Negative volume
                else:
                    date = "2024-13-45"  # Invalid date

            rows.append(f"{date},{symbol},{price},{volume},{market_cap},{sector}")

        return "\n".join(rows)
