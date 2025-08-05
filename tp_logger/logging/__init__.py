"""Core logging functionality for tp-logger."""

from .models import LogEntry
from .logger import TPLogger, setup_logging, get_logger
from .handlers import setup_console_logging
from .decorators import log_execution

__all__ = [
    "LogEntry",
    "TPLogger", 
    "setup_logging",
    "get_logger",
    "setup_console_logging",
    "log_execution"
]