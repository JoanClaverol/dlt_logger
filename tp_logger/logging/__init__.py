"""Core logging functionality for tp-logger.

This module provides the main logging infrastructure including:
- TPLogger: Main logger class with DLT integration
- Decorators: @log_execution and timed_operation context manager
- Setup functions: setup_logging() and get_logger()

Usage Examples:
    Direct logging:
        >>> from tp_logger.logging import TPLogger, setup_logging
        >>>
        >>> setup_logging(project_name="my_app")
        >>> logger = TPLogger("my_module")
        >>> logger.info("Process started", action="startup")
        >>> logger.log_action("user_login", "User authenticated", success=True, duration_ms=150)

    Decorator usage:
        >>> from tp_logger.logging import log_execution
        >>>
        >>> @log_execution("api_call")
        ... def fetch_data(user_id):
        ...     # Function automatically logged with timing
        ...     return f"data_for_{user_id}"

    Context manager usage:
        >>> from tp_logger.logging import get_logger, timed_operation
        >>>
        >>> logger = get_logger("database")
        >>> with timed_operation(logger, "database_query", user_id=123):
        ...     # Operation automatically timed and logged
        ...     pass
"""

from .models import LogEntry
from .logger import TPLogger, setup_logging, get_logger
from .handlers import setup_console_logging
from .decorators import log_execution, timed_operation

__all__ = [
    "LogEntry",
    "TPLogger",
    "setup_logging",
    "get_logger",
    "setup_console_logging",
    "log_execution",
    "timed_operation",
]
