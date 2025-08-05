"""dlt-logger: Simple logging library with DuckDB storage via DLT Hub.

dlt-logger provides structured logging with built-in analytics capabilities using
DuckDB for local storage and optional AWS Athena integration for cloud analytics.

Basic Usage:
    >>> import dlt_logger
    >>>
    >>> # Setup logging configuration
    >>> dlt_logger.setup_logging(
    ...     project_name="my_app",
    ...     db_path="./logs/app.duckdb"
    ... )
    >>>
    >>> # Get a logger instance
    >>> logger = dlt_logger.get_logger("my_module")
    >>> logger.info("Application started")
    >>>
    >>> # Use decorator for automatic function logging
    >>> @dlt_logger.log_execution("data_processing")
    ... def process_data():
    ...     return "processed"

Workflow Management:
    >>> # Use WorkflowManager for end-to-end operations
    >>> config = dlt_logger.LoggerConfig(
    ...     project_name="workflow_demo",
    ...     athena_destination=True,
    ...     aws_region="us-east-1"
    ... )
    >>> workflow = dlt_logger.WorkflowManager(config)
    >>> results = workflow.run_complete_workflow(sample_log_count=50)
"""

# Import from organized structure
from .logging import (
    LogEntry,
    TPLogger,
    get_logger,
    log_execution,
    setup_logging,
    timed_operation,
)
from .orchestrator import WorkflowManager
from .setup import LoggerConfig
from .utils import (
    detect_project_root,
    generate_sample_log_data,
    get_database_info_from_config,
    resolve_project_path,
)

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
    "LoggerConfig",
    "WorkflowManager",
    "detect_project_root",
    "generate_sample_log_data",
    "get_database_info_from_config",
    "resolve_project_path",
]
