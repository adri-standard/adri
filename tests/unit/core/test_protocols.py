"""Tests for core protocols and interfaces."""

import pytest
from typing import Any, Dict

from src.adri.core.protocols import ValidationRule, DimensionAssessor, Command
from src.adri.core.exceptions import ValidationRuleError


class MockValidationRule:
    """Mock validation rule for testing protocol compliance."""

    def __init__(self, always_valid: bool = True, error_message: str = "Validation failed"):
        self.always_valid = always_valid
        self.error_message = error_message

    def validate(self, value: Any, context: Dict[str, Any]) -> bool:
        return self.always_valid

    def get_error_message(self, value: Any) -> str:
        return f"{self.error_message}: {value}"


class MockDimensionAssessor(DimensionAssessor):
    """Mock dimension assessor for testing."""

    def __init__(self, dimension_name: str = "test", score: float = 15.0):
        self.dimension_name = dimension_name
        self.score = score

    def assess(self, data: Any, requirements: Dict[str, Any]) -> float:
        return self.score

    def get_dimension_name(self) -> str:
        return self.dimension_name


class MockCommand(Command):
    """Mock command for testing."""

    def __init__(self, name: str = "test", exit_code: int = 0):
        self.name = name
        self.exit_code = exit_code

    def execute(self, args: Dict[str, Any]) -> int:
        return self.exit_code

    def get_description(self) -> str:
        return f"Test command: {self.name}"

    def get_name(self) -> str:
        return self.name


class TestValidationRule:
    """Test ValidationRule protocol compliance."""

    def test_mock_validation_rule_implements_protocol(self):
        """Test that mock validation rule implements the protocol."""
        rule = MockValidationRule()

        # Should be able to call protocol methods
        assert rule.validate("test", {}) is True
        assert rule.get_error_message("test") == "Validation failed: test"

    def test_validation_rule_with_failure(self):
        """Test validation rule that fails."""
        rule = MockValidationRule(always_valid=False, error_message="Custom error")

        assert rule.validate("test", {}) is False
        assert rule.get_error_message("test") == "Custom error: test"

    def test_validation_rule_with_context(self):
        """Test validation rule with context."""
        rule = MockValidationRule()
        context = {"field_name": "email", "requirements": {"type": "string"}}

        # Context should be passed through
        assert rule.validate("test@example.com", context) is True


class TestDimensionAssessor:
    """Test DimensionAssessor abstract base class."""

    def test_mock_assessor_implements_abstract_methods(self):
        """Test that mock assessor implements required abstract methods."""
        assessor = MockDimensionAssessor("validity", 18.5)

        assert assessor.assess({}, {}) == 18.5
        assert assessor.get_dimension_name() == "validity"

    def test_get_weight_default(self):
        """Test default weight extraction from requirements."""
        assessor = MockDimensionAssessor()

        # Default weight should be 1.0
        assert assessor.get_weight({}) == 1.0

        # Should extract weight from requirements
        requirements = {"weight": 2.5}
        assert assessor.get_weight(requirements) == 2.5

    def test_get_minimum_score_default(self):
        """Test default minimum score extraction from requirements."""
        assessor = MockDimensionAssessor()

        # Default minimum should be 15.0
        assert assessor.get_minimum_score({}) == 15.0

        # Should extract minimum from requirements
        requirements = {"minimum_score": 12.0}
        assert assessor.get_minimum_score(requirements) == 12.0

    def test_cannot_instantiate_abstract_base(self):
        """Test that DimensionAssessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DimensionAssessor()


class TestCommand:
    """Test Command abstract base class."""

    def test_mock_command_implements_abstract_methods(self):
        """Test that mock command implements required abstract methods."""
        command = MockCommand("test-cmd", 42)

        assert command.execute({}) == 42
        assert command.get_description() == "Test command: test-cmd"
        assert command.get_name() == "test-cmd"

    def test_get_name_from_class_name(self):
        """Test automatic name generation from class name."""

        class SetupCommand(Command):
            def execute(self, args: Dict[str, Any]) -> int:
                return 0

            def get_description(self) -> str:
                return "Setup command"

        command = SetupCommand()
        assert command.get_name() == "setup"

    def test_get_name_with_command_suffix(self):
        """Test name generation strips 'Command' suffix."""

        class GenerateContractCommand(Command):
            def execute(self, args: Dict[str, Any]) -> int:
                return 0

            def get_description(self) -> str:
                return "Generate standard command"

        command = GenerateContractCommand()
        assert command.get_name() == "generatecontract"

    def test_get_name_with_underscores(self):
        """Test name generation converts underscores to hyphens."""

        class List_AssessmentsCommand(Command):
            def execute(self, args: Dict[str, Any]) -> int:
                return 0

            def get_description(self) -> str:
                return "List assessments command"

        command = List_AssessmentsCommand()
        assert command.get_name() == "list-assessments"

    def test_cannot_instantiate_abstract_base(self):
        """Test that Command cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Command()

    def test_command_with_custom_name(self):
        """Test command that overrides get_name."""

        class CustomCommand(Command):
            def execute(self, args: Dict[str, Any]) -> int:
                return 0

            def get_description(self) -> str:
                return "Custom command"

            def get_name(self) -> str:
                return "custom-name"

        command = CustomCommand()
        assert command.get_name() == "custom-name"

    def test_command_execution_with_args(self):
        """Test command execution with arguments."""

        class EchoCommand(Command):
            def execute(self, args: Dict[str, Any]) -> int:
                self.last_args = args
                return 0 if args.get('success', True) else 1

            def get_description(self) -> str:
                return "Echo command"

        command = EchoCommand()

        # Test successful execution
        assert command.execute({'message': 'hello', 'success': True}) == 0
        assert command.last_args == {'message': 'hello', 'success': True}

        # Test failed execution
        assert command.execute({'success': False}) == 1


class TestProtocolUsage:
    """Test protocol usage patterns."""

    def test_validation_rule_type_checking(self):
        """Test that validation rule protocol works with type checking."""
        def process_rule(rule: ValidationRule, value: Any) -> bool:
            return rule.validate(value, {})

        mock_rule = MockValidationRule(always_valid=True)
        assert process_rule(mock_rule, "test") is True

    def test_dimension_assessor_type_checking(self):
        """Test that dimension assessor protocol works with type checking."""
        def process_assessor(assessor: DimensionAssessor, data: Any) -> str:
            score = assessor.assess(data, {})
            return f"{assessor.get_dimension_name()}: {score}"

        mock_assessor = MockDimensionAssessor("completeness", 16.7)
        result = process_assessor(mock_assessor, {})
        assert result == "completeness: 16.7"

    def test_command_type_checking(self):
        """Test that command protocol works with type checking."""
        def process_command(command: Command, args: Dict[str, Any]) -> str:
            exit_code = command.execute(args)
            return f"{command.get_name()}: {exit_code} - {command.get_description()}"

        mock_command = MockCommand("test", 0)
        result = process_command(mock_command, {})
        assert result == "test: 0 - Test command: test"


if __name__ == "__main__":
    pytest.main([__file__])
