"""Core logging functionality for tp-logger using DLT Hub."""

import sys
import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable, List
from uuid import uuid4

import dlt
from loguru import logger

from .models import LogEntry
from .config import get_config, set_config, LoggerConfig


# Global pipeline instance
_pipeline: Optional[dlt.Pipeline] = None

# Generate a unique run ID for this session
RUN_ID = uuid4()


class InterceptHandler(logging.Handler):
    """Handler to intercept standard logging and redirect to loguru."""
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and depth > 0:
            if frame.f_code.co_filename != logging.__file__:
                break
            frame = frame.f_back
            depth -= 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def get_pipeline() -> dlt.Pipeline:
    """Get or create the DLT pipeline."""
    global _pipeline
    if _pipeline is None:
        config = get_config()
        _pipeline = dlt.pipeline(
            pipeline_name=config.pipeline_name,
            destination="duckdb",
            dataset_name="tp_logger_logs"
        )
    return _pipeline


@dlt.resource(
    write_disposition="append",
    columns={
        "id": {"data_type": "text"},
        "project_name": {"data_type": "text"},
        "module_name": {"data_type": "text"},
        "function_name": {"data_type": "text"},
        "run_id": {"data_type": "text"},
        "timestamp": {"data_type": "timestamp"},
        "level": {"data_type": "text"},
        "action": {"data_type": "text"},
        "message": {"data_type": "text"},
        "success": {"data_type": "bool"},
        "status_code": {"data_type": "bigint"},
        "duration_ms": {"data_type": "bigint"},
        "request_method": {"data_type": "text"},
        "context": {"data_type": "json"},
    }
)
def job_logs(log_entries: List[LogEntry]):
    """DLT resource for job logs."""
    for entry in log_entries:
        yield entry.model_dump()


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
        level: str,
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
            context=context or {}
        )
    
    def _log_to_dlt(self, log_entry: LogEntry):
        """Log entry using DLT."""
        try:
            # Run the pipeline with the log entry
            self.pipeline.run(job_logs([log_entry]))
        except Exception as e:
            print(f"DLT logging failed: {e}")
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method."""
        # Console logging
        if self.config.console_logging:
            getattr(self.loguru_logger, level.lower())(message)
        
        # Create log entry and store via DLT
        log_entry = self._create_log_entry(level=level.upper(), message=message, **kwargs)
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
        level: Optional[str] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
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
            **kwargs
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


def setup_logging(
    project_name: str = "tp_logger_app",
    db_path: str = "./logs/app.duckdb",
    log_level: str = "INFO",
    console_logging: bool = True
):
    """Setup tp-logger with the given configuration."""
    global _pipeline
    
    # Create configuration using the config module
    config = LoggerConfig(
        project_name=project_name,
        db_path=db_path,
        log_level=log_level,
        console_logging=console_logging
    )
    set_config(config)
    
    # Reset pipeline to use new config
    _pipeline = None
    
    # Setup console logging
    if console_logging:
        setup_console_logging()


def setup_console_logging():
    """Setup console logging with loguru."""
    config = get_config()
    
    if not config.console_logging:
        return
    
    # Configure loguru
    logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS Z}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(sys.stdout, format=log_format, level=config.log_level)
    
    # Setup intercept handler for standard logging
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(InterceptHandler())
    root_logger.setLevel(getattr(logging, config.log_level))
    root_logger.propagate = False


def get_logger(name: str) -> TPLogger:
    """Get a TPLogger instance."""
    return TPLogger(name)


def log_execution(action: Optional[str] = None):
    """Decorator to automatically log function execution with timing."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            module_name = func.__module__
            function_name = func.__name__
            action_name = action or f"{function_name}_execution"
            
            tp_logger = TPLogger(module_name)
            
            start_time = time.time()
            try:
                tp_logger.info(
                    f"Starting {action_name}",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                )
                
                result = func(*args, **kwargs)
                
                duration_ms = int((time.time() - start_time) * 1000)
                tp_logger.info(
                    f"Completed {action_name} in {duration_ms}ms",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                    duration_ms=duration_ms,
                )
                
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                tp_logger.log_exception(action_name, e)
                tp_logger._log(
                    level="ERROR",
                    message=f"Failed {action_name} after {duration_ms}ms",
                    action=action_name,
                    function_name=function_name,
                    success=False,
                    duration_ms=duration_ms,
                )
                raise
        
        return wrapper
    
    return decorator


@contextmanager
def timed_operation(tp_logger: TPLogger, action: str, **log_kwargs):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        tp_logger.info(f"Starting {action}", action=action, **log_kwargs)
        yield
        duration_ms = int((time.time() - start_time) * 1000)
        tp_logger.info(
            f"Completed {action} in {duration_ms}ms",
            action=action,
            success=True,
            duration_ms=duration_ms,
            **log_kwargs,
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        tp_logger.log_exception(action, e)
        tp_logger._log(
            level="ERROR",
            message=f"Failed {action} after {duration_ms}ms",
            action=action,
            success=False,
            duration_ms=duration_ms,
            **log_kwargs,
        )
        raise