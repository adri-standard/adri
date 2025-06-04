# ADRI Documentation Diagrams

This directory contains Mermaid diagram source files used throughout the ADRI documentation to visualize key concepts and processes.

## Diagram Inventory

### Core Concepts
- **99_percent_problem.mmd** - Visualizes the exponential value unlock from 50% to 99% reliability
- **adri_system_overview.mmd** - Shows how ADRI Protocol and Framework work together
- **usb_analogy.mmd** - Illustrates the USB standardization analogy for ADRI
- **five_dimensions_wheel.mmd** - Displays the five data quality dimensions
- **metadata_file_structure.mmd** - Shows companion metadata files and usage pattern

### Process Flows
- **assessment_process_flow.mmd** - Details the ADRI assessment workflow
- **discovery_flow.mmd** - Shows template discovery and matching process
- **validation_flow.mmd** - Illustrates validation and gap analysis workflow
- **quick_start_flowchart.mmd** - Decision tree for new users getting started
- **day_in_life_timeline.mmd** - Gantt chart showing daily data quality pain points
- **guard_mechanism_flow.mmd** - Illustrates @adri_guarded decorator decision flow

### Value & Implementation
- **value_levels_pyramid.mmd** - Shows ROI at different adoption levels
- **testing_pyramid.mmd** - Illustrates the testing strategy layers
- **cicd_pipeline.mmd** - Visualizes the CI/CD workflow
- **template_system.mmd** - Shows template hierarchy and components

## Usage

These diagrams are embedded in various documentation files using Mermaid's markdown syntax:

```markdown
```mermaid
[diagram content here]
```
```

## Rendering

The diagrams are rendered automatically by:
- GitHub's built-in Mermaid support
- MkDocs with the Mermaid extension
- Most modern markdown viewers

## Contributing

When adding new diagrams:
1. Create a `.mmd` file in this directory
2. Use clear, descriptive filenames
3. Include consistent styling with existing diagrams
4. Update this README with the new diagram
5. Embed the diagram in relevant documentation files
