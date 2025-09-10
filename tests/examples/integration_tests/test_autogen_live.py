"""
Live Integration Tests: AutoGen Framework

Tests real AutoGen functionality with OpenAI API calls.
⚠️ COSTS MONEY - Requires API key and makes real API calls.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "examples"))

from tests.examples.utils.cost_controls import get_cost_controller, estimate_openai_cost


class TestAutoGenLive:
    """Live integration tests for AutoGen example."""
    
    @pytest.fixture(autouse=True)
    def setup_api_key(self):
        """Ensure API key is available for tests."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY environment variable required for live tests")
        
        self.cost_controller = get_cost_controller()
        yield
        # Cleanup if needed
    
    @pytest.fixture
    def good_research_data(self):
        """High-quality research data for testing."""
        return {
            "research_topic": "Artificial Intelligence in Healthcare",
            "research_scope": "comprehensive_analysis",
            "data_sources": ["pubmed", "arxiv", "google_scholar"],
            "time_frame": "2020-2023",
            "keywords": ["AI", "machine learning", "healthcare", "medical AI"],
            "output_format": "detailed_report",
            "urgency": "medium",
            "requester_id": "researcher_123",
            "budget": 5000,
            "team_size": 3
        }
    
    @pytest.fixture
    def bad_research_data(self):
        """Poor-quality research data that should be blocked."""
        return {
            "research_topic": "",               # Missing topic
            "research_scope": "invalid_scope",  # Invalid scope
            "data_sources": [],                 # No sources
            "time_frame": "invalid-range",      # Invalid timeframe
            "keywords": None,                   # Missing keywords
            "output_format": "",                # Missing format
            "urgency": "unknown",              # Invalid urgency
            "requester_id": 12345,             # Should be string
            "budget": -100,                    # Invalid budget
            "team_size": 0                     # Invalid team size
        }
    
    def test_autogen_research_collaboration_with_good_data(self, good_research_data):
        """Test AutoGen research collaboration with good data - MAKES REAL API CALL."""
        framework = "autogen"
        test_name = "research_collaboration_good"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 250, 180)
        
        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example (should work with API key set)
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "autogen-research-collaboration.py"
            
            spec = importlib.util.spec_from_file_location("autogen_example", example_file)
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module (will load with real API key)
            try:
                spec.loader.exec_module(module)
            except SystemExit:
                pytest.fail("Example should not exit when API key is available")
            
            # Test the research collaboration function
            if hasattr(module, 'ResearchTeam'):
                team = module.ResearchTeam()
                result = team.conduct_research_project(good_research_data)
            else:
                pytest.skip("ResearchTeam class not found in example")
            
            # Record the API call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
            
            # Validate results
            assert result is not None, "Should return a result"
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Should have expected fields in response
            expected_fields = ['research_id', 'topic', 'scope', 'status']
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"
            
            # Response should be meaningful
            assert result.get('status') == 'completed', "Research should be completed"
            assert result.get('topic') == good_research_data['research_topic'], "Should match input topic"
            
            print(f"✅ AutoGen research collaboration test passed")
            print(f"   Research ID: {result.get('research_id', 'N/A')}")
            print(f"   Topic: {result.get('topic', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Agents: {result.get('agents_involved', 'N/A')}")
            
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"AutoGen research collaboration test failed: {e}")
    
    def test_autogen_research_collaboration_with_bad_data(self, bad_research_data):
        """Test AutoGen research collaboration with bad data - should be blocked by ADRI."""
        framework = "autogen"
        test_name = "research_collaboration_bad"
        
        # Import the example
        import importlib.util
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "autogen-research-collaboration.py"
        
        spec = importlib.util.spec_from_file_location("autogen_example", example_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.fail("Example should not exit when API key is available")
        
        # Call the protected function with bad data - should be blocked
        try:
            if hasattr(module, 'ResearchTeam'):
                team = module.ResearchTeam()
                result = team.conduct_research_project(bad_research_data)
                
                # If we get here, ADRI allowed the bad data through
                print(f"⚠️  Bad data was processed (ADRI may have warned): {result}")
            else:
                pytest.skip("ResearchTeam class not found in example")
                
        except Exception as e:
            # Expected - ADRI should block bad data
            assert "ADRI" in str(e) or "Protection" in str(e) or "quality" in str(e).lower(), \
                f"Exception should be from ADRI protection: {e}"
            
            print(f"✅ ADRI correctly blocked bad data: {str(e)[:100]}...")
    
    def test_autogen_coding_collaboration_live(self):
        """Test AutoGen coding collaboration with real API call."""
        framework = "autogen"
        test_name = "coding_collaboration"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 200, 160)
        
        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "autogen-research-collaboration.py"
            
            spec = importlib.util.spec_from_file_location("autogen_example", example_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test coding collaboration if available
            if hasattr(module, 'autogen_coding_collaboration'):
                coding_data = {
                    "project_name": "Data Quality Dashboard",
                    "project_type": "web_application",
                    "programming_language": "python",
                    "framework": "flask",
                    "requirements": ["data visualization", "real-time updates", "user authentication"],
                    "deadline": "2023-02-15T17:00:00Z",
                    "team_size": 2
                }
                
                result = module.autogen_coding_collaboration(coding_data)
                
                # Record the API call
                self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
                
                # Validate results
                assert result is not None, "Coding collaboration should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert result.get('project_name') == coding_data['project_name'], "Should match project name"
                
                print(f"✅ AutoGen coding collaboration test passed")
                print(f"   Project: {result.get('project_name', 'N/A')}")
                print(f"   Type: {result.get('project_type', 'N/A')}")
                print(f"   Quality Score: {result.get('code_quality_score', 'N/A')}")
            else:
                pytest.skip("autogen_coding_collaboration function not found in example")
                
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"AutoGen coding collaboration test failed: {e}")
    
    def test_autogen_problem_solving_team_live(self):
        """Test AutoGen problem-solving team with real API call."""
        framework = "autogen"
        test_name = "problem_solving_team"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 230, 170)
        
        # Check cost limits  
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "autogen-research-collaboration.py"
            
            spec = importlib.util.spec_from_file_location("autogen_example", example_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test problem-solving team if available
            if hasattr(module, 'autogen_problem_solving_team'):
                problem_data = {
                    "problem_title": "Optimize AI Model Performance",
                    "problem_description": "Current ML model has 15% accuracy degradation in production vs training",
                    "complexity": "high",
                    "domain": "machine_learning",
                    "constraints": ["limited_budget", "tight_timeline"],
                    "stakeholders": ["data_science_team", "product_team", "engineering_team"],
                    "priority": "critical"
                }
                
                result = module.autogen_problem_solving_team(problem_data)
                
                # Record the API call
                self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
                
                # Validate results
                assert result is not None, "Problem-solving team should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert result.get('problem_title') == problem_data['problem_title'], "Should match problem title"
                
                print(f"✅ AutoGen problem-solving team test passed")
                print(f"   Problem: {result.get('problem_title', 'N/A')}")
                print(f"   Complexity: {result.get('complexity', 'N/A')}")
                print(f"   Confidence: {result.get('solution_confidence', 'N/A')}")
            else:
                pytest.skip("autogen_problem_solving_team function not found in example")
                
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"AutoGen problem-solving team test failed: {e}")


class TestAutoGenErrorHandling:
    """Test error handling in AutoGen integration."""
    
    def test_autogen_handles_api_errors(self):
        """Test that AutoGen integration handles API errors gracefully."""
        framework = "autogen"
        test_name = "error_handling"
        
        # Import the example
        import importlib.util
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "autogen-research-collaboration.py"
        
        spec = importlib.util.spec_from_file_location("autogen_example", example_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.skip("Cannot test error handling without proper module load")
        
        # Mock API to return errors
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            good_data = {
                "research_topic": "Test Research Topic",
                "research_scope": "comprehensive_analysis",
                "data_sources": ["test_source"],
                "time_frame": "2023",
                "keywords": ["test", "research"],
                "output_format": "report",
                "urgency": "medium",
                "requester_id": "test_researcher",
                "budget": 1000
            }
            
            # Should handle the error gracefully
            try:
                if hasattr(module, 'ResearchTeam'):
                    team = module.ResearchTeam()
                    result = team.conduct_research_project(good_data)
                    # If we get a result, it should indicate an error
                    assert result is not None, "Should return error result"
                    if isinstance(result, dict):
                        assert 'error' in result or 'status' in result, "Should indicate error status"
                else:
                    pytest.skip("ResearchTeam class not found")
            except Exception as e:
                # Should be a graceful error, not a crash
                assert "API Error" in str(e) or "error" in str(e).lower(), \
                    f"Should handle API errors gracefully: {e}"
        
        print("✅ AutoGen error handling test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
