"""Pipeline management for tp-logger using DLT Hub."""

from typing import Optional
from uuid import uuid4

import dlt

from ..logging.models import LogEntry
from ..setup import get_config
from .columns_schema import JOB_LOGS_COLUMNS

# Global pipeline instance
_pipeline: Optional[dlt.Pipeline] = None

# Generate a unique run ID for this session
RUN_ID = uuid4()


def get_pipeline() -> dlt.Pipeline:
    """Get or create the DLT pipeline."""
    global _pipeline
    if _pipeline is None:
        config = get_config()

        # Add debugging for pipeline creation
        print("[LOGS PIPELINE] Creating new DLT pipeline...")
        print(f"[LOGS PIPELINE] Pipeline name: {config.pipeline_name}")
        print(f"[LOGS PIPELINE] Database path: {config.db_path}")
        print(f"[LOGS PIPELINE] Dataset name: {config.dataset_name}")

        # Ensure directory exists
        import os

        db_dir = os.path.dirname(config.db_path)
        if db_dir and not os.path.exists(db_dir):
            print(f"[LOGS PIPELINE] Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)

        try:
            # Set DLT working directory to be relative to the project root
            # This ensures .dlt folder is created in the right place
            dlt_working_dir = os.path.join(config.project_root, ".dlt_pipeline")
            os.makedirs(dlt_working_dir, exist_ok=True)

            _pipeline = dlt.pipeline(
                pipeline_name=config.pipeline_name,
                destination=dlt.destinations.duckdb(
                    credentials=f"duckdb:///{config.db_path}"
                ),
                dataset_name=config.dataset_name,
                pipelines_dir=dlt_working_dir,
            )
            print("[LOGS PIPELINE] Pipeline created successfully")
            print(f"[LOGS PIPELINE] Pipeline working directory: {_pipeline.working_dir}")
            print(f"[LOGS PIPELINE] Project root: {config.project_root}")
        except Exception as e:
            print(f"[LOGS PIPELINE] Failed to create pipeline: {type(e).__name__}: {str(e)}")
            raise
    else:
        config = get_config()
        print(f"[LOGS PIPELINE] Using existing pipeline for dataset: {config.dataset_name}")

    return _pipeline


def job_logs(log_entries: list[LogEntry]):
    """DLT resource for job logs with dynamic table name."""
    config = get_config()
    
    @dlt.resource(
        name=config.table_name,
        write_disposition="append",
        columns=JOB_LOGS_COLUMNS,
        max_table_nesting=0
    )
    def _job_logs_resource():
        for entry in log_entries:
            yield entry.model_dump()
    
    return _job_logs_resource()
