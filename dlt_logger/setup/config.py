"""Configuration management for dlt-logger."""

import os
from typing import Optional


class LoggerConfig:
    """Configuration class for dlt-logger."""

    def __init__(
        self,
        project_name: str = "dlt_logger_app",
        db_path: Optional[str] = None,
        log_level: str = "INFO",
        console_logging: bool = True,
        pipeline_name: str = "dlt_logger_pipeline",
        dataset_name: str = "dlt_logger_logs",
        sync_to_s3: bool = False,
        aws_s3_bucket: Optional[str] = None,
        aws_s3_key_prefix: str = "logs/",
        sync_interval_minutes: int = 60,
        athena_destination: bool = False,
        aws_region: Optional[str] = None,
        athena_database: Optional[str] = None,
        athena_s3_staging_bucket: Optional[str] = None,
    ):
        self.project_name = project_name
        self.db_path = db_path or "./logs/app.duckdb"
        self.log_level = log_level.upper()
        self.console_logging = console_logging
        self.pipeline_name = pipeline_name
        self.dataset_name = dataset_name
        self.sync_to_s3 = sync_to_s3
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_s3_key_prefix = aws_s3_key_prefix
        self.sync_interval_minutes = sync_interval_minutes
        self.athena_destination = athena_destination
        self.aws_region = aws_region
        self.athena_database = athena_database
        self.athena_s3_staging_bucket = athena_s3_staging_bucket

        # Validate S3 configuration
        if self.sync_to_s3 and not self.aws_s3_bucket:
            raise ValueError("aws_s3_bucket is required when sync_to_s3=True")

        # Validate Athena configuration
        if self.athena_destination:
            if not self.aws_region:
                raise ValueError("aws_region is required when athena_destination=True")
            if not self.athena_database:
                raise ValueError(
                    "athena_database is required when athena_destination=True"
                )
            if not self.athena_s3_staging_bucket:
                raise ValueError(
                    "athena_s3_staging_bucket is required when athena_destination=True"
                )

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
