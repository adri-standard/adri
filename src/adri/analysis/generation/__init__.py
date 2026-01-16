"""Contract generation components for the ADRI framework.

This package contains focused classes that replace the monolithic ContractGenerator
with modular, single-responsibility components for different aspects of contract
generation from data analysis.
"""

from .contract_builder import ContractBuilder
from .dimension_builder import DimensionRequirementsBuilder
from .explanation_generator import ExplanationGenerator
from .field_inference import FieldInferenceEngine

__all__ = [
    "FieldInferenceEngine",
    "DimensionRequirementsBuilder",
    "ContractBuilder",
    "ExplanationGenerator",
]
