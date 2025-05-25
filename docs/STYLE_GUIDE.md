# ADRI Documentation Style Guide

This guide helps maintain consistency across ADRI documentation while keeping it readable and accessible.

## Core Principles

1. **Clarity First**: Technical accuracy is important, but readability matters more
2. **Practical Examples**: Show real usage, not just theory
3. **Consistent Structure**: Follow patterns that help users find information quickly

## Terminology Guidelines

### First Use Rule
- Use the full term on first mention, then abbreviations are acceptable
- Example: "The Agent Data Readiness Index (ADRI) provides..." then "ADRI" thereafter

### Common Terms
- **ADRI**: Acceptable after first use of "Agent Data Readiness Index"
- **AI/ML**: Common abbreviations that don't need expansion
- **Agent**: Use naturally - no need to always say "AI agent"
- **Data reliability** vs **Data quality**: Prefer "reliability" when discussing ADRI concepts

## Document Structure

### Required Sections by Type

**Dimension Documents** should include:
- Overview
- Why It Matters (practical impact)
- How ADRI Measures (technical details)
- Example (concrete usage)

**Guide Documents** should include:
- Introduction (what and why)
- Prerequisites (what users need)
- Steps (how to do it)
- Example (complete walkthrough)

**Integration Documents** should include:
- Overview (what it integrates with)
- Installation (setup requirements)
- Configuration (options and settings)
- Usage (how to use it)
- Example (working code)

## Code Examples

### Language Specification
Always specify the language after triple backticks:
```python
# Python code
```

```bash
# Shell commands
```

```yaml
# Configuration files
```

### Code Block Types
- **Executable code**: Complete, runnable examples
- **Code snippets**: Partial code showing specific concepts
- **File paths**: Use inline code: `path/to/file.py`
- **Output examples**: Mark as `text` or appropriate format

## Links

### Internal Links
- Use relative paths: `[Link Text](./VISION.md)` (example)
- Link to sections: `[Section Name](#core-principles)` (example)
- Verify links exist before committing

### External Links
- Always use HTTPS where available
- Include descriptive link text (not "click here")
- Check that external resources are accessible

## Formatting

### Lists
- Use `-` for unordered lists (preferred)
- Use `1.` for ordered lists when sequence matters
- Be consistent within a document

### Emphasis
- Use `**bold**` for strong emphasis
- Use `*italic*` for subtle emphasis
- Use `code` for inline code, commands, or file names

## Writing Style

### Tone
- **Professional but approachable**: Technical docs don't have to be dry
- **Direct and clear**: Get to the point without being abrupt
- **Problem-focused**: Explain why something matters to the user

### Technical Terms
- Define technical terms on first use
- Use clear language - avoid jargon where possible
- Include error messages and problems users might encounter

## Vision Alignment

While maintaining readability, ensure documentation:
- Explains how features support data reliability for AI agents
- Includes practical examples of agent use cases
- References the five dimensions where relevant
- Maintains focus on actionable insights

## Quick Checklist

Before submitting documentation:
- [ ] All code blocks have language specified
- [ ] Internal links are verified
- [ ] First use of "ADRI" includes full name
- [ ] Required sections present for document type
- [ ] Examples are practical and complete
- [ ] No orphaned documents (linked from somewhere)

## Examples

### Good Practice
```markdown
# Getting Started with ADRI

The Agent Data Readiness Index (ADRI) helps ensure your AI agents work with reliable data.

## Prerequisites
- Python 3.8+
- Basic understanding of data quality concepts

## Installation
```bash
pip install adri
```
```

### Avoid
```markdown
# ADRI

ADRI is great. Here's code:

```
import stuff
```
```

---

Remember: Documentation is for users, not computers. Make it helpful, clear, and practical.
