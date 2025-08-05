"""Athena transfer functionality for tp-logger using DLT resources."""

import dlt
import duckdb
import os
from typing import Iterator, Dict, Any

from ..setup import get_config
from .columns_schema import JOB_LOGS_COLUMNS


def _get_logger():
    """Get logger instance, importing at runtime to avoid circular imports."""
    from ..logging import get_logger
    return get_logger("athena")


@dlt.resource(name="job_logs", write_disposition="append", columns=JOB_LOGS_COLUMNS)
def job_logs_resource(db_path: str, dataset_name: str) -> Iterator[Dict[str, Any]]:
    """
    A DLT resource that reads all job logs from the source DuckDB database.
    This function is completely self-contained to avoid DLT context conflicts.
    """
    # A resource should be self-contained and create its own connection
    with duckdb.connect(db_path, read_only=True) as conn:
        
        # Query all columns from the job_logs table
        query = f"""
        SELECT 
            *
        FROM {dataset_name}.job_logs
        ORDER BY timestamp DESC
        """
        
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Yield each row as a dictionary
        # This streams results without loading the whole table into memory
        for row in cursor.fetchall():
            yield dict(zip(columns, row))


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
            
        if not all([config.aws_region, config.athena_database, config.athena_s3_staging_bucket]):
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
            dataset_name="transferred_logs"
        )
        
        print("[ATHENA] Transfer pipeline created successfully")
        
        # Run the pipeline with the resource - pass parameters to avoid context conflicts
        print("[ATHENA] Starting data transfer...")
        load_info = transfer_pipeline.run(job_logs_resource(config.db_path, config.dataset_name))
        
        print(f"[ATHENA] Transfer completed successfully")
        return True
        
    except Exception as e:
        print(f"[ATHENA] ERROR: Transfer failed: {type(e).__name__}: {str(e)}")
        return False