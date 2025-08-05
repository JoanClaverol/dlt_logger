"""tp-logger: Simple logging library with DuckDB storage via DLT Hub."""

# Import from organized structure
from .logging import (
    setup_logging,
    get_logger,
    log_execution,
    TPLogger,
    LogEntry
)
from .setup import LoggerConfig
from .orchestrator import WorkflowManager
from .utils import generate_sample_log_data, get_database_info_from_config

__version__ = "0.1.0"
__author__ = "Joan Claverol"

# Main exports for easy import
__all__ = [
    "setup_logging",
    "get_logger", 
    "log_execution",
    "TPLogger",
    "LogEntry",
    "LoggerConfig",
    "WorkflowManager",
    "generate_sample_log_data",
    "get_database_info_from_config",
]
