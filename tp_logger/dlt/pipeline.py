"""Pipeline management for tp-logger using DLT Hub."""

from typing import Optional, List
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
        print("[PIPELINE] Creating new DLT pipeline...")
        print(f"[PIPELINE] Pipeline name: {config.pipeline_name}")
        print(f"[PIPELINE] Database path: {config.db_path}")
        print(f"[PIPELINE] Dataset name: {config.dataset_name}")

        # Ensure directory exists
        import os

        db_dir = os.path.dirname(config.db_path)
        if db_dir and not os.path.exists(db_dir):
            print(f"[PIPELINE] Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)

        try:
            _pipeline = dlt.pipeline(
                pipeline_name=config.pipeline_name,
                destination=dlt.destinations.duckdb(
                    credentials=f"duckdb:///{config.db_path}"
                ),
                dataset_name=config.dataset_name,
            )
            print("[PIPELINE] Pipeline created successfully")
            print(f"[PIPELINE] Pipeline working directory: {_pipeline.working_dir}")
        except Exception as e:
            print(f"[PIPELINE] Failed to create pipeline: {type(e).__name__}: {str(e)}")
            raise
    else:
        config = get_config()
        print(f"[PIPELINE] Using existing pipeline for dataset: {config.dataset_name}")

    return _pipeline


@dlt.resource(
    write_disposition="replace",
    columns=JOB_LOGS_COLUMNS,
)
def job_logs(log_entries: List[LogEntry]):
    """DLT resource for job logs."""
    for entry in log_entries:
        yield entry.model_dump()
