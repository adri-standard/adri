"""
Base class for all documentation tests
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import unittest
from dataclasses import dataclass
import markdown


@dataclass
class TestResult:
    """Container for test results"""
    passed: bool
    message: str
    details: Optional[Dict] = None
    

class BaseDocumentationTest(unittest.TestCase):
    """Base class providing common functionality for documentation tests"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_root = Path(__file__).parent.parent.parent
        self.docs_dir = self.project_root / "docs"
        self.results = []
        
    def get_all_markdown_files(self, directory: Path = None) -> List[Path]:
        """Get all markdown files in the documentation directory"""
        if directory is None:
            directory = self.docs_dir
        
        markdown_files = []
        for file_path in directory.rglob("*.md"):
            # Skip test coverage files
            if "test_coverage" not in str(file_path):
                markdown_files.append(file_path)
        return markdown_files
    
    def read_markdown_file(self, file_path: Path) -> str:
        """Read and return content of a markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse_markdown(self, content: str) -> Dict:
        """Parse markdown content and extract structured information"""
        # Parse markdown
        md = markdown.Markdown(extensions=['meta', 'toc', 'fenced_code'])
        html = md.convert(content)
        
        # Extract headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)\n```', content, re.DOTALL)
        
        # Extract links
        # Markdown links: [text](url)
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        # HTML links: <a href="url">text</a>
        html_links = re.findall(r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>', html)
        
        return {
            'html': html,
            'metadata': md.Meta if hasattr(md, 'Meta') else {},
            'headers': headers,
            'code_blocks': code_blocks,
            'links': md_links + [(url, text) for url, text in html_links],
            'raw_content': content
        }
    
    def extract_python_code_blocks(self, content: str) -> List[Tuple[str, int]]:
        """Extract Python code blocks with their line numbers"""
        code_blocks = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            # Check for code block start
            if line.strip().startswith('```python') or line.strip() == '```':
                start_line = i + 1
                i += 1
                code_lines = []
                
                # Collect code until closing ```
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code = '\n'.join(code_lines)
                    # Only add if it looks like Python code
                    if any(keyword in code for keyword in ['import', 'from', 'def', 'class', '=', 'print']):
                        code_blocks.append((code, start_line))
            i += 1
        
        return code_blocks
    
    def log_result(self, test_name: str, result: TestResult):
        """Log a test result"""
        self.results.append({
            'test': test_name,
            'passed': result.passed,
            'message': result.message,
            'details': result.details
        })
        
        if not result.passed:
            print(f"❌ {test_name}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"   {key}: {value}")
        else:
            print(f"✅ {test_name}: {result.message}")
    
    def generate_report(self, output_path: Path = None):
        """Generate an HTML report of test results"""
        if output_path is None:
            output_path = self.project_root / "tests/documentation/reports/doc_test_results.html"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Count results
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ADRI Documentation Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .result.pass {{ border-color: green; background: #f0fff0; }}
        .result.fail {{ border-color: red; background: #fff0f0; }}
        .details {{ margin-top: 10px; padding: 10px; background: #f9f9f9; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>ADRI Documentation Test Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {total}</p>
        <p class="passed">Passed: {passed}</p>
        <p class="failed">Failed: {failed}</p>
        <p>Pass Rate: {passed/total*100:.1f}%</p>
    </div>
    
    <h2>Test Results</h2>
"""
        
        for result in self.results:
            status_class = "pass" if result['passed'] else "fail"
            status_icon = "✅" if result['passed'] else "❌"
            
            html_content += f"""
    <div class="result {status_class}">
        <strong>{status_icon} {result['test']}</strong>
        <p>{result['message']}</p>
"""
            
            if result.get('details'):
                html_content += '<div class="details">'
                for key, value in result['details'].items():
                    if isinstance(value, list):
                        html_content += f"<strong>{key}:</strong><ul>"
                        for item in value:
                            html_content += f"<li>{item}</li>"
                        html_content += "</ul>"
                    else:
                        html_content += f"<p><strong>{key}:</strong> {value}</p>"
                html_content += '</div>'
            
            html_content += '</div>\n'
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📊 Report generated: {output_path}")
        
    def tearDown(self):
        """Generate report after all tests"""
        if hasattr(self, '_testMethodName') and self._testMethodName.startswith('test_all'):
            self.generate_report()
