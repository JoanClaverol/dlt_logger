"""Core TPLogger class for tp-logger."""

from typing import Optional, Dict, Any, Literal

from loguru import logger

from .models import LogEntry
from ..setup import get_config, set_config, LoggerConfig
from ..dlt import get_pipeline, job_logs, RUN_ID
from .handlers import setup_console_logging


class TPLogger:
    """Main logger class for tp-logger using DLT Hub integration.

    Provides structured logging with automatic storage to DuckDB via DLT pipelines.
    Supports both simple logging methods (info, warning, error) and advanced
    action logging with metadata like timing, success status, and context.

    Attributes:
        module_name (str): Name of the module this logger represents.
        config (LoggerConfig): Current logging configuration.
        pipeline (dlt.Pipeline): DLT pipeline for data storage.
        loguru_logger: Loguru logger instance for console output.

    Example:
        >>> logger = TPLogger("api_service")
        >>> logger.info("Request received", action="api_request")
        >>> logger.log_action("process_data", "Data processed successfully",
        ...                   success=True, duration_ms=250)
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.config = get_config()
        self.pipeline = get_pipeline()
        self.loguru_logger = logger.bind(name=module_name)

    def _create_log_entry(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        message: str,
        action: Optional[str] = None,
        function_name: Optional[str] = None,
        success: Optional[bool] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        request_method: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> LogEntry:
        """Create a LogEntry model."""
        return LogEntry(
            project_name=self.config.project_name,
            module_name=self.module_name,
            function_name=function_name,
            run_id=RUN_ID,
            level=level,
            action=action,
            message=message,
            success=success,
            status_code=status_code,
            duration_ms=duration_ms,
            request_method=request_method,
            context=context or {},
        )

    def _log_to_dlt(self, log_entry: LogEntry):
        """Log entry using DLT."""
        try:
            # Run the pipeline with the log entry
            self.pipeline.run(job_logs([log_entry]))
        except Exception as e:
            print(f"DLT logging failed: {e}")

    def _log(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        message: str,
        **kwargs,
    ):
        """Internal logging method."""
        # Console logging
        if self.config.console_logging:
            getattr(self.loguru_logger, level.lower())(message)

        # Create log entry and store via DLT
        log_entry = self._create_log_entry(level=level, message=message, **kwargs)
        self._log_to_dlt(log_entry)

    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log("CRITICAL", message, **kwargs)

    def log_action(
        self,
        action: str,
        message: str,
        success: bool = True,
        level: Optional[
            Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Log a specific action with structured metadata.

        This method is ideal for logging business operations, API calls,
        database queries, or any action that has a success/failure outcome.

        Args:
            action (str): Name of the action being performed (e.g., "user_login", "data_export").
            message (str): Human-readable message describing the action outcome.
            success (bool, optional): Whether the action succeeded. Defaults to True.
            level (str, optional): Log level. If None, defaults to "INFO" for success, "ERROR" for failure.
            duration_ms (int, optional): Action duration in milliseconds.
            context (dict, optional): Additional structured data about the action.
            **kwargs: Additional fields to include in the log entry.

        Example:
            >>> logger.log_action(
            ...     action="database_query",
            ...     message="Retrieved user profile",
            ...     success=True,
            ...     duration_ms=45,
            ...     context={"user_id": 123, "table": "users"}
            ... )
        """
        if level is None:
            level = "INFO" if success else "ERROR"

        self._log(
            level=level,
            message=message,
            action=action,
            success=success,
            duration_ms=duration_ms,
            context=context,
            **kwargs,
        )

    def log_exception(self, action: str, exception: Exception):
        """Log an exception."""
        self._log(
            level="ERROR",
            message=f"Exception in {action}: {str(exception)}",
            action=action,
            success=False,
            context={"exception_type": type(exception).__name__},
        )


def setup_logging(**kwargs):
    """Setup tp-logger with the given configuration.

    Initializes the logging system with DLT pipeline integration and optional
    console logging. This should be called once at application startup.

    Args:
        project_name (str, optional): Name of your project. Defaults to "tp_logger_app".
        db_path (str, optional): Path to DuckDB file. Defaults to "./logs/app.duckdb".
        log_level (str, optional): Minimum log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). Defaults to "INFO".
        console_logging (bool, optional): Enable console output. Defaults to True.
        dataset_name (str, optional): DLT dataset name. Defaults to "tp_logger_logs".
        pipeline_name (str, optional): DLT pipeline name. Defaults to "tp_logger_pipeline".
        athena_destination (bool, optional): Enable AWS Athena integration. Defaults to False.
        aws_region (str, optional): AWS region for Athena. Required if athena_destination=True.
        athena_database (str, optional): Athena database name. Required if athena_destination=True.
        athena_s3_staging_bucket (str, optional): S3 bucket for Athena staging. Required if athena_destination=True.

    Returns:
        None

    Raises:
        ValueError: If required Athena parameters are missing when athena_destination=True.

    Example:
        >>> setup_logging(
        ...     project_name="my_app",
        ...     db_path="./data/logs.duckdb",
        ...     log_level="DEBUG",
        ...     console_logging=True
        ... )
    """
    # Create configuration using the config module with provided parameters
    config = LoggerConfig(**kwargs)
    set_config(config)

    # Reset pipeline to use new config
    import tp_logger.dlt.pipeline as pipeline_module

    pipeline_module._pipeline = None

    # Setup console logging
    if config.console_logging:
        setup_console_logging()


def get_logger(name: str) -> TPLogger:
    """Get a TPLogger instance for the specified module.

    Creates a new TPLogger instance bound to the given module name.
    The logger will use the global configuration set by setup_logging().

    Args:
        name (str): Module or component name for the logger.

    Returns:
        TPLogger: Configured logger instance for the specified module.

    Example:
        >>> logger = get_logger("user_service")
        >>> logger.info("User authenticated", action="login", user_id=123)
    """
    return TPLogger(name)
