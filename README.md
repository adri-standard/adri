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

#### Interactive Mode

For a guided, step-by-step assessment experience, use the interactive mode:

```bash
adri interactive
```

This will start an interactive wizard that guides you through:
- Selecting the data source type
- Providing the data source path or connection details
- Choosing which dimensions to assess
- Customizing assessment parameters
- Selecting output formats
- Exploring the results

Interactive mode is especially helpful for new users or when you want to explore the full capabilities of ADRI.

#### Command-Line Mode

To assess a data source directly from the command line (for example, a CSV file), run:

```bash
adri assess --source your_data.csv --output report
```

This command generates two reports:
- A JSON report (e.g., `report.json`)
- An HTML report (e.g., `report.html`)

You can also specify which dimensions to assess:

```bash
adri assess --source your_data.csv --output report --dimensions validity completeness
```

This will only assess the specified dimensions (in this case, validity and completeness).

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

Assuming you have a sample data file named [sample_data.csv](https://github.com/ThinkEvolveSolve/agent-data-readiness-index/blob/main/sample_data.csv), you can run:

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

## Extending ADRI

ADRI is designed to be easily extensible with new dimensions and connectors. You can add:

- **New Dimensions**: Create custom assessors for additional data quality aspects
- **New Connectors**: Add support for different data sources beyond files

For detailed instructions on extending ADRI, see the [EXTENDING.md](EXTENDING.md) guide.

## Integrations with AI Agent Frameworks

ADRI provides integrations with popular AI agent frameworks. For detailed documentation, see the [INTEGRATIONS.md](INTEGRATIONS.md) guide.

### LangChain Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from adri.integrations.langchain import create_adri_tool

# Create LangChain agent with ADRI tool
llm = OpenAI(temperature=0)
adri_tool = create_adri_tool(min_score=70)
agent = initialize_agent(
    [adri_tool], 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Use the agent
agent.run("Assess the quality of customer_data.csv for use in a recommendation system")
```

### DSPy Integration

```python
import dspy
from adri.integrations.dspy import ADRIModule

# Create a DSPy pipeline with ADRI assessment
class DataQualityPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.adri = ADRIModule(min_score=70)
        self.analyzer = dspy.ChainOfThought("data_analysis")
        
    def forward(self, data_path):
        # First assess data quality
        quality_report = self.adri(data_path)
        
        # Only proceed if quality is sufficient
        if quality_report.score >= 70:
            analysis = self.analyzer(
                data=data_path,
                quality_report=quality_report
            )
            return analysis
        else:
            return f"Data quality insufficient: {quality_report.readiness_level}"
```

### CrewAI Integration

```python
from crewai import Crew, Task
from adri.integrations.crewai import create_data_quality_agent

# Create a data quality agent
data_quality_agent = create_data_quality_agent(min_score=70)

# Create a task for the agent
assess_task = Task(
    description="Assess the quality of customer_data.csv",
    expected_output="A detailed assessment of data quality",
    agent=data_quality_agent
)

# Create a crew with the agent and task
crew = Crew(
    agents=[data_quality_agent],
    tasks=[assess_task]
)

# Run the crew
result = crew.kickoff()
```

### ADRI Guard Decorator

```python
from adri.integrations import adri_guarded

@adri_guarded(min_score=70)
def analyze_customer_data(data_source, analysis_type):
    """
    This function will only run if data_source meets
    the minimum quality score of 70
    """
    print(f"Analyzing {data_source} for {analysis_type}")
    # ... analysis code ...
    return results
```

For more detailed examples, see the [examples](examples) directory.

## Architecture

ADRI uses a registry-based architecture that makes extension points explicit:

- **Base Classes**: Define interfaces for dimensions and connectors
- **Registries**: Manage registered components
- **Decorators**: Simplify registration of new components

This architecture allows for easy extension without modifying the core codebase.

## Additional Information

For detailed documentation, configuration details, and contribution guidelines, please refer to our [GitHub Wiki](https://github.com/verodat/agent-data-readiness-index/wiki).

## License
