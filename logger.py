import logging
import sys
import uuid
import time
import json
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable
import os

import duckdb
from loguru import logger


def _get_setting(key: str, default=None):
    """Get setting from environment variables or return default."""
    return os.getenv(key, default)


# Generate a unique tracing ID for this session
TRACING_ID = (
    str(uuid.uuid4())[: _get_setting("TRACING_ID_LENGTH", 8)]
    if _get_setting("GENERATE_TRACING_ID", True)
    else "NO_TRACE"
)

# Global run ID for tracking related operations
RUN_ID = str(uuid.uuid4())

# Project name from settings
PROJECT_NAME = _get_setting("LOGGER_PROJECT_NAME", "morning_podcast")

# Database connection
_db_connection = None


# Custom handler to intercept standard logging and redirect to loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the log originated
        frame, depth = sys._getframe(6), 6
        while frame and depth > 0:
            if frame.f_code.co_filename != logging.__file__:
                break
            frame = frame.f_back
            depth -= 1

        # Bind the custom value and log with loguru
        bound_logger = logger.bind(tracing_id=TRACING_ID)
        bound_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Define the log format from settings
LOG_FORMAT = _get_setting(
    "CONSOLE_LOG_FORMAT",
    (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS Z}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{extra[tracing_id]}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ),
)


def setup_logging(log_level: Optional[str] = None):
    """
    Setup loguru-based logging that intercepts standard Python logging.

    Args:
        log_level: The minimum log level to capture (default: from settings or DEBUG)
    """
    # Get log level from settings if not provided
    if log_level is None:
        log_level_str = _get_setting("LOG_LEVEL", "DEBUG")
        log_level_int = getattr(logging, log_level_str.upper(), logging.DEBUG)
    elif isinstance(log_level, str):
        log_level_int = getattr(logging, log_level.upper(), logging.DEBUG)
        log_level_str = log_level.upper()
    else:
        log_level_int = log_level
        log_level_str = "DEBUG"

    # Check if console logging is enabled
    if not _get_setting("CONSOLE_LOGGING_ENABLED", True):
        return
    # Configure loguru
    logger.remove()  # Remove default loguru handler
    logger.add(sys.stdout, format=LOG_FORMAT, level=log_level_str)

    # Get the root logger
    root_logger = logging.getLogger()

    # Clear all existing handlers from the root logger
    root_logger.handlers = []

    # Set the intercept handler as the only handler for the root logger
    root_logger.addHandler(InterceptHandler())
    root_logger.setLevel(log_level_int)

    # Prevent propagation to parent loggers unless explicitly needed (optional, adjust as needed)
    root_logger.propagate = False

    # Clear handlers from all existing named loggers to prevent duplication
    for logger_name in logging.Logger.manager.loggerDict:
        existing_logger = logging.getLogger(logger_name)
        existing_logger.handlers = []  # Remove all handlers
        existing_logger.addHandler(InterceptHandler())
        existing_logger.setLevel(log_level_int)
        existing_logger.propagate = False  # Prevent propagation to root logger

    # Add DLT logging intercept if enabled
    if _get_setting("ENABLE_DLT_LOGGING_INTERCEPT", True):
        logger_dlt = logging.getLogger("dlt")
        logger_dlt.addHandler(
            InterceptHandler()
        )  # Hack for dlt, since it's lazily initialised


def get_db_connection(db_path: Optional[str] = None, max_retries: int = 3) -> Optional[duckdb.DuckDBPyConnection]:
    """Get or create database connection with retry logic for lock conflicts."""
    global _db_connection
    if _db_connection is None:
        # Get DB path from settings if not provided
        if db_path is None:
            db_path = _get_setting("LOGGER_DB_PATH", "output/journals.duckdb")

        # Ensure db_path is a string and convert to absolute path if relative
        if db_path is None:
            db_path = "output/journals.duckdb"

        # Convert to absolute path if it's relative
        if not os.path.isabs(db_path):
            # If relative, make it relative to project root (two levels up from journals/)
            project_root = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(project_root, db_path)

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Retry logic for database connection with exponential backoff
        for attempt in range(max_retries):
            try:
                _db_connection = duckdb.connect(db_path)
                _ensure_job_logs_table()
                if attempt > 0:
                    print(f"Successfully connected to database on attempt {attempt + 1}")
                break
            except Exception as e:
                if "lock" in str(e).lower() or "conflicting" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        print(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"Failed to connect to database after {max_retries} attempts: {e}")
                        print("Continuing with console-only logging...")
                        _db_connection = None
                        break
                else:
                    print(f"Database connection error: {e}")
                    print("Continuing with console-only logging...")
                    _db_connection = None
                    break
    
    return _db_connection


def _ensure_job_logs_table():
    """Ensure the job_logs table exists."""
    global _db_connection
    if _db_connection is None:
        return

    try:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS job_logs (
            id                UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            project_name      TEXT            NOT NULL,
            module_name       TEXT,
            function_name     TEXT,
            run_id            UUID            NOT NULL,
            timestamp         TIMESTAMPTZ     NOT NULL DEFAULT now(),
            level             TEXT            NOT NULL CHECK (level IN (
                               'DEBUG','INFO','WARNING','ERROR','CRITICAL'
                             )) DEFAULT 'INFO',
            action            TEXT,
            message           TEXT,
            success           BOOLEAN,
            status_code       INT,
            duration_ms       BIGINT,
            request_method    TEXT,
            context           JSON DEFAULT '{}'
        );
        """
        _db_connection.execute(create_table_sql)
    except Exception as e:
        print(f"Failed to create job_logs table: {e}")
        # Don't raise, just continue with console logging


class DatabaseLogHandler:
    """Handler to write logs to the job_logs database table."""

    def __init__(self, db_path: Optional[str] = None):
        # Get DB path from settings if not provided
        if db_path is None:
            db_path = _get_setting("LOGGER_DB_PATH", "output/journals.duckdb")

        # Convert to absolute path if it's relative
        if db_path and not os.path.isabs(db_path):
            # If relative, make it relative to project root (two levels up from journals/)
            project_root = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(project_root, db_path)

        self.db_path = db_path
        self.connection = get_db_connection(db_path)
        self.db_available = self.connection is not None

    def log_to_db(
        self,
        module_name: str,
        level: str = "INFO",
        action: Optional[str] = None,
        message: Optional[str] = None,
        function_name: Optional[str] = None,
        success: Optional[bool] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        request_method: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log an entry to the database."""
        # Skip database logging if connection is not available
        if not self.db_available or not self.connection:
            return
            
        try:
            insert_sql = """
            INSERT INTO job_logs (
                project_name, module_name, function_name, run_id, level,
                action, message, success, status_code, duration_ms,
                request_method, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.connection.execute(
                insert_sql,
                [
                    PROJECT_NAME,
                    module_name,
                    function_name,
                    RUN_ID,
                    level,
                    action,
                    message,
                    success,
                    status_code,
                    duration_ms,
                    request_method,
                    json.dumps(context or {}),
                ],
            )
        except Exception as e:
            # Mark database as unavailable and continue with console logging
            self.db_available = False
            if _get_setting("LOGGER_ENABLED", True):
                print(f"Database logging failed, falling back to console only: {e}")


class EnhancedLogger:
    """Enhanced logger with database integration."""

    def __init__(self, module_name: str, db_path: Optional[str] = None):
        self.module_name = module_name
        self.db_handler = (
            DatabaseLogHandler(db_path)
            if _get_setting("LOGGER_ENABLED", True)
            else None
        )
        self.loguru_logger = logger.bind(tracing_id=TRACING_ID, name=module_name)

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method."""
        # Log to loguru (console) if enabled
        if _get_setting("CONSOLE_LOGGING_ENABLED", True):
            getattr(self.loguru_logger, level.lower())(message)

        # Log to database if enabled and handler exists
        if self.db_handler and _get_setting("LOGGER_ENABLED", True):
            self.db_handler.log_to_db(
                module_name=self.module_name,
                level=level.upper(),
                message=message,
                **kwargs,
            )

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

    def log_spider_action(
        self,
        action: str,
        message: str,
        success: bool = True,
        level: Optional[str] = None,
        request_method: str = "GET",
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log spider-specific actions.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, automatically determined: INFO for success, ERROR for failure.
        """
        # Determine log level if not explicitly provided
        if level is None:
            level = "INFO" if success else "ERROR"

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level.upper() not in valid_levels:
            level = "INFO" if success else "ERROR"

        # Add request_url to context if provided
        if context is None:
            context = {}

        self._log(
            level=level,
            message=message,
            action=action,
            success=success,
            request_method=request_method,
            status_code=status_code,
            duration_ms=duration_ms,
            context=context,
        )

    def log_pipeline_action(
        self,
        action: str,
        message: str,
        success: bool = True,
        level: Optional[str] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log pipeline-specific actions.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, automatically determined: INFO for success, ERROR for failure.
        """
        # Determine log level if not explicitly provided
        if level is None:
            level = "INFO" if success else "ERROR"

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level.upper() not in valid_levels:
            level = "INFO" if success else "ERROR"

        self._log(
            level=level,
            message=message,
            action=action,
            success=success,
            duration_ms=duration_ms,
            context=context,
        )

    def log_middleware_action(
        self,
        action: str,
        message: str,
        success: bool = True,
        level: Optional[str] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log middleware-specific actions.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, automatically determined: INFO for success, ERROR for failure.
        """
        # Determine log level if not explicitly provided
        if level is None:
            level = "INFO" if success else "ERROR"

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level.upper() not in valid_levels:
            level = "INFO" if success else "ERROR"

        self._log(
            level=level,
            message=message,
            action=action,
            success=success,
            duration_ms=duration_ms,
            context=context,
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


def log_execution(action: Optional[str] = None):
    """Decorator to automatically log function execution with timing."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the module name from the function
            module_name = func.__module__
            function_name = func.__name__
            action_name = action or f"{function_name}_execution"

            # Create logger for this module
            enhanced_logger = EnhancedLogger(module_name)

            start_time = time.time()
            try:
                enhanced_logger.info(
                    f"Starting {action_name}",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                )

                result = func(*args, **kwargs)

                duration_ms = int((time.time() - start_time) * 1000)
                enhanced_logger.info(
                    f"Completed {action_name} in {duration_ms}ms",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                enhanced_logger.log_exception(action_name, e)
                enhanced_logger._log(
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
def timed_operation(enhanced_logger: EnhancedLogger, action: str, **log_kwargs):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        enhanced_logger.info(f"Starting {action}", action=action, **log_kwargs)
        yield
        duration_ms = int((time.time() - start_time) * 1000)
        enhanced_logger.info(
            f"Completed {action} in {duration_ms}ms",
            action=action,
            success=True,
            duration_ms=duration_ms,
            **log_kwargs,
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        enhanced_logger.log_exception(action, e)
        enhanced_logger._log(
            level="ERROR",
            message=f"Failed {action} after {duration_ms}ms",
            action=action,
            success=False,
            duration_ms=duration_ms,
            **log_kwargs,
        )
        raise


def get_logger(name: str):
    """
    Get a loguru logger with tracing ID bound.

    Args:
        name: The logger name (typically __name__)

    Returns:
        A loguru logger instance with tracing_id bound
    """
    return logger.bind(tracing_id=TRACING_ID, name=name)


def get_db_logger(name: str, db_path: Optional[str] = None) -> EnhancedLogger:
    """
    Get an enhanced logger with database integration.

    Args:
        name: The module name (typically __name__)
        db_path: Path to the DuckDB database

    Returns:
        An EnhancedLogger instance
    """
    return EnhancedLogger(name, db_path)
