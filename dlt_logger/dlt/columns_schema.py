"""Centralized DLT column schema definitions for dlt-logger."""

from typing import Any

# DLT column definitions for job_logs table
# Based on LogEntry model from dlt_logger/logging/models.py
# These type hints ensure DLT can properly infer column types even when values are None
JOB_LOGS_COLUMNS: Any = {
    # Optional string fields that may be None
    "function_name": {"data_type": "text"},
    "module_name": {"data_type": "text"},
    "action": {"data_type": "text"},
    "message": {"data_type": "text"},
    "request_method": {"data_type": "text"},
    # Optional boolean field
    "success": {"data_type": "bool"},
    # Optional integer fields
    "status_code": {"data_type": "bigint"},
    "duration_ms": {"data_type": "bigint"},
    # Context field kept as JSON to prevent column expansion
    "context": {"data_type": "json"},
    # Note: Required fields like id, project_name, run_id, timestamp, level
    # are automatically inferred by DLT from the Pydantic model and
    # don't need explicit hints
}
