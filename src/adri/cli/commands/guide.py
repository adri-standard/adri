"""Guide command implementation for ADRI CLI.

This module contains the GuideCommand class that provides an interactive
walkthrough for first-time users, replacing the scattered --guide flags
with a cohesive learning experience.
"""

import sys
import time
from pathlib import Path
from typing import Any

import click

from ...core.protocols import Command


def _progressive_echo(text: str, delay: float = 0.0) -> None:
    """Print text with optional delay for progressive output.

    Args:
        text: Text to print
        delay: Delay in seconds after printing (only in interactive terminals)
    """
    click.echo(text)
    if delay > 0 and sys.stdout.isatty():
        time.sleep(delay)


class GuideCommand(Command):
    """Interactive guide command for first-time ADRI users.

    Provides a complete walkthrough of:
    1. Welcome and ADRI overview
    2. Project setup
    3. Decorator usage example
    4. Generating standards
    5. Assessing data
    6. Viewing results and logs
    7. Next steps and integration
    """

    def __init__(self):
        """Initialize guide command."""
        self.tutorial_path = Path("ADRI/tutorials/invoice_processing")
        self.steps_completed = []

    def get_description(self) -> str:
        """Get command description."""
        return "Interactive guide for first-time users"

    def get_name(self) -> str:
        """Get command name."""
        return "guide"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the interactive guide walkthrough.

        Args:
            args: Command arguments (none required)

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Run the complete interactive guide
            return self._run_interactive_guide()
        except KeyboardInterrupt:
            click.echo("\n\n⚠️  Guide interrupted by user")
            click.echo("💡 You can restart the guide anytime with: adri guide")
            return 130
        except Exception as e:
            click.echo(f"\n❌ Guide error: {e}")
            click.echo("💡 You can restart the guide with: adri guide")
            return 1

    def _run_interactive_guide(self) -> int:
        """Run the complete interactive guide flow."""
        # Step 1: Welcome and explain ADRI
        if not self._welcome_step():
            return 1

        # Step 2: Setup project structure
        if not self._setup_step():
            return 1

        # Step 3: Show decorator usage example
        if not self._decorator_example_step():
            return 1

        # Step 4: Generate standard from tutorial data
        if not self._generate_standard_step():
            return 1

        # Step 5: Assess test data with issues
        if not self._assess_data_step():
            return 1

        # Step 6: View results and logs
        if not self._view_results_step():
            return 1

        # Step 7: Explain next steps
        if not self._next_steps_conclusion():
            return 1

        return 0

    def _welcome_step(self) -> bool:
        """Show welcome message and ADRI overview."""
        _progressive_echo("🚀 Welcome to ADRI - AI Data Reliability Inspector", 0.5)
        _progressive_echo("=" * 58, 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("This interactive guide will walk you through:", 0.0)
        _progressive_echo("  1️⃣  Setting up your project", 0.0)
        _progressive_echo("  2️⃣  Understanding decorator usage", 0.0)
        _progressive_echo("  3️⃣  Creating quality standards", 0.0)
        _progressive_echo("  4️⃣  Assessing data quality", 0.0)
        _progressive_echo("  5️⃣  Reviewing audit logs", 0.0)
        _progressive_echo("  6️⃣  Integrating with AI agents", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("⏱️  This will take about 3 minutes", 0.0)
        _progressive_echo("", 0.5)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("What is ADRI?", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("ADRI prevents AI agents from breaking on bad data by:", 0.0)
        _progressive_echo("  • Validating data quality before agent execution", 0.0)
        _progressive_echo("  • Tracking data lineage and audit trails", 0.0)
        _progressive_echo("  • Blocking or warning on quality issues", 0.0)
        _progressive_echo("  • Integrating seamlessly with agent frameworks", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("Two key metrics:", 0.0)
        _progressive_echo(
            "  📊 System Health → Dataset-level quality score (0-100)", 0.0
        )
        _progressive_echo("  ✅ Batch Readiness → Row-level pass/fail gate", 0.5)
        _progressive_echo("", 0.0)

        return True

    def _setup_step(self) -> bool:
        """Initialize ADRI project structure."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Step 1: Project Setup", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)

        # Check if already set up
        config_path = Path("ADRI/config.yaml")
        tutorial_data = self.tutorial_path / "invoice_data.csv"

        if config_path.exists() and tutorial_data.exists():
            _progressive_echo("✅ ADRI is already set up in this project", 0.0)
            _progressive_echo(f"   Config: {config_path}", 0.0)
            _progressive_echo(f"   Tutorial data: {tutorial_data}", 0.5)
            _progressive_echo("", 0.0)
        else:
            _progressive_echo("Creating project structure...", 0.0)
            _progressive_echo("", 0.3)

            # Run setup command
            from .setup import SetupCommand

            setup_cmd = SetupCommand()
            result = setup_cmd.execute(
                {"force": True, "project_name": None, "guide": True}
            )

            if result != 0:
                click.echo("\n❌ Setup failed - please try again")
                return False

            _progressive_echo("", 0.5)

        return True

    def _decorator_example_step(self) -> bool:
        """Show and explain decorator usage."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Step 2: Understanding the Decorator", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "ADRI can protect your AI functions with a simple decorator:", 0.0
        )
        _progressive_echo("", 0.3)
        _progressive_echo("```python", 0.0)
        _progressive_echo("from adri import adri_assess", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("@adri_assess(", 0.0)
        _progressive_echo('    standard="invoice_standard.yaml",', 0.0)
        _progressive_echo('    guard_mode="block"  # Stop on bad data', 0.0)
        _progressive_echo(")", 0.0)
        _progressive_echo("def process_invoices(data):", 0.0)
        _progressive_echo('    """Your AI agent code here."""', 0.0)
        _progressive_echo("    return results", 0.0)
        _progressive_echo("```", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("What this does:", 0.0)
        _progressive_echo("  ✅ Validates data quality before function runs", 0.0)
        _progressive_echo("  🛡️  Blocks execution if data fails quality checks", 0.0)
        _progressive_echo("  📝 Logs all assessments for audit trails", 0.0)
        _progressive_echo("  🎯 Returns both results and quality metadata", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("Guard modes:", 0.0)
        _progressive_echo('  • "warn" → Log issues but continue execution', 0.0)
        _progressive_echo('  • "block" → Stop execution on quality failures', 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "💡 First, let's create a standard using the CLI, then you can", 0.0
        )
        _progressive_echo("   use it with the decorator in your code.", 0.5)
        _progressive_echo("", 0.0)

        return True

    def _generate_standard_step(self) -> bool:
        """Guide through generating standard from tutorial data."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Step 3: Generate Quality Standard", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "Now we'll create a quality standard from clean training data.", 0.0
        )
        _progressive_echo(
            "This defines what 'good data' looks like for your use case.", 0.5
        )
        _progressive_echo("", 0.0)

        # Check if training data exists
        training_file = self.tutorial_path / "invoice_data.csv"
        if not training_file.exists():
            click.echo(f"❌ Training data not found: {training_file}")
            click.echo("   Please ensure setup completed successfully")
            return False

        _progressive_echo("Generating standard from tutorial data...", 0.0)
        _progressive_echo("", 0.5)

        # Run generate-standard command
        from .generate_contract import GenerateContractCommand

        gen_cmd = GenerateContractCommand()
        result = gen_cmd.execute(
            {
                "data_path": "tutorials/invoice_processing/invoice_data.csv",
                "force": True,
                "output": None,
                "guide": True,
            }
        )

        if result != 0:
            click.echo("\n❌ Standard generation failed - please try again")
            return False

        _progressive_echo("", 0.5)
        return True

    def _assess_data_step(self) -> bool:
        """Guide through assessing test data."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Step 4: Assess Data Quality", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("Now let's test real-world data against our standard.", 0.0)
        _progressive_echo(
            "The test data has intentional issues to show how ADRI works.", 0.5
        )
        _progressive_echo("", 0.0)

        # Check if test data exists
        test_file = self.tutorial_path / "test_invoice_data.csv"
        standard_file = Path("ADRI/dev/contracts/invoice_data_ADRI_standard.yaml")

        if not test_file.exists():
            click.echo(f"❌ Test data not found: {test_file}")
            return False

        if not standard_file.exists():
            click.echo(f"❌ Standard not found: {standard_file}")
            click.echo("   Please ensure the previous step completed successfully")
            return False

        _progressive_echo("Running assessment...", 0.0)
        _progressive_echo("", 0.5)

        # Run assess command
        from .assess import AssessCommand

        assess_cmd = AssessCommand()
        result = assess_cmd.execute(
            {
                "data_path": "ADRI/tutorials/invoice_processing/test_invoice_data.csv",
                "standard_path": "ADRI/dev/contracts/invoice_data_ADRI_standard.yaml",
                "output_path": None,
                "guide": True,
            }
        )

        if result != 0:
            click.echo("\n⚠️  Assessment completed with issues (this is expected)")
            _progressive_echo("", 0.3)

        _progressive_echo("", 0.5)
        return True

    def _view_results_step(self) -> bool:
        """Show logs and assessment results."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Step 5: Review Audit Logs", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "ADRI maintains comprehensive audit logs of all assessments.", 0.0
        )
        _progressive_echo("Let's view the recent activity:", 0.5)
        _progressive_echo("", 0.0)

        # Run view-logs command
        from .view_logs import ViewLogsCommand

        logs_cmd = ViewLogsCommand()
        result = logs_cmd.execute({"recent": 5, "today": False, "verbose": False})

        if result != 0:
            click.echo("\n⚠️  Could not load audit logs (this is okay)")
            _progressive_echo("", 0.3)

        _progressive_echo("", 0.5)
        return True

    def _next_steps_conclusion(self) -> bool:
        """Explain what to do next."""
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("🎉 Guide Complete!", 0.0)
        _progressive_echo("─" * 58, 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("You now know how to:", 0.0)
        _progressive_echo("  ✅ Set up ADRI in your project", 0.0)
        _progressive_echo("  ✅ Generate quality standards", 0.0)
        _progressive_echo("  ✅ Assess data quality", 0.0)
        _progressive_echo("  ✅ Review audit logs", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("Next Steps:", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("1️⃣  Integrate with your AI agent code:", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("   ```python", 0.0)
        _progressive_echo("   from adri import adri_assess", 0.0)
        _progressive_echo("   ", 0.0)
        _progressive_echo("   @adri_assess(", 0.0)
        _progressive_echo('       standard="dev/standards/your_standard.yaml",', 0.0)
        _progressive_echo('       guard_mode="block"', 0.0)
        _progressive_echo("   )", 0.0)
        _progressive_echo("   def your_ai_function(data):", 0.0)
        _progressive_echo("       # Your agent logic here", 0.0)
        _progressive_echo("       return results", 0.0)
        _progressive_echo("   ```", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("2️⃣  Create standards for your own data:", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("   adri generate-contract your_data.csv", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("3️⃣  Explore additional commands:", 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("   adri list-contracts     # View all contracts", 0.0)
        _progressive_echo("   adri list-assessments   # View assessment history", 0.0)
        _progressive_echo("   adri show-config        # View configuration", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("📚 Documentation & Resources:", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo("  • README.md - Quick start guide", 0.0)
        _progressive_echo("  • QUICKSTART.md - Detailed walkthrough", 0.0)
        _progressive_echo("  • docs/CLI_REFERENCE.md - All CLI commands", 0.0)
        _progressive_echo("  • docs/GETTING_STARTED.md - Integration guide", 0.0)
        _progressive_echo("  • docs/GUIDE_WALKTHROUGH.md - This guide in detail", 0.5)
        _progressive_echo("", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("💡 Tips:", 0.0)
        _progressive_echo("─" * 58, 0.0)
        _progressive_echo("", 0.0)
        _progressive_echo(
            "  • Use 'dev' environment for testing and experimentation", 0.0
        )
        _progressive_echo(
            "  • Switch to 'prod' environment for production deployments", 0.0
        )
        _progressive_echo(
            "  • Review audit logs regularly for data quality trends", 0.0
        )
        _progressive_echo(
            "  • Adjust thresholds in standards based on your requirements", 0.5
        )
        _progressive_echo("", 0.0)
        _progressive_echo("🚀 Happy building with ADRI!", 0.0)
        _progressive_echo("", 0.0)

        return True
