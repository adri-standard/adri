#!/usr/bin/env python3
"""
Demo Credibility Tests - Main validation for ADRI demo experiences

Tests that demos are credible, relatable, and valuable for AI engineers.
Focuses on user experience rather than technical implementation details.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.demo_validation.demo_validator import DemoValidator


class TestDemoCredibility:
    """Test demo credibility from AI engineer perspective."""
    
    @classmethod
    def setup_class(cls):
        """Setup demo validator for all tests."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
        
        print(f"\n🎭 Testing Demo Credibility for {len(cls.examples)} examples")
        print("=" * 60)
        
        if not cls.examples:
            pytest.skip("No examples found to validate")
    
    def test_all_examples_show_real_problems(self):
        """Test that all examples demonstrate real, recognizable problems."""
        failed_examples = []
        
        for example_path in self.examples:
            is_valid, reason = self.validator.validate_problem_recognition(example_path)
            
            if not is_valid:
                failed_examples.append(f"{example_path.name}: {reason}")
            else:
                framework = self.validator.extract_framework_name(example_path)
                print(f"✅ {framework.upper()}: {reason}")
        
        if failed_examples:
            failure_msg = "\n".join([f"   • {fail}" for fail in failed_examples])
            pytest.fail(f"Examples don't show real problems:\n{failure_msg}")
    
    def test_all_examples_have_credible_solutions(self):
        """Test that ADRI protection feels natural and credible."""
        failed_examples = []
        
        for example_path in self.examples:
            is_credible, reason = self.validator.validate_solution_credibility(example_path)
            
            if not is_credible:
                failed_examples.append(f"{example_path.name}: {reason}")
            else:
                framework = self.validator.extract_framework_name(example_path)
                print(f"✅ {framework.upper()}: {reason}")
        
        if failed_examples:
            failure_msg = "\n".join([f"   • {fail}" for fail in failed_examples])
            pytest.fail(f"Examples have credibility issues:\n{failure_msg}")
    
    def test_all_examples_have_clear_value(self):
        """Test that value proposition is immediately clear."""
        failed_examples = []
        
        for example_path in self.examples:
            is_clear, reason = self.validator.validate_value_clarity(example_path)
            
            if not is_clear:
                failed_examples.append(f"{example_path.name}: {reason}")
            else:
                framework = self.validator.extract_framework_name(example_path)
                print(f"✅ {framework.upper()}: {reason}")
        
        if failed_examples:
            failure_msg = "\n".join([f"   • {fail}" for fail in failed_examples])
            pytest.fail(f"Examples have unclear value propositions:\n{failure_msg}")
    
    def test_all_examples_feel_natural(self):
        """Test that examples feel like natural framework usage."""
        failed_examples = []
        
        for example_path in self.examples:
            is_natural, reason = self.validator.validate_workflow_naturalness(example_path)
            
            if not is_natural:
                failed_examples.append(f"{example_path.name}: {reason}")
            else:
                framework = self.validator.extract_framework_name(example_path)
                print(f"✅ {framework.upper()}: {reason}")
        
        if failed_examples:
            failure_msg = "\n".join([f"   • {fail}" for fail in failed_examples])
            pytest.fail(f"Examples feel unnatural:\n{failure_msg}")
    
    def test_all_examples_execute_properly(self):
        """Test that examples execute without crashing."""
        failed_examples = []
        
        for example_path in self.examples:
            executed_ok, reason = self.validator.test_example_execution(example_path)
            
            if not executed_ok:
                failed_examples.append(f"{example_path.name}: {reason}")
            else:
                framework = self.validator.extract_framework_name(example_path)
                print(f"✅ {framework.upper()}: {reason}")
        
        if failed_examples:
            failure_msg = "\n".join([f"   • {fail}" for fail in failed_examples])
            pytest.fail(f"Examples have execution issues:\n{failure_msg}")
    
    def test_setup_tool_integration(self):
        """Test that setup tool exists and looks professional."""
        is_integrated, reason = self.validator.validate_setup_tool_integration()
        
        if is_integrated:
            print(f"✅ Setup Tool: {reason}")
        else:
            pytest.fail(f"Setup tool integration issue: {reason}")
    
    def test_overall_demo_credibility_score(self):
        """Test overall credibility across all examples."""
        all_results = []
        credible_frameworks = []
        issues_found = []
        
        print(f"\n📊 Overall Demo Credibility Assessment:")
        print("-" * 50)
        
        for example_path in self.examples:
            results = self.validator.validate_demo_credibility(example_path)
            all_results.append(results)
            
            framework = results["framework"]
            score = results["overall_score"]
            credible = results["credible"]
            
            status = "✅ CREDIBLE" if credible else "❌ NEEDS WORK"
            print(f"{framework.upper():15} {score:5.1f}% - {status}")
            
            if credible:
                credible_frameworks.append(framework)
            else:
                # Collect specific issues
                for validation_name, validation_result in results["validations"].items():
                    if not validation_result["passed"]:
                        issue = f"{framework}: {validation_name} - {validation_result['reason']}"
                        issues_found.append(issue)
        
        # Calculate overall metrics
        total_examples = len(all_results)
        credible_count = len(credible_frameworks)
        overall_credibility = (credible_count / total_examples) * 100 if total_examples > 0 else 0
        
        print(f"\n🎯 Summary:")
        print(f"   • Total examples: {total_examples}")
        print(f"   • Credible examples: {credible_count}")
        print(f"   • Overall credibility: {overall_credibility:.1f}%")
        
        # Success criteria: 80% of examples should be credible
        if overall_credibility >= 80.0:
            print(f"🎉 Demo experiences ready for AI engineers!")
        else:
            print(f"🔧 Demo experiences need improvement")
            if issues_found:
                print(f"\n⚠️ Issues to address:")
                for issue in issues_found[:5]:  # Show top 5 issues
                    print(f"   • {issue}")
                if len(issues_found) > 5:
                    print(f"   ... and {len(issues_found) - 5} more issues")
        
        # Assert credibility threshold
        assert overall_credibility >= 70.0, \
            f"Demo credibility too low: {overall_credibility:.1f}% (need ≥70%)"


class TestFrameworkSpecificCredibility:
    """Test framework-specific credibility concerns."""
    
    @classmethod
    def setup_class(cls):
        """Setup validator for framework-specific tests."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
    
    def test_langchain_demonstrates_conversation_issues(self):
        """Test that LangChain example shows real conversation validation issues."""
        langchain_examples = [ex for ex in self.examples 
                             if self.validator.extract_framework_name(ex) == "langchain"]
        
        if not langchain_examples:
            pytest.skip("No LangChain examples found")
        
        for example_path in langchain_examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should demonstrate real LangChain problems
            langchain_problems = [
                "customer service", "conversation", "chat", "response",
                "validation", "data quality", "llm"
            ]
            
            found_problems = [p for p in langchain_problems if p.lower() in content.lower()]
            
            assert len(found_problems) >= 3, \
                f"LangChain example should show realistic conversation problems, found: {found_problems}"
    
    def test_autogen_demonstrates_coordination_issues(self):
        """Test that AutoGen example shows real multi-agent coordination issues."""
        autogen_examples = [ex for ex in self.examples 
                           if self.validator.extract_framework_name(ex) == "autogen"]
        
        if not autogen_examples:
            pytest.skip("No AutoGen examples found")
        
        for example_path in autogen_examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should demonstrate real AutoGen problems
            autogen_problems = [
                "agent", "collaboration", "research", "coordination",
                "multi-agent", "conversation", "validation"
            ]
            
            found_problems = [p for p in autogen_problems if p.lower() in content.lower()]
            
            assert len(found_problems) >= 3, \
                f"AutoGen example should show realistic coordination problems, found: {found_problems}"
    
    def test_crewai_demonstrates_workflow_issues(self):
        """Test that CrewAI example shows real workflow coordination issues."""
        crewai_examples = [ex for ex in self.examples 
                          if self.validator.extract_framework_name(ex) == "crewai"]
        
        if not crewai_examples:
            pytest.skip("No CrewAI examples found")
        
        for example_path in crewai_examples:
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should demonstrate real CrewAI problems
            crewai_problems = [
                "crew", "agent", "task", "business", "analysis",
                "workflow", "coordination", "validation"
            ]
            
            found_problems = [p for p in crewai_problems if p.lower() in content.lower()]
            
            assert len(found_problems) >= 3, \
                f"CrewAI example should show realistic workflow problems, found: {found_problems}"


@pytest.mark.integration
class TestDemoUserExperience:
    """Test the actual user experience of running demos."""
    
    @classmethod
    def setup_class(cls):
        """Setup for user experience tests."""
        cls.validator = DemoValidator()
        cls.examples = cls.validator.discover_examples()
    
    def test_demo_setup_to_execution_workflow(self):
        """Test the complete workflow an AI engineer would experience."""
        # 1. Setup tool should exist and be runnable
        is_integrated, reason = self.validator.validate_setup_tool_integration()
        assert is_integrated, f"Setup tool issue: {reason}"
        
        # 2. Examples should exist and be discoverable
        assert len(self.examples) >= 5, \
            f"Need at least 5 examples for credible demos, found {len(self.examples)}"
        
        # 3. Each example should execute without crashes
        execution_failures = []
        for example_path in self.examples:
            executed_ok, reason = self.validator.test_example_execution(example_path, timeout=15)
            if not executed_ok:
                execution_failures.append(f"{example_path.name}: {reason}")
        
        if execution_failures:
            failure_msg = "\n".join([f"   • {fail}" for fail in execution_failures])
            pytest.fail(f"Demo execution workflow broken:\n{failure_msg}")
        
        print(f"✅ Complete demo workflow validated for {len(self.examples)} frameworks")
    
    def test_demo_problem_solution_clarity(self):
        """Test that problem → solution flow is clear in each demo."""
        unclear_demos = []
        
        for example_path in self.examples:
            # Check for clear problem → solution narrative
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have problem indicators early in file
            first_third = content[:len(content)//3]
            problem_words = ["problem", "issue", "failure", "error", "validation"]
            has_early_problem = any(word in first_third.lower() for word in problem_words)
            
            # Should have solution indicators with ADRI
            solution_words = ["ADRI", "@adri_protected", "protection", "solution"]
            has_solution = any(word in content for word in solution_words)
            
            if not (has_early_problem and has_solution):
                framework = self.validator.extract_framework_name(example_path)
                unclear_demos.append(f"{framework}: Missing clear problem→solution flow")
        
        if unclear_demos:
            failure_msg = "\n".join([f"   • {demo}" for demo in unclear_demos])
            pytest.fail(f"Demos lack clear problem→solution narrative:\n{failure_msg}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
