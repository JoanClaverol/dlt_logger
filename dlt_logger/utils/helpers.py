"""Utility functions and helpers for tp-logger."""

import inspect
import os
from pathlib import Path
from typing import Any, Optional


def ensure_directory_exists(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def format_duration(duration_ms: Optional[int]) -> str:
    """Format duration in milliseconds to human-readable string."""
    if duration_ms is None:
        return "N/A"

    if duration_ms < 1000:
        return f"{duration_ms}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.2f}s"
    else:
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) / 1000
        return f"{minutes}m {seconds:.2f}s"


def sanitize_context(context: dict[str, Any]) -> dict[str, Any]:
    """Sanitize context dictionary by removing or masking sensitive data.

    Identifies and redacts potentially sensitive information like passwords,
    API keys, tokens, and other authentication data to prevent accidental
    logging of secrets.

    Args:
        context (dict): Dictionary containing context data to sanitize.

    Returns:
        dict: Sanitized dictionary with sensitive values replaced by "***REDACTED***".

    Note:
        Sensitive keys detected (case-insensitive): password, token, secret, key,
        api_key, access_token, refresh_token, auth, authorization.

    Example:
        >>> context = {"user_id": 123, "api_key": "secret123", "message": "hello"}
        >>> clean = sanitize_context(context)
        >>> print(clean)
        {"user_id": 123, "api_key": "***REDACTED***", "message": "hello"}
    """
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "key",
        "api_key",
        "access_token",
        "refresh_token",
        "auth",
        "authorization",
    }

    sanitized = {}
    for key, value in context.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value

    return sanitized


def generate_sample_log_data(count: int = 10) -> list[dict[str, Any]]:
    """Generate sample log data for testing and demonstration purposes.

    Creates realistic log entries with random actions, success/failure outcomes,
    and structured context data. Useful for testing the logging pipeline
    and demonstrating tp-logger capabilities.

    Args:
        count (int, optional): Number of sample log entries to generate. Defaults to 10.

    Returns:
        list: List of dictionaries containing sample log data with keys:
            - action (str): Random action name
            - message (str): Descriptive message about the action
            - success (bool): Random success/failure status
            - level (str): Log level based on success status
            - duration_ms (int): Random duration between 50-5000ms
            - context (dict): Random user, session, and IP data

    Example:
        >>> samples = generate_sample_log_data(count=3)
        >>> for sample in samples:
        ...     print(f"{sample['action']}: {sample['success']}")
        user_login: True
        data_fetch: False
        file_upload: True
    """
    import random
    from uuid import uuid4

    actions = ["user_login", "data_fetch", "file_upload", "api_call", "database_query"]
    statuses = [True, False]
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]

    sample_data = []
    for _i in range(count):
        action = random.choice(actions)
        success = random.choice(statuses)
        level = "ERROR" if not success else random.choice(levels)

        data = {
            "action": action,
            "message": f"Sample {action} operation {'succeeded' if success else 'failed'}",
            "success": success,
            "level": level,
            "duration_ms": random.randint(50, 5000),
            "context": {
                "user_id": str(uuid4()),
                "session_id": str(uuid4()),
                "ip_address": f"192.168.1.{random.randint(1, 254)}",
            },
        }
        sample_data.append(data)

    return sample_data


def get_database_info(
    db_path: str, dataset_name: str, table_name: str = "job_logs"
) -> dict[str, Any]:
    """Get information about the DuckDB database.

    Args:
        db_path: Path to the DuckDB database file
        dataset_name: Schema/dataset name to query (from config)
        table_name: Name of the logs table (configurable)
    """
    import duckdb

    try:
        with duckdb.connect(db_path, read_only=True) as conn:
            # Get table info using the configurable dataset name
            tables_query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dataset_name}'"
            tables = conn.execute(tables_query).fetchall()

            info = {
                "database_path": db_path,
                "dataset_name": dataset_name,
                "table_name": table_name,
                "exists": os.path.exists(db_path),
                "tables": [table[0] for table in tables] if tables else [],
                "file_size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2)
                if os.path.exists(db_path)
                else 0,
            }

            # Get row count if the specified table exists
            if table_name in info["tables"]:
                count_query = f"SELECT COUNT(*) FROM {dataset_name}.{table_name}"
                count = conn.execute(count_query).fetchone()[0]
                info["total_logs"] = count

            return info

    except Exception as e:
        return {
            "database_path": db_path,
            "dataset_name": dataset_name,
            "table_name": table_name,
            "exists": os.path.exists(db_path),
            "error": str(e),
            "file_size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2)
            if os.path.exists(db_path)
            else 0,
        }


def get_database_info_from_config() -> dict[str, Any]:
    """Get database info using values from the current configuration."""
    from ..setup import get_config

    config = get_config()
    return get_database_info(
        db_path=config.db_path,
        dataset_name=config.dataset_name,
        table_name="job_logs",  # This could also be made configurable in LoggerConfig if needed
    )


def detect_project_root(caller_frame_depth: int = 3) -> str:
    """Detect the project root directory from the calling code.

    This function inspects the call stack to find where dlt_logger was called from
    and attempts to detect the project root directory by looking for common project
    indicators like pyproject.toml, setup.py, requirements.txt, or .git directory.

    Args:
        caller_frame_depth (int): How many frames up the stack to look for the caller.
                                 Default is 3 (typically the user's code calling setup_logging).

    Returns:
        str: Absolute path to the detected project root directory.
             Falls back to current working directory if detection fails.

    Example:
        >>> # Called from user's project at /home/user/myproject/main.py
        >>> root = detect_project_root()
        >>> print(root)  # '/home/user/myproject'
    """
    try:
        # Get the caller's frame
        frame = inspect.currentframe()
        for _ in range(caller_frame_depth):
            if frame is None:
                break
            frame = frame.f_back

        if frame is None:
            return os.getcwd()

        # Get the file path of the caller
        caller_file = frame.f_code.co_filename
        caller_dir = os.path.dirname(os.path.abspath(caller_file))

        # Walk up the directory tree looking for project root indicators
        project_root = find_project_root_from_path(caller_dir)
        return project_root

    except Exception:
        # Fallback to current working directory
        return os.getcwd()


def find_project_root_from_path(start_path: str) -> str:
    """Find the project root by walking up from a starting path.

    Looks for common project indicators in each parent directory:
    - pyproject.toml (Python projects using modern standards)
    - setup.py (traditional Python projects)
    - requirements.txt (pip-based projects)
    - .git (Git repositories)
    - Cargo.toml (Rust projects)
    - package.json (Node.js projects)

    Args:
        start_path (str): Directory path to start searching from.

    Returns:
        str: Absolute path to the project root, or start_path if no indicators found.
    """
    project_indicators = [
        'pyproject.toml',
        'setup.py',
        'requirements.txt',
        '.git',
        'Cargo.toml',
        'package.json',
        'go.mod',
        'Dockerfile',
        '.gitignore'
    ]

    current_path = Path(start_path).resolve()

    # Walk up the directory tree
    for path in [current_path] + list(current_path.parents):
        # Check if any project indicators exist in this directory
        for indicator in project_indicators:
            if (path / indicator).exists():
                return str(path)

    # If no indicators found, return the starting path
    return start_path


def resolve_project_path(relative_path: str, project_root: Optional[str] = None) -> str:
    """Resolve a relative path to an absolute path based on project root.

    Converts relative paths to absolute paths using the project root as the base.
    If the path is already absolute, returns it unchanged.

    Args:
        relative_path (str): The path to resolve (relative or absolute).
        project_root (str, optional): Base directory for relative paths.
                                    If None, auto-detects project root.

    Returns:
        str: Absolute path resolved from the project root.

    Example:
        >>> # If project root is '/home/user/myproject'
        >>> path = resolve_project_path('./logs/app.db')
        >>> print(path)  # '/home/user/myproject/logs/app.db'
        >>>
        >>> # Absolute paths are returned unchanged
        >>> path = resolve_project_path('/tmp/logs.db')
        >>> print(path)  # '/tmp/logs.db'
    """
    # If already absolute, return as-is
    if os.path.isabs(relative_path):
        return relative_path

    # Get project root if not provided
    if project_root is None:
        project_root = detect_project_root(caller_frame_depth=4)  # Go one frame deeper

    # Resolve relative to project root
    return os.path.abspath(os.path.join(project_root, relative_path))
