"""Core logging functionality for dlt-logger.

This module provides the main logging infrastructure including:
- TPLogger: Main logger class with DLT integration
- Decorators: @log_execution and timed_operation context manager
- Setup functions: setup_logging() and get_logger()

Usage Examples:
    Direct logging:
        >>> from dlt_logger.logging import TPLogger, setup_logging
        >>>
        >>> setup_logging(project_name="my_app")
        >>> logger = TPLogger("my_module")
        >>> logger.info("Process started", action="startup")
        >>> logger.log_action("user_login", "User authenticated", success=True, duration_ms=150)

    Decorator usage:
        >>> from dlt_logger.logging import log_execution
        >>>
        >>> @log_execution("api_call")
        ... def fetch_data(user_id):
        ...     # Function automatically logged with timing
        ...     return f"data_for_{user_id}"

    Context manager usage:
        >>> from dlt_logger.logging import get_logger, timed_operation
        >>>
        >>> logger = get_logger("database")
        >>> with timed_operation(logger, "database_query", user_id=123):
        ...     # Operation automatically timed and logged
        ...     pass
"""

from .decorators import log_execution, timed_operation
from .handlers import setup_console_logging
from .logger import TPLogger, get_logger, setup_logging
from .models import LogEntry

__all__ = [
    "LogEntry",
    "TPLogger",
    "setup_logging",
    "get_logger",
    "setup_console_logging",
    "log_execution",
    "timed_operation",
]
