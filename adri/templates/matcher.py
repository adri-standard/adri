"""
Template matcher for intelligent data type discovery.

This module provides the core functionality for matching data sources
against templates based on column patterns, data patterns, and statistical profiles.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ColumnMatchResult:
    """Result of column matching operation."""
    confidence: float
    matched_columns: Dict[str, str]  # template_col -> data_col mapping
    missing_columns: List[str]
    match_details: Dict[str, Any] = None


@dataclass
class TemplateMatchResult:
    """Result of template matching operation."""
    template_id: str
    confidence: float
    column_match: ColumnMatchResult
    pattern_match_score: float = 0.0
    statistical_match_score: float = 0.0
    match_details: Dict[str, Any] = None
    match_type: str = "discovered"  # "discovered", "specified", or "default"
    match_reason: str = None


class TemplateMatcher:
    """
    Matches data sources against templates using multiple criteria.
    
    The matcher uses a multi-factor approach:
    1. Column name matching (exact, fuzzy, synonyms)
    2. Data pattern recognition
    3. Statistical profiling
    4. Value domain analysis
    """
    
    def __init__(self, fuzzy_threshold: float = 0.7):
        """
        Initialize the template matcher.
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
    
    def match_columns(self, data_columns: List[str], 
                     template_spec: Dict) -> ColumnMatchResult:
        """
        Match data columns against template column specification.
        
        Args:
            data_columns: List of column names in the data
            template_spec: Template column specification with:
                - required_columns: List of required column names
                - optional_columns: List of optional column names
                - column_synonyms: Dict mapping template columns to synonyms
        
        Returns:
            ColumnMatchResult with confidence score and mapping
        """
        # Normalize column names for comparison
        data_cols_lower = [col.lower() for col in data_columns]
        
        required_cols = template_spec.get('required_columns', [])
        optional_cols = template_spec.get('optional_columns', [])
        synonyms = template_spec.get('column_synonyms', {})
        
        matched_columns = {}
        missing_columns = []
        match_types = {}  # Track how each column was matched
        
        # Try to match each required column
        for req_col in required_cols:
            req_col_lower = req_col.lower()
            
            # 1. Try exact match (case-insensitive)
            if req_col_lower in data_cols_lower:
                idx = data_cols_lower.index(req_col_lower)
                matched_columns[req_col] = data_columns[idx]
                match_types[req_col] = 'exact'
                continue
            
            # 2. Try synonym match
            if req_col in synonyms:
                matched = False
                for synonym in synonyms[req_col]:
                    synonym_lower = synonym.lower()
                    if synonym_lower in data_cols_lower:
                        idx = data_cols_lower.index(synonym_lower)
                        matched_columns[req_col] = data_columns[idx]
                        match_types[req_col] = 'synonym'
                        matched = True
                        break
                if matched:
                    continue
            
            # 3. Try fuzzy match
            best_match, best_score = self._find_best_fuzzy_match(
                req_col_lower, data_cols_lower
            )
            if best_score >= self.fuzzy_threshold:
                idx = data_cols_lower.index(best_match)
                matched_columns[req_col] = data_columns[idx]
                match_types[req_col] = 'fuzzy'
                continue
            
            # No match found
            missing_columns.append(req_col)
        
        # Try to match optional columns (don't affect missing list)
        for opt_col in optional_cols:
            opt_col_lower = opt_col.lower()
            
            # Try exact match
            if opt_col_lower in data_cols_lower:
                idx = data_cols_lower.index(opt_col_lower)
                matched_columns[opt_col] = data_columns[idx]
                match_types[opt_col] = 'exact'
                continue
            
            # Try synonym match
            if opt_col in synonyms:
                for synonym in synonyms[opt_col]:
                    synonym_lower = synonym.lower()
                    if synonym_lower in data_cols_lower:
                        idx = data_cols_lower.index(synonym_lower)
                        matched_columns[opt_col] = data_columns[idx]
                        match_types[opt_col] = 'synonym'
                        break
        
        # Calculate confidence score
        confidence = self._calculate_column_confidence(
            required_cols, optional_cols, matched_columns, match_types
        )
        
        return ColumnMatchResult(
            confidence=confidence,
            matched_columns=matched_columns,
            missing_columns=missing_columns,
            match_details={'match_types': match_types}
        )
    
    def _find_best_fuzzy_match(self, target: str, 
                              candidates: List[str]) -> Tuple[str, float]:
        """
        Find the best fuzzy match for a target string.
        
        Args:
            target: String to match (from template)
            candidates: List of candidate strings (from data)
        
        Returns:
            Tuple of (best_match, similarity_score)
        """
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            # Use SequenceMatcher for fuzzy matching
            score = SequenceMatcher(None, target, candidate).ratio()
            
            # Also check for substring matches
            if target in candidate or candidate in target:
                score = max(score, 0.8)  # Boost substring matches
            
            # Check if candidate is abbreviation of target
            if self._is_abbreviation(candidate, target):
                score = max(score, 0.85)
            
            # Also check if target is abbreviation of candidate (less common)
            if self._is_abbreviation(target, candidate):
                score = max(score, 0.75)
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match, best_score
    
    def _is_abbreviation(self, short: str, long: str) -> bool:
        """
        Check if short is likely an abbreviation of long.
        
        Examples:
            - 'amt' -> 'amount'
            - 'cust_id' -> 'customer_id'
            - 'dt' -> 'date'
            - 'opp_id' -> 'opportunity_id'
        """
        # Common abbreviation patterns
        abbrev_patterns = [
            (r'amt', 'amount'),
            (r'qty', 'quantity'),
            (r'dt', 'date'),
            (r'id$', 'identifier'),
            (r'num', 'number'),
            (r'desc', 'description'),
            (r'addr', 'address'),
            (r'opp', 'opportunity'),
            (r'oppt', 'opportunity'),
            (r'cust', 'customer'),
            (r'prod', 'product'),
            (r'qty', 'quantity'),
            (r'val', 'value'),
        ]
        
        # Check direct pattern matches
        for pattern, full in abbrev_patterns:
            if re.search(pattern, short.lower()) and full in long.lower():
                return True
        
        # Remove common separators for character matching
        short_parts = short.lower().split('_')
        long_parts = long.lower().split('_')
        
        # Check if each part of short matches start of corresponding part in long
        if len(short_parts) == len(long_parts):
            matches = 0
            for s_part, l_part in zip(short_parts, long_parts):
                if l_part.startswith(s_part) or s_part in abbrev_patterns:
                    matches += 1
            if matches == len(short_parts):
                return True
        
        # Check if all characters in short appear in order in long
        short_clean = short.lower().replace('_', '').replace('-', '')
        long_clean = long.lower().replace('_', '').replace('-', '')
        
        long_idx = 0
        matched_chars = 0
        for char in short_clean:
            found = False
            for i in range(long_idx, len(long_clean)):
                if long_clean[i] == char:
                    long_idx = i + 1
                    matched_chars += 1
                    found = True
                    break
            if not found:
                break
        
        # Consider it an abbreviation if most characters match in order
        if matched_chars >= len(short_clean) * 0.7:
            return True
        
        return False
    
    def _calculate_column_confidence(self, required_cols: List[str],
                                   optional_cols: List[str],
                                   matched_columns: Dict[str, str],
                                   match_types: Dict[str, str]) -> float:
        """
        Calculate confidence score based on column matches.
        
        Args:
            required_cols: List of required columns
            optional_cols: List of optional columns
            matched_columns: Mapping of matched columns
            match_types: How each column was matched
        
        Returns:
            Confidence score between 0 and 1
        """
        if not required_cols:
            return 1.0  # No requirements = perfect match
        
        # Calculate required column score
        required_matched = sum(1 for col in required_cols if col in matched_columns)
        required_score = required_matched / len(required_cols)
        
        # Apply match type weights
        match_weights = {
            'exact': 1.0,
            'synonym': 0.95,
            'fuzzy': 0.85
        }
        
        weighted_score = 0.0
        for col in required_cols:
            if col in matched_columns:
                match_type = match_types.get(col, 'exact')
                weight = match_weights.get(match_type, 0.8)
                weighted_score += weight / len(required_cols)
        
        # Bonus for optional columns (up to 10% boost)
        if optional_cols:
            optional_matched = sum(1 for col in optional_cols if col in matched_columns)
            optional_bonus = (optional_matched / len(optional_cols)) * 0.1
            weighted_score = min(1.0, weighted_score + optional_bonus)
        
        return weighted_score
    
    def match_template(self, df: pd.DataFrame, template: Dict) -> TemplateMatchResult:
        """
        Perform comprehensive template matching against a DataFrame.
        
        Args:
            df: DataFrame to match
            template: Complete template specification
        
        Returns:
            TemplateMatchResult with overall confidence and details
        """
        template_id = template.get('id', 'unknown')
        
        # Get pattern matching specification
        pattern_spec = template.get('pattern_matching', {})
        
        # 1. Column matching (40% weight)
        column_result = self.match_columns(
            list(df.columns),
            pattern_spec
        )
        
        # 2. Data pattern matching (30% weight) - TODO: Implement
        pattern_score = 0.5  # Placeholder
        
        # 3. Statistical matching (20% weight) - TODO: Implement
        statistical_score = 0.5  # Placeholder
        
        # 4. Value domain matching (10% weight) - TODO: Implement
        domain_score = 0.5  # Placeholder
        
        # Calculate weighted overall confidence
        weights = {
            'columns': 0.4,
            'patterns': 0.3,
            'statistics': 0.2,
            'domains': 0.1
        }
        
        overall_confidence = (
            column_result.confidence * weights['columns'] +
            pattern_score * weights['patterns'] +
            statistical_score * weights['statistics'] +
            domain_score * weights['domains']
        )
        
        return TemplateMatchResult(
            template_id=template_id,
            confidence=overall_confidence,
            column_match=column_result,
            pattern_match_score=pattern_score,
            statistical_match_score=statistical_score,
            match_details={
                'weights': weights,
                'scores': {
                    'columns': column_result.confidence,
                    'patterns': pattern_score,
                    'statistics': statistical_score,
                    'domains': domain_score
                }
            }
        )
    
    def find_matching_templates(self, df: pd.DataFrame, 
                              templates: List[Dict],
                              top_n: int = 3) -> List[TemplateMatchResult]:
        """
        Find the best matching templates for a DataFrame.
        
        Args:
            df: DataFrame to analyze
            templates: List of template specifications
            top_n: Number of top matches to return
        
        Returns:
            List of TemplateMatchResult objects, sorted by confidence
        """
        results = []
        
        for template in templates:
            try:
                result = self.match_template(df, template)
                results.append(result)
            except Exception as e:
                logger.error(f"Error matching template {template.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by confidence and return top N
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:top_n]
    
    def find_best_match(self, df: pd.DataFrame, 
                       templates: List[Dict],
                       confidence_threshold: float = 0.5,
                       generic_template: Optional[Dict] = None) -> TemplateMatchResult:
        """
        Find the best matching template with fallback to generic template.
        
        Args:
            df: DataFrame to analyze
            templates: List of template specifications
            confidence_threshold: Minimum confidence to accept a match
            generic_template: Generic template to use as fallback
        
        Returns:
            Best TemplateMatchResult, using generic template if no good match
        """
        # Try to find matches
        matches = self.find_matching_templates(df, templates, top_n=1)
        
        if matches and matches[0].confidence >= confidence_threshold:
            # Good match found
            return matches[0]
        
        # No good match - use generic template
        if generic_template:
            # Create a generic match result
            generic_result = TemplateMatchResult(
                template_id=generic_template.get('template', {}).get('id', 'generic-minimal'),
                confidence=0.0,  # Zero confidence indicates default was used
                column_match=ColumnMatchResult(
                    confidence=0.0,
                    matched_columns={},
                    missing_columns=[],
                    match_details={'reason': 'Generic template - no pattern matching performed'}
                ),
                match_type="default",
                match_reason="No domain-specific template matched with sufficient confidence"
            )
            return generic_result
        
        # No generic template available - return best match anyway
        if matches:
            matches[0].match_type = "low_confidence"
            matches[0].match_reason = f"Best available match (confidence: {matches[0].confidence:.2f})"
            return matches[0]
        
        # No matches at all
        raise ValueError("No templates available for matching")


# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_matcher_column_matching.py
#    - tests/unit/templates/test_pattern_analyzer.py
#    - tests/unit/templates/test_confidence_scoring.py
# 
# 2. Integration tests:
#    - tests/integration/test_discovery_template_matching.py
#
# Complete test coverage details are documented in:
# tests/plans/template_driven_discovery_test_plan.md
# ----------------------------------------------
