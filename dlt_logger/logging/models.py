"""Pydantic models for tp-logger data structures."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Model for a log entry matching the job_logs table schema."""

    id: UUID = Field(default_factory=uuid4)
    project_name: str
    module_name: Optional[str] = None
    function_name: Optional[str] = None
    run_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    action: Optional[str] = None
    message: Optional[str] = None
    success: Optional[bool] = None
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    request_method: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)}
