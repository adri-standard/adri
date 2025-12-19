"""Path resolution utilities for the ADRI framework.

This module contains utilities for resolving paths, finding project roots,
and handling path operations consistently across the ADRI system.
"""

from pathlib import Path

from ..core.exceptions import FileOperationError, ProjectNotFoundError


def find_adri_project_root(start_path: str | Path | None = None) -> Path | None:
    """Find the ADRI project root directory by searching for ADRI/config.yaml.

    Searches upward from the current directory until it finds a directory
    containing ADRI/config.yaml or reaches the filesystem root.

    Args:
        start_path: Starting path for search (uses current directory if None)

    Returns:
        Path to project root, or None if not found
    """
    current_path = Path(start_path) if start_path else Path.cwd()

    # Resolve to absolute path to handle symlinks properly
    current_path = current_path.resolve()

    while current_path != current_path.parent:
        config_file = current_path / "ADRI" / "config.yaml"
        if config_file.exists():
            return current_path
        current_path = current_path.parent

    # Check root directory
    config_file = current_path / "ADRI" / "config.yaml"
    return current_path if config_file.exists() else None


def resolve_project_path(
    relative_path: str | Path, project_root: Path | None = None
) -> Path:
    """Resolve a path relative to the ADRI project root.

    If an ADRI project is found, resolves the path relative to the project root.
    Tutorial paths and dev/prod paths are automatically prefixed with ADRI/.

    Args:
        relative_path: Path relative to project root
        project_root: Project root path (auto-discovered if None)

    Returns:
        Resolved absolute path

    Raises:
        ProjectNotFoundError: If project root cannot be found
    """
    if project_root is None:
        project_root = find_adri_project_root()
        if project_root is None:
            raise ProjectNotFoundError(
                "ADRI project root not found",
                "No ADRI/config.yaml found in current directory tree",
            )

    relative_path = str(relative_path)

    # Handle different path prefixes
    if relative_path.startswith("ADRI/"):
        return project_root / relative_path
    elif relative_path.startswith("tutorials/"):
        return project_root / "ADRI" / relative_path
    elif relative_path.startswith(("dev/", "prod/")):
        return project_root / "ADRI" / relative_path
    else:
        return project_root / "ADRI" / relative_path


def shorten_home_path(path: str | Path) -> str:
    """Return a home-shortened absolute path, e.g. ~/project/file.txt.

    Args:
        path: Path to shorten

    Returns:
        Path string with home directory replaced by ~
    """
    try:
        abs_path = Path(path).resolve()
        home_path = Path.home().resolve()

        try:
            relative_to_home = abs_path.relative_to(home_path)
            return f"~/{relative_to_home}"
        except ValueError:
            # Path is not under home directory
            return str(abs_path)
    except Exception:
        return str(path)


def get_relative_to_project_root(
    path: str | Path, project_root: Path | None = None
) -> str:
    """Return path relative to ADRI project root if under it, else home-shortened path.

    Additionally, strip leading 'ADRI/' for display brevity when under the root.

    Args:
        path: Path to make relative
        project_root: Project root path (auto-discovered if None)

    Returns:
        Relative path string for display
    """
    try:
        if project_root is None:
            project_root = find_adri_project_root()

        abs_path = Path(path).resolve()

        if project_root:
            project_root_abs = project_root.resolve()
            try:
                relative_path = abs_path.relative_to(project_root_abs)
                relative_str = str(relative_path)

                # Strip ADRI/ prefix for cleaner display
                if relative_str.startswith("ADRI/"):
                    relative_str = relative_str[5:]  # len("ADRI/")

                return relative_str
            except ValueError:
                # Path is not under project root
                return shorten_home_path(abs_path)
        else:
            return shorten_home_path(abs_path)
    except Exception:
        return shorten_home_path(path)


def get_project_root_display(project_root: Path | None = None) -> str:
    """Get a display string for the project root.

    Args:
        project_root: Project root path (auto-discovered if None)

    Returns:
        Display string indicating project root location
    """
    if project_root is None:
        project_root = find_adri_project_root()

    if project_root:
        return f"📂 Project Root: {shorten_home_path(project_root)}"
    else:
        return "📂 Project Root: (not detected)"


def ensure_directory_exists(path: str | Path) -> Path:
    """Ensure that a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        Path object for the directory

    Raises:
        FileOperationError: If directory cannot be created
    """
    path = Path(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise FileOperationError(f"Failed to create directory: {path}", str(e))


def safe_file_operation(operation_name: str, file_path: str | Path) -> None:
    """Context manager for safe file operations with error handling.

    This is a helper that can be used to wrap file operations and provide
    consistent error messages.

    Args:
        operation_name: Description of the operation for error messages
        file_path: Path to the file being operated on

    Raises:
        FileOperationError: If the operation fails
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError:
                raise FileOperationError(
                    f"{operation_name} failed: File not found", f"Path: {file_path}"
                )
            except PermissionError:
                raise FileOperationError(
                    f"{operation_name} failed: Permission denied", f"Path: {file_path}"
                )
            except OSError as e:
                raise FileOperationError(
                    f"{operation_name} failed: {e}", f"Path: {file_path}"
                )

        return wrapper

    return decorator


def is_safe_path(path: str | Path, base_directory: str | Path | None = None) -> bool:
    """Check if a path is safe (doesn't contain directory traversal attempts).

    Args:
        path: Path to validate
        base_directory: Base directory to restrict access to (uses project root if None)

    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(path).resolve()

        if base_directory is None:
            base_directory = find_adri_project_root()
            if base_directory is None:
                return False  # No project root found, be safe
        else:
            base_directory = Path(base_directory).resolve()

        # Check if resolved path is under base directory
        try:
            path.relative_to(base_directory)
            return True
        except ValueError:
            return False

    except Exception:
        return False


def get_file_extension(file_path: str | Path) -> str:
    """Get the file extension in lowercase.

    Args:
        file_path: Path to get extension from

    Returns:
        File extension including the dot (e.g., '.csv', '.yaml')
    """
    return Path(file_path).suffix.lower()


def normalize_path_separators(path: str | Path) -> str:
    """Normalize path separators for cross-platform compatibility.

    Args:
        path: Path to normalize

    Returns:
        Path string with normalized separators
    """
    return str(Path(path)).replace("\\", "/")


def get_common_path_prefix(*paths: str | Path) -> Path | None:
    """Find the common path prefix among multiple paths.

    Args:
        *paths: Variable number of paths to find common prefix for

    Returns:
        Common path prefix, or None if no common prefix
    """
    if not paths:
        return None

    try:
        resolved_paths = [Path(p).resolve() for p in paths]

        if len(resolved_paths) == 1:
            return resolved_paths[0].parent

        # Find common prefix by comparing path parts
        common_parts = []
        min_parts = min(len(p.parts) for p in resolved_paths)

        for i in range(min_parts):
            parts_at_i = [p.parts[i] for p in resolved_paths]
            if len(set(parts_at_i)) == 1:  # All paths have same part at this position
                common_parts.append(parts_at_i[0])
            else:
                break

        if common_parts:
            return Path(*common_parts)

    except Exception:
        pass

    return None


class PathResolver:
    """Helper class for resolving paths within an ADRI project.

    Provides a stateful interface for path resolution that caches the
    project root discovery for better performance.
    """

    def __init__(self, project_root: str | Path | None = None):
        """Initialize the path resolver.

        Args:
            project_root: Project root path (auto-discovered if None)
        """
        self._project_root = Path(project_root) if project_root else None
        self._project_root_cached = False

    @property
    def project_root(self) -> Path | None:
        """Get the project root, caching the result."""
        if not self._project_root_cached:
            if self._project_root is None:
                self._project_root = find_adri_project_root()
            self._project_root_cached = True
        return self._project_root

    def resolve(self, relative_path: str | Path) -> Path:
        """Resolve a path relative to the project root.

        Args:
            relative_path: Path to resolve

        Returns:
            Resolved absolute path

        Raises:
            ProjectNotFoundError: If project root cannot be found
        """
        return resolve_project_path(relative_path, self.project_root)

    def relative_to_root(self, path: str | Path) -> str:
        """Get path relative to project root for display.

        Args:
            path: Path to make relative

        Returns:
            Relative path string
        """
        return get_relative_to_project_root(path, self.project_root)

    def ensure_under_project(self, path: str | Path) -> bool:
        """Ensure a path is under the project root.

        Args:
            path: Path to validate

        Returns:
            True if path is under project root
        """
        return is_safe_path(path, self.project_root)


# Backward compatibility aliases for CLI commands
rel_to_project_root = get_relative_to_project_root
