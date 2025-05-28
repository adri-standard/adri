"""
Evaluation results for ADRI certification templates.

This module provides classes for representing the results of evaluating
an ADRI assessment against certification templates.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TemplateGap:
    """
    Represents a gap between actual data quality and template requirements.
    """
    requirement_id: str
    requirement_type: str  # 'overall', 'dimension', 'rule', 'field'
    requirement_description: str
    expected_value: Any
    actual_value: Any
    gap_severity: str  # 'blocking', 'high', 'medium', 'low'
    remediation_hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'requirement_id': self.requirement_id,
            'requirement_type': self.requirement_type,
            'description': self.requirement_description,
            'expected': self.expected_value,
            'actual': self.actual_value,
            'severity': self.gap_severity,
            'remediation': self.remediation_hint
        }
    
    @property
    def gap_size(self) -> float:
        """Calculate the size of the gap if numeric."""
        # Handle boolean values specially
        if isinstance(self.expected_value, bool) or isinstance(self.actual_value, bool):
            return 0.0
        try:
            return float(self.expected_value) - float(self.actual_value)
        except (TypeError, ValueError):
            return 0.0


@dataclass
class TemplateRequirement:
    """
    Represents a single requirement from a template.
    """
    requirement_id: str
    requirement_type: str
    description: str
    condition: str  # e.g., "validity >= 18"
    severity: str  # Impact if not met
    dimension: Optional[str] = None
    custom_rule: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.requirement_id,
            'type': self.requirement_type,
            'description': self.description,
            'condition': self.condition,
            'severity': self.severity,
            'dimension': self.dimension,
            'custom_rule': self.custom_rule
        }


@dataclass
class TemplateEvaluation:
    """
    Results of evaluating an assessment report against a template.
    """
    template_id: str
    template_version: str
    template_name: str
    evaluation_time: datetime = field(default_factory=datetime.now)
    
    # Core results
    compliant: bool = False
    compliance_score: float = 0.0  # Percentage of requirements met
    
    # Detailed results
    gaps: List[TemplateGap] = field(default_factory=list)
    passed_requirements: List[str] = field(default_factory=list)
    failed_requirements: List[str] = field(default_factory=list)
    
    # Certification eligibility
    certification_eligible: bool = False
    certification_blockers: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    estimated_remediation_effort: Optional[str] = None  # 'low', 'medium', 'high'
    
    def add_gap(self, gap: TemplateGap):
        """Add a gap to the evaluation."""
        self.gaps.append(gap)
        self.failed_requirements.append(gap.requirement_id)
        
        # Update certification eligibility
        if gap.gap_severity in ['blocking', 'high']:
            self.certification_eligible = False
            if gap.gap_severity == 'blocking':
                self.certification_blockers.append(gap.requirement_description)
    
    def add_passed_requirement(self, requirement_id: str):
        """Record a passed requirement."""
        self.passed_requirements.append(requirement_id)
    
    def finalize(self):
        """
        Finalize the evaluation results.
        
        Calculates compliance score and determines certification eligibility.
        """
        total_requirements = len(self.passed_requirements) + len(self.failed_requirements)
        if total_requirements > 0:
            self.compliance_score = (len(self.passed_requirements) / total_requirements) * 100
        
        # Check if compliant (all requirements passed)
        self.compliant = len(self.failed_requirements) == 0
        
        # Certification eligible if no blockers and no high severity gaps
        has_high_severity = any(gap.gap_severity == 'high' for gap in self.gaps)
        if not self.certification_blockers and not has_high_severity:
            self.certification_eligible = True
        
        # Estimate remediation effort
        self._estimate_remediation_effort()
    
    def _estimate_remediation_effort(self):
        """Estimate the effort required to achieve compliance."""
        blocking_count = sum(1 for gap in self.gaps if gap.gap_severity == 'blocking')
        high_count = sum(1 for gap in self.gaps if gap.gap_severity == 'high')
        
        if blocking_count > 2 or high_count > 5:
            self.estimated_remediation_effort = 'high'
        elif blocking_count > 0 or high_count > 0:
            self.estimated_remediation_effort = 'medium'
        elif len(self.gaps) > 0:
            self.estimated_remediation_effort = 'low'
        else:
            self.estimated_remediation_effort = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'template_id': self.template_id,
            'template_version': self.template_version,
            'template_name': self.template_name,
            'evaluation_time': self.evaluation_time.isoformat(),
            'compliant': self.compliant,
            'compliance_score': round(self.compliance_score, 1),
            'certification_eligible': self.certification_eligible,
            'certification_blockers': self.certification_blockers,
            'gaps': [gap.to_dict() for gap in self.gaps],
            'passed_requirements': self.passed_requirements,
            'failed_requirements': self.failed_requirements,
            'recommendations': self.recommendations,
            'estimated_remediation_effort': self.estimated_remediation_effort,
            'summary': self.get_summary()
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the evaluation."""
        if self.compliant:
            return f"✅ Fully compliant with {self.template_name}"
        else:
            gap_summary = f"{len(self.gaps)} gaps found"
            if self.certification_blockers:
                gap_summary += f" ({len(self.certification_blockers)} blocking)"
            return f"❌ Not compliant with {self.template_name} - {gap_summary}"
    
    def get_remediation_plan(self) -> List[Dict[str, Any]]:
        """
        Generate a prioritized remediation plan.
        
        Returns:
            List of remediation actions ordered by priority
        """
        plan = []
        
        # Group gaps by severity
        severity_order = ['blocking', 'high', 'medium', 'low']
        gaps_by_severity = {s: [] for s in severity_order}
        
        for gap in self.gaps:
            gaps_by_severity[gap.gap_severity].append(gap)
        
        # Create prioritized actions
        priority = 1
        for severity in severity_order:
            for gap in gaps_by_severity[severity]:
                action = {
                    'priority': priority,
                    'severity': severity,
                    'requirement': gap.requirement_description,
                    'current_state': f"{gap.actual_value}",
                    'target_state': f"{gap.expected_value}",
                    'remediation': gap.remediation_hint or 'Address gap to meet requirement'
                }
                plan.append(action)
                priority += 1
        
        return plan

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_evaluation.py
#    - tests/unit/templates/test_template_gap.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_evaluation_reporting.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
