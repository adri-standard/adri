"""
Metadata generator for ADRI.

This module provides functionality to automatically generate starter metadata files
based on analysis of data sources. It reduces the manual effort required to create
ADRI metadata files by pre-filling them with detected patterns and statistics.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from collections import Counter
import re

from adri.version import __version__

logger = logging.getLogger(__name__)


class MetadataGenerator:
    """Generate ADRI metadata files based on data analysis."""
    
    def __init__(self, file_connector):
        """
        Initialize the metadata generator.
        
        Args:
            file_connector: FileConnector instance with loaded data
        """
        self.connector = file_connector
        self.df = file_connector.df
        self.inferred_types = file_connector.infer_column_types()
        self.base_name = file_connector.file_path.stem
        self.output_dir = file_connector.file_path.parent
        
    def generate_all_metadata(self, output_dir: Optional[Path] = None) -> Path:
        """
        Generate a single metadata file containing all five dimensions.
        
        Args:
            output_dir: Optional output directory for metadata file
            
        Returns:
            Path to the generated metadata file
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            
        # Generate metadata for all dimensions
        combined_metadata = {
            "_generated_by": "adri init",
            "_generated_at": datetime.now().isoformat(),
            "_adri_version": __version__,
            "_data_source": self.base_name,
            "_comment": "Auto-generated ADRI metadata. Please review and adjust all TODO sections."
        }
        
        # Generate each dimension's metadata
        metadata_generators = {
            'validity': self.generate_validity_metadata,
            'completeness': self.generate_completeness_metadata,
            'freshness': self.generate_freshness_metadata,
            'consistency': self.generate_consistency_metadata,
            'plausibility': self.generate_plausibility_metadata
        }
        
        for dimension, generator_func in metadata_generators.items():
            try:
                metadata = generator_func()
                combined_metadata[dimension] = metadata
                logger.info(f"Generated {dimension} metadata")
            except Exception as e:
                logger.error(f"Error generating {dimension} metadata: {e}")
                # Include empty section with error note
                combined_metadata[dimension] = {
                    "_error": f"Failed to generate: {str(e)}",
                    "_comment": f"TODO: Manually create {dimension} metadata"
                }
                
        # Save combined metadata
        file_path = self._save_combined_metadata(combined_metadata)
        logger.info(f"Generated combined metadata file: {file_path}")
        
        return file_path
    
    def generate_validity_metadata(self) -> Dict[str, Any]:
        """Generate validity metadata based on inferred column types."""
        metadata = {
            "_comment": "Auto-generated validity metadata. Please review and adjust.",
            "has_explicit_validity_info": True,
            "type_definitions": {},
            "validation_results": {
                "overall_valid": True,
                "fields": {}
            }
        }
        
        # Analyze each column
        for column, type_info in self.inferred_types.items():
            col_type = type_info["type"]
            values = self.df[column].dropna()
            
            # Base type definition
            type_def = {
                "type": self._map_to_json_type(col_type),
                "description": f"TODO: Add description for {column}",
                "_detected_type": col_type,
                "_confidence": round(type_info["confidence"], 2)
            }
            
            # Add type-specific constraints
            if col_type in ["numeric", "integer"]:
                numeric_values = pd.to_numeric(values, errors='coerce').dropna()
                if len(numeric_values) > 0:
                    type_def["range"] = [
                        float(numeric_values.min()),
                        float(numeric_values.max())
                    ]
                    type_def["_comment"] = "TODO: Verify if this range is correct"
                    
            elif col_type == "categorical":
                unique_values = values.unique()
                if len(unique_values) <= 20:  # Only include if reasonable number
                    # Convert to strings to handle boolean and other types
                    type_def["allowed_values"] = sorted([str(v) for v in unique_values])
                else:
                    type_def["_comment"] = f"Has {len(unique_values)} unique values - too many to list"
                    
            elif col_type == "id":
                # Try to detect ID pattern
                str_values = values.astype(str)
                lengths = str_values.str.len().value_counts()
                if len(lengths) == 1:  # Consistent length
                    type_def["_detected_pattern"] = f"Fixed length: {lengths.index[0]}"
                    
                # Check for common prefixes
                if len(str_values) > 0:
                    first_chars = str_values.str[:3].value_counts()
                    if len(first_chars) <= 5:
                        type_def["_common_prefixes"] = first_chars.index.tolist()
                        
            elif col_type == "date":
                type_def["format"] = "TODO: Specify date format (e.g., YYYY-MM-DD)"
                # Try to detect format
                sample_dates = values.head(5).tolist()
                type_def["_samples"] = [str(d) for d in sample_dates]
                
            metadata["type_definitions"][column] = type_def
            
            # Check for invalid values
            if col_type in ["numeric", "integer"]:
                invalid_count = len(values) - len(pd.to_numeric(values, errors='coerce').dropna())
            elif col_type == "date":
                invalid_count = len(values) - len(pd.to_datetime(values, errors='coerce').dropna())
            else:
                invalid_count = 0
                
            metadata["validation_results"]["fields"][column] = {
                "valid": invalid_count == 0,
                "invalid_count": int(invalid_count)
            }
            
            if invalid_count > 0:
                metadata["validation_results"]["overall_valid"] = False
                
        return metadata
    
    def generate_completeness_metadata(self) -> Dict[str, Any]:
        """Generate completeness metadata based on missing value analysis."""
        total_rows = len(self.df)
        
        metadata = {
            "_comment": "Auto-generated completeness metadata. Please review and adjust required fields.",
            "has_explicit_completeness_info": True,
            "overall_completeness": round(1 - self.df.isna().mean().mean(), 3),
            "fields": {},
            "sections": {
                "_comment": "TODO: Define logical sections grouping related fields"
            }
        }
        
        # Analyze each column
        for column in self.df.columns:
            missing_count = self.df[column].isna().sum()
            completeness = 1 - (missing_count / total_rows)
            
            field_info = {
                "completeness": round(completeness, 3),
                "required": bool(completeness == 1.0),  # Ensure it's a proper boolean
                "missing_count": int(missing_count),
                "missing_percent": round(missing_count / total_rows * 100, 1)
            }
            
            # Detect what values represent "missing"
            if missing_count < total_rows:  # Some non-null values exist
                values = self.df[column].dropna()
                # Check for common missing indicators
                missing_indicators = []
                for indicator in ["", "N/A", "n/a", "NA", "null", "None", "-", "unknown"]:
                    if indicator in values.values:
                        missing_indicators.append(indicator)
                        
                if missing_indicators:
                    field_info["missing_values"] = missing_indicators
                    field_info["_comment"] = "TODO: Verify these values should be treated as missing"
                    
            # Add reason placeholder for fields with missing data
            if missing_count > 0:
                field_info["missing_reason"] = "TODO: Explain why this field might be missing"
                
            metadata["fields"][column] = field_info
            
        return metadata
    
    def generate_freshness_metadata(self) -> Dict[str, Any]:
        """Generate freshness metadata based on timestamp detection."""
        metadata = {
            "_comment": "Auto-generated freshness metadata. Please review and set appropriate values.",
            "has_explicit_freshness_info": True,
            "dataset_timestamp": "TODO: When was this dataset last updated?",
            "update_frequency": "TODO: daily|weekly|monthly|quarterly|yearly|real-time",
            "generation_process": "TODO: How is this data generated/updated?",
            "freshness_sla": {
                "max_age_hours": 24,
                "meets_sla": True,
                "_comment": "TODO: Adjust max_age_hours based on your requirements"
            },
            "fields": {}
        }
        
        # Detect timestamp fields
        timestamp_columns = []
        for column, type_info in self.inferred_types.items():
            is_timestamp = False
            timestamp_info = {
                "timestamp_field": False
            }
            
            # Check if it's a date type or has date-like name
            if type_info["type"] == "date" or any(
                indicator in column.lower() 
                for indicator in ["date", "time", "created", "updated", "modified", "timestamp"]
            ):
                is_timestamp = True
                timestamp_columns.append(column)
                
                timestamp_info = {
                    "timestamp_field": True,
                    "timestamp_format": "TODO: Specify format (e.g., YYYY-MM-DD HH:MM:SS)",
                    "timestamp_timezone": "TODO: Specify timezone (e.g., UTC)",
                    "_detected_automatically": True
                }
                
                # Try to detect format from samples
                try:
                    sample_values = self.df[column].dropna().head(3)
                    if len(sample_values) > 0:
                        timestamp_info["_samples"] = [str(v) for v in sample_values]
                except:
                    pass
                    
            metadata["fields"][column] = timestamp_info
            
        # Add historical updates placeholder
        metadata["historical_updates"] = [
            {
                "timestamp": "TODO: Add historical update timestamps",
                "description": "Example update"
            }
        ]
        
        # Add detected timestamp columns summary
        if timestamp_columns:
            metadata["_detected_timestamp_columns"] = timestamp_columns
            metadata["_suggestion"] = f"Consider using {timestamp_columns[0]} as the primary freshness indicator"
            
        return metadata
    
    def generate_consistency_metadata(self) -> Dict[str, Any]:
        """Generate consistency metadata based on relationship detection."""
        metadata = {
            "_comment": "Auto-generated consistency metadata. Please review and add business rules.",
            "has_explicit_consistency_info": True,
            "rules": [],
            "cross_dataset_consistency": [],
            "overall_consistency_valid": True
        }
        
        # Detect potential relationships
        numeric_columns = [
            col for col, info in self.inferred_types.items() 
            if info["type"] in ["numeric", "integer"]
        ]
        
        # Check for potential sum relationships
        if len(numeric_columns) >= 2:
            # Add example numeric relationship rule
            metadata["rules"].append({
                "id": "CS.1.1",
                "name": "TODO: Name this rule",
                "description": f"TODO: Define relationship between {', '.join(numeric_columns[:2])}",
                "fields": numeric_columns[:2],
                "condition": f"TODO: e.g., {numeric_columns[0]} > {numeric_columns[1]} or other business rule",
                "valid": True,
                "_comment": "This is an example - please update with actual business rules"
            })
            
        # Check for ID relationships
        id_columns = [
            col for col, info in self.inferred_types.items() 
            if info["type"] == "id" or "id" in col.lower()
        ]
        
        if len(id_columns) >= 2:
            metadata["rules"].append({
                "id": "CS.2.1",
                "name": "ID consistency check",
                "description": f"TODO: Define relationship between {id_columns[0]} and {id_columns[1]}",
                "fields": id_columns[:2],
                "condition": "TODO: Define the consistency rule",
                "valid": True
            })
            
        # Add placeholder for cross-dataset rules
        metadata["cross_dataset_consistency"].append({
            "id": "CS.X.1",
            "name": "TODO: Cross-dataset rule name",
            "description": "TODO: Describe consistency check with external dataset",
            "related_dataset": "TODO: Specify related dataset",
            "condition": "TODO: Define the consistency condition",
            "valid": True
        })
        
        # Detect potential categorical relationships
        categorical_columns = [
            col for col, info in self.inferred_types.items() 
            if info["type"] == "categorical"
        ]
        
        if len(categorical_columns) >= 2:
            # Could check if one categorical is subset of another, hierarchies, etc.
            metadata["_detected_categorical_columns"] = categorical_columns
            metadata["_suggestion"] = "Consider adding rules for categorical relationships"
            
        return metadata
    
    def generate_plausibility_metadata(self) -> Dict[str, Any]:
        """Generate plausibility metadata based on statistical analysis."""
        metadata = {
            "_comment": "Auto-generated plausibility metadata. Please review thresholds.",
            "has_explicit_plausibility_info": True,
            "rule_results": [],
            "valid_overall": True,
            "communication_format": "json"
        }
        
        rule_id_counter = 1
        
        # Analyze numeric columns for outliers
        for column, type_info in self.inferred_types.items():
            if type_info["type"] in ["numeric", "integer"]:
                try:
                    numeric_values = pd.to_numeric(self.df[column], errors='coerce').dropna()
                    if len(numeric_values) > 10:  # Need sufficient data
                        mean = numeric_values.mean()
                        std = numeric_values.std()
                        
                        # Z-score based outlier detection
                        z_threshold = 3.0
                        outliers = numeric_values[abs((numeric_values - mean) / std) > z_threshold]
                        
                        rule = {
                            "id": f"P.{rule_id_counter}.0",
                            "rule_name": f"{column} outlier detection",
                            "type": "outlier_detection",
                            "field": column,
                            "valid": len(outliers) == 0,
                            "message": f"Values should be within {z_threshold} standard deviations of mean",
                            "statistics": {
                                "mean": round(float(mean), 2),
                                "std_dev": round(float(std), 2),
                                "outlier_threshold": z_threshold,
                                "outlier_count": len(outliers)
                            }
                        }
                        
                        if len(outliers) > 0:
                            rule["examples"] = outliers.head(3).tolist()
                            metadata["valid_overall"] = False
                            
                        metadata["rule_results"].append(rule)
                        rule_id_counter += 1
                        
                except Exception as e:
                    logger.warning(f"Error analyzing {column} for outliers: {e}")
                    
            # Check for implausible categorical values
            elif type_info["type"] == "categorical":
                value_counts = self.df[column].value_counts()
                total_count = len(self.df[column].dropna())
                
                # Flag rare categories (less than 0.1%)
                rare_threshold = 0.001
                rare_values = value_counts[value_counts / total_count < rare_threshold]
                
                if len(rare_values) > 0:
                    rule = {
                        "id": f"P.{rule_id_counter}.0",
                        "rule_name": f"{column} rare values check",
                        "type": "frequency_check",
                        "field": column,
                        "valid": False,
                        "message": f"Found {len(rare_values)} very rare values (< {rare_threshold*100}%)",
                        "examples": rare_values.index.tolist()[:5],
                        "_comment": "TODO: Verify if these rare values are valid"
                    }
                    metadata["rule_results"].append(rule)
                    rule_id_counter += 1
                    
        # Add domain-specific rule placeholders
        metadata["rule_results"].append({
            "id": f"P.{rule_id_counter}.0",
            "rule_name": "TODO: Add domain-specific rule",
            "type": "domain_specific",
            "field": "TODO: Specify field",
            "condition": "TODO: Define what makes values plausible in your domain",
            "valid": True,
            "message": "TODO: Describe the plausibility check"
        })
        
        return metadata
    
    def _map_to_json_type(self, inferred_type: str) -> str:
        """Map inferred types to JSON schema types."""
        type_mapping = {
            "numeric": "number",
            "integer": "integer",
            "categorical": "string",
            "text": "string",
            "id": "string",
            "date": "string",  # Dates are strings with format
            "unknown": "string"
        }
        return type_mapping.get(inferred_type, "string")
    
    def _save_combined_metadata(self, metadata: Dict[str, Any]) -> Path:
        """Save combined metadata to a single JSON file with pretty formatting."""
        filename = f"{self.base_name}.adri_metadata.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return file_path

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/utils/test_metadata_generator.py
#      * Tests all metadata generation methods
#      * Tests type inference and mapping
#      * Tests edge cases (empty data, nulls)
#      * Tests file I/O operations
# 
# 2. Integration tests:
#    - tests/integration/test_cli_init.py
#      * Tests complete CLI command flow
#      * Tests different file formats
#      * Tests error handling
#      * Tests output directory handling
#
# 3. Example tests:
#    - tests/unit/examples/test_06_metadata_generation.py
#      * Verifies example demonstrates the feature
#      * Checks for proper documentation
#
# Complete test coverage details are documented in:
# docs/test_coverage/metadata_generator_test_coverage.md
# ----------------------------------------------
