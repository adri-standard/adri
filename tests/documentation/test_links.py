"""
Phase 2: Test all links in documentation
"""
import time
from pathlib import Path
from typing import List, Dict
import unittest
from collections import defaultdict

from base_doc_test import BaseDocumentationTest, TestResult
from utils.link_validator import LinkValidator, Link, LinkType, LinkCheckResult


class TestLinks(BaseDocumentationTest):
    """Test all links in ADRI documentation"""
    
    def setUp(self):
        super().__init__()
        self.validator = LinkValidator(self.project_root)
        self.skip_external = False  # Set to True to skip external URL checks
    
    def test_all_links(self):
        """Test all links in documentation"""
        print("\n" + "="*60)
        print("Testing Links in Documentation")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        all_links = []
        links_by_type = defaultdict(list)
        
        # Extract all links
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            print(f"\n📄 Extracting links from {relative_path}")
            
            try:
                links = self.validator.extract_links_from_markdown(str(md_file))
                all_links.extend(links)
                
                # Group by type
                for link in links:
                    links_by_type[link.link_type].append(link)
                
                print(f"   Found {len(links)} links")
                
            except Exception as e:
                self.log_result(
                    f"Extract links from {relative_path}",
                    TestResult(False, f"Failed to extract links: {str(e)}")
                )
        
        # Print summary by type
        print("\n" + "-"*40)
        print("Links by type:")
        for link_type, links in links_by_type.items():
            print(f"  {link_type.value}: {len(links)}")
        print("-"*40 + "\n")
        
        # Filter links to check
        if self.skip_external:
            print("⚠️  Skipping external URL checks")
            links_to_check = [l for l in all_links if l.link_type != LinkType.EXTERNAL]
        else:
            links_to_check = all_links
        
        # Validate links
        print(f"\nValidating {len(links_to_check)} links...")
        start_time = time.time()
        
        results = self.validator.validate_links_parallel(links_to_check)
        
        elapsed = time.time() - start_time
        print(f"Validation completed in {elapsed:.1f} seconds")
        
        # Process results
        failed_links = []
        redirected_links = []
        
        for result in results:
            link = result.link
            relative_source = Path(link.source_file).relative_to(self.project_root)
            test_name = f"{relative_source}:{link.line_number} - {link.text[:50]}..."
            
            if result.is_valid:
                if result.redirect_url:
                    redirected_links.append(result)
                    self.log_result(
                        test_name,
                        TestResult(
                            True,
                            "Link valid (redirected)",
                            details={
                                'url': link.url,
                                'redirect_to': result.redirect_url,
                                'type': link.link_type.value
                            }
                        )
                    )
                else:
                    self.log_result(
                        test_name,
                        TestResult(True, "Link valid", details={'url': link.url})
                    )
            else:
                failed_links.append(result)
                self.log_result(
                    test_name,
                    TestResult(
                        False,
                        "Link invalid",
                        details={
                            'url': link.url,
                            'error': result.error,
                            'type': link.link_type.value,
                            'status_code': result.status_code
                        }
                    )
                )
        
        # Summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"Total links found: {len(all_links)}")
        print(f"Links checked: {len(links_to_check)}")
        print(f"Valid links: {len(links_to_check) - len(failed_links)}")
        print(f"Failed links: {len(failed_links)}")
        print(f"Redirected links: {len(redirected_links)}")
        
        if self.skip_external:
            skipped = len(all_links) - len(links_to_check)
            print(f"External links skipped: {skipped}")
        
        # Print failed links summary
        if failed_links:
            print("\n" + "-"*40)
            print("Failed Links:")
            for result in failed_links[:10]:  # Show first 10
                link = result.link
                relative_source = Path(link.source_file).relative_to(self.project_root)
                print(f"\n  📍 {relative_source}:{link.line_number}")
                print(f"     Link: {link.url}")
                print(f"     Text: {link.text}")
                print(f"     Error: {result.error}")
            
            if len(failed_links) > 10:
                print(f"\n  ... and {len(failed_links) - 10} more")
        
        # Test fails if there are broken links
        if failed_links:
            self.fail(f"{len(failed_links)} broken links found")
    
    def test_no_duplicate_links_in_file(self):
        """Check for duplicate links within the same file"""
        print("\n" + "="*60)
        print("Checking for Duplicate Links")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        files_with_duplicates = []
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            
            try:
                links = self.validator.extract_links_from_markdown(str(md_file))
                
                # Check for exact duplicates
                url_counts = defaultdict(list)
                for link in links:
                    url_counts[link.url].append(link)
                
                duplicates = {url: links for url, links in url_counts.items() if len(links) > 1}
                
                if duplicates:
                    files_with_duplicates.append((relative_path, duplicates))
                    
                    # Log duplicates
                    for url, duplicate_links in duplicates.items():
                        self.log_result(
                            f"{relative_path} - Duplicate link: {url}",
                            TestResult(
                                False,
                                f"Link appears {len(duplicate_links)} times",
                                details={
                                    'lines': [link.line_number for link in duplicate_links],
                                    'url': url
                                }
                            )
                        )
                else:
                    self.log_result(
                        f"{relative_path} - No duplicate links",
                        TestResult(True, "No duplicate links found")
                    )
                    
            except Exception as e:
                self.log_result(
                    f"{relative_path} - Check duplicates",
                    TestResult(False, f"Failed to check: {str(e)}")
                )
        
        # Summary
        if files_with_duplicates:
            print(f"\n⚠️  Found duplicate links in {len(files_with_duplicates)} files")
            # This is a warning, not a failure
    
    def test_external_links_use_https(self):
        """Ensure external links use HTTPS where possible"""
        print("\n" + "="*60)
        print("Checking External Links for HTTPS")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        http_links = []
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            
            try:
                links = self.validator.extract_links_from_markdown(str(md_file))
                
                for link in links:
                    if link.link_type == LinkType.EXTERNAL and link.url.startswith('http://'):
                        # Skip localhost
                        if 'localhost' in link.url or '127.0.0.1' in link.url:
                            continue
                        
                        http_links.append(link)
                        
                        self.log_result(
                            f"{relative_path}:{link.line_number} - HTTP link",
                            TestResult(
                                False,
                                "Consider using HTTPS",
                                details={
                                    'url': link.url,
                                    'text': link.text,
                                    'suggestion': link.url.replace('http://', 'https://')
                                }
                            )
                        )
                        
            except Exception as e:
                self.log_result(
                    f"{relative_path} - Check HTTPS",
                    TestResult(False, f"Failed to check: {str(e)}")
                )
        
        # Summary
        if http_links:
            print(f"\n⚠️  Found {len(http_links)} HTTP links that could use HTTPS")
            # This is a warning, not a failure


if __name__ == '__main__':
    unittest.main()
