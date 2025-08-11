"""Configuration management for dlt-logger."""

import os
from typing import Optional

from ..utils.helpers import detect_project_root, resolve_project_path


class LoggerConfig:
    """Configuration class for dlt-logger."""

    def __init__(
        self,
        project_name: str,
        log_level: str,
        pipeline_name: str,
        dataset_name: str,
        table_name: str,
        db_path: Optional[str] = None,
        console_logging: bool = True,
        sync_to_s3: bool = False,
        aws_s3_bucket: Optional[str] = None,
        aws_s3_key_prefix: str = "logs/",
        sync_interval_minutes: int = 60,
        athena_destination: bool = False,
        aws_region: Optional[str] = None,
        athena_database: Optional[str] = None,
        athena_s3_staging_bucket: Optional[str] = None,
        project_root: Optional[str] = None,
    ):
        self.project_name = project_name
        self.log_level = log_level.upper()
        self.console_logging = console_logging
        self.pipeline_name = pipeline_name
        self.dataset_name = dataset_name
        self.table_name = table_name
        self.sync_to_s3 = sync_to_s3
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_s3_key_prefix = aws_s3_key_prefix
        self.sync_interval_minutes = sync_interval_minutes
        self.athena_destination = athena_destination
        self.aws_region = aws_region
        self.athena_database = athena_database
        self.athena_s3_staging_bucket = athena_s3_staging_bucket

        # Auto-detect project root if not provided
        if project_root is None:
            self.project_root = detect_project_root(caller_frame_depth=4)
        else:
            self.project_root = os.path.abspath(project_root)

        # Resolve database path relative to project root
        if db_path is None:
            db_path = "./logs/app.duckdb"
        self.db_path = resolve_project_path(db_path, self.project_root)

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
        raise ValueError(
            "Logger configuration not initialized. Please call setup_logging() first with "
            "required parameters: project_name, log_level, pipeline_name, dataset_name, table_name"
        )
    return _config


def set_config(config: LoggerConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
