"""
Interactive mode for the Agent Data Readiness Index CLI.

This module provides an interactive, guided experience for running
ADRI assessments.
"""

import logging
import os
from typing import Any, Dict, cast

import inquirer  # type: ignore
import pandas as pd
from inquirer import errors  # type: ignore

from .assessor import DataSourceAssessor
from .dimensions import DimensionRegistry

logger = logging.getLogger(__name__)


def validate_file_path(_: Any, current: str) -> str:
    """
    Validate that the file path exists.

    Args:
        _: Unused parameter required by inquirer
        current: The file path to validate

    Returns:
        The validated file path

    Raises:
        ValidationError: If the file does not exist
    """
    if not os.path.exists(current):
        raise errors.ValidationError(
            "", reason=f"File does not exist: {current}"
        )
    return current


def validate_output_path(_: Any, current: str) -> str:
    """
    Validate that the output path is valid.

    Args:
        _: Unused parameter required by inquirer
        current: The output path to validate

    Returns:
        The validated output path

    Raises:
        ValidationError: If the output path is invalid
    """
    try:
        # Check if the directory exists or can be created
        output_dir = os.path.dirname(current)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return current
    except Exception as e:
        raise errors.ValidationError("", reason=f"Invalid output path: {e}")


def run_interactive_mode() -> int:
    """
    Run the interactive assessment mode.

    This function guides the user through the process of assessing a data
    source
    with step-by-step prompts and explanations.

    Returns:
        Exit code (0 for success)
    """
    print("\nWelcome to the ADRI Interactive Assessment!")
    print("This wizard will guide you through assessing your data source.\n")

    # Step 1: Select data source type
    questions = [
        inquirer.List(
            "source_type",
            message="What type of data source would you like to assess?",
            choices=[
                ("File (CSV, JSON, etc.)", "file"),
                ("Database", "database"),
                ("API", "api"),
            ],
        ),
    ]
    answers = cast(Dict[str, Any], inquirer.prompt(questions))
    source_type = answers["source_type"]

    # Step 2: Get source details based on type
    source_path = None
    connection_string = None
    table_name = None

    if source_type == "file":
        questions = [
            inquirer.Text(
                "source_path",
                message="Please enter the path to your data file:",
                validate=validate_file_path,
            ),
        ]
        answers = cast(Dict[str, Any], inquirer.prompt(questions))
        source_path = answers["source_path"]

        # Display file info
        try:
            if source_path.endswith(".csv"):
                df = pd.read_csv(source_path)
                print(
                    f"\nFile detected: CSV with {len(df)} rows and "
                    f"{len(df.columns)} columns."
                )
            elif source_path.endswith(".json"):
                df = pd.read_json(source_path)
                print(
                    f"\nFile detected: JSON with {len(df)} rows and "
                    f"{len(df.columns)} columns."
                )
            else:
                print(f"\nFile detected: {os.path.basename(source_path)}")
        except Exception as e:
            print(f"\nFile detected, but could not read details: {e}")

    elif source_type == "database":
        questions = [
            inquirer.Text(
                "connection_string",
                message="Please enter the database connection string:",
            ),
            inquirer.Text(
                "table_name",
                message="Please enter the table name:",
            ),
        ]
        answers = cast(Dict[str, Any], inquirer.prompt(questions))
        connection_string = answers["connection_string"]
        table_name = answers["table_name"]

    elif source_type == "api":
        questions = [
            inquirer.Text(
                "connection_string",
                message="Please enter the API endpoint URL:",
            ),
        ]
        answers = cast(Dict[str, Any], inquirer.prompt(questions))
        connection_string = answers["connection_string"]

    # Step 3: Select dimensions to assess
    available_dimensions = DimensionRegistry.list_dimensions()
    dimension_descriptions = {
        "validity": "Checks if data conforms to expected formats and rules",
        "completeness": "Evaluates missing values and coverage",
        "freshness": "Assesses data timeliness and currency",
        "consistency": "Checks for internal and referential consistency",
        "plausibility": "Evaluates if data values are reasonable and credible",
    }

    dimension_choices = []
    for dim in available_dimensions:
        desc = dimension_descriptions.get(dim)
        dimension_choices.append((f"{dim} - {desc}", dim))

    questions = [
        inquirer.Checkbox(
            "dimensions",
            message="Which dimensions would you like to assess?",
            choices=dimension_choices,
            default=available_dimensions,  # Select all by default
        ),
    ]
    answers = cast(Dict[str, Any], inquirer.prompt(questions))
    selected_dimensions = answers["dimensions"]

    # Step 4: Ask about customization
    questions = [
        inquirer.Confirm(
            "customize",
            message="Would you like to customize assessment parameters?",
            default=False,
        ),
    ]
    answers = cast(Dict[str, Any], inquirer.prompt(questions))
    customize = answers["customize"]

    # Step 5: Customize parameters if requested
    custom_config: Dict[str, Dict[str, float]] = {}
    if customize:
        for dim in selected_dimensions:
            questions = [
                inquirer.Text(
                    "weight",
                    message=(
                        f"Weight for {dim} dimension "
                        f"(0.5-2.0, default is 1.0):"
                    ),
                    default="1.0",
                    validate=lambda _, x: 0.5 <= float(x) <= 2.0,
                ),
                inquirer.Text(
                    "threshold",
                    message=(
                        f"Threshold for {dim} dimension "
                        f"(0.0-1.0, default varies):"
                    ),
                    default="0.8",
                    validate=lambda _, x: 0.0 <= float(x) <= 1.0,
                ),
            ]
            answers = cast(Dict[str, Any], inquirer.prompt(questions))
            custom_config[dim] = {
                "weight": float(answers["weight"]),
                "threshold": float(answers["threshold"]),
            }

    # Step 6: Output format selection
    questions = [
        inquirer.Checkbox(
            "output_formats",
            message="How would you like to receive the results?",
            choices=[
                ("Terminal summary", "terminal"),
                ("HTML report", "html"),
                ("JSON report", "json"),
            ],
            default=["terminal", "html"],
        ),
        inquirer.Text(
            "output_path",
            message="Where would you like to save the report?",
            default="adri_report",
            validate=validate_output_path,
        ),
    ]
    answers = cast(Dict[str, Any], inquirer.prompt(questions))
    output_formats = answers["output_formats"]
    output_path = answers["output_path"]

    # Step 7: Run the assessment
    print("\nRunning assessment...")

    # Create assessor with selected dimensions and custom config
    assessor = DataSourceAssessor(
        dimensions=selected_dimensions if selected_dimensions else None,
        config=custom_config if custom_config else None,
    )

    # Run assessment based on source type
    if source_type == "file" and source_path:
        report = assessor.assess_file(source_path)
    elif source_type == "database" and connection_string and table_name:
        report = assessor.assess_database(connection_string, table_name)
    elif source_type == "api" and connection_string:
        report = assessor.assess_api(connection_string)
    else:
        print("Error: Missing required parameters for assessment.")
        return 1

    # Step 8: Display results
    print("\nAssessment complete!\n")

    if "terminal" in output_formats:
        report.print_summary()

    # Save reports in selected formats
    if "html" in output_formats:
        html_path = (
            f"{output_path}.html"
            if not output_path.endswith(".html")
            else output_path
        )
        report.save_html(html_path)
        print(f"HTML report saved to: {html_path}")

    if "json" in output_formats:
        json_path = (
            f"{output_path}.json"
            if not output_path.endswith(".json")
            else output_path
        )
        report.save_json(json_path)
        print(f"JSON report saved to: {json_path}")

    # Step 9: Offer additional options
    while True:
        questions = [
            inquirer.List(
                "next_action",
                message="Would you like to:",
                choices=[
                    (
                        "View detailed results for a specific dimension",
                        "view_dimension",
                    ),
                    (
                        "Generate improvement recommendations",
                        "recommendations",
                    ),
                    ("Exit", "exit"),
                ],
            ),
        ]
        answers = cast(Dict[str, Any], inquirer.prompt(questions))
        next_action = answers["next_action"]

        if next_action == "exit":
            break
        elif next_action == "view_dimension":
            # Ask which dimension to view
            questions = [
                inquirer.List(
                    "dimension",
                    message="View detailed results for which dimension?",
                    choices=[
                        (dim, dim) for dim in report.dimension_results.keys()
                    ],
                ),
            ]
            answers = cast(Dict[str, Any], inquirer.prompt(questions))
            selected_dim = answers["dimension"]

            # Display detailed results for the selected dimension
            dim_results = report.dimension_results[selected_dim]
            print(f"\n=== {selected_dim.capitalize()} Dimension Details ===")
            print(f"Score: {dim_results['score']}/20")
            print("\nFindings:")
            for i, finding in enumerate(dim_results["findings"], 1):
                print(f"{i}. {finding}")
            print("\nRecommendations:")
            for i, rec in enumerate(dim_results["recommendations"], 1):
                print(f"{i}. {rec}")
            print()

        elif next_action == "recommendations":
            # Display all recommendations
            print("\n=== Improvement Recommendations ===")
            all_recs = []
            for dim, results in report.dimension_results.items():
                for rec in results["recommendations"]:
                    all_recs.append(f"[{dim.capitalize()}] {rec}")

            for i, rec in enumerate(all_recs, 1):
                print(f"{i}. {rec}")
            print()

    print("Thank you for using ADRI Interactive Assessment!")
    return 0
