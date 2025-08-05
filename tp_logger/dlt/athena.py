"""Athena transfer functionality for tp-logger using DLT resources."""

import dlt
import duckdb
import os
from typing import Iterator, Dict, Any, List

from ..setup import get_config
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
)
def job_logs_resource(
    db_path: str, dataset_name: str, batch_size: int = 10000
) -> Iterator[List[Dict[str, Any]]]:
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

    try:
        print("[ATHENA] Starting Athena transfer process")

        # Validate Athena configuration
        if not config.athena_destination:
            print("[ATHENA] ERROR: athena_destination must be True")
            return False

        if not all(
            [config.aws_region, config.athena_database, config.athena_s3_staging_bucket]
        ):
            print("[ATHENA] ERROR: Missing required Athena configuration")
            return False

        # Check if source database exists
        if not os.path.exists(config.db_path):
            print(f"[ATHENA] ERROR: Source database does not exist: {config.db_path}")
            return False

        print(f"[ATHENA] Using database: {config.db_path}")
        print(f"[ATHENA] Using dataset: {config.dataset_name}")
        print(f"[ATHENA] AWS Region: {config.aws_region}")
        print(f"[ATHENA] Athena Database: {config.athena_database}")

        # Create a clean, isolated pipeline to Athena destination
        transfer_pipeline = dlt.pipeline(
            pipeline_name="athena_log_transfer",
            destination=dlt.destinations.athena(lakeformation_config=None),
            dataset_name="transferred_logs",
        )

        print("[ATHENA] Transfer pipeline created successfully")

        # Run the pipeline with the resource - pass parameters to avoid context conflicts
        print("[ATHENA] Starting data transfer...")
        transfer_pipeline.run(job_logs_resource(config.db_path, config.dataset_name))

        print("[ATHENA] Transfer completed successfully")
        return True

    except Exception as e:
        print(f"[ATHENA] ERROR: Transfer failed: {type(e).__name__}: {str(e)}")
        return False
