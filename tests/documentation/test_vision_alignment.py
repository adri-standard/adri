"""
Phase 3: Test vision alignment in documentation
"""
from pathlib import Path
from typing import List, Dict
import unittest

from base_doc_test import BaseDocumentationTest, TestResult
from utils.vision_checker import VisionChecker, VisionIssue, VisionAlignmentResult


class TestVisionAlignment(BaseDocumentationTest):
    """Test documentation alignment with ADRI vision"""
    
    def setUp(self):
        super().__init__()
        vision_path = self.docs_dir / "VISION.md"
        self.checker = VisionChecker(vision_path)
    
    def test_all_documents_vision_alignment(self):
        """Test all documents for vision alignment"""
        print("\n" + "="*60)
        print("Testing Vision Alignment in Documentation")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        all_results = []
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            print(f"\n📄 Checking {relative_path}")
            
            try:
                result = self.checker.check_document(md_file)
                all_results.append(result)
                
                # Log result
                if result.is_aligned:
                    self.log_result(
                        f"{relative_path} - Vision alignment",
                        TestResult(
                            True,
                            f"Fully aligned (score: {result.score:.2f})"
                        )
                    )
                else:
                    # Log each issue
                    for issue in result.issues[:5]:  # Show first 5 issues
                        test_name = f"{relative_path}:{issue.line_number} - {issue.issue_type}"
                        self.log_result(
                            test_name,
                            TestResult(
                                False,
                                issue.message,
                                details={
                                    'context': issue.context[:100] if issue.context else '',
                                    'suggestion': issue.suggestion[:100] if issue.suggestion else ''
                                }
                            )
                        )
                    
                    if len(result.issues) > 5:
                        print(f"   ... and {len(result.issues) - 5} more issues")
                
                print(f"   Score: {result.score:.2f}, Issues: {len(result.issues)}")
                
            except Exception as e:
                self.log_result(
                    f"{relative_path} - Vision check",
                    TestResult(False, f"Failed to check: {str(e)}")
                )
        
        # Generate and print summary report
        if all_results:
            report = self.checker.generate_alignment_report(all_results)
            print(report)
            
            # Save report
            report_path = self.project_root / "tests/documentation/reports/vision_alignment_report.txt"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"\n📊 Detailed report saved to: {report_path}")
        
        # Fail if average score is too low
        avg_score = sum(r.score for r in all_results) / len(all_results) if all_results else 0
        if avg_score < 0.8:  # 80% threshold
            self.fail(f"Average vision alignment score too low: {avg_score:.2f}")
    
    def test_terminology_consistency(self):
        """Test for consistent terminology across all documents"""
        print("\n" + "="*60)
        print("Testing Terminology Consistency")
        print("="*60 + "\n")
        
        # Track term usage across documents
        term_usage = {}
        for canonical, variants in self.checker.core_terms.items():
            term_usage[canonical] = {
                'canonical_count': 0,
                'variant_counts': {v: 0 for v in variants},
                'files_using_canonical': [],
                'files_using_variants': []
            }
        
        markdown_files = self.get_all_markdown_files()
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # Check each term
                for canonical, variants in self.checker.core_terms.items():
                    canonical_lower = canonical.lower()
                    
                    # Count canonical usage
                    if canonical_lower in content:
                        term_usage[canonical]['canonical_count'] += content.count(canonical_lower)
                        term_usage[canonical]['files_using_canonical'].append(str(relative_path))
                    
                    # Count variant usage
                    for variant in variants:
                        variant_lower = variant.lower()
                        if variant_lower in content:
                            count = content.count(variant_lower)
                            term_usage[canonical]['variant_counts'][variant] += count
                            if str(relative_path) not in term_usage[canonical]['files_using_variants']:
                                term_usage[canonical]['files_using_variants'].append(str(relative_path))
                
            except Exception as e:
                self.log_result(
                    f"{relative_path} - Term analysis",
                    TestResult(False, f"Failed to analyze: {str(e)}")
                )
        
        # Report on term usage
        print("\nTerminology Usage Report:")
        print("-" * 40)
        
        inconsistent_terms = []
        
        for canonical, usage in term_usage.items():
            total_variant_count = sum(usage['variant_counts'].values())
            
            if total_variant_count > 0:
                print(f"\n'{canonical}':")
                print(f"  Canonical usage: {usage['canonical_count']} times in {len(usage['files_using_canonical'])} files")
                print(f"  Variant usage: {total_variant_count} times in {len(usage['files_using_variants'])} files")
                
                for variant, count in usage['variant_counts'].items():
                    if count > 0:
                        print(f"    - '{variant}': {count} times")
                
                # Mark as inconsistent if variants are used more than canonical
                if total_variant_count > usage['canonical_count']:
                    inconsistent_terms.append(canonical)
        
        # Log results
        if inconsistent_terms:
            self.log_result(
                "Terminology consistency",
                TestResult(
                    False,
                    f"Inconsistent use of {len(inconsistent_terms)} terms",
                    details={'terms': inconsistent_terms}
                )
            )
        else:
            self.log_result(
                "Terminology consistency",
                TestResult(True, "All terms used consistently")
            )
    
    def test_no_deprecated_terms(self):
        """Ensure no deprecated terms are used"""
        print("\n" + "="*60)
        print("Checking for Deprecated Terms")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        files_with_deprecated = []
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                deprecated_found = []
                
                for line_num, line in enumerate(lines, 1):
                    # Skip code blocks
                    if line.strip().startswith(('```', '    ', '\t')):
                        continue
                    
                    line_lower = line.lower()
                    for deprecated, replacement in self.checker.deprecated_terms.items():
                        if deprecated.lower() in line_lower:
                            deprecated_found.append({
                                'term': deprecated,
                                'replacement': replacement,
                                'line': line_num,
                                'context': line.strip()
                            })
                
                if deprecated_found:
                    files_with_deprecated.append((relative_path, deprecated_found))
                    
                    for item in deprecated_found[:3]:  # Show first 3
                        self.log_result(
                            f"{relative_path}:{item['line']} - Deprecated term",
                            TestResult(
                                False,
                                f"Replace '{item['term']}' with '{item['replacement']}'",
                                details={'context': item['context']}
                            )
                        )
                
            except Exception as e:
                self.log_result(
                    f"{relative_path} - Deprecated term check",
                    TestResult(False, f"Failed to check: {str(e)}")
                )
        
        # Summary
        if files_with_deprecated:
            total_deprecated = sum(len(items) for _, items in files_with_deprecated)
            print(f"\n❌ Found {total_deprecated} deprecated terms in {len(files_with_deprecated)} files")
            self.fail(f"Found {total_deprecated} deprecated terms")
        else:
            print("\n✅ No deprecated terms found")


if __name__ == '__main__':
    unittest.main()
