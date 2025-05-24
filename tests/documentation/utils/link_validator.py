"""
Link validation utilities for documentation testing
"""
import re
import os
import requests
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, urljoin
import concurrent.futures
import time


class LinkType(Enum):
    """Types of links found in documentation"""
    INTERNAL_DOC = "internal_doc"      # Links to other docs
    INTERNAL_CODE = "internal_code"    # Links to code files  
    EXTERNAL = "external"              # External URLs
    ANCHOR = "anchor"                  # #section links
    IMAGE = "image"                    # Image references
    EMAIL = "email"                    # mailto: links


@dataclass
class Link:
    """Container for extracted link"""
    url: str
    text: str
    line_number: int
    link_type: LinkType
    source_file: str
    

@dataclass 
class LinkCheckResult:
    """Result of checking a link"""
    link: Link
    is_valid: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    redirect_url: Optional[str] = None


class LinkValidator:
    """Validate links in documentation"""
    
    def __init__(self, project_root: Path, timeout: int = 5):
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.timeout = timeout
        self.checked_urls = {}  # Cache for external URL checks
        
    def extract_links_from_markdown(self, filepath: str) -> List[Link]:
        """Extract all links from a markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        links = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Markdown links: [text](url)
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
            for text, url in md_links:
                link_type = self._classify_link(url)
                links.append(Link(
                    url=url,
                    text=text,
                    line_number=line_num,
                    link_type=link_type,
                    source_file=filepath
                ))
            
            # Reference-style links: [text][ref]
            ref_links = re.findall(r'\[([^\]]+)\]\[([^\]]+)\]', line)
            # We'll need to resolve these with link definitions
            
            # HTML links: <a href="url">
            html_links = re.findall(r'<a\s+href="([^"]+)"[^>]*>([^<]*)</a>', line)
            for url, text in html_links:
                link_type = self._classify_link(url)
                links.append(Link(
                    url=url,
                    text=text or "HTML Link",
                    line_number=line_num,
                    link_type=link_type,
                    source_file=filepath
                ))
            
            # Image links: ![alt](url)
            img_links = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            for alt, url in img_links:
                links.append(Link(
                    url=url,
                    text=f"Image: {alt}" if alt else "Image",
                    line_number=line_num,
                    link_type=LinkType.IMAGE,
                    source_file=filepath
                ))
        
        # Extract link definitions: [ref]: url
        link_defs = re.findall(r'^\[([^\]]+)\]:\s*(.+)$', content, re.MULTILINE)
        link_def_dict = {ref: url for ref, url in link_defs}
        
        # Resolve reference-style links
        for line_num, line in enumerate(lines, 1):
            ref_links = re.findall(r'\[([^\]]+)\]\[([^\]]+)\]', line)
            for text, ref in ref_links:
                if ref in link_def_dict:
                    url = link_def_dict[ref]
                    link_type = self._classify_link(url)
                    links.append(Link(
                        url=url,
                        text=text,
                        line_number=line_num,
                        link_type=link_type,
                        source_file=filepath
                    ))
        
        return links
    
    def _classify_link(self, url: str) -> LinkType:
        """Classify the type of link"""
        # Email
        if url.startswith('mailto:'):
            return LinkType.EMAIL
        
        # External URL
        if url.startswith(('http://', 'https://', 'ftp://')):
            return LinkType.EXTERNAL
        
        # Anchor
        if url.startswith('#'):
            return LinkType.ANCHOR
        
        # Check file extension for internal links
        if url.endswith(('.md', '.markdown')):
            return LinkType.INTERNAL_DOC
        
        if url.endswith(('.py', '.yaml', '.yml', '.json', '.txt', '.csv')):
            return LinkType.INTERNAL_CODE
        
        # Default to internal doc for relative paths
        return LinkType.INTERNAL_DOC
    
    def validate_link(self, link: Link) -> LinkCheckResult:
        """Validate a single link"""
        try:
            if link.link_type == LinkType.EXTERNAL:
                return self._check_external_link(link)
            elif link.link_type == LinkType.INTERNAL_DOC:
                return self._check_internal_doc_link(link)
            elif link.link_type == LinkType.INTERNAL_CODE:
                return self._check_internal_code_link(link)
            elif link.link_type == LinkType.ANCHOR:
                return self._check_anchor_link(link)
            elif link.link_type == LinkType.IMAGE:
                return self._check_image_link(link)
            elif link.link_type == LinkType.EMAIL:
                # Just validate email format
                return LinkCheckResult(
                    link=link,
                    is_valid='@' in link.url.replace('mailto:', ''),
                    error=None if '@' in link.url else "Invalid email format"
                )
            else:
                return LinkCheckResult(
                    link=link,
                    is_valid=False,
                    error=f"Unknown link type: {link.link_type}"
                )
        except Exception as e:
            return LinkCheckResult(
                link=link,
                is_valid=False,
                error=str(e)
            )
    
    def _check_external_link(self, link: Link) -> LinkCheckResult:
        """Check if external URL is reachable"""
        url = link.url
        
        # Check cache first
        if url in self.checked_urls:
            cached_result = self.checked_urls[url]
            return LinkCheckResult(
                link=link,
                is_valid=cached_result['is_valid'],
                status_code=cached_result.get('status_code'),
                error=cached_result.get('error'),
                redirect_url=cached_result.get('redirect_url')
            )
        
        try:
            # Make HEAD request first (faster)
            response = requests.head(
                url, 
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'ADRI Documentation Link Checker'}
            )
            
            # Some servers don't support HEAD, try GET
            if response.status_code == 405:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    headers={'User-Agent': 'ADRI Documentation Link Checker'},
                    stream=True  # Don't download full content
                )
            
            is_valid = response.status_code < 400
            redirect_url = str(response.url) if str(response.url) != url else None
            
            # Cache result
            self.checked_urls[url] = {
                'is_valid': is_valid,
                'status_code': response.status_code,
                'redirect_url': redirect_url
            }
            
            return LinkCheckResult(
                link=link,
                is_valid=is_valid,
                status_code=response.status_code,
                redirect_url=redirect_url
            )
            
        except requests.exceptions.Timeout:
            error = f"Timeout after {self.timeout}s"
            self.checked_urls[url] = {'is_valid': False, 'error': error}
            return LinkCheckResult(link=link, is_valid=False, error=error)
        except requests.exceptions.ConnectionError as e:
            error = f"Connection error: {str(e)}"
            self.checked_urls[url] = {'is_valid': False, 'error': error}
            return LinkCheckResult(link=link, is_valid=False, error=error)
        except Exception as e:
            error = f"Error checking URL: {str(e)}"
            self.checked_urls[url] = {'is_valid': False, 'error': error}
            return LinkCheckResult(link=link, is_valid=False, error=error)
    
    def _check_internal_doc_link(self, link: Link) -> LinkCheckResult:
        """Check if internal documentation link exists"""
        source_path = Path(link.source_file)
        source_dir = source_path.parent
        
        # Handle anchor in URL
        url = link.url.split('#')[0] if '#' in link.url else link.url
        
        # Resolve relative path
        if url.startswith('/'):
            # Absolute path from docs root
            target_path = self.docs_dir / url.lstrip('/')
        else:
            # Relative to current file
            target_path = (source_dir / url).resolve()
        
        # Check if file exists
        if target_path.exists():
            # If there's an anchor, validate it exists in the file
            if '#' in link.url:
                anchor = link.url.split('#')[1]
                return self._check_anchor_in_file(link, target_path, anchor)
            return LinkCheckResult(link=link, is_valid=True)
        else:
            # Try adding .md extension
            if not url.endswith('.md'):
                target_with_md = target_path.with_suffix('.md')
                if target_with_md.exists():
                    return LinkCheckResult(link=link, is_valid=True)
            
            return LinkCheckResult(
                link=link,
                is_valid=False,
                error=f"File not found: {target_path.relative_to(self.project_root)}"
            )
    
    def _check_internal_code_link(self, link: Link) -> LinkCheckResult:
        """Check if internal code file exists"""
        source_path = Path(link.source_file)
        source_dir = source_path.parent
        
        # Resolve path relative to project root
        if link.url.startswith('/'):
            target_path = self.project_root / link.url.lstrip('/')
        else:
            # Try relative to source file first
            target_path = (source_dir / link.url).resolve()
            if not target_path.exists():
                # Try relative to project root
                target_path = self.project_root / link.url
        
        if target_path.exists():
            return LinkCheckResult(link=link, is_valid=True)
        else:
            return LinkCheckResult(
                link=link,
                is_valid=False,
                error=f"Code file not found: {link.url}"
            )
    
    def _check_anchor_link(self, link: Link) -> LinkCheckResult:
        """Check if anchor exists in the same file"""
        source_path = Path(link.source_file)
        anchor = link.url.lstrip('#')
        return self._check_anchor_in_file(link, source_path, anchor)
    
    def _check_anchor_in_file(self, link: Link, filepath: Path, anchor: str) -> LinkCheckResult:
        """Check if an anchor exists in a markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert headers to anchors (GitHub style)
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        anchors = set()
        
        for header in headers:
            # Convert header to anchor format
            # Remove markdown formatting
            clean_header = re.sub(r'\*\*|__|\*|_|`', '', header)
            # Convert to lowercase, replace spaces with hyphens
            anchor_text = clean_header.lower().strip()
            anchor_text = re.sub(r'[^\w\s-]', '', anchor_text)
            anchor_text = re.sub(r'[-\s]+', '-', anchor_text)
            anchors.add(anchor_text)
        
        # Also check for HTML anchors
        html_anchors = re.findall(r'<a\s+(?:name|id)="([^"]+)"', content)
        anchors.update(html_anchors)
        
        if anchor in anchors:
            return LinkCheckResult(link=link, is_valid=True)
        else:
            return LinkCheckResult(
                link=link,
                is_valid=False,
                error=f"Anchor '#{anchor}' not found in {filepath.name}"
            )
    
    def _check_image_link(self, link: Link) -> LinkCheckResult:
        """Check if image file exists"""
        # Images might be external or internal
        if link.url.startswith(('http://', 'https://')):
            return self._check_external_link(link)
        else:
            # Check as internal file
            source_path = Path(link.source_file)
            source_dir = source_path.parent
            
            if link.url.startswith('/'):
                target_path = self.project_root / link.url.lstrip('/')
            else:
                target_path = (source_dir / link.url).resolve()
            
            if target_path.exists():
                return LinkCheckResult(link=link, is_valid=True)
            else:
                return LinkCheckResult(
                    link=link,
                    is_valid=False,
                    error=f"Image not found: {link.url}"
                )
    
    def validate_links_parallel(self, links: List[Link], max_workers: int = 10) -> List[LinkCheckResult]:
        """Validate multiple links in parallel"""
        results = []
        
        # Separate external links for parallel checking
        external_links = [l for l in links if l.link_type == LinkType.EXTERNAL]
        other_links = [l for l in links if l.link_type != LinkType.EXTERNAL]
        
        # Check non-external links sequentially (fast)
        for link in other_links:
            results.append(self.validate_link(link))
        
        # Check external links in parallel
        if external_links:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_link = {executor.submit(self.validate_link, link): link 
                                for link in external_links}
                
                for future in concurrent.futures.as_completed(future_to_link):
                    result = future.result()
                    results.append(result)
        
        return results
