"""
Vision alignment checking utilities for documentation testing
"""
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class VisionIssue:
    """Container for vision alignment issues"""
    issue_type: str
    message: str
    line_number: int
    context: str
    suggestion: Optional[str] = None


@dataclass 
class VisionAlignmentResult:
    """Result of vision alignment check"""
    file_path: str
    is_aligned: bool
    issues: List[VisionIssue]
    score: float  # 0.0 to 1.0


class VisionChecker:
    """Check documentation alignment with ADRI vision"""
    
    def __init__(self, vision_doc_path: Path):
        self.vision_doc_path = vision_doc_path
        self._load_vision_requirements()
        
    def _load_vision_requirements(self):
        """Load core vision requirements from VISION.md"""
        # Core terminology that must be used consistently
        self.core_terms = {
            "Agent Data Readiness Index": ["ADRI", "agent data readiness"],
            "data reliability": ["data quality"],  # Prefer reliability over quality
            "five dimensions": ["5 dimensions", "dimensions"],
            "validity": ["valid", "validation"],
            "completeness": ["complete", "missing data"],
            "freshness": ["fresh", "stale", "timeliness"],
            "consistency": ["consistent", "inconsistent"],
            "plausibility": ["plausible", "implausible", "reasonable"],
            "guard": ["guards", "guardrail"],
            "assessor": ["assessment", "evaluate"],
            "data sources": ["datasource", "data source"],
        }
        
        # Terms to avoid or replace
        self.deprecated_terms = {
            "data quality": "data reliability",
            "ML": "machine learning",
            "AI": "artificial intelligence", 
            "LLM": "large language model",
            "agent": "AI agent",  # Be specific
        }
        
        # Required sections for certain document types
        self.required_sections = {
            "dimension": ["Overview", "Why It Matters", "How ADRI Measures", "Example"],
            "guide": ["Introduction", "Prerequisites", "Steps", "Example"],
            "integration": ["Overview", "Installation", "Configuration", "Usage", "Example"],
        }
        
        # Key principles from vision
        self.key_principles = [
            "open standard",
            "actionable insights",
            "five dimensions",
            "data reliability",
            "AI agent",
            "proactive data management",
            "comprehensive assessment",
        ]
        
        # Tone guidelines
        self.tone_words = {
            "positive": ["enable", "empower", "improve", "enhance", "ensure", "optimize"],
            "avoid": ["fail", "problem", "issue", "error", "wrong", "bad"],
        }
    
    def check_document(self, doc_path: Path) -> VisionAlignmentResult:
        """Check a document for vision alignment"""
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        issues = []
        
        # Check terminology consistency
        term_issues = self._check_terminology(lines)
        issues.extend(term_issues)
        
        # Check for deprecated terms
        deprecated_issues = self._check_deprecated_terms(lines)
        issues.extend(deprecated_issues)
        
        # Check tone
        tone_issues = self._check_tone(lines)
        issues.extend(tone_issues)
        
        # Check required sections based on doc type
        section_issues = self._check_required_sections(doc_path, content)
        issues.extend(section_issues)
        
        # Check key principles coverage
        principle_issues = self._check_key_principles(content)
        issues.extend(principle_issues)
        
        # Calculate alignment score
        score = self._calculate_alignment_score(issues, len(lines))
        
        return VisionAlignmentResult(
            file_path=str(doc_path),
            is_aligned=len(issues) == 0,
            issues=issues,
            score=score
        )
    
    def _check_terminology(self, lines: List[str]) -> List[VisionIssue]:
        """Check for consistent use of core terminology"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Check for inconsistent terminology
            for canonical, variants in self.core_terms.items():
                canonical_lower = canonical.lower()
                
                # If canonical term is used, good!
                if canonical_lower in line_lower:
                    continue
                
                # Check if any variant is used instead
                for variant in variants:
                    variant_lower = variant.lower()
                    if variant_lower in line_lower and canonical_lower not in line_lower:
                        # Special case: Allow abbreviations after first use
                        if variant == "ADRI" and self._has_prior_definition(lines, line_num, canonical):
                            continue
                        
                        issues.append(VisionIssue(
                            issue_type="terminology",
                            message=f"Use '{canonical}' instead of '{variant}'",
                            line_number=line_num,
                            context=line.strip(),
                            suggestion=line.replace(variant, canonical)
                        ))
        
        return issues
    
    def _check_deprecated_terms(self, lines: List[str]) -> List[VisionIssue]:
        """Check for deprecated terminology"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            for deprecated, replacement in self.deprecated_terms.items():
                if deprecated.lower() in line_lower:
                    # Allow if it's in a code block
                    if line.strip().startswith(('```', '    ', '\t')):
                        continue
                    
                    issues.append(VisionIssue(
                        issue_type="deprecated_term",
                        message=f"Replace '{deprecated}' with '{replacement}'",
                        line_number=line_num,
                        context=line.strip(),
                        suggestion=re.sub(
                            re.escape(deprecated), 
                            replacement, 
                            line, 
                            flags=re.IGNORECASE
                        )
                    ))
        
        return issues
    
    def _check_tone(self, lines: List[str]) -> List[VisionIssue]:
        """Check document tone aligns with vision"""
        issues = []
        
        # Count positive vs negative tone
        positive_count = 0
        negative_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Skip code blocks and comments
            if line.strip().startswith(('```', '#', '//', '<!--')):
                continue
            
            # Check for negative tone words
            for avoid_word in self.tone_words["avoid"]:
                if avoid_word in line_lower:
                    # Allow in certain contexts
                    if any(ok in line_lower for ok in ["no problem", "no issue", "no error", "avoid"]):
                        continue
                    
                    negative_count += 1
                    
                    # Find positive alternative
                    suggestion = line
                    if "fail" in line_lower:
                        suggestion = re.sub(r'\bfail\w*\b', 'need improvement', line, flags=re.IGNORECASE)
                    elif "problem" in line_lower:
                        suggestion = re.sub(r'\bproblem\w*\b', 'challenge', line, flags=re.IGNORECASE)
                    elif "issue" in line_lower:
                        suggestion = re.sub(r'\bissue\w*\b', 'consideration', line, flags=re.IGNORECASE)
                    
                    issues.append(VisionIssue(
                        issue_type="tone",
                        message=f"Consider more positive phrasing instead of '{avoid_word}'",
                        line_number=line_num,
                        context=line.strip(),
                        suggestion=suggestion.strip()
                    ))
            
            # Count positive words
            for positive_word in self.tone_words["positive"]:
                if positive_word in line_lower:
                    positive_count += 1
        
        # Check overall tone balance
        if positive_count < negative_count * 2:  # Should have at least 2x positive
            issues.append(VisionIssue(
                issue_type="tone_balance",
                message="Document tone is too negative. Add more empowering language.",
                line_number=0,
                context=f"Positive words: {positive_count}, Negative words: {negative_count}",
                suggestion="Review the VISION.md for tone guidelines"
            ))
        
        return issues
    
    def _check_required_sections(self, doc_path: Path, content: str) -> List[VisionIssue]:
        """Check if document has required sections based on type"""
        issues = []
        doc_name = doc_path.name.lower()
        
        # Determine document type
        doc_type = None
        if "dimension" in doc_name:
            doc_type = "dimension"
        elif any(word in doc_name for word in ["guide", "get_started", "implementation"]):
            doc_type = "guide"
        elif "integration" in doc_name:
            doc_type = "integration"
        
        if doc_type and doc_type in self.required_sections:
            required = self.required_sections[doc_type]
            
            # Extract headers
            headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            header_texts = [h.strip().lower() for h in headers]
            
            for section in required:
                section_lower = section.lower()
                if not any(section_lower in h for h in header_texts):
                    issues.append(VisionIssue(
                        issue_type="missing_section",
                        message=f"Missing required section: '{section}'",
                        line_number=0,
                        context=f"Document type: {doc_type}",
                        suggestion=f"Add a section titled '## {section}'"
                    ))
        
        return issues
    
    def _check_key_principles(self, content: str) -> List[VisionIssue]:
        """Check if key principles are mentioned"""
        issues = []
        content_lower = content.lower()
        
        # Check which principles are mentioned
        mentioned_principles = []
        for principle in self.key_principles:
            if principle.lower() in content_lower:
                mentioned_principles.append(principle)
        
        # Documents should mention at least some key principles
        if len(mentioned_principles) < 2:
            missing = [p for p in self.key_principles[:3] if p not in mentioned_principles]
            issues.append(VisionIssue(
                issue_type="missing_principles",
                message="Document should reference core ADRI principles",
                line_number=0,
                context=f"Mentioned: {mentioned_principles}",
                suggestion=f"Consider mentioning: {', '.join(missing)}"
            ))
        
        return issues
    
    def _has_prior_definition(self, lines: List[str], current_line: int, term: str) -> bool:
        """Check if a term was defined earlier in the document"""
        for i in range(current_line - 1):
            if term.lower() in lines[i].lower():
                return True
        return False
    
    def _calculate_alignment_score(self, issues: List[VisionIssue], total_lines: int) -> float:
        """Calculate overall alignment score"""
        if total_lines == 0:
            return 1.0
        
        # Weight different issue types
        weights = {
            "terminology": 2.0,
            "deprecated_term": 3.0,
            "tone": 1.0,
            "tone_balance": 5.0,
            "missing_section": 10.0,
            "missing_principles": 5.0,
        }
        
        total_penalty = 0
        for issue in issues:
            penalty = weights.get(issue.issue_type, 1.0)
            total_penalty += penalty
        
        # Normalize to 0-1 range
        max_penalty = total_lines * 0.1  # Assume max 10% of lines could have issues
        score = max(0, 1.0 - (total_penalty / max_penalty))
        
        return score
    
    def generate_alignment_report(self, results: List[VisionAlignmentResult]) -> str:
        """Generate a summary report of vision alignment"""
        aligned_count = sum(1 for r in results if r.is_aligned)
        total_count = len(results)
        avg_score = sum(r.score for r in results) / total_count if total_count > 0 else 0
        
        # Group issues by type
        issues_by_type = defaultdict(int)
        for result in results:
            for issue in result.issues:
                issues_by_type[issue.issue_type] += 1
        
        report = f"""
Vision Alignment Report
======================

Overall Statistics:
- Documents analyzed: {total_count}
- Fully aligned: {aligned_count} ({aligned_count/total_count*100:.1f}%)
- Average alignment score: {avg_score:.2f}

Issues by Type:
"""
        for issue_type, count in sorted(issues_by_type.items(), key=lambda x: x[1], reverse=True):
            report += f"- {issue_type}: {count}\n"
        
        # List documents with lowest scores
        low_score_docs = sorted(results, key=lambda x: x.score)[:5]
        if low_score_docs:
            report += "\nDocuments needing attention:\n"
            for doc in low_score_docs:
                report += f"- {Path(doc.file_path).name}: {doc.score:.2f} ({len(doc.issues)} issues)\n"
        
        return report
