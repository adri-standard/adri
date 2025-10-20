"""Component registry system for the ADRI framework.

This module provides a centralized registry system for managing and discovering
framework components like dimension assessors, CLI commands, data loaders, and
other pluggable components.
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypeVar

from .exceptions import (
    ComponentNotFoundError,
    ComponentRegistrationError,
    RegistryError,
)
from .protocols import Command, DimensionAssessor

T = TypeVar("T")


class ComponentRegistry(ABC):
    """Abstract base class for component registries.

    Provides the fundamental interface that all specialized registries implement.
    """

    def __init__(self):
        """Initialize the component registry."""
        self._components: dict[str, Any] = {}
        self._aliases: dict[str, str] = {}

    @abstractmethod
    def get_component_type_name(self) -> str:
        """Get the name of the component type this registry manages.

        Returns:
            Component type name for error messages
        """

    def register(
        self, name: str, component: Any, aliases: list[str] | None = None
    ) -> None:
        """Register a component in the registry.

        Args:
            name: Primary name for the component
            component: The component instance or class to register
            aliases: Optional list of alternative names for the component

        Raises:
            ComponentRegistrationError: If registration fails
        """
        if name in self._components:
            raise ComponentRegistrationError(
                f"Component '{name}' is already registered in {self.get_component_type_name()} registry"
            )

        try:
            self._validate_component(component)
            self._components[name] = component

            # Register aliases
            if aliases:
                for alias in aliases:
                    if alias in self._aliases:
                        raise ComponentRegistrationError(
                            f"Alias '{alias}' is already registered"
                        )
                    self._aliases[alias] = name

        except Exception as e:
            raise ComponentRegistrationError(
                f"Failed to register component '{name}'", str(e)
            )

    def get(self, name: str) -> Any:
        """Get a component from the registry.

        Args:
            name: Name or alias of the component

        Returns:
            The requested component

        Raises:
            ComponentNotFoundError: If component is not found
        """
        # Check if it's an alias first
        actual_name = self._aliases.get(name, name)

        if actual_name not in self._components:
            raise ComponentNotFoundError(
                self.get_component_type_name(),
                name,
                f"Available components: {list(self.list_components())}",
            )

        return self._components[actual_name]

    def unregister(self, name: str) -> None:
        """Unregister a component from the registry.

        Args:
            name: Name of the component to unregister

        Raises:
            ComponentNotFoundError: If component is not found
        """
        if name not in self._components:
            raise ComponentNotFoundError(self.get_component_type_name(), name)

        del self._components[name]

        # Remove any aliases pointing to this component
        aliases_to_remove = [
            alias for alias, target in self._aliases.items() if target == name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]

    def list_components(self) -> list[str]:
        """List all registered component names.

        Returns:
            List of component names
        """
        return list(self._components.keys())

    def list_aliases(self) -> dict[str, str]:
        """List all registered aliases and their targets.

        Returns:
            Dictionary mapping aliases to component names
        """
        return self._aliases.copy()

    def clear(self) -> None:
        """Clear all registered components and aliases."""
        self._components.clear()
        self._aliases.clear()

    @abstractmethod
    def _validate_component(self, component: Any) -> None:
        """Validate that a component meets the requirements for this registry.

        Args:
            component: Component to validate

        Raises:
            ComponentRegistrationError: If component is invalid
        """


class DimensionRegistry(ComponentRegistry):
    """Registry for dimension assessor components.

    Manages the registration and discovery of dimension assessors that implement
    the DimensionAssessor protocol.
    """

    def get_component_type_name(self) -> str:
        """Get the component type name for this registry."""
        return "dimension_assessor"

    def _validate_component(self, component: Any) -> None:
        """Validate that a component is a valid dimension assessor.

        Args:
            component: Component to validate

        Raises:
            ComponentRegistrationError: If component is invalid
        """
        # Check if it's a class or instance that implements DimensionAssessor
        if inspect.isclass(component):
            if not issubclass(component, DimensionAssessor):
                raise ComponentRegistrationError(
                    "Component class must inherit from DimensionAssessor"
                )
        else:
            if not isinstance(component, DimensionAssessor):
                raise ComponentRegistrationError(
                    "Component instance must implement DimensionAssessor protocol"
                )

    def get_assessor(self, dimension_name: str) -> DimensionAssessor:
        """Get a dimension assessor by dimension name.

        Args:
            dimension_name: Name of the dimension (e.g., 'validity', 'completeness')

        Returns:
            Dimension assessor instance

        Raises:
            ComponentNotFoundError: If assessor is not found
        """
        component = self.get(dimension_name)

        # If it's a class, instantiate it
        if inspect.isclass(component):
            return component()

        return component

    def assess_dimension(
        self, dimension_name: str, data: Any, requirements: dict[str, Any]
    ) -> float:
        """Assess a dimension using the registered assessor.

        Args:
            dimension_name: Name of the dimension to assess
            data: Data to assess
            requirements: Dimension requirements from standard

        Returns:
            Assessment score (0.0-20.0)

        Raises:
            ComponentNotFoundError: If assessor is not found
        """
        assessor = self.get_assessor(dimension_name)
        return assessor.assess(data, requirements)


class CommandRegistry(ComponentRegistry):
    """Registry for CLI command components.

    Manages the registration and discovery of CLI commands that implement
    the Command protocol.
    """

    def get_component_type_name(self) -> str:
        """Get the component type name for this registry."""
        return "command"

    def _validate_component(self, component: Any) -> None:
        """Validate that a component is a valid command.

        Args:
            component: Component to validate

        Raises:
            ComponentRegistrationError: If component is invalid
        """
        # Check if it's a class or instance that implements Command
        if inspect.isclass(component):
            if not issubclass(component, Command):
                raise ComponentRegistrationError(
                    "Command class must inherit from Command"
                )
        else:
            if not isinstance(component, Command):
                raise ComponentRegistrationError(
                    "Command instance must implement Command protocol"
                )

    def get_command(self, command_name: str) -> Command:
        """Get a command by name.

        Args:
            command_name: Name of the command

        Returns:
            Command instance

        Raises:
            ComponentNotFoundError: If command is not found
        """
        component = self.get(command_name)

        # If it's a class, instantiate it
        if inspect.isclass(component):
            return component()

        return component

    def execute_command(self, command_name: str, args: dict[str, Any]) -> int:
        """Execute a command with the given arguments.

        Args:
            command_name: Name of the command to execute
            args: Command arguments

        Returns:
            Exit code from command execution

        Raises:
            ComponentNotFoundError: If command is not found
        """
        command = self.get_command(command_name)
        return command.execute(args)


class LoaderRegistry(ComponentRegistry):
    """Registry for data and standard loader components.

    Manages the registration and discovery of loaders that implement
    the DataLoader or StandardLoader protocols.
    """

    def get_component_type_name(self) -> str:
        """Get the component type name for this registry."""
        return "loader"

    def _validate_component(self, component: Any) -> None:
        """Validate that a component is a valid loader.

        Args:
            component: Component to validate

        Raises:
            ComponentRegistrationError: If component is invalid
        """
        # Check if it implements either DataLoader or StandardLoader protocol
        if inspect.isclass(component):
            # For classes, check if they have the required methods
            if not (
                hasattr(component, "load") and callable(getattr(component, "load"))
            ):
                raise ComponentRegistrationError(
                    "Loader class must implement 'load' method"
                )
        else:
            # For instances, check if they implement the protocols
            if not (hasattr(component, "load") and callable(component.load)):
                raise ComponentRegistrationError(
                    "Loader instance must implement 'load' method"
                )

    def get_loader_for_format(self, file_format: str) -> Any | None:
        """Get a loader that supports the specified file format.

        Args:
            file_format: File format/extension (e.g., '.csv', '.json')

        Returns:
            Loader instance that supports the format, or None if not found
        """
        for loader_name in self.list_components():
            try:
                loader = self.get(loader_name)

                # Instantiate if it's a class
                if inspect.isclass(loader):
                    loader = loader()

                # Check if it supports the format
                if hasattr(loader, "get_supported_formats"):
                    if file_format in loader.get_supported_formats():
                        return loader

            except (ImportError, TypeError, AttributeError):
                continue  # Skip loaders that fail to instantiate

        return None


class SerializerRegistry(ComponentRegistry):
    """Registry for result serializer components.

    Manages the registration and discovery of serializers that implement
    the ResultSerializer protocol.
    """

    def get_component_type_name(self) -> str:
        """Get the component type name for this registry."""
        return "serializer"

    def _validate_component(self, component: Any) -> None:
        """Validate that a component is a valid result serializer.

        Args:
            component: Component to validate

        Raises:
            ComponentRegistrationError: If component is invalid
        """
        required_methods = ["serialize", "get_format_name"]

        if inspect.isclass(component):
            for method_name in required_methods:
                if not (
                    hasattr(component, method_name)
                    and callable(getattr(component, method_name))
                ):
                    raise ComponentRegistrationError(
                        f"Serializer class must implement '{method_name}' method"
                    )
        else:
            for method_name in required_methods:
                if not (
                    hasattr(component, method_name)
                    and callable(getattr(component, method_name))
                ):
                    raise ComponentRegistrationError(
                        f"Serializer instance must implement '{method_name}' method"
                    )

    def get_serializer_for_format(self, format_name: str) -> Any | None:
        """Get a serializer that supports the specified format.

        Args:
            format_name: Format name (e.g., 'json', 'yaml', 'xml')

        Returns:
            Serializer instance that supports the format, or None if not found
        """
        for serializer_name in self.list_components():
            try:
                serializer = self.get(serializer_name)

                # Instantiate if it's a class
                if inspect.isclass(serializer):
                    serializer = serializer()

                # Check if it supports the format
                if hasattr(serializer, "get_format_name"):
                    if serializer.get_format_name().lower() == format_name.lower():
                        return serializer

            except (ImportError, TypeError, AttributeError):
                continue  # Skip serializers that fail to instantiate

        return None


class GlobalRegistry:
    """Global registry that manages all component types.

    Provides a unified interface for accessing all component registries
    and supports auto-discovery of components.
    """

    def __init__(self):
        """Initialize the global registry with all component types."""
        self.dimensions = DimensionRegistry()
        self.commands = CommandRegistry()
        self.loaders = LoaderRegistry()
        self.serializers = SerializerRegistry()

    def get_registry(self, registry_type: str) -> ComponentRegistry:
        """Get a specific component registry by type.

        Args:
            registry_type: Type of registry ('dimensions', 'commands', 'loaders', 'serializers')

        Returns:
            The requested component registry

        Raises:
            RegistryError: If registry type is not found
        """
        registries = {
            "dimensions": self.dimensions,
            "commands": self.commands,
            "loaders": self.loaders,
            "serializers": self.serializers,
        }

        if registry_type not in registries:
            raise RegistryError(
                f"Registry type '{registry_type}' not found",
                f"Available types: {list(registries.keys())}",
            )

        return registries[registry_type]

    def auto_discover_components(self, package_path: str) -> None:
        """Auto-discover and register components from a package.

        Args:
            package_path: Python package path to scan for components

        Raises:
            RegistryError: If auto-discovery fails
        """
        try:
            self._discover_dimension_assessors(f"{package_path}.validator.dimensions")
            self._discover_commands(f"{package_path}.cli.commands")
            self._discover_loaders(f"{package_path}.validator.loaders")
            self._discover_serializers(f"{package_path}.utils.serializers")
        except Exception as e:
            raise RegistryError("Auto-discovery failed", str(e))

    def _discover_dimension_assessors(self, package_path: str) -> None:
        """Discover dimension assessors in the specified package."""
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            for py_file in package_dir.glob("*.py"):
                if py_file.stem.startswith("_"):
                    continue

                module_name = f"{package_path}.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            obj.__module__ == module_name
                            and issubclass(obj, DimensionAssessor)
                            and obj != DimensionAssessor
                        ):

                            # Use the dimension name as the registry key
                            instance = obj()
                            dimension_name = instance.get_dimension_name()
                            self.dimensions.register(dimension_name, obj)

                except ImportError:
                    continue  # Skip modules that can't be imported

        except ImportError:
            pass  # Package doesn't exist, skip discovery

    def _discover_commands(self, package_path: str) -> None:
        """Discover CLI commands in the specified package."""
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            for py_file in package_dir.glob("*.py"):
                if py_file.stem.startswith("_"):
                    continue

                module_name = f"{package_path}.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            obj.__module__ == module_name
                            and issubclass(obj, Command)
                            and obj != Command
                        ):

                            # Use the command name as the registry key
                            instance = obj()
                            command_name = instance.get_name()
                            self.commands.register(command_name, obj)

                except ImportError:
                    continue

        except ImportError:
            pass

    def _discover_loaders(self, package_path: str) -> None:
        """Discover data loaders in the specified package."""
        try:
            module = importlib.import_module(package_path)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    obj.__module__ == module.__name__
                    and hasattr(obj, "load")
                    and callable(getattr(obj, "load"))
                ):

                    self.loaders.register(name.lower(), obj)

        except ImportError:
            pass

    def _discover_serializers(self, package_path: str) -> None:
        """Discover result serializers in the specified package."""
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            for py_file in package_dir.glob("*.py"):
                if py_file.stem.startswith("_"):
                    continue

                module_name = f"{package_path}.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            obj.__module__ == module_name
                            and hasattr(obj, "serialize")
                            and callable(getattr(obj, "serialize"))
                        ):

                            self.serializers.register(name.lower(), obj)

                except ImportError:
                    continue

        except ImportError:
            pass

    def clear_all(self) -> None:
        """Clear all component registries."""
        self.dimensions.clear()
        self.commands.clear()
        self.loaders.clear()
        self.serializers.clear()


# Global registry instance
_global_registry: GlobalRegistry | None = None


def get_global_registry() -> GlobalRegistry:
    """Get the global component registry instance.

    Returns:
        The global registry instance (creates one if it doesn't exist)
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = GlobalRegistry()
    return _global_registry


def create_command_registry() -> dict[str, Command]:
    """Create a dictionary of all registered commands.

    Returns:
        Dictionary mapping command names to command instances
    """
    registry = get_global_registry()
    commands = {}

    for command_name in registry.commands.list_components():
        commands[command_name] = registry.commands.get_command(command_name)

    return commands
