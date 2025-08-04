"""Core TPLogger class for tp-logger."""

from typing import Optional, Dict, Any, List, Literal

from loguru import logger

from .models import LogEntry
from .config import get_config, set_config, LoggerConfig
from .pipeline import get_pipeline, job_logs, RUN_ID
from .handlers import setup_console_logging


class TPLogger:
    """Main logger class for tp-logger using DLT."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.config = get_config()
        self.pipeline = get_pipeline()
        self.loguru_logger = logger.bind(name=module_name)

        # Buffer for batch writes (optional optimization)
        self._log_buffer: List[LogEntry] = []

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
        """Log a specific action with metadata."""
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

    Args:
        project_name (str): Name of your project
        db_path (str): Path to DuckDB file
        log_level (str): Minimum log level
        console_logging (bool): Enable console output
        dataset_name (str): DLT dataset name
        pipeline_name (str): DLT pipeline name

    All parameters are optional and will use defaults from config.py if not provided.
    """
    # Create configuration using the config module with provided parameters
    config = LoggerConfig(**kwargs)
    set_config(config)

    # Reset pipeline to use new config
    import tp_logger.pipeline as pipeline_module

    pipeline_module._pipeline = None

    # Setup console logging
    if config.console_logging:
        setup_console_logging()


def get_logger(name: str) -> TPLogger:
    """Get a TPLogger instance."""
    return TPLogger(name)
