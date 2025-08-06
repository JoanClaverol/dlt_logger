"""Logging handlers for tp-logger."""

import logging
import sys

from loguru import logger

from ..setup import get_config


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
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stdout, format=log_format, level=config.log_level)

    # Setup intercept handler for standard logging
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(InterceptHandler())
    root_logger.setLevel(getattr(logging, config.log_level))
    root_logger.propagate = False
