"""
File connector for the Agent Data Readiness Index.

This module provides the FileConnector class that interfaces with
file-based data sources (CSV, JSON, etc.) for assessment.
"""

import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import pandas as pd

from .base import BaseConnector
from . import register_connector
from ..utils.inference import (
    is_numeric, is_integer, is_date_like, is_id_like, 
    find_inconsistent_values, detect_outliers, 
    is_mostly_positive, find_invalid_dates,
    id_pattern_confidence, categorical_confidence,
    check_id_consistency
)

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
        
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    quality_metadata["adri_metadata"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load ADRI metadata file: {e}")
        
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
        # Check for ADRI metadata file with validity section
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    return 'validity' in metadata
            except:
                pass
        
        # Legacy check
        validation_file = self.file_path.with_suffix('.validation.json')
        return validation_file.exists()
    
    def get_validation_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any validation performed on this data source."""
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    if 'validity' in metadata:
                        return metadata['validity'].get('validation_results')
            except Exception as e:
                logger.warning(f"Error reading ADRI metadata: {e}")
        
        # Legacy validation file
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
        # Check for ADRI metadata file with completeness section
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    return 'completeness' in metadata
            except:
                pass
                
        # Legacy check
        completeness_file = self.file_path.with_suffix('.completeness.json')
        return completeness_file.exists()
    
    def get_completeness_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any completeness checks on this data source."""
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    if 'completeness' in metadata:
                        completeness_info = metadata['completeness'].copy()
                        completeness_info["has_explicit_completeness_info"] = True
                        
                        # Add actual values
                        completeness_info["actual_missing_values_by_column"] = {
                            col: int(self.df[col].isna().sum())
                            for col in self.df.columns
                        }
                        completeness_info["actual_overall_completeness_percent"] = float(
                            (1 - self.df.isna().mean().mean()) * 100
                        )
                        
                        return completeness_info
            except Exception as e:
                logger.warning(f"Error reading ADRI metadata: {e}")
        
        # Legacy completeness file
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
        # Check for ADRI metadata file with consistency section
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    return 'consistency' in metadata
            except:
                pass
                
        # Legacy check
        consistency_file = self.file_path.with_suffix('.consistency.json')
        return consistency_file.exists()
    
    def get_consistency_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any consistency checks on this data source."""
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    if 'consistency' in metadata:
                        return metadata['consistency']
            except Exception as e:
                logger.warning(f"Error reading ADRI metadata: {e}")
                
        # Legacy consistency file
        consistency_file = self.file_path.with_suffix('.consistency.json')
        if consistency_file.exists():
            try:
                with open(consistency_file, 'r', encoding=self.encoding) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading consistency file: {e}")
                
        return None
    
    def supports_freshness_check(self) -> bool:
        """Check if this data source supports freshness checking."""
        # Check for ADRI metadata file with freshness section
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    return 'freshness' in metadata
            except:
                pass
                
        # Legacy check
        freshness_file = self.file_path.with_suffix('.freshness.json')
        return freshness_file.exists()
    
    def get_freshness_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any freshness checks on this data source."""
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    if 'freshness' in metadata:
                        freshness_info = metadata['freshness'].copy()
                        freshness_info["has_explicit_freshness_info"] = True
                        
                        # Add file stats
                        stat = self.file_path.stat()
                        freshness_info["file_modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        freshness_info["file_age_hours"] = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
                        
                        return freshness_info
            except Exception as e:
                logger.warning(f"Error reading ADRI metadata: {e}")
                
        # Legacy freshness file
        freshness_file = self.file_path.with_suffix('.freshness.json')
        if freshness_file.exists():
            try:
                with open(freshness_file, 'r', encoding=self.encoding) as f:
                    freshness_info = json.load(f)
                    freshness_info["has_explicit_freshness_info"] = True
                    
                    # Add file stats
                    stat = self.file_path.stat()
                    freshness_info["file_modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    freshness_info["file_age_hours"] = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
                    
                    return freshness_info
            except Exception as e:
                logger.warning(f"Error reading freshness file: {e}")
        
        # Default response
        stat = self.file_path.stat()
        return {
            "has_explicit_freshness_info": False,
            "file_modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_age_hours": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
        }
    
    def supports_plausibility_check(self) -> bool:
        """Check if this data source supports plausibility checking."""
        # Check for ADRI metadata file with plausibility section
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    return 'plausibility' in metadata
            except:
                pass
                
        # Legacy check
        plausibility_file = self.file_path.with_suffix('.plausibility.json')
        return plausibility_file.exists()
    
    def get_plausibility_results(self) -> Optional[Dict[str, Any]]:
        """Get results of any plausibility checks on this data source."""
        # Check for ADRI metadata file first
        adri_metadata_file = self.file_path.parent / f"{self.file_path.stem}.adri_metadata.json"
        if adri_metadata_file.exists():
            try:
                with open(adri_metadata_file, 'r', encoding=self.encoding) as f:
                    metadata = json.load(f)
                    if 'plausibility' in metadata:
                        plausibility_info = metadata['plausibility'].copy()
                        plausibility_info["has_explicit_plausibility_info"] = True
                        return plausibility_info
            except Exception as e:
                logger.warning(f"Error reading ADRI metadata: {e}")
        
        # Legacy plausibility file
        plausibility_file = self.file_path.with_suffix('.plausibility.json')
        if not plausibility_file.exists():
            # If no explicit plausibility file, generate basic plausibility analysis
            inferred_types = self.infer_column_types()
            numeric_columns = [col for col, info in inferred_types.items() 
                              if info["type"] in ["numeric", "integer"]]
            
            # Basic plausibility checks
            outliers_by_column = {}
            for col in numeric_columns:
                try:
                    numeric_values = pd.to_numeric(self.df[col], errors='coerce')
                    outlier_info = detect_outliers(numeric_values)
                    if outlier_info.get("outliers_found", False):
                        outliers_by_column[col] = outlier_info
                except Exception as e:
                    logger.warning(f"Error detecting outliers in {col}: {e}")
            
            return {
                "has_explicit_plausibility_info": False,
                "rule_results": [
                    {
                        "type": "outlier_detection",
                        "field": col,
                        "valid": not info.get("outliers_found", False),
                        "outlier_count": info.get("outlier_count", 0),
                        "outlier_threshold": info.get("threshold", None),
                        "outlier_examples": info.get("outlier_examples", [])[:3]
                    }
                    for col, info in outliers_by_column.items()
                ],
                "valid_overall": not any(info.get("outliers_found", False) for info in outliers_by_column.values()),
                "explicitly_communicated": False
            }
            
        try:
            with open(plausibility_file, 'r', encoding=self.encoding) as f:
                plausibility_info = json.load(f)
                
            plausibility_info["has_explicit_plausibility_info"] = True
            return plausibility_info
            
        except Exception as e:
            logger.warning(f"Error processing plausibility info: {e}")
            return None
        
    def infer_column_types(self):
        """
        Automatically infer the implied data type for each column based on data patterns.
        
        Returns:
            Dictionary mapping column names to their inferred types and confidence levels
        """
        column_types = {}
        
        for column in self.df.columns:
            # Get non-null values for analysis
            values = self.df[column].dropna()
            if len(values) == 0:
                column_types[column] = {"type": "unknown", "confidence": 0.0}
                continue
                
            # Try different type checks
            
            # Check for date patterns
            date_count = sum(is_date_like(val) for val in values)
            date_confidence = date_count / len(values) if len(values) > 0 else 0
            
            # Check for numeric patterns
            numeric_count = sum(is_numeric(val) for val in values)
            numeric_confidence = numeric_count / len(values) if len(values) > 0 else 0
            
            # Check for integer patterns
            integer_count = sum(is_integer(val) for val in values)
            integer_confidence = integer_count / len(values) if len(values) > 0 else 0
            
            # Check for ID patterns (alphanumeric with consistent format)
            id_conf = id_pattern_confidence(values)
            
            # Determine most likely type
            confidences = {
                "date": date_confidence,
                "numeric": numeric_confidence,
                "integer": integer_confidence,
                "id": id_conf,
                "categorical": categorical_confidence(values),
                "text": 0.5  # Default confidence
            }
            
            most_likely_type = max(confidences, key=confidences.get)
            confidence = confidences[most_likely_type]
            
            # Special case handling: prefer numeric over integer if close
            if most_likely_type == "integer" and confidences["numeric"] > 0.9:
                most_likely_type = "numeric"
                confidence = confidences["numeric"]
                
            # Special case: if column name contains 'date' and date confidence is reasonable
            if "date" in column.lower() and date_confidence > 0.5:
                most_likely_type = "date"
                confidence = max(confidence, date_confidence)
            
            # Special case: if column name contains 'id' and id confidence is reasonable
            if "id" in column.lower() and id_conf > 0.5:
                most_likely_type = "id"
                confidence = max(confidence, id_conf)
                
            column_types[column] = {
                "type": most_likely_type,
                "confidence": confidence,
                "consistent": confidence > 0.9  # 90% consistency threshold
            }
            
        return column_types
        
    def analyze_validity(self):
        """
        Analyze validity issues in the dataset based on inferred types.
        
        Returns:
            Dictionary containing validity analysis results
        """
        inferred_types = self.infer_column_types()
        validity_issues = {
            "type_inconsistencies": {},
            "format_inconsistencies": {},
            "range_violations": {},
            "statistical_outliers": {},
            "valid_overall": True
        }
        
        for column, type_info in inferred_types.items():
            column_type = type_info["type"]
            
            # Skip columns with unknown type
            if column_type == "unknown":
                continue
            
            # ID columns: special handling using specialized ID consistency checker
            if column_type == "id":
                # Check if values follow a consistent pattern
                consistency_result = check_id_consistency(self.df[column].tolist())
                
                if not consistency_result["consistent"] and consistency_result["inconsistent_values"]:
                    validity_issues["type_inconsistencies"][column] = {
                        "expected_type": column_type,
                        "inconsistent_count": len(consistency_result["inconsistent_values"]),
                        "inconsistent_examples": consistency_result["inconsistent_values"][:5],
                        "common_pattern": consistency_result.get("common_pattern", "unknown")
                    }
                    validity_issues["valid_overall"] = False
                    
            # Other column types: general type consistency check
            elif not type_info["consistent"]:
                # Find values that don't match the predominant pattern
                inconsistent_values = find_inconsistent_values(self.df[column], column_type)
                if inconsistent_values:
                    validity_issues["type_inconsistencies"][column] = {
                        "expected_type": column_type,
                        "inconsistent_count": len(inconsistent_values),
                        "inconsistent_examples": inconsistent_values[:5]  # Just show a few examples
                    }
                    validity_issues["valid_overall"] = False
            
            # Column-specific checks based on inferred type
            if column_type == "numeric" or column_type == "integer":
                # Check for negative values where most are positive
                try:
                    numeric_values = pd.to_numeric(self.df[column], errors='coerce')
                    if is_mostly_positive(numeric_values):
                        negative_values = numeric_values[numeric_values < 0]
                        negative_count = len(negative_values)
                        if negative_count > 0:
                            validity_issues["range_violations"][column] = {
                                "type": "negative_values",
                                "count": int(negative_count),
                                "examples": negative_values.head(3).tolist()
                            }
                            validity_issues["valid_overall"] = False
                            
                    # Check for outliers
                    outlier_info = detect_outliers(numeric_values)
                    if outlier_info.get("outliers_found", False):
                        validity_issues["statistical_outliers"][column] = outlier_info
                except:
                    pass
                    
            elif column_type == "date":
                # Check for invalid dates
                invalid_dates = find_invalid_dates(self.df[column])
                if invalid_dates:
                    validity_issues["format_inconsistencies"][column] = {
                        "type": "invalid_dates",
                        "count": len(invalid_dates),
                        "examples": invalid_dates[:3]
                    }
                    validity_issues["valid_overall"] = False
                    
                # Try to parse dates and check for future dates when unreasonable
                try:
                    dates = pd.to_datetime(self.df[column], errors='coerce')
                    valid_dates = dates.dropna()
                    
                    if len(valid_dates) > 0:
                        # Check for future dates if most are past/present
                        now = pd.Timestamp.now()
                        future_dates = valid_dates[valid_dates > now]
                        
                        if len(future_dates) > 0 and len(future_dates) < 0.1 * len(valid_dates):
                            validity_issues["range_violations"][f"{column}_future"] = {
                                "type": "future_dates",
                                "count": len(future_dates),
                                "examples": future_dates.head(3).dt.strftime("%Y-%m-%d").tolist()
                            }
                except:
                    pass
            
            # ID columns check for pattern consistency
            elif column_type == "id":
                # Check if values follow consistent patterns
                values = self.df[column].dropna().astype(str)
                
                # Check if some values have different length
                length_counts = values.str.len().value_counts()
                if len(length_counts) > 1:
                    # If there's variation in ID length, flag it
                    main_length = length_counts.idxmax()
                    inconsistent_length = values[values.str.len() != main_length]
                    
                    if len(inconsistent_length) < len(values) * 0.2:  # Less than 20% are irregular
                        validity_issues["format_inconsistencies"][f"{column}_length"] = {
                            "type": "inconsistent_length",
                            "main_length": int(main_length),
                            "count": len(inconsistent_length),
                            "examples": inconsistent_length.head(3).tolist()
                        }
                        validity_issues["valid_overall"] = False
        
        return validity_issues
    
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

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/connectors/test_file.py (direct FileConnector tests)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (file processing in CLI pipeline)
#
# 3. Usage in dimension tests:
#    - tests/unit/dimensions/test_validity_detection.py
#    - tests/unit/dimensions/test_completeness.py
#    - tests/unit/dimensions/test_freshness_basic.py
#    - tests/unit/dimensions/test_consistency_basic.py
#    - tests/unit/dimensions/test_plausibility_basic.py
#
# 4. Test datasets:
#    - test_datasets/ideal_dataset.csv
#    - test_datasets/invalid_dataset.csv
#    - test_datasets/stale_dataset.csv
#    - test_datasets/incomplete_dataset.csv
#    - test_datasets/inconsistent_dataset.csv
#    - test_datasets/implausible_dataset.csv
#    - test_datasets/mixed_issues_dataset.csv
#
# Complete test coverage details are documented in:
# docs/test_coverage/CONNECTORS_test_coverage.md
# ----------------------------------------------
