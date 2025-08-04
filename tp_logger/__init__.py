"""tp-logger: Simple logging library with DuckDB storage via DLT Hub."""

from .core import (
    setup_logging,
    get_logger,
    log_execution,
    timed_operation,
    TPLogger
)
from .models import LogEntry
from .config import LoggerConfig

__version__ = "0.1.0"
__author__ = "Joan Claverol"

# Main exports for easy import
__all__ = [
    "setup_logging",
    "get_logger", 
    "log_execution",
    "timed_operation",
    "TPLogger",
    "LogEntry",
    "LoggerConfig"
]