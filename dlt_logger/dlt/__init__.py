"""DLT operations for storage and transfer in dlt-logger.

This module handles DLT Hub integration for:
- DuckDB pipeline management and log storage
- AWS Athena transfer operations
- Schema management for log data
- Batch processing and resource management

Usage Examples:
    Pipeline operations:
        >>> from dlt_logger.dlt import get_pipeline, job_logs, RUN_ID
        >>> from dlt_logger.logging.models import LogEntry
        >>>
        >>> pipeline = get_pipeline()
        >>> log_entry = LogEntry(
        ...     project_name="test", run_id=RUN_ID, level="INFO", message="Test"
        ... )
        >>> pipeline.run(job_logs([log_entry]))

    Athena transfer:
        >>> from dlt_logger.dlt import transfer_logs_to_athena
        >>> from dlt_logger.setup import LoggerConfig, set_config
        >>>
        >>> config = LoggerConfig(
        ...     project_name="athena_demo",
        ...     log_level="INFO",
        ...     pipeline_name="athena_pipeline",
        ...     dataset_name="athena_logs",
        ...     table_name="log_events",
        ...     athena_destination=True,
        ...     aws_region="us-east-1",
        ...     athena_database="logs_db",
        ...     athena_s3_staging_bucket="my-logs-bucket"
        ... )
        >>> set_config(config)
        >>> success = transfer_logs_to_athena()
        >>> print(f"Transfer {'succeeded' if success else 'failed'}")

Note:
    This module requires DLT Hub and appropriate destination credentials.
    For Athena operations, valid AWS credentials and S3 bucket access are required.
"""

import warnings
from .athena import job_logs_resource, transfer_logs_to_athena
from .pipeline import RUN_ID, get_pipeline, job_logs


def transfer_to_athena() -> bool:
    """
    Transfer logs from local DuckDB to AWS Athena.
    
    .. deprecated:: 0.1.1
        Use `transfer_logs_to_athena` instead. This function will be removed in v0.2.0.
    
    Returns:
        bool: True if successful, False otherwise
    """
    warnings.warn(
        "transfer_to_athena is deprecated and will be removed in v0.2.0. "
        "Use transfer_logs_to_athena instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return transfer_logs_to_athena()

__all__ = [
    "get_pipeline",
    "job_logs",
    "RUN_ID",
    "job_logs_resource",
    "transfer_logs_to_athena",
    "transfer_to_athena",  # Backward compatibility (deprecated)
]
