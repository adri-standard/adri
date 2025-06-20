# ADRI Implementation Guide

This guide provides best practices for implementing the Agent Data Readiness Index (ADRI) in your AI agent workflows.

## Implementation Patterns

### 1. Pre-execution Quality Gate

The most common pattern is to use ADRI as a quality gate before allowing an AI agent to process data:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import DataSourceAssessor
from adri.connectors import FileConnector

def quality_gate(data_path, minimum_score=70):
    """Verify data meets minimum quality standards before processing"""
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    if result.score < minimum_score:
        raise ValueError(f"Data quality insufficient ({result.score}/100). Minimum required: {minimum_score}")
    
    return True

# In your agent workflow
try:
    if quality_gate("customer_data.csv"):
        # Data passed quality check, proceed with agent
        response = my_ai_agent.process("customer_data.csv")
except ValueError as e:
    # Handle quality failure
    print(f"Cannot process data: {e}")
    # Implement fallback strategy or request data improvement
```

### 2. Dimension-Specific Requirements

For some applications, specific dimensions may be more critical:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of dimension-specific requirements (snippet - not meant to be executed directly)
from adri import DataSourceAssessor
from adri.connectors import FileConnector

def dimension_specific_gate(data_path, requirements):
    """Check that specific dimensions meet minimum thresholds"""
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    failures = []
    for dimension, min_score in requirements.items():
        actual_score = result.dimension_scores.get(dimension, 0)
        if actual_score < min_score:
            failures.append(f"{dimension}: {actual_score}/20 (required: {min_score}/20)")
    
    if failures:
        raise ValueError(f"Data quality requirements not met: {', '.join(failures)}")
    
    return True

# Example: Financial application requiring high validity and consistency
requirements = {
    "validity": 18,       # 18/20 minimum for validity
    "consistency": 16,    # 16/20 minimum for consistency
    "freshness": 15       # 15/20 minimum for freshness
}

# In your actual application:
# try:
#     if dimension_specific_gate("financial_data.csv", requirements):
#         process_financial_data()
# except ValueError as e:
#     request_data_improvements(str(e))
```

### 3. Adaptive Agent Behavior

Use ADRI scores to adapt agent behavior based on data quality:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of adaptive agent behavior (snippet - not meant to be executed directly)
from adri import DataSourceAssessor
from adri.connectors import FileConnector

def adaptive_agent(data_path):
    """Adjust agent behavior based on data quality assessment"""
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    # Determine confidence level based on overall score
    if result.score >= 90:
        confidence = "high"
    elif result.score >= 70:
        confidence = "medium"
    else:
        confidence = "low"
    
    # Check for specific dimension issues
    issues = {}
    for dimension, score in result.dimension_scores.items():
        if score < 15:  # Less than 15/20 is concerning
            issues[dimension] = score
    
    return {
        "overall_quality": result.score,
        "confidence": confidence,
        "issues": issues,
        "report": result.get_summary()
    }

# In your agent workflow (example usage):
# quality_assessment = adaptive_agent("customer_data.csv")
# 
# if quality_assessment["confidence"] == "high":
#     # Proceed with standard processing
#     response = standard_agent_process()
# elif quality_assessment["confidence"] == "medium":
#     # Add warnings to output
#     response = cautious_agent_process(quality_assessment["issues"])
# else:
#     # Use conservative processing with explicit uncertainty
#     response = conservative_agent_process(quality_assessment["report"])
```

### 4. Continuous Monitoring

Implement ADRI in a monitoring system to track data quality over time:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of continuous monitoring (snippet - not meant to be executed directly)
from adri import DataSourceAssessor
from adri.connectors import FileConnector
import datetime
import json

def monitor_data_quality(data_path, history_file="quality_history.json"):
    """Track data quality over time"""
    # Assess current quality
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    # Create entry for history
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "overall_score": result.score,
        "dimension_scores": result.dimension_scores,
        "data_path": data_path
    }
    
    # Load history
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"entries": []}
    
    # Add new entry
    history["entries"].append(entry)
    
    # Save updated history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    
    # Check for significant changes
    if len(history["entries"]) > 1:
        previous = history["entries"][-2]["overall_score"]
        current = entry["overall_score"]
        if abs(current - previous) > 5:  # More than 5-point change
            print(f"Significant quality change detected: {previous} → {current}")
    
    return result

# Schedule regular monitoring
# monitor_data_quality("production_data.csv")
```

## Integration with AI Frameworks

### LangChain Integration

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of LangChain integration (snippet - not meant to be executed)
# from adri import DataSourceAssessor
# from adri.connectors import FileConnector
# from langchain.agents import Tool
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain.prompts import PromptTemplate
# from langchain.llms import OpenAI

# Create ADRI quality check tool
def check_data_quality(data_path):
    # In actual implementation:
    # connector = FileConnector(data_path)
    # assessor = DataSourceAssessor(connector)
    # result = assessor.assess()
    # return f"Data quality score: {result.score}/100\nDimension scores: {result.dimension_scores}"
    pass

# Define the tool
# tools = [
#     Tool(
#         name="DataQualityChecker",
#         func=check_data_quality,
#         description="Checks the quality of a data file. Input should be a path to a CSV file."
#     )
# ]

# Create agent with the tool
# prompt = PromptTemplate.from_template("""
# You are an AI assistant that can check data quality before processing.
# You have access to the following tools: {tools}
# 
# Use the tools to help with the following request:
# {input}
# 
# {format_instructions}
# """)
# 
# llm = OpenAI(temperature=0)
# agent = create_react_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage
# agent_executor.run("Check the quality of customer_data.csv before I use it for analysis")
```

### Hugging Face Integration

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of using the adri_guarded decorator with Hugging Face
# This is a conceptual example - not meant to be executed directly

# In a real implementation:
# from adri.integrations.guard import adri_guarded
# from transformers import pipeline

# Example decorator usage
def hugging_face_example():
    """Example showing how to use the adri_guarded decorator with Hugging Face"""
    
    # Define a guarded pipeline function
    # @adri_guarded(min_score=70, dimensions={"validity": 15})
    # def process_with_transformer(data_source, model_name="distilbert-base-uncased"):
    #     # This function will only run if data quality is sufficient
    #     model = pipeline("text-classification", model=model_name)
    #     # Process data...
    #     return results
    
    # Example call
    # results = process_with_transformer("sentiment_data.csv")
    pass
```

## Best Practices

### Setting Appropriate Thresholds

- **Start Conservative**: Begin with lower thresholds (e.g., 60-70) and gradually increase as data quality improves
- **Dimension-Specific**: Set different thresholds for different dimensions based on your use case
- **Use Templates**: Leverage ADRI templates for standardized requirements in your industry

### Error Handling

Implement graceful degradation when data quality is insufficient:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of error handling (snippet - not meant to be executed)
# try:
#     if quality_gate("data.csv", minimum_score=75):
#         # Full processing
#         result = full_processing_pipeline()
# except ValueError as e:
#     if "quality insufficient" in str(e):
#         # Attempt processing with reduced functionality
#         result = reduced_functionality_pipeline()
#         result["warnings"] = ["Limited accuracy due to data quality issues"]
#     else:
#         # Other error
#         raise
```

### Reporting and Feedback

Provide actionable feedback when data quality issues are detected:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of generating actionable feedback (snippet - not meant to be executed directly)
def generate_quality_report(data_path):
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    report = {
        "overall_score": result.score,
        "dimension_scores": result.dimension_scores,
        "passed": result.score >= 70,
        "improvement_actions": []
    }
    
    # Generate specific improvement actions
    if result.dimension_scores.get("validity", 0) < 15:
        report["improvement_actions"].append(
            "Fix data type issues in columns: " + 
            ", ".join(result.get_issues_by_dimension("validity"))
        )
    
    if result.dimension_scores.get("completeness", 0) < 15:
        report["improvement_actions"].append(
            "Address missing values in critical fields: " + 
            ", ".join(result.get_issues_by_dimension("completeness"))
        )
    
    # Add more dimension-specific actions...
    
    return report
```

### Performance Considerations

- **Caching Results**: Cache assessment results for unchanged data to avoid repeated processing
- **Sampling**: For very large datasets, use sampling to speed up assessment
- **Async Processing**: Implement asynchronous assessment for non-blocking operations

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example of asynchronous processing (snippet - not meant to be executed directly)
import asyncio
from adri import DataSourceAssessor
from adri.connectors import FileConnector

async def async_quality_check(data_path):
    # Run assessment in a thread pool
    loop = asyncio.get_event_loop()
    connector = FileConnector(data_path)
    assessor = DataSourceAssessor(connector)
    
    # Run CPU-intensive assessment in thread pool
    result = await loop.run_in_executor(None, assessor.assess)
    return result

# Example usage in async context
# async def process_data():
#     quality_result = await async_quality_check("large_dataset.csv")
#     if quality_result.score >= 70:
#         # Process data
#         pass
```

## Conclusion

By following these implementation patterns and best practices, you can effectively integrate ADRI into your AI agent workflows to ensure data quality and improve agent performance. Adapt these examples to your specific use case and requirements.

For more detailed information, refer to the [API Reference](reference/api/index.md) and [Understanding Templates](reference/templates/index.md) documentation.
