#!/usr/bin/env python3
"""
AI Engineer First Impression Tests

Tests the critical first 30 seconds of demo experience.
Validates that AI engineers immediately recognize value and want to continue.
"""

import pytest
import sys
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.demo_validation.demo_validator import DemoValidator


class TestFirstImpression:
    """Test the critical first 30 seconds of AI engineer experience."""
    
    @classmethod
    def setup_class(cls):
        """Setup for first impression testing."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
        
        print(f"\n⚡ Testing First Impression Experience for {len(cls.examples)} examples")
        print("=" * 65)
        print("🎯 Goal: AI engineer says 'This solves my real problem' within 30 seconds")
        
        if not cls.examples:
            pytest.skip("No examples found to validate first impressions")
    
    def test_immediate_problem_recognition(self):
        """Test that problems are recognizable within first 10 lines of code."""
        unrecognizable_problems = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check first 10 lines for problem indicators
            first_lines = ''.join(lines[:10]).lower()
            
            # Framework-specific problem patterns AI engineers will recognize
            framework = self.validator.extract_framework_name(example_path)
            
            framework_problem_patterns = {
                "langchain": [
                    "customer service", "conversation", "chat response", 
                    "llm validation", "conversation flow"
                ],
                "crewai": [
                    "business analysis", "multi-agent", "crew coordination",
                    "agent workflow", "task execution"
                ],
                "autogen": [
                    "research collaboration", "agent conversation", 
                    "multi-agent coordination", "group chat"
                ],
                "llamaindex": [
                    "document processing", "query engine", "rag system",
                    "knowledge retrieval", "document analysis"
                ],
                "haystack": [
                    "knowledge management", "pipeline", "document search",
                    "information retrieval", "knowledge base"
                ],
                "langgraph": [
                    "workflow automation", "state management", "graph workflow",
                    "process automation", "workflow state"
                ],
                "semantic-kernel": [
                    "ai orchestration", "function calling", "ai planning",
                    "kernel execution", "ai coordination"
                ]
            }
            
            expected_patterns = framework_problem_patterns.get(framework, [])
            found_patterns = [p for p in expected_patterns if p in first_lines]
            
            if len(found_patterns) == 0:
                unrecognizable_problems.append(
                    f"{framework}: No recognizable problems in first 10 lines"
                )
            else:
                print(f"✅ {framework.upper()}: Immediate problem recognition - {found_patterns[0]}")
        
        if unrecognizable_problems:
            failure_msg = "\n".join([f"   • {prob}" for prob in unrecognizable_problems])
            pytest.fail(f"Problems not immediately recognizable:\n{failure_msg}")
    
    def test_value_proposition_visibility(self):
        """Test that value is visible in file header/docstring."""
        unclear_value = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract header/docstring (first 500 characters)
            header = content[:500]
            
            # Value indicators that should be in header
            value_phrases = [
                "prevents", "protection", "validation", "quality", "reliable",
                "solves", "fixes", "eliminates", "stops", "avoids", "prevents",
                "adri", "data quality", "validation errors"
            ]
            
            found_value = [phrase for phrase in value_phrases 
                          if phrase.lower() in header.lower()]
            
            framework = self.validator.extract_framework_name(example_path)
            
            if len(found_value) < 2:
                unclear_value.append(
                    f"{framework}: Value not clear in header (found: {found_value})"
                )
            else:
                print(f"✅ {framework.upper()}: Clear value in header - {found_value[:2]}")
        
        if unclear_value:
            failure_msg = "\n".join([f"   • {val}" for val in unclear_value])
            pytest.fail(f"Value proposition not immediately visible:\n{failure_msg}")
    
    def test_professional_first_appearance(self):
        """Test that examples look professional, not like toy demos."""
        unprofessional_examples = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            framework = self.validator.extract_framework_name(example_path)
            
            # Check for professional markers
            professional_indicators = [
                "#!/usr/bin/env python3",  # Proper shebang
                '"""',  # Proper docstring
                "import",  # Real imports
                "def ",  # Real functions
                "if __name__",  # Proper script structure
            ]
            
            found_professional = [ind for ind in professional_indicators 
                                if ind in content]
            
            # Check for unprofessional markers
            unprofessional_indicators = [
                "todo", "fixme", "hack", "temp", "test123", 
                "hello world", "foo", "bar", "baz"
            ]
            
            found_unprofessional = [ind for ind in unprofessional_indicators 
                                  if ind.lower() in content.lower()]
            
            if len(found_professional) < 4:
                unprofessional_examples.append(
                    f"{framework}: Lacks professional structure ({len(found_professional)}/5 markers)"
                )
            elif len(found_unprofessional) > 0:
                unprofessional_examples.append(
                    f"{framework}: Contains unprofessional elements: {found_unprofessional}"
                )
            else:
                print(f"✅ {framework.upper()}: Professional appearance")
        
        if unprofessional_examples:
            failure_msg = "\n".join([f"   • {ex}" for ex in unprofessional_examples])
            pytest.fail(f"Examples don't look professional:\n{failure_msg}")
    
    def test_realistic_business_context(self):
        """Test that examples use realistic business scenarios."""
        unrealistic_examples = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            framework = self.validator.extract_framework_name(example_path)
            
            # Realistic business context indicators
            business_contexts = [
                "customer", "business", "company", "organization", "enterprise",
                "client", "service", "product", "market", "sales", "support",
                "analysis", "report", "document", "research", "workflow"
            ]
            
            found_business = [ctx for ctx in business_contexts 
                            if ctx.lower() in content.lower()]
            
            # Unrealistic/toy indicators (red flags)
            toy_indicators = [
                "example", "demo", "test", "sample", "placeholder",
                "lorem ipsum", "fake", "mock", "dummy"
            ]
            
            # Count realistic vs toy references (allowing some "example" usage)
            toy_count = sum(content.lower().count(toy.lower()) for toy in toy_indicators)
            business_count = len(found_business)
            
            if business_count < 3:
                unrealistic_examples.append(
                    f"{framework}: Lacks business context ({business_count} business terms)"
                )
            elif toy_count > 5:  # Allow some "example" usage but not excessive
                unrealistic_examples.append(
                    f"{framework}: Too many toy/demo references ({toy_count} occurrences)"
                )
            else:
                print(f"✅ {framework.upper()}: Realistic business context")
        
        if unrealistic_examples:
            failure_msg = "\n".join([f"   • {ex}" for ex in unrealistic_examples])
            pytest.fail(f"Examples lack realistic business context:\n{failure_msg}")
    
    def test_easy_entry_point(self):
        """Test that getting started is immediately obvious."""
        confusing_entry = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            framework = self.validator.extract_framework_name(example_path)
            
            # Check for clear entry point indicators
            entry_indicators = [
                "python " + example_path.name,  # Clear run command
                "if __name__",  # Standard Python entry point
                "def main",  # Clear main function
                "# Run", "# Usage", "# Execute"  # Usage instructions
            ]
            
            found_entry = [ind for ind in entry_indicators if ind in content]
            
            # Check file is executable (has shebang)
            has_shebang = content.startswith("#!")
            
            if len(found_entry) < 2 and not has_shebang:
                confusing_entry.append(
                    f"{framework}: Entry point not clear (no shebang, {len(found_entry)} indicators)"
                )
            elif not has_shebang:
                confusing_entry.append(
                    f"{framework}: Missing executable shebang"
                )
            else:
                print(f"✅ {framework.upper()}: Clear entry point")
        
        if confusing_entry:
            failure_msg = "\n".join([f"   • {entry}" for entry in confusing_entry])
            pytest.fail(f"Examples have confusing entry points:\n{failure_msg}")
    
    def test_adri_prominence_without_overwhelming(self):
        """Test that ADRI is prominent but doesn't overwhelm the example."""
        adri_balance_issues = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            framework = self.validator.extract_framework_name(example_path)
            
            # Count ADRI mentions
            adri_mentions = (
                content.count("ADRI") + 
                content.count("adri") + 
                content.count("@adri_protected")
            )
            
            # Count total lines for proportion
            total_lines = len(content.split('\n'))
            
            # ADRI should be present but not overwhelming
            if adri_mentions == 0:
                adri_balance_issues.append(
                    f"{framework}: ADRI not visible enough (0 mentions)"
                )
            elif adri_mentions > total_lines // 10:  # More than 10% of lines
                adri_balance_issues.append(
                    f"{framework}: ADRI too overwhelming ({adri_mentions} mentions in {total_lines} lines)"
                )
            else:
                proportion = (adri_mentions / total_lines) * 100
                print(f"✅ {framework.upper()}: Good ADRI balance ({proportion:.1f}% of content)")
        
        if adri_balance_issues:
            failure_msg = "\n".join([f"   • {issue}" for issue in adri_balance_issues])
            pytest.fail(f"ADRI prominence/balance issues:\n{failure_msg}")


class TestThirtySecondExperience:
    """Test what an AI engineer experiences in first 30 seconds."""
    
    @classmethod
    def setup_class(cls):
        """Setup for 30-second experience testing."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
    
    def test_header_tells_complete_story(self):
        """Test that file header tells the complete problem→solution story."""
        incomplete_stories = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract header (first docstring + comments)
            lines = content.split('\n')
            header_lines = []
            
            in_docstring = False
            for line in lines[:20]:  # First 20 lines max
                if '"""' in line:
                    in_docstring = not in_docstring
                    header_lines.append(line)
                elif in_docstring or line.strip().startswith('#'):
                    header_lines.append(line)
                elif line.strip() and not line.startswith(('import', 'from')):
                    break  # Stop at first real code
            
            header_text = '\n'.join(header_lines).lower()
            framework = self.validator.extract_framework_name(example_path)
            
            # Story elements that should be in header
            has_problem = any(word in header_text for word in 
                            ["problem", "issue", "challenge", "fails", "error"])
            has_solution = any(word in header_text for word in 
                             ["adri", "protection", "solution", "prevents", "solves"])
            has_value = any(word in header_text for word in 
                          ["quality", "reliable", "validation", "benefit"])
            has_context = any(word in header_text for word in 
                            ["customer", "business", "production", "real-world"])
            
            story_elements = [has_problem, has_solution, has_value, has_context]
            story_score = sum(story_elements)
            
            if story_score < 3:
                missing = []
                if not has_problem: missing.append("problem description")
                if not has_solution: missing.append("ADRI solution")
                if not has_value: missing.append("value proposition")
                if not has_context: missing.append("business context")
                
                incomplete_stories.append(
                    f"{framework}: Incomplete story in header (missing: {', '.join(missing)})"
                )
            else:
                print(f"✅ {framework.upper()}: Complete story in header ({story_score}/4 elements)")
        
        if incomplete_stories:
            failure_msg = "\n".join([f"   • {story}" for story in incomplete_stories])
            pytest.fail(f"Headers don't tell complete story:\n{failure_msg}")
    
    def test_framework_authenticity_immediate(self):
        """Test that framework usage looks authentic in first glance."""
        inauthentic_usage = []
        
        for example_path in self.examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            framework = self.validator.extract_framework_name(example_path)
            
            # Get first 30 lines (what's visible in first glance)
            first_30_lines = '\n'.join(content.split('\n')[:30])
            
            # Framework-specific authenticity patterns
            authenticity_patterns = {
                "langchain": ["from langchain", "ChatOpenAI", "LLMChain"],
                "crewai": ["from crewai", "Agent", "Crew", "Task"],
                "autogen": ["import autogen", "ConversableAgent", "GroupChat"],
                "llamaindex": ["from llama_index", "VectorStoreIndex", "ServiceContext"],
                "haystack": ["from haystack", "Pipeline", "Component"],
                "langgraph": ["from langgraph", "StateGraph", "MessageState"],
                "semantic-kernel": ["semantic_kernel", "Kernel", "Function"]
            }
            
            expected_patterns = authenticity_patterns.get(framework, [])
            found_patterns = [p for p in expected_patterns if p in first_30_lines]
            
            if len(found_patterns) < 2:
                inauthentic_usage.append(
                    f"{framework}: Doesn't look like authentic {framework} usage in first 30 lines"
                )
            else:
                print(f"✅ {framework.upper()}: Authentic usage immediately visible")
        
        if inauthentic_usage:
            failure_msg = "\n".join([f"   • {usage}" for usage in inauthentic_usage])
            pytest.fail(f"Examples don't look authentically framework-specific:\n{failure_msg}")


class TestFirstImpressionMetrics:
    """Test measurable first impression metrics."""
    
    @classmethod
    def setup_class(cls):
        """Setup for metrics testing."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
    
    def test_overall_first_impression_score(self):
        """Calculate and validate overall first impression score."""
        print(f"\n📊 First Impression Score Assessment")
        print("-" * 50)
        
        total_score = 0
        framework_scores = {}
        
        for example_path in self.examples:
            framework = self.validator.extract_framework_name(example_path)
            
            # Calculate first impression score (0-100)
            score_components = {
                "problem_recognition": 0,
                "value_visibility": 0,
                "professional_appearance": 0,
                "business_realism": 0,
                "clear_entry": 0
            }
            
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Problem recognition (25 points)
            first_lines = '\n'.join(content.split('\n')[:10]).lower()
            if any(word in first_lines for word in 
                  ["problem", "issue", "validation", "failure", "error"]):
                score_components["problem_recognition"] = 25
            
            # Value visibility (25 points)
            header = content[:500].lower()
            value_words = ["adri", "protection", "prevents", "quality", "reliable"]
            if sum(1 for word in value_words if word in header) >= 2:
                score_components["value_visibility"] = 25
            
            # Professional appearance (20 points)
            if ("#!/usr/bin/env python3" in content and 
                '"""' in content and 
                "if __name__" in content):
                score_components["professional_appearance"] = 20
            
            # Business realism (15 points)
            business_words = ["customer", "business", "service", "analysis"]
            if sum(1 for word in business_words if word.lower() in content.lower()) >= 2:
                score_components["business_realism"] = 15
            
            # Clear entry point (15 points)
            if content.startswith("#!") and "def main" in content:
                score_components["clear_entry"] = 15
            
            framework_score = sum(score_components.values())
            framework_scores[framework] = framework_score
            total_score += framework_score
            
            status = "🎯 EXCELLENT" if framework_score >= 80 else \
                    "✅ GOOD" if framework_score >= 70 else \
                    "⚠️ NEEDS WORK" if framework_score >= 60 else \
                    "❌ POOR"
            
            print(f"{framework.upper():15} {framework_score:3d}/100 - {status}")
        
        # Calculate overall average
        avg_score = total_score / len(self.examples) if self.examples else 0
        
        print(f"\n🎯 Overall First Impression: {avg_score:.1f}/100")
        
        # Validate acceptable threshold
        if avg_score >= 75.0:
            print("🎉 First impressions ready for AI engineers!")
        elif avg_score >= 65.0:
            print("✅ Good first impressions, minor improvements possible")
        else:
            print("⚠️ First impressions need significant improvement")
        
        # Assert minimum threshold
        assert avg_score >= 60.0, \
            f"First impression score too low: {avg_score:.1f}/100 (need ≥60)"
        
        return framework_scores


if __name__ == "__main__":
    # Run first impression tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
