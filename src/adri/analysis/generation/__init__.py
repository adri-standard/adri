"""Standard generation components for the ADRI framework.

This package contains focused classes that replace the monolithic StandardGenerator
with modular, single-responsibility components for different aspects of standard
generation from data analysis.
"""

from .dimension_builder import DimensionRequirementsBuilder
from .explanation_generator import ExplanationGenerator
from .field_inference import FieldInferenceEngine
from .standard_builder import StandardBuilder

__all__ = [
    "FieldInferenceEngine",
    "DimensionRequirementsBuilder",
    "StandardBuilder",
    "ExplanationGenerator",
]
