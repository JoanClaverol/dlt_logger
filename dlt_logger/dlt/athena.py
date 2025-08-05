"""Athena transfer functionality for tp-logger using DLT resources."""

import os
from collections.abc import Iterator
from typing import Any

import dlt
import duckdb

from ..setup import get_config
from .columns_schema import JOB_LOGS_COLUMNS


def _get_logger():
    """Get logger instance, importing at runtime to avoid circular imports."""
    from ..logging import get_logger

    return get_logger("athena")


@dlt.resource(
    name="job_logs",
    write_disposition="merge",
    columns=JOB_LOGS_COLUMNS,
    parallelized=True,
    merge_key="_dlt_id",
    table_format="iceberg"

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

            # Yield batch as a list of dictionaries
            batch_data = [dict(zip(columns, row)) for row in batch_rows]
            yield batch_data


def transfer_to_athena() -> bool:
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
            message="Starting Athena transfer process",
            success=True,
            context={
                "source_db": config.db_path,
                "dataset": config.dataset_name,
                "aws_region": config.aws_region,
                "athena_database": config.athena_database,
                "s3_staging_bucket": config.athena_s3_staging_bucket
            }
        )

        # Validate Athena configuration
        if not config.athena_destination:
            logger.log_action(
                action="athena_validation",
                message="Athena transfer failed: athena_destination must be True",
                success=False,
                context={"athena_destination": config.athena_destination}
            )
            return False

        if not all(
            [config.aws_region, config.athena_database, config.athena_s3_staging_bucket]
        ):
            logger.log_action(
                action="athena_validation",
                message="Athena transfer failed: Missing required configuration",
                success=False,
                context={
                    "aws_region": config.aws_region,
                    "athena_database": config.athena_database,
                    "athena_s3_staging_bucket": config.athena_s3_staging_bucket
                }
            )
            return False

        # Check if source database exists
        if not os.path.exists(config.db_path):
            logger.log_action(
                action="athena_validation",
                message="Athena transfer failed: Source database does not exist",
                success=False,
                context={"db_path": config.db_path}
            )
            return False

        # Log configuration validation success
        logger.info(
            "Athena configuration validated successfully",
            context={
                "database": config.db_path,
                "dataset": config.dataset_name,
                "aws_region": config.aws_region,
                "athena_database": config.athena_database
            }
        )

        # Create a clean, isolated pipeline to Athena destination
        transfer_pipeline = dlt.pipeline(
            pipeline_name="athena_log_transfer",
            destination=dlt.destinations.athena(lakeformation_config=None),
            dataset_name=config.dataset_name,  # Use configured dataset name
        )

        logger.info("Athena transfer pipeline created successfully")

        # Run the pipeline with the resource - pass parameters to avoid context conflicts
        logger.info("Starting data transfer to Athena...")
        transfer_pipeline.run(job_logs_resource(config.db_path, config.dataset_name))

        # Log successful completion
        logger.log_action(
            action="athena_transfer_complete",
            message="Athena transfer completed successfully",
            success=True,
            context={
                "source_db": config.db_path,
                "dataset": config.dataset_name,
                "destination_pipeline": "athena_log_transfer"
            }
        )
        return True

    except Exception as e:
        # Log failure with exception details
        logger.log_action(
            action="athena_transfer_error",
            message=f"Athena transfer failed: {str(e)}",
            success=False,
            context={
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "source_db": config.db_path,
                "dataset": config.dataset_name
            }
        )
        return False
