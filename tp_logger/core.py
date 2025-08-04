"""Core logging functionality for tp-logger."""

import json
import os
import sys
import time
import uuid
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Dict, Any, Callable

import duckdb
from loguru import logger

from .config import get_config


# Generate a unique run ID for this session
RUN_ID = str(uuid.uuid4())

# Database connection
_db_connection: Optional[duckdb.DuckDBPyConnection] = None


def _get_tracing_id() -> str:
    """Generate a tracing ID for this session."""
    return str(uuid.uuid4())[:8]


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


def get_db_connection(max_retries: int = 3) -> Optional[duckdb.DuckDBPyConnection]:
    """Get or create database connection with retry logic."""
    global _db_connection
    
    if _db_connection is None:
        config = get_config()
        db_path = config.db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                _db_connection = duckdb.connect(db_path)
                _ensure_job_logs_table()
                if attempt > 0:
                    print(f"Connected to database on attempt {attempt + 1}")
                break
            except Exception as e:
                if "lock" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Database locked, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database connection failed: {e}")
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


class TPLogger:
    """Main logger class for tp-logger."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.config = get_config()
        self.tracing_id = _get_tracing_id()
        self.connection = get_db_connection()
        self.loguru_logger = logger.bind(tracing_id=self.tracing_id, name=module_name)
    
    def _log_to_db(
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
    ):
        """Log entry to database."""
        if not self.connection:
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
                    self.config.project_name,
                    self.module_name,
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
            print(f"Database logging failed: {e}")
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method."""
        # Console logging
        if self.config.console_logging:
            getattr(self.loguru_logger, level.lower())(message)
        
        # Database logging
        self._log_to_db(level=level.upper(), message=message, **kwargs)
    
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