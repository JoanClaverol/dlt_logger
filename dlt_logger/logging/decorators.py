"""Decorators and context managers for dlt-logger."""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from .logger import TPLogger


def log_execution(
    action: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to automatically log function execution with timing."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            module_name = func.__module__
            function_name = func.__name__
            action_name = action or f"{function_name}_execution"

            dlt_logger = TPLogger(module_name)

            start_time = time.time()
            try:
                dlt_logger.info(
                    f"Starting {action_name}",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                )

                result = func(*args, **kwargs)

                duration_ms = int((time.time() - start_time) * 1000)
                dlt_logger.info(
                    f"Completed {action_name} in {duration_ms}ms",
                    action=action_name,
                    function_name=function_name,
                    success=True,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                dlt_logger.log_exception(action_name, e)
                dlt_logger._log(
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
def timed_operation(dlt_logger: TPLogger, action: str, **log_kwargs):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        dlt_logger.info(f"Starting {action}", action=action, **log_kwargs)
        yield
        duration_ms = int((time.time() - start_time) * 1000)
        dlt_logger.info(
            f"Completed {action} in {duration_ms}ms",
            action=action,
            success=True,
            duration_ms=duration_ms,
            **log_kwargs,
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        dlt_logger.log_exception(action, e)
        dlt_logger._log(
            level="ERROR",
            message=f"Failed {action} after {duration_ms}ms",
            action=action,
            success=False,
            duration_ms=duration_ms,
            **log_kwargs,
        )
        raise
