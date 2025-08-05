"""Utility functions and helpers for tp-logger.

This module provides utility functions for:
- Directory and file management
- Duration formatting
- Context sanitization (removes sensitive data)
- Sample data generation for testing
- Database inspection and analysis

Usage Examples:
    File utilities:
        >>> from tp_logger.utils import ensure_directory_exists, format_duration
        >>>
        >>> ensure_directory_exists("./logs/app.duckdb")  # Creates ./logs/ if needed
        >>> print(format_duration(1500))  # "1.50s"
        >>> print(format_duration(65000))  # "1m 5.00s"

    Sample data generation:
        >>> from tp_logger.utils import generate_sample_log_data
        >>>
        >>> sample_logs = generate_sample_log_data(count=5)
        >>> for log in sample_logs:
        ...     print(f"{log['action']}: {log['message']}")

    Database inspection:
        >>> from tp_logger.utils import get_database_info_from_config
        >>>
        >>> db_info = get_database_info_from_config()
        >>> print(f"Database has {db_info['total_logs']} log entries")
        >>> print(f"Tables: {db_info['tables']}")

    Context sanitization:
        >>> from tp_logger.utils import sanitize_context
        >>>
        >>> context = {"user_id": 123, "api_key": "secret123", "data": "public"}
        >>> clean = sanitize_context(context)
        >>> # Result: {"user_id": 123, "api_key": "***REDACTED***", "data": "public"}
"""

from .helpers import (
    ensure_directory_exists,
    format_duration,
    sanitize_context,
    generate_sample_log_data,
    get_database_info,
    get_database_info_from_config,
)

__all__ = [
    "ensure_directory_exists",
    "format_duration",
    "sanitize_context",
    "generate_sample_log_data",
    "get_database_info",
    "get_database_info_from_config",
]
