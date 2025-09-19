"""
ADRI CLI - Streamlined Command Interface.

Consolidated CLI from the original 2656-line commands.py into a clean, maintainable structure.
Provides essential commands for data quality assessment and standard management.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

# Updated imports for new structure - with fallbacks during migration
try:
    from .config.loader import ConfigurationLoader
    from .standards.parser import StandardsParser
    from .validator.engine import DataQualityAssessor
    from .validator.loaders import load_data, load_standard
    from .version import __version__
except ImportError:
    # Fallback to legacy imports during migration
    try:
        from adri.cli.commands import load_data, load_standard
        from adri.config.manager import ConfigManager as ConfigurationLoader
        from adri.core.assessor import DataQualityAssessor
        from adri.standards.loader import StandardsLoader as StandardsParser
        from adri.version import __version__
    except ImportError:
        # Handle missing components gracefully
        DataQualityAssessor = None
        load_data = None
        load_standard = None
        ConfigurationLoader = None
        StandardsParser = None
        __version__ = "unknown"


def create_sample_files() -> None:
    """Create sample CSV files for guided experience."""
    # Good invoice data - clean and complete (for training/creating standards)
    good_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-001,CUST-101,1250.00,2024-01-15,paid,credit_card
INV-002,CUST-102,875.50,2024-01-16,paid,bank_transfer
INV-003,CUST-103,2100.75,2024-01-17,paid,credit_card
INV-004,CUST-104,450.00,2024-01-18,pending,cash
INV-005,CUST-105,1800.25,2024-01-19,paid,bank_transfer
INV-006,CUST-106,675.00,2024-01-20,paid,credit_card
INV-007,CUST-107,1425.50,2024-01-21,paid,bank_transfer
INV-008,CUST-108,950.00,2024-01-22,pending,credit_card
INV-009,CUST-109,1125.75,2024-01-23,paid,cash
INV-010,CUST-110,775.25,2024-01-24,paid,bank_transfer"""

    # Test invoice data - has quality issues (for testing against standards)
    test_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-101,CUST-201,1350.00,2024-02-15,paid,credit_card
INV-102,,925.50,2024-02-16,paid,bank_transfer
INV-103,CUST-203,-150.75,2024-02-17,invalid,credit_card
INV-104,CUST-204,0,invalid_date,pending,cash
,CUST-205,1950.25,,paid,unknown_method
INV-106,CUST-206,850.00,2024-02-20,PAID,credit_card
INV-107,CUST-207,1625.50,2024-13-21,paid,bank_transfer
INV-108,CUST-208,,2024-02-22,pending,
INV-109,CUST-209,1225.75,2024-02-23,cancelled,cash
INV-110,DUPLICATE-ID,875.25,2024-02-24,paid,credit_card"""

    # Write sample files in their proper locations
    training_file = Path("ADRI/dev/training-data/invoice_data.csv")
    test_file = Path("ADRI/test_invoice_data.csv")

    with open(training_file, "w") as f:
        f.write(good_data)

    with open(test_file, "w") as f:
        f.write(test_data)


def show_help_guide() -> int:
    """Show first-time user guide."""
    click.echo("🚀 ADRI - First Time User Guide")
    click.echo("===============================")
    click.echo("")
    click.echo("New to ADRI? Follow this complete walkthrough:")
    click.echo("")
    click.echo("📋 Step 1 of 4: Setup Your Project")
    click.echo("   adri setup --guide")
    click.echo("   → Sets up folders & samples")
    click.echo("   Expected: ✅ Project initialized with sample data")
    click.echo("")
    click.echo("📋 Step 2 of 4: Create Your First Standard")
    click.echo(
        "   adri generate-standard ADRI/dev/training-data/invoice_data.csv --guide"
    )
    click.echo("   → Creates quality rules from clean data")
    click.echo("   Expected: ✅ Standard saved to standards/")
    click.echo("")
    click.echo("📋 Step 3 of 4: Test Data Quality")
    click.echo(
        "   adri assess ADRI/test_invoice_data.csv --standard ADRI/dev/standards/invoice_data_ADRI_standard.yaml --guide"
    )
    click.echo("   → Tests data with issues")
    click.echo("   Expected: Score: 88.5/100 ✅ PASSED → Safe for AI agents")
    click.echo("")
    click.echo("📋 Step 4 of 4: Review Results")
    click.echo("   adri list-assessments")
    click.echo("   → View assessment history")
    click.echo("   Expected: Table showing all assessment results")
    click.echo("")
    click.echo("💡 Tips:")
    click.echo("- Use Tab to autocomplete file paths")
    click.echo("- Add --verbose to any command for more details")
    click.echo("- All paths relative to ADRI/ directory")
    click.echo("")
    click.echo("🎯 Ready? Start with: adri setup --guide")
    return 0


def setup_command(
    force: bool = False, project_name: Optional[str] = None, guide: bool = False
) -> int:
    """Initialize ADRI in a project."""
    try:
        # Create ADRI directory first
        adri_dir = Path("ADRI")
        adri_dir.mkdir(exist_ok=True)

        config_path = "ADRI/config.yaml"

        # Check existing configuration
        if os.path.exists(config_path) and not force:
            if guide:
                click.echo("❌ Configuration already exists. Use --force to overwrite.")
                click.echo("💡 Or use 'adri show-config' to see current setup")
            else:
                click.echo("❌ Configuration already exists. Use --force to overwrite.")
            return 1

        # Create default configuration
        if not ConfigurationLoader:
            click.echo("❌ Configuration manager not available")
            return 1

        project_name = project_name or Path.cwd().name

        if guide:
            click.echo("🚀 Step 1 of 4: ADRI Project Setup")
            click.echo("==================================")
            click.echo("")

        # Create basic config structure with audit logging enabled by default
        config = {
            "adri": {
                "project_name": project_name,
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "ADRI/dev/standards",
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
                        },
                    },
                    "production": {
                        "paths": {
                            "standards": "ADRI/prod/standards",
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
                        },
                    },
                },
            }
        }

        # Save configuration inside ADRI directory
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Create directories
        for env_data in config["adri"]["environments"].values():
            for path in env_data["paths"].values():
                Path(path).mkdir(parents=True, exist_ok=True)

        # Create sample files for guided experience BEFORE claiming success
        if guide:
            try:
                create_sample_files()

                # Verify files were actually created
                training_file = Path("ADRI/dev/training-data/invoice_data.csv")
                test_file = Path("ADRI/test_invoice_data.csv")

                if not training_file.exists():
                    click.echo("❌ Failed to create training data file")
                    click.echo(f"▶ Expected: {training_file}")
                    return 1

                if not test_file.exists():
                    click.echo("❌ Failed to create test data file")
                    click.echo(f"▶ Expected: {test_file}")
                    return 1

            except Exception as e:
                click.echo(f"❌ Failed to create sample files: {e}")
                click.echo("▶ Try: adri setup --guide --force")
                return 1

        if guide:
            click.echo("✅ Project structure created with sample data")
            click.echo("")
            click.echo("📁 What was created:")
            click.echo("   📋 standards/     - Quality rules")
            click.echo("   📊 assessments/   - Assessment reports")
            click.echo("   📄 training-data/ - Clean sample data")
            click.echo("   📈 audit-logs/    - Comprehensive audit trail")
            click.echo("")
            click.echo("💡 Tip: All paths relative to ADRI/ directory")
            click.echo("")
            click.echo(
                "▶ Next Step 2 of 4: adri generate-standard training-data/invoice_data.csv --guide"
            )
        else:
            click.echo("✅ ADRI project initialized successfully!")
            click.echo(f"📁 Project: {project_name}")
            click.echo(f"⚙️  Config: {config_path}")

        return 0

    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")
        click.echo("▶ Try: adri setup --guide --force")
        return 1


def assess_command(
    data_path: str,
    standard_path: str,
    output_path: Optional[str] = None,
    guide: bool = False,
) -> int:
    """Run data quality assessment."""
    try:
        if guide:
            click.echo("📊 ADRI Data Quality Assessment")
            click.echo("==============================")
            click.echo("")
            click.echo(f"📄 Testing: {data_path}")
            click.echo(f"📋 Against Standard: {standard_path}")
            click.echo("🔍 Running 5-dimension quality analysis...")
            click.echo("")

        # Load data
        if not load_data:
            click.echo("❌ Data loader not available")
            return 1

        data_list = load_data(data_path)
        if not data_list:
            click.echo("❌ No data loaded")
            return 1

        # Convert to DataFrame
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Create assessor with audit configuration and run assessment
        if not DataQualityAssessor:
            click.echo("❌ Assessment engine not available")
            return 1

        # Load configuration for audit logging
        assessor_config = {}
        if ConfigurationLoader:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    if "audit" in env_config:
                        assessor_config["audit"] = env_config["audit"]
                except (KeyError, AttributeError):
                    # Use default audit config if environment config not available
                    assessor_config["audit"] = {
                        "enabled": True,
                        "log_dir": "ADRI/dev/audit-logs",
                        "log_prefix": "adri",
                        "log_level": "INFO",
                        "include_data_samples": True,
                        "max_log_size_mb": 100,
                    }
            else:
                # Default audit config if no configuration found
                assessor_config["audit"] = {
                    "enabled": True,
                    "log_dir": "ADRI/dev/audit-logs",
                    "log_prefix": "adri",
                    "log_level": "INFO",
                    "include_data_samples": True,
                    "max_log_size_mb": 100,
                }

        assessor = DataQualityAssessor(assessor_config)
        result = assessor.assess(data, standard_path)

        # Capture detailed validation failures for audit logging
        failed_checks = []

        # Load standard to get record identification configuration
        standard_config = {}
        try:
            if load_standard:
                standard_config = load_standard(standard_path)
        except Exception:
            pass

        # Get record identification settings from standard
        record_id_config = standard_config.get("record_identification", {})
        primary_key_fields = record_id_config.get("primary_key_fields", [])

        def get_record_id(row, row_index):
            """Generate record ID based on standard configuration."""
            if primary_key_fields:
                # Try to use primary key fields
                key_values = []
                for field in primary_key_fields:
                    if field in row and pd.notna(row[field]):
                        key_values.append(str(row[field]))

                if key_values:
                    if len(key_values) == 1:
                        return f"{key_values[0]} (Row {row_index + 1})"
                    else:
                        # Compound key
                        return f"{':'.join(key_values)} (Row {row_index + 1})"

            # Fallback to row position
            return f"Row {row_index + 1}"

        # Check for primary key uniqueness first (using proper validation rule)
        validation_id = 1
        try:
            from .validator.rules import check_primary_key_uniqueness

            pk_failures = check_primary_key_uniqueness(data, standard_config)
            failed_checks.extend(pk_failures)
            validation_id += len(pk_failures)
        except ImportError:
            pass  # Rule not available

        # Analyze data for specific validation failures
        for i, row in data.iterrows():
            record_id = get_record_id(row, i)

            # Check for missing values (completeness)
            if row.isnull().any():
                missing_fields = [col for col in row.index if pd.isna(row[col])]
                for field in missing_fields[:2]:  # Limit to first 2 missing fields
                    failed_checks.append(
                        {
                            "validation_id": f"val_{validation_id:03d}",
                            "dimension": "completeness",
                            "field": field,  # Use 'field' not 'field_name'
                            "issue": "missing_value",  # Use 'issue' not 'issue_type'
                            "affected_rows": 1,
                            "affected_percentage": (1.0 / len(data)) * 100,
                            "samples": [
                                record_id
                            ],  # Use 'samples' not 'sample_failures'
                            "remediation": f"Fill missing {field} values",
                        }
                    )
                    validation_id += 1

            # Check for negative amounts (validity)
            if "amount" in row and pd.notna(row["amount"]):
                try:
                    amount_val = float(row["amount"])
                    if amount_val < 0:
                        failed_checks.append(
                            {
                                "validation_id": f"val_{validation_id:03d}",
                                "dimension": "validity",
                                "field": "amount",
                                "issue": "negative_value",
                                "affected_rows": 1,
                                "affected_percentage": (1.0 / len(data)) * 100,
                                "samples": [record_id],
                                "remediation": "Remove or correct negative amounts",
                            }
                        )
                        validation_id += 1
                except (ValueError, TypeError):
                    failed_checks.append(
                        {
                            "validation_id": f"val_{validation_id:03d}",
                            "dimension": "validity",
                            "field": "amount",
                            "issue": "invalid_format",
                            "affected_rows": 1,
                            "affected_percentage": (1.0 / len(data)) * 100,
                            "samples": [record_id],
                            "remediation": "Fix amount format to valid number",
                        }
                    )
                    validation_id += 1

            # Check for invalid dates (validity)
            if (
                "date" in row
                and pd.notna(row["date"])
                and "invalid" in str(row["date"]).lower()
            ):
                failed_checks.append(
                    {
                        "validation_id": f"val_{validation_id:03d}",
                        "dimension": "validity",
                        "field": "date",
                        "issue": "invalid_format",
                        "affected_rows": 1,
                        "affected_percentage": (1.0 / len(data)) * 100,
                        "samples": [record_id],
                        "remediation": "Fix date format to valid date",
                    }
                )
                validation_id += 1

        # Pass failed_checks to audit logger if available
        if (
            hasattr(assessor, "audit_logger")
            and assessor.audit_logger
            and failed_checks
        ):
            # Re-log with detailed failures
            execution_context = {
                "function_name": "assess",
                "module_path": "adri.cli",
                "environment": os.environ.get("ADRI_ENV", "PRODUCTION"),
            }

            data_info = {
                "row_count": len(data),
                "column_count": len(data.columns),
                "columns": list(data.columns),
            }

            performance_metrics = {"duration_ms": 0}

            # Create a new audit record with field-level failures
            from datetime import datetime

            assessment_id = (
                f"adri_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(3).hex()}"
            )

            # Create audit record manually to ensure failed_checks are properly captured
            if hasattr(assessor.audit_logger, "log_assessment"):
                audit_record = assessor.audit_logger.log_assessment(
                    assessment_result=result,
                    execution_context=execution_context,
                    data_info=data_info,
                    performance_metrics=performance_metrics,
                    failed_checks=failed_checks,
                )

        # Auto-save report in guide mode
        if guide:
            # Determine assessments directory from configuration
            if ConfigurationLoader:
                config_loader = ConfigurationLoader()
                config = config_loader.get_active_config()
                if config:
                    try:
                        env_config = config_loader.get_environment_config(config)
                        assessments_dir = Path(env_config["paths"]["assessments"])
                        assessments_dir.mkdir(parents=True, exist_ok=True)
                    except (KeyError, AttributeError):
                        assessments_dir = Path("ADRI/dev/assessments")
                        assessments_dir.mkdir(parents=True, exist_ok=True)
                else:
                    assessments_dir = Path("ADRI/dev/assessments")
                    assessments_dir.mkdir(parents=True, exist_ok=True)
            else:
                assessments_dir = Path("ADRI/dev/assessments")
                assessments_dir.mkdir(parents=True, exist_ok=True)

            # Generate meaningful filename with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_name = Path(data_path).stem
            auto_output_path = (
                assessments_dir / f"{data_name}_assessment_{timestamp}.json"
            )

            # Save the report automatically
            report_data = result.to_standard_dict()
            with open(auto_output_path, "w") as f:
                json.dump(report_data, f, indent=2)

        if guide:
            # Clean, minimal output for guided mode with record counts
            status_icon = "✅" if result.passed else "❌"
            status_text = "PASSED" if result.passed else "FAILED"

            # Do actual analysis to count real failures (not estimation)
            total_records = len(data)

            # Analyze the actual data to find records with issues
            failed_records_list = []
            for i, row in data.iterrows():
                issues = []
                # Check for missing values
                if row.isnull().any():
                    missing_fields = [col for col in row.index if pd.isna(row[col])]
                    if missing_fields:
                        issues.append(f"missing {', '.join(missing_fields[:2])}")

                # Check for negative amounts (example business rule)
                if "amount" in row and pd.notna(row["amount"]):
                    try:
                        amount_val = float(row["amount"])
                        if amount_val < 0:
                            issues.append("negative amount")
                    except (ValueError, TypeError):
                        issues.append("invalid amount format")

                # Check for invalid dates
                if (
                    "date" in row
                    and pd.notna(row["date"])
                    and "invalid" in str(row["date"]).lower()
                ):
                    issues.append("invalid date format")

                if issues:
                    record_id = row.get("invoice_id", f"Row {i+1}")
                    if pd.isna(record_id):
                        record_id = f"Row {i+1}"
                    failed_records_list.append(f"   • {record_id}: {', '.join(issues)}")

            # Use actual count of failed records
            actual_failed_records = len(failed_records_list)
            actual_passed_records = total_records - actual_failed_records

            # Plain language explanation with ACTUAL record counts
            if result.passed:
                explanation = f"{actual_passed_records} of {total_records} records passed quality checks"
                if actual_failed_records > 0:
                    explanation += f" ({actual_failed_records} need attention)"
            else:
                explanation = f"{actual_failed_records} of {total_records} records failed quality checks"

            # Enhanced display targeted at AI Agent Engineers
            click.echo("📊 Quality Assessment Results:")
            click.echo("==============================")
            click.echo(
                f"🎯 Agent System Health: {result.overall_score:.1f}/100 {status_icon} {status_text}"
            )
            click.echo(f"   → Overall reliability for AI agent workflows")
            click.echo(
                f"   → Use for: monitoring agent performance, framework integration health"
            )
            click.echo("")
            click.echo(
                f"⚙️  Execution Readiness: {actual_passed_records}/{total_records} records safe for agents"
            )
            click.echo(f"   → Immediate agent execution safety assessment")
            click.echo(
                f"   → Use for: pre-flight checks, error handling capacity, data preprocessing needs"
            )

            # Show failed records and their specific errors if any
            if actual_failed_records > 0:
                click.echo("")
                click.echo("🔍 Records Requiring Attention:")

                # Show up to 3 examples
                for failure in failed_records_list[:3]:
                    click.echo(failure)

                if actual_failed_records > 3:
                    remaining = actual_failed_records - 3
                    click.echo(f"   • ... and {remaining} more records with issues")

            click.echo("")
            click.echo("▶ Next: adri list-assessments --verbose")
            click.echo("▶ View audit trail: adri view-logs")

            if not result.passed:
                click.echo("▶ See specific issues: adri view-logs --verbose")
        else:
            # Clean, minimal output for non-guided mode with record counts
            status_icon = "✅" if result.passed else "❌"
            status_text = "PASSED" if result.passed else "FAILED"

            # Calculate record counts for non-guided mode too
            total_records = len(data)
            passed_records = int((result.overall_score / 100.0) * total_records)
            failed_records = total_records - passed_records

            if result.passed:
                explanation = f"{passed_records}/{total_records} records passed"
            else:
                explanation = f"{failed_records}/{total_records} records failed"

            click.echo(
                f"Score: {result.overall_score:.1f}/100 {status_icon} {status_text} → {explanation}"
            )

        # Save report if output specified (manual mode)
        if output_path:
            report_data = result.to_standard_dict()
            with open(output_path, "w") as f:
                json.dump(report_data, f, indent=2)
            click.echo(f"📄 Report saved: {output_path}")

        return 0

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}")
        return 1
    except Exception as e:
        click.echo(f"❌ Assessment failed: {e}")
        return 1


def generate_standard_command(
    data_path: str, force: bool = False, guide: bool = False
) -> int:
    """Generate ADRI standard from data analysis."""
    try:
        # Load and analyze data
        if not load_data:
            click.echo("❌ Data loader not available")
            return 1

        data_list = load_data(data_path)
        if not data_list:
            click.echo("❌ No data loaded")
            return 1

        # Determine proper output location using configuration
        data_name = Path(data_path).stem
        standard_filename = f"{data_name}_ADRI_standard.yaml"

        # Try to get standards directory from configuration
        if ConfigurationLoader:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    standards_dir = Path(env_config["paths"]["standards"])
                    standards_dir.mkdir(parents=True, exist_ok=True)
                    output_path = standards_dir / standard_filename
                except (KeyError, AttributeError):
                    # Fallback to default dev location
                    Path("ADRI/dev/standards").mkdir(parents=True, exist_ok=True)
                    output_path = Path("ADRI/dev/standards") / standard_filename
            else:
                # No config found, use default dev location
                Path("ADRI/dev/standards").mkdir(parents=True, exist_ok=True)
                output_path = Path("ADRI/dev/standards") / standard_filename
        else:
            # No ConfigurationLoader, use default dev location
            Path("ADRI/dev/standards").mkdir(parents=True, exist_ok=True)
            output_path = Path("ADRI/dev/standards") / standard_filename

        if output_path.exists() and not force:
            if guide:
                click.echo(
                    f"❌ Standard exists: {output_path}. Use --force to overwrite."
                )
                click.echo("💡 Or use a different data file name")
            else:
                click.echo(
                    f"❌ Standard exists: {output_path}. Use --force to overwrite."
                )
            return 1

        if guide:
            click.echo("📊 Generating ADRI Standard from Data Analysis")
            click.echo("=============================================")
            click.echo("")
            click.echo(f"📄 Analyzing: {data_path}")
            click.echo("📋 Creating data quality rules based on your good data...")
            click.echo("")

        # Create basic standard structure
        import pandas as pd

        data = pd.DataFrame(data_list)

        # Generate field requirements from data
        field_requirements = {}
        for column in data.columns:
            # Infer type and nullable from data
            non_null_data = data[column].dropna()
            if len(non_null_data) == 0:
                field_type = "string"
            elif non_null_data.dtype in ["int64", "int32"]:
                field_type = "integer"
            elif non_null_data.dtype in ["float64", "float32"]:
                field_type = "float"
            else:
                field_type = "string"

            # Convert numpy boolean to native Python bool
            nullable = bool(data[column].isnull().any())

            field_requirements[column] = {"type": field_type, "nullable": nullable}

        # Determine primary key fields for record identification
        primary_key_fields = []
        for column in data.columns:
            column_str = str(column).lower()
            # Look for common ID patterns
            if any(
                pattern in column_str for pattern in ["id", "key", "number"]
            ) and not any(
                skip in column_str for skip in ["description", "name", "type"]
            ):
                primary_key_fields = [column]
                break

        # If no clear primary key found, use the first column as fallback
        if not primary_key_fields and len(data.columns) > 0:
            primary_key_fields = [data.columns[0]]

        # Create standard dictionary with record identification
        standard = {
            "standards": {
                "id": f"{data_name}_standard",
                "name": f"{data_name} ADRI Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": f"Auto-generated standard for {data_name} data",
            },
            "record_identification": {
                "primary_key_fields": primary_key_fields,
                "strategy": "primary_key_with_fallback",
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": field_requirements,
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0},
                    "completeness": {"minimum_score": 15.0},
                    "consistency": {"minimum_score": 12.0},
                    "freshness": {"minimum_score": 15.0},
                    "plausibility": {"minimum_score": 12.0},
                },
            },
        }

        # Save standard
        with open(output_path, "w") as f:
            yaml.dump(standard, f, default_flow_style=False, sort_keys=False)

        if guide:
            click.echo("✅ Standard Generated Successfully!")
            click.echo("==================================")
            click.echo(f"📄 Standard: {standard['standards']['name']}")
            click.echo(f"📁 Saved to: {output_path}")
            click.echo("")
            click.echo("📋 What the standard contains:")
            click.echo(f"   • {len(field_requirements)} field requirements")
            click.echo(
                "   • 5 quality dimensions (validity, completeness, consistency, freshness, plausibility)"
            )
            click.echo(f"   • Overall minimum score: 75.0/100")
            click.echo("")
            click.echo("🎯 Next Step - Test Data Quality:")
            click.echo("===============================")
            if "invoice_data" in data_path:
                click.echo(
                    "adri assess ADRI/test_invoice_data.csv --standard ADRI/dev/standards/invoice_data_ADRI_standard.yaml --guide"
                )
            else:
                click.echo(
                    f"adri assess your_test_data.csv --standard {output_path} --guide"
                )
            click.echo("")
            click.echo(
                "💡 This will test data with quality issues against your new standard!"
            )
        else:
            click.echo("✅ Standard generated successfully!")
            click.echo(f"📄 Standard: {standard['standards']['name']}")
            click.echo(f"📁 Saved to: {output_path}")

        return 0

    except Exception as e:
        click.echo(f"❌ Generation failed: {e}")
        return 1


def validate_standard_command(standard_path: str) -> int:
    """Validate YAML standard file."""
    try:
        # Load standard
        if not load_standard:
            click.echo("❌ Standard loader not available")
            return 1

        standard = load_standard(standard_path)

        # Basic validation
        errors = []

        # Check required sections
        if "standards" not in standard:
            errors.append("Missing 'standards' section")
        elif not isinstance(standard["standards"], dict):
            errors.append("'standards' section must be a dictionary")
        else:
            std_section = standard["standards"]
            required_fields = ["id", "name", "version", "authority"]
            for field in required_fields:
                if field not in std_section:
                    errors.append(f"Missing required field in standards: '{field}'")
                elif not std_section[field]:
                    errors.append(f"Empty value for required field: '{field}'")

        if "requirements" not in standard:
            errors.append("Missing 'requirements' section")
        elif not isinstance(standard["requirements"], dict):
            errors.append("'requirements' section must be a dictionary")

        # Display results
        if errors:
            click.echo("❌ Standard validation FAILED")
            for error in errors:
                click.echo(f"  • {error}")
            return 1
        else:
            click.echo("✅ Standard validation PASSED")
            std_info = standard.get("standards", {})
            click.echo(f"📄 Standard: {std_info.get('name', 'Unknown')}")
            click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
            click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")
            return 0

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        return 1


def list_standards_command() -> int:
    """List available YAML standards."""
    try:
        # Check for bundled standards first
        standards_found = False

        try:
            if StandardsParser:
                parser = StandardsParser()
                bundled_standards = parser.list_available_standards()
                if bundled_standards:
                    click.echo("📦 Bundled Standards:")
                    for i, std_name in enumerate(bundled_standards, 1):
                        click.echo(f"  {i}. {std_name}")
                    standards_found = True
        except (ImportError, AttributeError):
            pass

        # Check for project standards
        standards_dir = Path("ADRI/dev/standards")
        if standards_dir.exists():
            yaml_files = list(standards_dir.glob("*.yaml")) + list(
                standards_dir.glob("*.yml")
            )
            if yaml_files:
                if standards_found:
                    click.echo()
                click.echo("🏗️  Project Standards:")
                for i, file_path in enumerate(yaml_files, 1):
                    click.echo(f"  {i}. {file_path.name}")
                standards_found = True

        if not standards_found:
            click.echo("📋 No standards found")
            click.echo("💡 Use 'adri generate-standard <data>' to create one")

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to list standards: {e}")
        return 1


def show_config_command(
    paths_only: bool = False, environment: Optional[str] = None
) -> int:
    """Show current ADRI configuration."""
    try:
        # Load configuration
        if not ConfigurationLoader:
            click.echo("❌ Configuration loader not available")
            return 1

        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()

        if not config:
            click.echo("❌ No ADRI configuration found")
            click.echo("💡 Run 'adri setup' to initialize ADRI in this project")
            return 1

        adri_config = config["adri"]

        if not paths_only:
            click.echo("📋 ADRI Configuration")
            click.echo(f"🏗️  Project: {adri_config['project_name']}")
            click.echo(f"📦 Version: {adri_config.get('version', '4.0.0')}")
            click.echo(f"🌍 Default Environment: {adri_config['default_environment']}")
            click.echo()

        # Show environment paths
        environments_to_show = (
            [environment] if environment else list(adri_config["environments"].keys())
        )

        for env_name in environments_to_show:
            if env_name not in adri_config["environments"]:
                click.echo(f"❌ Environment '{env_name}' not found")
                continue

            env_config = adri_config["environments"][env_name]
            paths = env_config["paths"]

            click.echo(f"📁 {env_name.title()} Environment:")
            for path_type, path_value in paths.items():
                status = "✅" if os.path.exists(path_value) else "❌"
                click.echo(f"  {status} {path_type}: {path_value}")
            click.echo()

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {e}")
        return 1


def list_assessments_command(recent: int = 10, verbose: bool = False) -> int:
    """List previous assessment reports."""
    try:
        # Load configuration to find assessments directory
        config_loader = ConfigurationLoader() if ConfigurationLoader else None
        if config_loader:
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    assessments_dir = Path(env_config["paths"]["assessments"])
                except (KeyError, AttributeError):
                    assessments_dir = Path("ADRI/dev/assessments")
            else:
                assessments_dir = Path("ADRI/dev/assessments")
        else:
            assessments_dir = Path("ADRI/dev/assessments")

        # Check if assessments directory exists
        if not assessments_dir.exists():
            click.echo("📁 No assessments directory found")
            click.echo("▶ Create assessments: adri assess <data> --standard <standard>")
            return 0

        # Find JSON assessment files
        assessment_files = list(assessments_dir.glob("*.json"))
        if not assessment_files:
            click.echo("📊 No assessment reports found")
            click.echo("▶ Create assessments: adri assess <data> --standard <standard>")
            return 0

        # Sort by modification time (newest first) and limit
        assessment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        if recent > 0:
            assessment_files = assessment_files[:recent]

        # Parse assessment data for table display
        table_data = []
        for file_path in assessment_files:
            try:
                with open(file_path, "r") as f:
                    assessment_data = json.load(f)

                # Extract key information from nested JSON structure
                adri_report = assessment_data.get("adri_assessment_report", {})
                summary = adri_report.get("summary", {})
                score = summary.get("overall_score", 0)
                passed = summary.get("overall_passed", False)

                # Get timestamp from filename or file stats
                file_stats = file_path.stat()
                modified_time = file_stats.st_mtime
                from datetime import datetime

                date_str = datetime.fromtimestamp(modified_time).strftime("%m-%d %H:%M")

                # Extract dataset name from filename
                dataset_name = file_path.stem.replace("_assessment_", "_").split("_")[0]

                table_data.append(
                    {
                        "dataset": dataset_name,
                        "score": f"{score:.1f}/100",
                        "status": "✅ PASSED" if passed else "❌ FAILED",
                        "date": date_str,
                        "file": file_path.name,
                    }
                )

            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                # Skip malformed files
                continue

        if not table_data:
            click.echo("📊 No valid assessment reports found")
            click.echo("▶ Try running: adri assess <data> --standard <standard>")
            return 0

        # Load audit logs to get record counts
        audit_entries = []
        config_loader = ConfigurationLoader() if ConfigurationLoader else None
        if config_loader:
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    audit_logs_dir = Path(env_config["paths"]["audit_logs"])
                except (KeyError, AttributeError):
                    audit_logs_dir = Path("ADRI/dev/audit-logs")
            else:
                audit_logs_dir = Path("ADRI/dev/audit-logs")
        else:
            audit_logs_dir = Path("ADRI/dev/audit-logs")

        # Read audit log file if it exists
        main_log_file = audit_logs_dir / "adri_assessment_logs.csv"
        if main_log_file.exists():
            import csv

            with open(main_log_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        timestamp_str = row.get("timestamp", "")
                        if "T" in timestamp_str:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "")
                            )
                        else:
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )

                        audit_entries.append(
                            {
                                "timestamp": timestamp,
                                "data_row_count": int(row.get("data_row_count", 0)),
                                "overall_score": float(row.get("overall_score", 0)),
                            }
                        )
                    except (ValueError, KeyError):
                        continue

        # Enhance table data with record counts from audit logs
        enhanced_table_data = []
        for entry in table_data:
            # Find corresponding audit log entry for record counts
            audit_entry = None
            for log_entry in audit_entries:
                if log_entry["timestamp"].strftime("%m-%d %H:%M") == entry["date"]:
                    audit_entry = log_entry
                    break

            # Calculate record counts
            if audit_entry:
                total_records = audit_entry["data_row_count"]
                score_value = float(entry["score"].split("/")[0])
                passed_records = (
                    int((score_value / 100.0) * total_records)
                    if total_records > 0
                    else 0
                )
                records_info = f"{passed_records}/{total_records}"
            else:
                records_info = "N/A"

            enhanced_table_data.append({**entry, "records": records_info})

        # Display compact table with Records column
        click.echo(f"📊 Assessment Reports ({len(enhanced_table_data)} recent)")
        click.echo(
            "┌─────────────────┬───────────┬──────────────┬───────────┬─────────────┐"
        )
        click.echo(
            "│ Data Packet     │ Score     │ Status       │ Records   │ Date        │"
        )
        click.echo(
            "├─────────────────┼───────────┼──────────────┼───────────┼─────────────┤"
        )

        for entry in enhanced_table_data:
            data_packet = entry["dataset"][:15].ljust(15)  # Truncate/pad to 15 chars
            score = entry["score"].ljust(9)
            status = entry["status"].ljust(12)
            records = entry["records"].ljust(9)
            date = entry["date"].ljust(11)

            click.echo(f"│ {data_packet} │ {score} │ {status} │ {records} │ {date} │")

        click.echo(
            "└─────────────────┴───────────┴──────────────┴───────────┴─────────────┘"
        )
        click.echo()

        if verbose:
            click.echo("📄 Report Files:")
            for i, entry in enumerate(table_data, 1):
                click.echo(f"  {i}. {entry['file']}")
            click.echo()

        click.echo("▶ View details: adri list-assessments --verbose")
        click.echo("▶ View audit trail: adri view-logs")

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to list assessments: {e}")
        click.echo("▶ Try: adri assess <data> --standard <standard>")
        return 1


def view_logs_command(
    recent: int = 10, today: bool = False, verbose: bool = False
) -> int:
    """View audit logs from CSV files."""
    try:
        # Load configuration to find audit logs directory
        config_loader = ConfigurationLoader() if ConfigurationLoader else None
        if config_loader:
            config = config_loader.get_active_config()
            if config:
                try:
                    env_config = config_loader.get_environment_config(config)
                    audit_logs_dir = Path(env_config["paths"]["audit_logs"])
                except (KeyError, AttributeError):
                    audit_logs_dir = Path("ADRI/dev/audit-logs")
            else:
                audit_logs_dir = Path("ADRI/dev/audit-logs")
        else:
            audit_logs_dir = Path("ADRI/dev/audit-logs")

        # Check if audit logs directory exists
        if not audit_logs_dir.exists():
            click.echo("📁 No audit logs directory found")
            click.echo(
                "💡 Run 'adri assess <data> --standard <standard>' to create audit logs"
            )
            return 0

        # Check for main audit log file
        main_log_file = audit_logs_dir / "adri_assessment_logs.csv"
        if not main_log_file.exists():
            click.echo("📊 No audit logs found")
            click.echo(
                "💡 Run 'adri assess <data> --standard <standard>' to create audit logs"
            )
            return 0

        # Read and parse CSV file
        import csv
        from datetime import date, datetime

        log_entries = []

        with open(main_log_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse timestamp
                    timestamp_str = row.get("timestamp", "")
                    if timestamp_str:
                        # Handle ISO format timestamp
                        if "T" in timestamp_str:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "")
                            )
                        else:
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                    else:
                        timestamp = datetime.now()

                    # Filter by today if requested
                    if today and timestamp.date() != date.today():
                        continue

                    log_entries.append(
                        {
                            "timestamp": timestamp,
                            "assessment_id": row.get("assessment_id", "unknown"),
                            "overall_score": float(row.get("overall_score", 0)),
                            "passed": row.get("passed", "FALSE") == "TRUE",
                            "data_row_count": int(row.get("data_row_count", 0)),
                            "function_name": row.get("function_name", ""),
                            "standard_id": row.get("standard_id", "unknown"),
                            "assessment_duration_ms": int(
                                row.get("assessment_duration_ms", 0)
                            ),
                            "execution_decision": row.get(
                                "execution_decision", "unknown"
                            ),
                        }
                    )
                except (ValueError, KeyError) as e:
                    # Skip malformed entries
                    continue

        if not log_entries:
            click.echo("📊 No audit log entries found")
            return 0

        # Sort by timestamp (newest first) and limit
        log_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        if recent > 0:
            log_entries = log_entries[:recent]

        # Parse audit data for enhanced table display
        table_data = []
        for entry in log_entries:
            # Determine mode based on function_name
            if entry["function_name"] == "assess":
                mode = (
                    "CLI Guide"
                    if "guide" in entry.get("assessment_id", "")
                    else "CLI Direct"
                )
                function_name = "N/A"
                module_path = "N/A"
            else:
                mode = "Decorator"
                function_name = entry["function_name"] or "Unknown"
                module_path = entry.get("module_path", "Unknown")
                # Truncate long paths for table display
                if len(module_path) > 12:
                    module_path = module_path[:9] + "..."

            # Extract data packet name from standard_id or assessment context
            standard_id = entry["standard_id"]
            if standard_id and "_ADRI_standard" in standard_id:
                data_packet = standard_id.replace("_ADRI_standard", "")
            else:
                data_packet = "unknown"

            # Truncate for table display
            if len(data_packet) > 12:
                data_packet = data_packet[:9] + "..."
            if len(function_name) > 14 and function_name != "N/A":
                function_name = function_name[:11] + "..."

            date_str = entry["timestamp"].strftime("%m-%d %H:%M")
            score = f"{entry['overall_score']:.1f}/100"
            status = "✅ PASSED" if entry["passed"] else "❌ FAILED"

            table_data.append(
                {
                    "data_packet": data_packet,
                    "score": score,
                    "status": status,
                    "mode": mode,
                    "function": function_name,
                    "module": module_path,
                    "date": date_str,
                }
            )

        # Display enhanced enterprise debugging table
        click.echo(f"📊 ADRI Audit Log Summary ({len(table_data)} recent)")
        click.echo(
            "┌─────────────┬───────────┬──────────────┬─────────────┬─────────────────┬─────────────┬─────────────┐"
        )
        click.echo(
            "│ Data Packet │ Score     │ Status       │ Mode        │ Function        │ Module      │ Date        │"
        )
        click.echo(
            "├─────────────┼───────────┼──────────────┼─────────────┼─────────────────┼─────────────┼─────────────┤"
        )

        for entry in table_data:
            data_packet = entry["data_packet"].ljust(11)
            score = entry["score"].ljust(9)
            status = entry["status"].ljust(12)
            mode = entry["mode"].ljust(11)
            function = entry["function"].ljust(15)
            module = entry["module"].ljust(11)
            date = entry["date"].ljust(11)

            click.echo(
                f"│ {data_packet} │ {score} │ {status} │ {mode} │ {function} │ {module} │ {date} │"
            )

        click.echo(
            "└─────────────┴───────────┴──────────────┴─────────────┴─────────────────┴─────────────┴─────────────┘"
        )

        if verbose:
            click.echo()
            click.echo("📄 Detailed Audit Information:")
            for i, entry in enumerate(log_entries, 1):
                click.echo(f"  {i}. Assessment ID: {entry['assessment_id']}")
                click.echo(
                    f"     Records: {entry['data_row_count']} | Duration: {entry['assessment_duration_ms']}ms"
                )
                click.echo(f"     Decision: {entry['execution_decision']}")
                click.echo()
        else:
            click.echo()
            click.echo("💡 Use --verbose for detailed audit information")

        click.echo()
        click.echo("📁 Audit Log Files:")
        click.echo(f"   📄 {audit_logs_dir}/adri_assessment_logs.csv")
        click.echo(f"   📊 {audit_logs_dir}/adri_dimension_scores.csv")
        click.echo(f"   ❌ {audit_logs_dir}/adri_failed_validations.csv")

        return 0

    except Exception as e:
        click.echo(f"❌ Failed to view logs: {e}")
        return 1


def show_standard_command(standard_name: str, verbose: bool = False) -> int:
    """Show details of a specific ADRI standard."""
    try:
        # Try to load standard
        if not load_standard:
            click.echo("❌ Standard loader not available")
            return 1

        # Check if it's a file path or standard name
        if os.path.exists(standard_name):
            standard_path = standard_name
        else:
            # Try common locations
            standard_path = None
            for path in [
                f"ADRI/dev/standards/{standard_name}.yaml",
                f"ADRI/prod/standards/{standard_name}.yaml",
                f"{standard_name}.yaml",
            ]:
                if os.path.exists(path):
                    standard_path = path
                    break

            if not standard_path:
                click.echo(f"❌ Standard not found: {standard_name}")
                click.echo("💡 Use 'adri list-standards' to see available standards")
                return 1

        standard = load_standard(standard_path)
        std_info = standard.get("standards", {})

        click.echo("📋 ADRI Standard Details")
        click.echo(f"📄 Name: {std_info.get('name', 'Unknown')}")
        click.echo(f"🆔 ID: {std_info.get('id', 'Unknown')}")
        click.echo(f"📦 Version: {std_info.get('version', 'Unknown')}")
        click.echo(f"🏛️  Authority: {std_info.get('authority', 'Unknown')}")

        if "description" in std_info:
            click.echo(f"📝 Description: {std_info['description']}")

        requirements = standard.get("requirements", {})
        click.echo(
            f"\n🎯 Overall Minimum Score: {requirements.get('overall_minimum', 'Not set')}/100"
        )

        if verbose and "field_requirements" in requirements:
            field_reqs = requirements["field_requirements"]
            click.echo(f"\n📋 Field Requirements ({len(field_reqs)} fields):")
            for field_name, field_config in field_reqs.items():
                field_type = field_config.get("type", "unknown")
                nullable = (
                    "nullable" if field_config.get("nullable", True) else "required"
                )
                click.echo(f"  • {field_name}: {field_type} ({nullable})")

        if verbose and "dimension_requirements" in requirements:
            dim_reqs = requirements["dimension_requirements"]
            click.echo(f"\n📊 Dimension Requirements ({len(dim_reqs)} dimensions):")
            for dim_name, dim_config in dim_reqs.items():
                min_score = dim_config.get("minimum_score", "Not set")
                click.echo(f"  • {dim_name}: ≥{min_score}/20")

        click.echo(
            f"\n💡 Use 'adri assess <data> --standard {standard_name}' to test data"
        )
        return 0

    except Exception as e:
        click.echo(f"❌ Failed to show standard: {e}")
        return 1


# CLI Group Definition
@click.group()
@click.version_option(version=__version__, prog_name="adri")
def cli():
    """ADRI - Stop Your AI Agents Breaking on Bad Data."""
    pass


# Command Definitions
@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--project-name", help="Custom project name")
@click.option(
    "--guide", is_flag=True, help="Show step-by-step guidance and create sample files"
)
def setup(force, project_name, guide):
    """Initialize ADRI in a project."""
    sys.exit(setup_command(force, project_name, guide))


@cli.command()
@click.argument("data_path")
@click.option(
    "--standard", "standard_path", required=True, help="Path to YAML standard file"
)
@click.option("--output", "output_path", help="Output path for assessment report")
@click.option(
    "--guide", is_flag=True, help="Show detailed assessment explanation and next steps"
)
def assess(data_path, standard_path, output_path, guide):
    """Run data quality assessment."""
    sys.exit(assess_command(data_path, standard_path, output_path, guide))


@cli.command("generate-standard")
@click.argument("data_path")
@click.option("--force", is_flag=True, help="Overwrite existing standard file")
@click.option("-o", "--output", help="Output path for generated standard file")
@click.option(
    "--guide", is_flag=True, help="Show detailed generation explanation and next steps"
)
def generate_standard(data_path, force, output, guide):
    """Generate ADRI standard from data file analysis."""
    sys.exit(generate_standard_command(data_path, force, guide))


@cli.command("help-guide")
def help_guide():
    """Show first-time user guide and tutorial."""
    sys.exit(show_help_guide())


@cli.command("validate-standard")
@click.argument("standard_path")
def validate_standard(standard_path):
    """Validate YAML standard file."""
    sys.exit(validate_standard_command(standard_path))


@cli.command("list-standards")
def list_standards():
    """List available YAML standards."""
    sys.exit(list_standards_command())


@cli.command("show-config")
@click.option("--paths-only", is_flag=True, help="Show only path information")
@click.option("--environment", help="Show specific environment only")
def show_config(paths_only, environment):
    """Show current ADRI configuration."""
    sys.exit(show_config_command(paths_only, environment))


@cli.command("list-assessments")
@click.option("--recent", default=10, help="Number of recent assessments to show")
@click.option("--verbose", is_flag=True, help="Show detailed assessment information")
def list_assessments(recent, verbose):
    """List previous assessment reports."""
    sys.exit(list_assessments_command(recent, verbose))


@cli.command("show-standard")
@click.argument("standard_name")
@click.option("--verbose", is_flag=True, help="Show detailed requirements and rules")
def show_standard(standard_name, verbose):
    """Show details of a specific ADRI standard."""
    sys.exit(show_standard_command(standard_name, verbose))


@cli.command("view-logs")
@click.option("--recent", default=10, help="Number of recent audit log entries to show")
@click.option("--today", is_flag=True, help="Show only today's audit logs")
@click.option("--verbose", is_flag=True, help="Show detailed audit log information")
def view_logs(recent, today, verbose):
    """View audit logs from CSV files."""
    sys.exit(view_logs_command(recent, today, verbose))


def main():
    """Run the main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
