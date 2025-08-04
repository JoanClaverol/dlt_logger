"""Configuration management for tp-logger."""

import os
from typing import Optional


class LoggerConfig:
    """Configuration class for tp-logger."""
    
    def __init__(
        self,
        project_name: str = "tp_logger_app",
        db_path: Optional[str] = None,
        log_level: str = "INFO",
        console_logging: bool = True,
        pipeline_name: str = "tp_logger_pipeline",
        sync_to_s3: bool = False,
        aws_s3_bucket: Optional[str] = None,
        aws_s3_key_prefix: str = "logs/",
        sync_interval_minutes: int = 60,
    ):
        self.project_name = project_name
        self.db_path = db_path or "./logs/app.duckdb"
        self.log_level = log_level.upper()
        self.console_logging = console_logging
        self.pipeline_name = pipeline_name
        self.sync_to_s3 = sync_to_s3
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_s3_key_prefix = aws_s3_key_prefix
        self.sync_interval_minutes = sync_interval_minutes
        
        # Validate S3 configuration
        if self.sync_to_s3 and not self.aws_s3_bucket:
            raise ValueError("aws_s3_bucket is required when sync_to_s3=True")
    
    def get_setting(self, key: str, default=None):
        """Get setting from environment or config."""
        env_key = f"TP_LOGGER_{key.upper()}"
        return os.getenv(env_key, getattr(self, key.lower(), default))


# Global config instance
_config: Optional[LoggerConfig] = None


def get_config() -> LoggerConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = LoggerConfig()
    return _config


def set_config(config: LoggerConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config