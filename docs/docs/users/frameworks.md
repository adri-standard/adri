---
sidebar_position: 4
---

# Framework Playbooks

**Fix real data-quality failures documented in popular AI agent frameworks.**
Each playbook gives you the exact ADRI commands and decorator code to reproduce the win with sample data. Swap in your own datasets once you see it working.

> All paths assume you ran `adri setup --guide`, which creates sample invoice data and ADRI project folders.

Replace `data/...` paths with your own datasets when you move beyond the tutorial sample.

See [Core Concepts](core-concepts.md) for standard naming, protection modes, and the five dimensions.

## LangChain – Chain Execution Failures

**Documented issue**: Type mismatches or missing fields break chains (e.g. GitHub issues #21030, #21152).

1. Generate a standard from the clean tutorial dataset:
   ```bash
   adri generate-standard examples/data/invoice_data.csv \
     --output examples/standards/invoice_data_ADRI_standard.yaml
   ```
2. Assess a messy dataset before you call the chain:
   ```bash
   adri assess examples/data/test_invoice_data.csv \
     --standard examples/standards/invoice_data_ADRI_standard.yaml
   ```
3. Guard the function that feeds the chain:
   ```python
   from adri import adri_protected

   @adri_protected(standard="invoice_data_standard", data_param="invoice_rows")
   def build_chain_inputs(invoice_rows):
       return prompt | model | parser
   ```
4. Expected console output when bad rows appear:
   ```
   ⚠️  ADRI Data Quality Warning:
   📊 Score: 62.4 (below threshold)
   ```
5. Link to next step: need centralized audit for LangChain runs? See [Adoption Journey](adoption-journey.md#stage-2).

## CrewAI – Agent Coordination Breakdowns

**Documented issue**: Inconsistent task payloads cause crew conflicts (GitHub issues #541, #612).

1. Generate or update a standard specific to CrewAI task data:
   ```bash
   adri generate-standard data/crew_tasks_good.json \
     --output ADRI/dev/standards/crew_task_standard.yaml
   ```
2. Validate every task bundle before kickoff:
   ```bash
   adri assess data/crew_tasks_batch.json \
     --standard ADRI/dev/standards/crew_task_standard.yaml
   ```
3. Decorate the function that prepares inputs:
   ```python
   @adri_protected(standard="crew_task_standard", data_param="task_payload", on_failure="continue")
   def kickoff_crew(task_payload):
       return crew.kickoff(inputs=task_payload)
   ```
4. When invalid payloads arrive ADRI logs the issue, lets the crew continue (because `on_failure="continue"`), and writes an audit file to `ADRI/dev/assessments` so you can spot the discrepancy.

## LlamaIndex – Index Corruption

**Documented issue**: Corrupted metadata or empty documents break retrieval (GitHub issues #10915, #11442).

1. Build a standard from known-good documents:
   ```bash
   adri generate-standard data/llamaindex_docs_clean.json \
     --output ADRI/dev/standards/llamaindex_document_standard.yaml
   ```
2. Block malformed docs before ingestion:
   ```bash
   adri assess data/llamaindex_docs_incoming.json \
     --standard ADRI/dev/standards/llamaindex_document_standard.yaml
   ```
3. Decorate the ingestion hook:
   ```python
   @adri_protected(standard="llamaindex_document_standard", data_param="documents")
   def ingest_documents(documents):
       index = vector_store.add_documents(documents)
       return index
   ```
4. Add dimension requirements if freshness is a concern:
   ```python
   @adri_protected(
       standard="llamaindex_document_standard",
       data_param="documents",
       dimensions={"freshness": 16, "validity": 18},
   )
   def ingest_documents(documents):
       ...
   ```

## LangGraph – State Corruption

1. Create a state standard (custom YAML or generated from success logs).
2. Validate state snapshots in CI before rolling out a new graph:
   ```bash
   adri assess data/langgraph_state_snapshot.json \
     --standard ADRI/dev/standards/langgraph_state_standard.yaml
   ```
3. Wrap state transitions:
   ```python
   @adri_protected(standard="langgraph_state_standard", data_param="state")
   def execute_node(state):
       return node.run(state)
   ```
4. Use `on_failure="raise"` in production to stop corrupted state from cascading across the graph.

## Semantic Kernel – Plugin Input Validation

1. Generate a standard from successful plugin calls.
2. Validate inbound parameters before execution:
   ```bash
   adri assess data/semantic_kernel_calls_dev.csv \
     --standard ADRI/dev/standards/kernel_plugin_standard.yaml
   ```
3. Guard plugin dispatch:
   ```python
   @adri_protected(standard="kernel_plugin_standard", data_param="call_params", on_failure="warn")
   def invoke_plugin(call_params):
       return kernel.invoke_plugin(call_params)
   ```
4. If you need selective blocking (drop only bad rows), set `on_failure="continue"` and inspect the generated logs.

## Universal Pattern

```python
from adri import adri_protected

@adri_protected(standard="invoice_data_standard", data_param="invoice_rows", min_score=80)
def protected_function(invoice_rows):
    return framework_function(invoice_rows)
```

1. Generate a standard once from a good payload batch.
2. Reuse it everywhere that dataset appears (CLI → decorator).
3. Decide failure handling using `on_failure`.
4. Store the YAML under version control so agents, data engineering, and compliance teams share the same contract.

## Next: Operationalise the Wins

- Use `adri list-standards` and `adri show-standard <name>` to document requirements for each framework integration.
- Want centralised audit and compliance for production agents? Follow the [Adoption Journey](adoption-journey.md) to move from Steps 1–4 (OSS) to Steps 5–10 (Verodat MCP).
