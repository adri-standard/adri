# ADRI Interactive Guide Walkthrough

This document provides a detailed overview of the `adri guide` command - an interactive walkthrough designed for first-time users to learn ADRI quickly and effectively.

## Overview

The `adri guide` command replaces the scattered `--guide` flags across individual commands with a unified, cohesive learning experience. It provides a complete end-to-end walkthrough of ADRI's core functionality in approximately 3 minutes.

## Quick Start

To run the interactive guide:

```bash
adri guide
```

That's it! The guide will walk you through everything step-by-step.

## What the Guide Covers

The interactive guide consists of 7 sequential steps:

### Step 1: Welcome & Overview
- Introduction to ADRI and its purpose
- Explanation of two key metrics: System Health and Batch Readiness
- Overview of what to expect from the walkthrough

### Step 2: Project Setup
- Initializes ADRI directory structure
- Creates tutorial data files for hands-on learning
- Sets up development and production environments

### Step 3: Understanding the Decorator
- Shows how to use the `@adri_assess` decorator
- Explains failure modes (`warn` vs `raise`)
- Demonstrates integration with AI agent functions

### Step 4: Generate Quality Standard
- Creates a quality standard from clean training data
- Explains the standard structure and key controls
- Shows how ADRI learns what "good data" looks like

### Step 5: Assess Data Quality
- Runs assessment against test data with intentional issues
- Demonstrates System Health scores
- Shows Batch Readiness gate in action
- Identifies specific data quality issues

### Step 6: Review Audit Logs
- Displays comprehensive audit trail
- Shows lineage tracking and validation details
- Demonstrates compliance and monitoring capabilities

### Step 7: Next Steps & Integration
- Provides guidance on integrating ADRI with your code
- Shows how to create standards for your own data
- Lists additional commands for advanced usage

## Guide Features

### Progressive Output
The guide uses timed, progressive output in interactive terminals to create a natural learning pace. This helps users absorb information without feeling overwhelmed.

### Error Handling
The guide gracefully handles:
- Missing files or data
- Keyboard interrupts (Ctrl+C)
- Pre-existing configurations
- General exceptions

Users can restart the guide at any time with `adri guide`.

### Hands-On Learning
The guide uses real data from the invoice processing tutorial:
- **Training data**: Clean, valid invoice records
- **Test data**: Invoices with intentional quality issues

This hands-on approach helps users understand how ADRI works in practice.

## Understanding the Outputs

### System Health Score
```
System Health (Score): 88.5/100 ✅ PASSED
```
- Dataset-level quality across all 5 dimensions
- Use for: monitoring, integration confidence, trend tracking
- Based on weighted dimension scores

### Batch Readiness Gate
```
Batch Readiness (Gate): 7/10 rows ✅ READY
```
- Row-level safety assessment
- Use for: pre-flight checks before agent execution
- Shows which specific rows have issues

### Failed Records Analysis
The guide identifies specific issues:
```
• INV-102: missing customer_id (fill missing customer_id values)
• INV-103: negative amount (should be ≥ 0)
• INV-104: invalid date format (use YYYY-MM-DD)
```

## After the Guide

Once you complete the guide, you'll have:

1. **A working ADRI setup** with proper directory structure
2. **Tutorial data** to experiment with
3. **Generated standard** from the invoice example
4. **Assessment results** showing how ADRI catches issues
5. **Audit logs** demonstrating lineage tracking

### Next Actions

1. **Integrate with your code**:
   ```python
   from adri.validator.decorators import adri_protected

   @adri_protected(
       standard="your_standard",
       on_failure="raise"
   )
   def your_ai_function(data):
       # Your agent logic here
       return results
   ```

2. **Create standards for your data**:
   ```bash
   adri generate-standard your_clean_data.csv
   ```

3. **Assess your data**:
   ```bash
   adri assess your_test_data.csv \
       --standard dev/contracts/your_data_ADRI_standard.yaml
   ```

4. **Explore additional commands**:
   ```bash
   adri list-standards       # View all standards
   adri list-assessments     # View assessment history
   adri show-config          # View configuration
   adri view-logs            # View audit logs
   ```

## Command Comparison

### Old Approach (Scattered --guide flags)
```bash
# Step 1
adri setup --guide

# Step 2
adri generate-standard data.csv --guide

# Step 3
adri assess test.csv --standard std.yaml --guide

# Step 4
# No consolidated way to see the complete picture
```

**Problems:**
- Users had to know about each `--guide` flag
- No cohesive narrative
- Easy to miss steps
- Inconsistent experience

### New Approach (Unified guide command)
```bash
adri guide
```

**Benefits:**
- Single command for complete walkthrough
- Cohesive, narrative experience
- Can't miss steps - it's sequential
- Consistent, polished experience
- Can be restarted anytime

## Technical Details

### File Structure Created
```
ADRI/
├── config.yaml
├── tutorials/
│   └── invoice_processing/
│       ├── invoice_data.csv (clean training data)
│       └── test_invoice_data.csv (data with issues)
├── dev/
│   ├── standards/
│   │   └── invoice_data_ADRI_standard.yaml
│   ├── assessments/
│   │   └── test_invoice_data_assessment_*.json
│   ├── training-data/
│   │   └── invoice_data_*.csv (snapshot)
│   └── audit-logs/
│       ├── adri_assessment_logs.jsonl
│       ├── adri_dimension_scores.jsonl
│       └── adri_failed_validations.jsonl
└── prod/
    └── (same structure as dev/)
```

### Integration with Other Commands

The guide command internally uses:
- `SetupCommand` - For project initialization
- `GenerateStandardCommand` - For standard creation
- `AssessCommand` - For data quality assessment
- `ViewLogsCommand` - For audit log display

Each command is called with `guide=True` to enable enhanced output formatting.

## Tips for Using the Guide

### Best Practices

1. **Run in a clean directory** - Easier to see what the guide creates
2. **Use a terminal with color support** - Better visual experience
3. **Take your time** - The guide is self-paced with progressive output
4. **Experiment after** - Try modifying the tutorial data to see different results

### Troubleshooting

**Guide interrupted?**
- Just run `adri guide` again
- The guide will detect existing setup and continue

**Want to start fresh?**
- Delete the `ADRI/` directory
- Run `adri guide` again

**Need help with a specific command?**
- Use `adri <command> --help` for detailed options
- See [CLI_REFERENCE.md](CLI_REFERENCE.md) for all commands

## Feedback

The guide is designed to evolve based on user feedback. If you have suggestions for improvement:

1. What parts were confusing?
2. What would you like to see added?
3. Was the pacing too fast or too slow?

Share feedback through GitHub issues or discussions.

## See Also

- [README.md](../README.md) - Project overview and quick start
- [QUICKSTART.md](../QUICKSTART.md) - Detailed getting started guide
- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete CLI command reference
- [GETTING_STARTED.md](GETTING_STARTED.md) - Integration guide for developers
- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - Technical architecture details

## Version Information

- **Introduced**: ADRI 4.1.0
- **Replaces**: Scattered `--guide` flags on individual commands
- **Status**: Stable

---

**Ready to get started?** Just run `adri guide` and begin your ADRI journey!
