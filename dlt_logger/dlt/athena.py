"""Athena transfer functionality for tp-logger using DLT resources."""

import os
from collections.abc import Iterator
from typing import Any

import dlt
import duckdb

from ..setup import get_config
from ..logging.models import LogEntry
from .columns_schema import JOB_LOGS_COLUMNS


def _get_logger():
    """Get logger instance, importing at runtime to avoid circular imports."""
    from ..logging import get_logger

    return get_logger("athena")


@dlt.resource(
    name="job_logs",
    write_disposition="append",
    columns=JOB_LOGS_COLUMNS,
    parallelized=True,
    table_format="iceberg",
    max_table_nesting=0
)
def job_logs_resource(
    db_path: str, dataset_name: str, batch_size: int = 10000
) -> Iterator[list[dict[str, Any]]]:
    """
    A DLT resource that reads job logs from the source DuckDB database in batches.
    Uses batch processing and parallelization for improved performance.

    Args:
        db_path: Path to the source DuckDB database
        dataset_name: Name of the dataset containing job_logs table
        batch_size: Number of rows to process in each batch (default: 10000)
    """
    # A resource should be self-contained and create its own connection
    with duckdb.connect(db_path, read_only=True) as conn:
        # Query all columns from the job_logs table without expensive ORDER BY
        query = f"""
        SELECT
            *
        FROM {dataset_name}.job_logs
        """

        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Process rows in batches for better performance
        while True:
            batch_rows = cursor.fetchmany(batch_size)
            if not batch_rows:
                break

            # Convert batch to LogEntry models to ensure only valid fields are uploaded
            batch_data = []
            for row in batch_rows:
                row_dict = dict(zip(columns, row))
                try:
                    # Validate through LogEntry model and get only defined fields
                    log_entry = LogEntry(**row_dict)
                    batch_data.append(log_entry.model_dump())
                except Exception as e:
                    # Skip invalid entries but log the issue
                    print(f"[ATHENA] Skipping invalid log entry: {e}")
                    continue
            
            if batch_data:
                yield batch_data


def transfer_logs_to_athena() -> bool:
    """
    Transfer logs from local DuckDB to AWS Athena.
    Simplified implementation to avoid DLT context conflicts.

    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    logger = _get_logger()

    try:
        # Log transfer start with structured data
        logger.log_action(
            action="athena_transfer_start",
            message="Logging: Starting Athena transfer process",
            success=True,
        )

        # Validate Athena configuration
        if not config.athena_destination:
            logger.log_action(
                action="athena_validation",
                message="Logging: Athena transfer failed: athena_destination must be True",
                success=False,
            )
            return False

        if not all(
            [config.aws_region, config.athena_database, config.athena_s3_staging_bucket]
        ):
            logger.log_action(
                action="athena_validation",
                message="Logging: Athena transfer failed: Missing required configuration",
                success=False,
            )
            return False

        # Check if source database exists
        if not os.path.exists(config.db_path):
            logger.log_action(
                action="athena_validation",
                message="Athena transfer failed: Source database does not exist",
                success=False,
            )
            return False

        # Log configuration validation success
        logger.info("Logging: Athena configuration validated successfully")

        # Create a clean, isolated pipeline to Athena destination
        transfer_pipeline = dlt.pipeline(
            pipeline_name="athena_log_transfer",
            destination=dlt.destinations.athena(lakeformation_config=None),
            dataset_name=config.dataset_name,  # Use configured dataset name
        )

        logger.info("Logging: Athena transfer pipeline created successfully")

        # Run the pipeline with the resource - pass parameters to avoid conflicts
        logger.info("Logging: Starting data transfer to Athena...")
        transfer_pipeline.run(job_logs_resource(config.db_path, config.dataset_name))

        # Log successful completion
        logger.log_action(
            action="athena_transfer_complete",
            message="Logging: Athena transfer completed successfully",
            success=True,
        )
        return True

    except Exception as e:
        # Log failure with exception details
        logger.log_action(
            action="athena_transfer_error",
            message=f"Logging: Athena transfer failed: {str(e)}",
            success=False,
        )
        return False
