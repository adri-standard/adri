"""
Phase 4: Test content structure in documentation
"""
import re
from pathlib import Path
from typing import List, Dict, Set
import unittest
from collections import defaultdict

from base_doc_test import BaseDocumentationTest, TestResult


class TestContentStructure(BaseDocumentationTest):
    """Test documentation structure and formatting"""
    
    def setUp(self):
        super().__init__()
        # Define expected structure patterns
        self.doc_patterns = {
            "dimension": {
                "filename_pattern": r".*Dimension\.md$",
                "required_headers": ["Overview", "Why It Matters", "How ADRI Measures"],
                "optional_headers": ["Example", "Best Practices", "Common Issues"],
                "max_depth": 3,
            },
            "guide": {
                "filename_pattern": r"(GET_STARTED|Implementation-Guide|EXTENDING|IMPLEMENTING_GUARDS)\.md$",
                "required_headers": ["Introduction"],
                "optional_headers": ["Prerequisites", "Steps", "Example", "Next Steps"],
                "max_depth": 4,
            },
            "integration": {
                "filename_pattern": r"(INTEGRATIONS|langchain|crewai|dspy).*\.md$",
                "required_headers": ["Overview"],
                "optional_headers": ["Installation", "Configuration", "Usage", "Example"],
                "max_depth": 3,
            },
            "reference": {
                "filename_pattern": r"(API_REFERENCE|DEVELOPER|PROJECT_STRUCTURE)\.md$",
                "required_headers": [],
                "optional_headers": ["Overview", "Reference", "Classes", "Functions"],
                "max_depth": 4,
            }
        }
    
    def test_document_structure(self):
        """Test that documents follow expected structure"""
        print("\n" + "="*60)
        print("Testing Document Structure")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            doc_type = self._identify_doc_type(md_file)
            
            print(f"\n📄 Checking {relative_path} (type: {doc_type or 'general'})")
            
            # Parse document
            content = self.read_markdown_file(md_file)
            parsed = self.parse_markdown(content)
            
            # Check structure based on document type
            if doc_type:
                pattern = self.doc_patterns[doc_type]
                
                # Check required headers
                headers = [h[1].strip() for h in parsed['headers']]
                missing_headers = []
                
                for required in pattern['required_headers']:
                    if not any(required.lower() in h.lower() for h in headers):
                        missing_headers.append(required)
                
                if missing_headers:
                    self.log_result(
                        f"{relative_path} - Required headers",
                        TestResult(
                            False,
                            f"Missing required headers for {doc_type}",
                            details={'missing': missing_headers}
                        )
                    )
                else:
                    self.log_result(
                        f"{relative_path} - Required headers",
                        TestResult(True, f"All required headers present for {doc_type}")
                    )
                
                # Check header depth
                max_depth = max(len(h[0]) for h in parsed['headers']) if parsed['headers'] else 0
                if max_depth > pattern['max_depth']:
                    self.log_result(
                        f"{relative_path} - Header depth",
                        TestResult(
                            False,
                            f"Headers too deep: {max_depth} (max: {pattern['max_depth']})"
                        )
                    )
            
            # General structure checks
            self._check_header_hierarchy(relative_path, parsed['headers'])
            self._check_code_block_formatting(relative_path, content)
            self._check_link_formatting(relative_path, parsed['links'])
    
    def test_metadata_completeness(self):
        """Test that documents have complete metadata"""
        print("\n" + "="*60)
        print("Testing Document Metadata")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            
            content = self.read_markdown_file(md_file)
            
            # Check for title (first H1)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                self.log_result(
                    f"{relative_path} - Title",
                    TestResult(False, "Missing H1 title at beginning of document")
                )
            else:
                self.log_result(
                    f"{relative_path} - Title",
                    TestResult(True, f"Title: {title_match.group(1)}")
                )
            
            # Check for description/introduction paragraph
            lines = content.split('\n')
            has_intro = False
            
            # Look for non-empty paragraph after title
            found_title = False
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    found_title = True
                    continue
                
                if found_title and line.strip() and not line.startswith(('#', '```', '|')):
                    has_intro = True
                    break
            
            if not has_intro:
                self.log_result(
                    f"{relative_path} - Introduction",
                    TestResult(False, "Missing introduction paragraph after title")
                )
    
    def test_consistent_formatting(self):
        """Test for consistent formatting across documents"""
        print("\n" + "="*60)
        print("Testing Formatting Consistency")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        formatting_stats = {
            'code_fence_style': defaultdict(int),  # ``` vs ~~~
            'list_style': defaultdict(int),         # -, *, 1.
            'header_style': defaultdict(int),       # # with or without trailing #
            'bold_style': defaultdict(int),         # ** vs __
            'link_style': defaultdict(int),         # inline vs reference
        }
        
        for md_file in markdown_files:
            content = self.read_markdown_file(md_file)
            
            # Check code fence style
            if '```' in content:
                formatting_stats['code_fence_style']['```'] += 1
            if '~~~' in content:
                formatting_stats['code_fence_style']['~~~'] += 1
            
            # Check list style
            if re.search(r'^\s*-\s+', content, re.MULTILINE):
                formatting_stats['list_style']['-'] += 1
            if re.search(r'^\s*\*\s+', content, re.MULTILINE):
                formatting_stats['list_style']['*'] += 1
            if re.search(r'^\s*\d+\.\s+', content, re.MULTILINE):
                formatting_stats['list_style']['numbered'] += 1
            
            # Check header style
            if re.search(r'^#+\s+.*\s+#+\s*$', content, re.MULTILINE):
                formatting_stats['header_style']['with_trailing'] += 1
            if re.search(r'^#+\s+.*[^#]\s*$', content, re.MULTILINE):
                formatting_stats['header_style']['without_trailing'] += 1
            
            # Check bold style
            if '**' in content:
                formatting_stats['bold_style']['**'] += 1
            if '__' in content and not '**' in content:
                formatting_stats['bold_style']['__'] += 1
        
        # Report inconsistencies
        print("\nFormatting Statistics:")
        print("-" * 40)
        
        for category, styles in formatting_stats.items():
            if len(styles) > 1:
                print(f"\n{category}:")
                for style, count in styles.items():
                    print(f"  {style}: {count} files")
                
                # Log as warning
                self.log_result(
                    f"Formatting - {category}",
                    TestResult(
                        False,
                        f"Inconsistent {category.replace('_', ' ')}",
                        details=dict(styles)
                    )
                )
    
    def test_no_orphaned_documents(self):
        """Test that all documents are referenced somewhere"""
        print("\n" + "="*60)
        print("Testing for Orphaned Documents")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        
        # Build reference map
        referenced_files = set()
        reference_map = defaultdict(list)
        
        for md_file in markdown_files:
            content = self.read_markdown_file(md_file)
            relative_path = md_file.relative_to(self.project_root)
            
            # Find all markdown links
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md[^)]*)\)', content)
            
            for link_text, link_url in md_links:
                # Clean the URL
                clean_url = link_url.split('#')[0]
                
                # Resolve the path
                if clean_url.startswith('/'):
                    ref_path = self.docs_dir / clean_url.lstrip('/')
                else:
                    ref_path = (md_file.parent / clean_url).resolve()
                
                if ref_path.exists():
                    ref_relative = ref_path.relative_to(self.project_root)
                    referenced_files.add(str(ref_relative))
                    reference_map[str(ref_relative)].append(str(relative_path))
        
        # Check mkdocs.yml navigation
        mkdocs_path = self.project_root / "config/mkdocs.yml"
        if mkdocs_path.exists():
            with open(mkdocs_path, 'r') as f:
                mkdocs_content = f.read()
            
            # Extract files from nav
            nav_files = re.findall(r':\s*([^:]+\.md)', mkdocs_content)
            for nav_file in nav_files:
                nav_path = self.docs_dir / nav_file
                if nav_path.exists():
                    nav_relative = nav_path.relative_to(self.project_root)
                    referenced_files.add(str(nav_relative))
                    reference_map[str(nav_relative)].append("mkdocs.yml")
        
        # Special files that don't need to be referenced
        special_files = ['docs/index.md', 'README.md', 'CONTRIBUTING.md']
        
        # Find orphaned documents
        orphaned = []
        for md_file in markdown_files:
            relative_path = str(md_file.relative_to(self.project_root))
            
            if relative_path not in referenced_files and relative_path not in special_files:
                # Skip test coverage files
                if 'test_coverage' not in relative_path:
                    orphaned.append(relative_path)
        
        # Report results
        if orphaned:
            print(f"\n⚠️  Found {len(orphaned)} orphaned documents:")
            for doc in orphaned[:10]:
                print(f"  - {doc}")
            
            if len(orphaned) > 10:
                print(f"  ... and {len(orphaned) - 10} more")
            
            self.log_result(
                "Orphaned documents",
                TestResult(
                    False,
                    f"Found {len(orphaned)} unreferenced documents",
                    details={'orphaned': orphaned[:10]}
                )
            )
        else:
            self.log_result(
                "Orphaned documents",
                TestResult(True, "All documents are properly referenced")
            )
    
    def _identify_doc_type(self, file_path: Path) -> str:
        """Identify the type of document based on filename"""
        filename = file_path.name
        
        for doc_type, pattern_info in self.doc_patterns.items():
            if re.match(pattern_info['filename_pattern'], filename):
                return doc_type
        
        return None
    
    def _check_header_hierarchy(self, file_path: Path, headers: List[tuple]):
        """Check that headers follow proper hierarchy"""
        if not headers:
            return
        
        issues = []
        prev_level = 0
        
        for i, (hashes, text) in enumerate(headers):
            level = len(hashes)
            
            # First header should be H1
            if i == 0 and level != 1:
                issues.append(f"First header should be H1, found H{level}: {text}")
            
            # Headers shouldn't skip levels
            if level > prev_level + 1:
                issues.append(f"Header level skip at line {i+1}: H{prev_level} -> H{level}")
            
            prev_level = level
        
        if issues:
            self.log_result(
                f"{file_path} - Header hierarchy",
                TestResult(False, "Header hierarchy issues", details={'issues': issues})
            )
    
    def _check_code_block_formatting(self, file_path: Path, content: str):
        """Check code block formatting"""
        # Check for code blocks without language specification
        unspecified_blocks = re.findall(r'^```\s*\n', content, re.MULTILINE)
        
        if unspecified_blocks:
            self.log_result(
                f"{file_path} - Code blocks",
                TestResult(
                    False,
                    f"Found {len(unspecified_blocks)} code blocks without language",
                    details={'suggestion': 'Add language after ``` (e.g., ```python)'}
                )
            )
    
    def _check_link_formatting(self, file_path: Path, links: List[tuple]):
        """Check link formatting"""
        issues = []
        
        for text, url in links:
            # Check for empty link text
            if not text.strip():
                issues.append(f"Empty link text for URL: {url}")
            
            # Check for raw URLs as link text
            if url == text:
                issues.append(f"Raw URL used as link text: {url}")
        
        if issues:
            self.log_result(
                f"{file_path} - Link formatting",
                TestResult(
                    False,
                    "Link formatting issues",
                    details={'issues': issues[:5]}  # Show first 5
                )
            )


if __name__ == '__main__':
    unittest.main()
