"""Pipeline management for tp-logger using DLT Hub."""

from typing import Optional, List
from uuid import uuid4

import dlt

from .models import LogEntry
from .config import get_config


# Global pipeline instance
_pipeline: Optional[dlt.Pipeline] = None

# Generate a unique run ID for this session
RUN_ID = uuid4()


def get_pipeline() -> dlt.Pipeline:
    """Get or create the DLT pipeline."""
    global _pipeline
    if _pipeline is None:
        config = get_config()
        _pipeline = dlt.pipeline(
            pipeline_name=config.pipeline_name,
            destination="duckdb",
            dataset_name=config.dataset_name,
        )
    return _pipeline


@dlt.resource(
    write_disposition="append",
    columns={
        "id": {"data_type": "text"},
        "project_name": {"data_type": "text"},
        "module_name": {"data_type": "text"},
        "function_name": {"data_type": "text"},
        "run_id": {"data_type": "text"},
        "timestamp": {"data_type": "timestamp"},
        "level": {"data_type": "text"},
        "action": {"data_type": "text"},
        "message": {"data_type": "text"},
        "success": {"data_type": "bool"},
        "status_code": {"data_type": "bigint"},
        "duration_ms": {"data_type": "bigint"},
        "request_method": {"data_type": "text"},
        "context": {"data_type": "json"},
    },
)
def job_logs(log_entries: List[LogEntry]):
    """DLT resource for job logs."""
    for entry in log_entries:
        yield entry.model_dump()
