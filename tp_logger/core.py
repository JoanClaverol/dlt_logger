"""Core logging functionality for tp-logger using DLT Hub."""

# Import all public APIs from the modular components
from .logger import TPLogger, setup_logging, get_logger
from .decorators import log_execution, timed_operation
from .athena import upload_to_athena
from .pipeline import RUN_ID, get_pipeline

# Re-export all public APIs to maintain backward compatibility
__all__ = [
    "TPLogger",
    "setup_logging",
    "get_logger",
    "log_execution",
    "timed_operation",
    "upload_to_athena",
    "RUN_ID",
    "get_pipeline",
]
