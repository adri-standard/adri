<![CDATA[
# Agent Data Readiness Index (ADRI)

ADRI is a command line tool and an open standard for evaluating data quality for agentic AI systems. It assesses data sources across five key dimensions: Validity, Completeness, Freshness, Consistency, and Plausibility.

## Installation

You can install ADRI from PyPI:

```bash
pip install adri
```

## Setting Up Your Environment

For the best experience, it's recommended to run ADRI in a virtual environment. Follow these simple steps:

1. **Open a Terminal:** Open Command Prompt (on Windows) or Terminal (on macOS/Linux).
2. **Navigate to Your Workspace:** Use the `cd` command to go to the folder where you wish to work. For example:
   ```bash
   cd C:\path\to\your\folder
   ```
3. **Create a Virtual Environment:** Run the following command to create a virtual environment named `venv`:
   ```bash
   python -m venv venv
   ```
   This will create a folder named `venv` in your current directory.
4. **Activate the Virtual Environment:**
   - On **Windows**, run:
     ```bash
     venv\Scripts\activate
     ```
   - On **macOS/Linux**, run:
     ```bash
     source venv/bin/activate
     ```
   Once activated, your terminal prompt will show the environment name (e.g., `(venv)`).
5. **Install ADRI:** With the virtual environment activated, install ADRI:
   ```bash
   pip install adri
   ```

## Usage

### Running an Assessment

To assess a data source (for example, a CSV file), run:

```bash
adri assess --source your_data.csv --output report
```

This command generates two reports:
- A JSON report (e.g., `report.json`)
- An HTML report (e.g., `report.html`)

If you encounter permission issues or "Access is denied" errors when running the `adri` command directly (commonly on Windows), try:

```bash
python -m adri.cli assess --source your_data.csv --output report
```

### Viewing a Report

To view a generated assessment report in the terminal, use:

```bash
adri report view report.json
```

If there are issues running the command directly, try:

```bash
python -m adri.cli report view report.json
```

### Troubleshooting

- **Executable Issues:** If you receive "Access is denied" when invoking `adri` directly (especially on Windows), using `python -m adri.cli` bypasses this problem.
- **Dependency Problems:** Ensure your environment has the necessary dependencies. ADRI depends on packages such as pandas, matplotlib, jinja2, and pyyaml. If needed, you can manually install them:
  ```bash
  pip install pandas matplotlib jinja2 pyyaml
  ```
- **Environment Setup:** Always make sure your virtual environment is activated before running commands.

## Example

Assuming you have a sample data file named `sample_data.csv`, you can run:

```bash
adri assess --source sample_data.csv --output test_report
```

Then, to view the generated report:

```bash
adri report view test_report.json
```

Or, if facing issues with the standalone command:

```bash
python -m adri.cli assess --source sample_data.csv --output test_report
python -m adri.cli report view test_report.json
```

## Additional Information

For detailed documentation, configuration details, and contribution guidelines, please refer to our [GitHub Wiki](https://github.com/verodat/agent-data-readiness-index/wiki).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
]]>
