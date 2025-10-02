"""Tests for core exception hierarchy."""

import pytest

from src.adri.core.exceptions import (
    ADRIError,
    ConfigurationError,
    ProjectNotFoundError,
    EnvironmentError,
    DataLoadingError,
    DataFormatError,
    DataValidationError,
    StandardError,
    StandardNotFoundError,
    StandardValidationError,
    StandardGenerationError,
    AssessmentError,
    DimensionAssessmentError,
    ValidationRuleError,
    CommandError,
    CommandNotFoundError,
    CommandExecutionError,
    ArgumentValidationError,
    RegistryError,
    ComponentNotFoundError,
    ComponentRegistrationError,
    FileOperationError,
    FileNotFoundError,
    FilePermissionError,
    SerializationError,
    PerformanceError,
    ResourceExhaustedError,
    TimeoutError,
    chain_exception,
    format_validation_errors
)


class TestADRIError:
    """Test base ADRI exception class."""

    def test_basic_error_creation(self):
        """Test creating a basic ADRI error."""
        error = ADRIError("Test message")
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.details is None

    def test_error_with_details(self):
        """Test creating an ADRI error with details."""
        error = ADRIError("Test message", "Additional details")
        assert str(error) == "Test message: Additional details"
        assert error.message == "Test message"
        assert error.details == "Additional details"

    def test_inheritance_from_exception(self):
        """Test that ADRIError inherits from Exception."""
        error = ADRIError("Test")
        assert isinstance(error, Exception)


class TestConfigurationErrors:
    """Test configuration-related exceptions."""

    def test_configuration_error(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Config problem")
        assert isinstance(error, ADRIError)
        assert str(error) == "Config problem"

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError creation."""
        error = ProjectNotFoundError("Project not found")
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Project not found"

    def test_environment_error(self):
        """Test EnvironmentError creation."""
        error = EnvironmentError("Env problem", "Missing dev environment")
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Env problem: Missing dev environment"


class TestDataErrors:
    """Test data-related exceptions."""

    def test_data_loading_error(self):
        """Test DataLoadingError creation."""
        error = DataLoadingError("Failed to load")
        assert isinstance(error, ADRIError)
        assert str(error) == "Failed to load"

    def test_data_format_error(self):
        """Test DataFormatError creation."""
        error = DataFormatError("Invalid format")
        assert isinstance(error, DataLoadingError)
        assert str(error) == "Invalid format"

    def test_data_validation_error(self):
        """Test DataValidationError creation."""
        error = DataValidationError("Validation failed")
        assert isinstance(error, ADRIError)
        assert str(error) == "Validation failed"


class TestStandardErrors:
    """Test standard-related exceptions."""

    def test_standard_error(self):
        """Test StandardError creation."""
        error = StandardError("Standard problem")
        assert isinstance(error, ADRIError)
        assert str(error) == "Standard problem"

    def test_standard_not_found_error(self):
        """Test StandardNotFoundError creation."""
        error = StandardNotFoundError("Standard missing")
        assert isinstance(error, StandardError)
        assert str(error) == "Standard missing"

    def test_standard_validation_error(self):
        """Test StandardValidationError creation."""
        error = StandardValidationError("Invalid standard")
        assert isinstance(error, StandardError)
        assert str(error) == "Invalid standard"

    def test_standard_generation_error(self):
        """Test StandardGenerationError creation."""
        error = StandardGenerationError("Generation failed")
        assert isinstance(error, StandardError)
        assert str(error) == "Generation failed"


class TestAssessmentErrors:
    """Test assessment-related exceptions."""

    def test_assessment_error(self):
        """Test AssessmentError creation."""
        error = AssessmentError("Assessment failed")
        assert isinstance(error, ADRIError)
        assert str(error) == "Assessment failed"

    def test_dimension_assessment_error(self):
        """Test DimensionAssessmentError creation."""
        error = DimensionAssessmentError("validity", "Score calculation failed")
        assert isinstance(error, AssessmentError)
        assert error.dimension_name == "validity"
        assert "Assessment failed for dimension 'validity'" in str(error)
        assert "Score calculation failed" in str(error)

    def test_dimension_assessment_error_with_details(self):
        """Test DimensionAssessmentError with details."""
        error = DimensionAssessmentError(
            "completeness",
            "Missing data",
            "50% of required fields are empty"
        )
        assert error.dimension_name == "completeness"
        assert "Assessment failed for dimension 'completeness'" in str(error)
        assert "Missing data" in str(error)
        assert "50% of required fields are empty" in str(error)

    def test_validation_rule_error(self):
        """Test ValidationRuleError creation."""
        error = ValidationRuleError("email_format", "email", "Invalid format")
        assert isinstance(error, AssessmentError)
        assert error.rule_name == "email_format"
        assert error.field_name == "email"
        assert "Validation rule 'email_format' failed for field 'email'" in str(error)

    def test_validation_rule_error_without_field(self):
        """Test ValidationRuleError without field name."""
        error = ValidationRuleError("uniqueness", message="Duplicate values found")
        assert error.rule_name == "uniqueness"
        assert error.field_name is None
        assert "Validation rule 'uniqueness' failed" in str(error)
        assert "Duplicate values found" in str(error)


class TestCommandErrors:
    """Test CLI command-related exceptions."""

    def test_command_error(self):
        """Test CommandError creation."""
        error = CommandError("Command failed")
        assert isinstance(error, ADRIError)
        assert str(error) == "Command failed"

    def test_command_not_found_error(self):
        """Test CommandNotFoundError creation."""
        error = CommandNotFoundError("Command not found")
        assert isinstance(error, CommandError)
        assert str(error) == "Command not found"

    def test_command_execution_error(self):
        """Test CommandExecutionError creation."""
        error = CommandExecutionError("assess", 1, "Invalid arguments")
        assert isinstance(error, CommandError)
        assert error.command_name == "assess"
        assert error.exit_code == 1
        assert "Command 'assess' failed with exit code 1" in str(error)
        assert "Invalid arguments" in str(error)

    def test_command_execution_error_without_message(self):
        """Test CommandExecutionError without message."""
        error = CommandExecutionError("setup", 2)
        assert error.command_name == "setup"
        assert error.exit_code == 2
        assert "Command 'setup' failed with exit code 2" in str(error)

    def test_argument_validation_error(self):
        """Test ArgumentValidationError creation."""
        error = ArgumentValidationError("Missing required argument")
        assert isinstance(error, CommandError)
        assert str(error) == "Missing required argument"


class TestRegistryErrors:
    """Test component registry-related exceptions."""

    def test_registry_error(self):
        """Test RegistryError creation."""
        error = RegistryError("Registry problem")
        assert isinstance(error, ADRIError)
        assert str(error) == "Registry problem"

    def test_component_not_found_error(self):
        """Test ComponentNotFoundError creation."""
        error = ComponentNotFoundError("dimension_assessor", "validity")
        assert isinstance(error, RegistryError)
        assert error.component_type == "dimension_assessor"
        assert error.component_name == "validity"
        assert "dimension_assessor 'validity' not found in registry" in str(error)

    def test_component_not_found_error_with_details(self):
        """Test ComponentNotFoundError with details."""
        error = ComponentNotFoundError(
            "command",
            "unknown",
            "Available commands: setup, assess, generate"
        )
        assert error.component_type == "command"
        assert error.component_name == "unknown"
        assert "command 'unknown' not found in registry" in str(error)
        assert "Available commands: setup, assess, generate" in str(error)

    def test_component_registration_error(self):
        """Test ComponentRegistrationError creation."""
        error = ComponentRegistrationError("Registration failed")
        assert isinstance(error, RegistryError)
        assert str(error) == "Registration failed"


class TestFileErrors:
    """Test file operation-related exceptions."""

    def test_file_operation_error(self):
        """Test FileOperationError creation."""
        error = FileOperationError("File operation failed")
        assert isinstance(error, ADRIError)
        assert str(error) == "File operation failed"

    def test_file_not_found_error(self):
        """Test FileNotFoundError creation."""
        error = FileNotFoundError("File missing")
        assert isinstance(error, FileOperationError)
        assert str(error) == "File missing"

    def test_file_permission_error(self):
        """Test FilePermissionError creation."""
        error = FilePermissionError("Permission denied")
        assert isinstance(error, FileOperationError)
        assert str(error) == "Permission denied"


class TestResourceErrors:
    """Test resource and performance-related exceptions."""

    def test_serialization_error(self):
        """Test SerializationError creation."""
        error = SerializationError("Serialization failed")
        assert isinstance(error, ADRIError)
        assert str(error) == "Serialization failed"

    def test_performance_error(self):
        """Test PerformanceError creation."""
        error = PerformanceError("Too slow")
        assert isinstance(error, ADRIError)
        assert str(error) == "Too slow"

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError creation."""
        error = ResourceExhaustedError("Out of memory")
        assert isinstance(error, ADRIError)
        assert str(error) == "Out of memory"

    def test_timeout_error(self):
        """Test TimeoutError creation."""
        error = TimeoutError("Operation timed out")
        assert isinstance(error, ADRIError)
        assert str(error) == "Operation timed out"


class TestErrorUtilities:
    """Test error utility functions."""

    def test_chain_exception(self):
        """Test exception chaining utility."""
        original = ValueError("Original error")
        new_error = ADRIError("New error")

        chained = chain_exception(new_error, original)

        assert chained is new_error
        assert chained.__cause__ is original

    def test_format_validation_errors_empty(self):
        """Test formatting empty validation errors."""
        result = format_validation_errors([])
        assert result == "No validation errors"

    def test_format_validation_errors_single(self):
        """Test formatting single validation error."""
        errors = ["Field 'email' is invalid"]
        result = format_validation_errors(errors)
        assert result == "Validation error: Field 'email' is invalid"

    def test_format_validation_errors_multiple(self):
        """Test formatting multiple validation errors."""
        errors = [
            "Field 'email' is invalid",
            "Field 'age' is missing",
            "Field 'phone' has wrong format"
        ]
        result = format_validation_errors(errors)

        assert result.startswith("Validation errors:")
        assert "- Field 'email' is invalid" in result
        assert "- Field 'age' is missing" in result
        assert "- Field 'phone' has wrong format" in result


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_custom_exceptions_inherit_from_adri_error(self):
        """Test that all custom exceptions inherit from ADRIError."""
        exception_classes = [
            ConfigurationError,
            DataLoadingError,
            StandardError,
            AssessmentError,
            CommandError,
            RegistryError,
            FileOperationError,
            SerializationError,
            PerformanceError,
            ResourceExhaustedError,
            TimeoutError
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, ADRIError)

    def test_specific_exceptions_inherit_from_base_categories(self):
        """Test that specific exceptions inherit from their base categories."""
        inheritance_tests = [
            (ProjectNotFoundError, ConfigurationError),
            (EnvironmentError, ConfigurationError),
            (DataFormatError, DataLoadingError),
            (StandardNotFoundError, StandardError),
            (StandardValidationError, StandardError),
            (StandardGenerationError, StandardError),
            (DimensionAssessmentError, AssessmentError),
            (ValidationRuleError, AssessmentError),
            (CommandNotFoundError, CommandError),
            (CommandExecutionError, CommandError),
            (ArgumentValidationError, CommandError),
            (ComponentNotFoundError, RegistryError),
            (ComponentRegistrationError, RegistryError),
            (FileNotFoundError, FileOperationError),
            (FilePermissionError, FileOperationError),
        ]

        for specific, base in inheritance_tests:
            assert issubclass(specific, base)

    def test_exception_instantiation_and_raising(self):
        """Test that exceptions can be instantiated and raised properly."""
        test_exceptions = [
            ADRIError("test"),
            ConfigurationError("test"),
            DataLoadingError("test"),
            StandardError("test"),
            AssessmentError("test"),
            CommandError("test"),
            RegistryError("test"),
            FileOperationError("test"),
            SerializationError("test"),
        ]

        for exc in test_exceptions:
            # Should be able to raise and catch
            with pytest.raises(type(exc)):
                raise exc

            # Should be catchable as ADRIError
            with pytest.raises(ADRIError):
                raise exc

            # Should be catchable as Exception
            with pytest.raises(Exception):
                raise exc


if __name__ == "__main__":
    pytest.main([__file__])
