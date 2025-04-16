"""
Integrations for the Agent Data Readiness Index.

This package provides integrations with popular AI agent frameworks:
- LangChain: Tools and utilities for LangChain agents
- DSPy: Modules for DSPy pipelines
- CrewAI: Agents and tasks for CrewAI

It also includes the adri_guarded decorator for enforcing data quality standards
in agent functions.
"""

from .guard import adri_guarded

__all__ = ["adri_guarded"]
