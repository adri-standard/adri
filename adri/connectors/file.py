"""
File connector for the Agent Data Readiness Index.

This module provides the FileConnector class that interfaces with
file-based data sources (CSV, JSON, etc.) for assessment.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import pandas as pd

from .base import BaseConnector
from . import register_connector

logger = logging.getLogger(__name__)


@register_connector(
    name="file",
    description="Connector for file-based data sources (CSV, JSON, Excel, etc.)"
)
class FileConnector(BaseConnector):
    """
    Connector for file-based data sources.
    
    Supports CSV, JSON, Excel, and other tabular file formats.
    """
    
    def __init__(
        self, 
        file_path: Union[str, Path], 
        file_type: Optional[str] = None,
        encoding: str = 'utf-8',
        sample_size: int = 1000
    ):
        """
        Initialize a file connector.
        
        Args:
            file_path: Path to the file
            file_type: Optional file type override (csv, json, etc.)
            encoding: File encoding
            sample_size: Maximum number of records to load for sampling
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.sample_size = sample_size
        
        # Determine file type if not provided
        if file_type:
            self.file_type = file_type.lower()
        else:
            self.file_type = self.file_path.suffix.lower().lstrip('.')
            
        # Load the data
        self._load_data()
        
    def _load_data(self):
        """Load data from the file."""
        logger.info(f"Loading data from {self.file_path}")
        
        try:
            if self.file_type in ('csv', ''):
                self.df = pd.read_csv(self.file_path, nrows=self.sample_size)
            elif self.file_type == 'json':
                self.df = pd.read_json(self.file_path)
                if len(self.df) > self.sample_size:
                    self.df = self.df.head(self.sample_size)
            elif self.file_type in ('xlsx', 'xls'):
                self.df = pd.read_excel(self.file_path, nrows=self.sample_size)
            elif self.file_type == 'parquet':
                self.df = pd.read_parquet(self.file_path)
                if len(self.df) > self.sample_size:
                    self.df = self.df.head(self.sample_size)
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")
                
            logger.info(f"Loaded {len(self.df)} records")
            
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise
            
    def get_name(self) -> str:
        """Get the name of this data source."""
        return self.file_path.name
    
    def get_type(self) -> str:
        """Get the type of this data source."""
        return f"file-{self.file_type}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data source."""
        stat = self.file_path.stat()
        return {
            "file_path": str(self.file_path),
            "file_type": self.file_type,
            "file_size_bytes": stat.st_size,
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "num_records": len(self.df),
            "num_columns": len(self.df.columns),
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema information for this data source."""
        schema = {}
        
        # Get data types
        dtypes = self.df.dtypes.to_dict()
        schema["fields"] = [
            {
                "name": col,
                "type": str(dtype),
                "nullable": self.df[col].isna().any(),
                "unique_values": self.df[col].nunique(),
            }
            for col, dtype in dtypes.items()
        ]
        
        # Check for explicit schema information in file
        if self.file_type == 'json':
            # Look for schema in the first few rows
            schema_info = self._extract_schema_from_json()
            if schema_info:
                schema["explicit_schema"] = schema_info
                
        return schema
    
    def _extract_schema_from_json(self) -> Optional[Dict[str, Any]]:
        """Extract schema information from a JSON file if present."""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
                
            # Check common schema locations
            if isinstance(data, dict):
                for key in ['schema', 'meta', 'metadata', 'fields']:
                    if key in data:
                        return data[key]
                        
            return None
        except Exception:
            return None
    
    def sample_data(self, n: int = 100) -> List[Dict[str, Any]]:
        """Get a sample of data from this data source."""
        return self.df.head(n).to_dict('records')
    
    def get_update_frequency(self) -> Optional[str]:
        """Get information about how frequently this data is updated."""
        # Files don't typically have explicit update frequency metadata
        return None
    
    def get_last_update_time(self) -> Optional[str]:
        """Get the last time this data was updated."""
        return datetime.fromtimestamp(self.file_path.stat().st_mtime).isoformat()
    
    def get_data_size(self) -> Optional[int]:
        """Get the size of the data (number of records)."""
        return len(self.df)
    
    def get_quality_metadata(self) -> Dict[str, Any]:
        """Get any explicit quality metadata provided by the data source."""
        quality_metadata = {}
        
        # Check for companion metadata files
        metadata_file = self.file_path.with_suffix('.meta.json')
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding=self.encoding) as f:
                    quality_metadata["metadata_file"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata file: {e}")
        
        # Check for a data dictionary (CSV)
        dict_file = self.file_path.with_name(f"{self.file_path.stem}_dictionary.csv")
        if dict_file.exists():
            try:
                quality_metadata["data_dictionary"] = pd.read_csv(dict_file).to_dict('records')
            except Exception as e:
                logger.warning(f"Could not load data dictionary: {e}")
        
        # Add basic quality statistics
        quality_metadata["missing_values"] = {
            col: int(self.df[col].isna().sum())
            for col in self.df.columns
            if self.df[col].isna().any()
        }
        
        quality_metadata["missing_values_percent"] = {
            col: float(self.df[col].isna().mean() * 100)
            for col in self.df.columns
            if self.df[col].isna().any()
        }
        
        return quality_metadata
    
    def supports_validation(self) -> bool:
        """Check if this data source supports validation."""
        validation_file = self.file_path.with_suffix('.validation.json')
        return validation_file.exists()
    
    def get_validation_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any validation performed on this data source."""
        validation_file = self.file_path.with_suffix('.validation.json')
        
        if not validation_file.exists():
            return None
            
        try:
            with open(validation_file, 'r', encoding=self.encoding) as f:
                validation_rules = json.load(f)
                
            results = {"rule_results": []}
            
            for rule in validation_rules.get("rules", []):
                rule_name = rule.get("name", "Unnamed rule")
                field = rule.get("field")
                condition = rule.get("condition")
                
                if not field or not condition or field not in self.df.columns:
                    continue
                    
                import re
                
                if "min_value" in condition:
                    valid = (self.df[field] >= condition["min_value"]).all()
                    message = f"Values must be >= {condition['min_value']}"
                elif "max_value" in condition:
                    valid = (self.df[field] <= condition["max_value"]).all()
                    message = f"Values must be <= {condition['max_value']}"
                elif "pattern" in condition:
                    pattern = re.compile(condition["pattern"])
                    valid = self.df[field].astype(str).str.match(pattern).all()
                    message = f"Values must match pattern: {condition['pattern']}"
                elif "allowed_values" in condition:
                    valid = self.df[field].isin(condition["allowed_values"]).all()
                    message = f"Values must be one of: {condition['allowed_values']}"
                else:
                    continue
                    
                results["rule_results"].append({
                    "rule_name": rule_name,
                    "field": field,
                    "valid": valid,
                    "message": message,
                    "failure_count": int((~self.df[field].isin(condition.get("allowed_values", []))).sum())
                    if "allowed_values" in condition else 0
                })
                
            results["valid_overall"] = all(r["valid"] for r in results["rule_results"])
            return results
            
        except Exception as e:
            logger.warning(f"Error processing validation rules: {e}")
            return None
    
    def supports_completeness_check(self) -> bool:
        """Check if this data source supports completeness checking."""
        completeness_file = self.file_path.with_suffix('.completeness.json')
        return completeness_file.exists()
    
    def get_completeness_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any completeness checks on this data source."""
        completeness_file = self.file_path.with_suffix('.completeness.json')
        
        if not completeness_file.exists():
            return {
                "has_explicit_completeness_info": False,
                "missing_values_by_column": {
                    col: int(self.df[col].isna().sum())
                    for col in self.df.columns
                },
                "missing_values_percent_by_column": {
                    col: float(self.df[col].isna().mean() * 100)
                    for col in self.df.columns
                },
                "overall_completeness_percent": float((1 - self.df.isna().mean().mean()) * 100)
            }
            
        try:
            with open(completeness_file, 'r', encoding=self.encoding) as f:
                completeness_info = json.load(f)
                
            completeness_info["has_explicit_completeness_info"] = True
            completeness_info["actual_missing_values_by_column"] = {
                col: int(self.df[col].isna().sum())
                for col in self.df.columns
            }
            completeness_info["actual_overall_completeness_percent"] = float(
                (1 - self.df.isna().mean().mean()) * 100
            )
            
            return completeness_info
            
        except Exception as e:
            logger.warning(f"Error processing completeness info: {e}")
            return None
    
    def supports_consistency_check(self) -> bool:
        """Check if this data source supports consistency checking."""
        consistency_file = self.file_path.with_suffix('.consistency.json')
        return consistency_file.exists()
    
    def get_consistency_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any consistency checks on this data source."""
        return None
    
    def supports_freshness_check(self) -> bool:
        """Check if this data source supports freshness checking."""
        freshness_file = self.file_path.with_suffix('.freshness.json')
        return freshness_file.exists()
    
    def get_freshness_results(self) -> Optional[Dict[str, Any]]:
        stat = self.file_path.stat()
        return {
            "has_explicit_freshness_info": False,
            "file_modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_age_hours": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
        }
    
    def supports_plausibility_check(self) -> bool:
        """Check if this data source supports plausibility checking."""
        plausibility_file = self.file_path.with_suffix('.plausibility.json')
        return plausibility_file.exists()
    
    def get_plausibility_results(self) -> Optional[Dict[str, Any]]:
        return None
    
    def get_agent_accessibility(self) -> Dict[str, Any]:
        accessibility = {
            "format_machine_readable": True,
            "requires_authentication": False,
            "has_api": False,
            "has_documentation": False,
        }
        
        doc_files = [
            self.file_path.with_suffix('.md'),
            self.file_path.with_suffix('.txt'),
            self.file_path.with_suffix('.pdf'),
            self.file_path.with_name(f"{self.file_path.stem}_README.md"),
        ]
        
        for doc_file in doc_files:
            if doc_file.exists():
                accessibility["has_documentation"] = True
                accessibility["documentation_file"] = str(doc_file)
                break
                
        return accessibility
    
    def get_data_lineage(self) -> Optional[Dict[str, Any]]:
        return None
    
    def get_governance_metadata(self) -> Optional[Dict[str, Any]]:
        return None
