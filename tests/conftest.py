"""Pytest configuration and fixtures for dlt-logger tests."""

import os
import tempfile
import pytest
import duckdb

from dlt_logger.setup import LoggerConfig, set_config
from dlt_logger.setup.config import _config


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        yield db_path


@pytest.fixture
def test_config(temp_db_path):
    """Create a test configuration."""
    config = LoggerConfig(
        project_name="test_project",
        db_path=temp_db_path,
        log_level="DEBUG",
        console_logging=False,  # Disable console logging for tests
        dataset_name="test_logs",
        pipeline_name="test_pipeline",
    )
    return config


@pytest.fixture
def setup_test_logging(test_config):
    """Setup test logging configuration."""
    # Store original config
    global _config
    original_config = _config

    # Set test config
    set_config(test_config)

    yield test_config

    # Restore original config
    _config = original_config


@pytest.fixture
def sample_log_data():
    """Sample log data for testing."""
    return {
        "project_name": "test_project",
        "module_name": "test_module",
        "function_name": "test_function",
        "level": "INFO",
        "action": "test_action",
        "message": "Test message",
        "success": True,
        "duration_ms": 100,
        "context": {"key": "value"},
    }


@pytest.fixture
def mock_dlt_pipeline(monkeypatch):
    """Mock DLT pipeline for testing."""

    class MockPipeline:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.runs = []

        def run(self, resource_func):
            """Mock run method that stores data."""
            # If it's a resource function (generator), call it and collect data
            if hasattr(resource_func, "__call__"):
                try:
                    # Call the resource function with sample data
                    from tp_logger.models import LogEntry
                    from uuid import uuid4

                    sample_entries = [LogEntry(project_name="test", run_id=uuid4())]
                    result = list(resource_func(sample_entries))
                    self.runs.extend(result)
                    return {"status": "success", "records": len(result)}
                except Exception:
                    # Fallback: just record that run was called
                    self.runs.append("run_called")
                    return {"status": "success", "records": 1}
            else:
                self.runs.append(resource_func)
                return {"status": "success", "records": 1}

    def mock_pipeline(*args, **kwargs):
        return MockPipeline(*args, **kwargs)

    monkeypatch.setattr("dlt.pipeline", mock_pipeline)
    return MockPipeline


@pytest.fixture
def db_connection(temp_db_path):
    """Create a DuckDB connection for testing."""
    conn = duckdb.connect(temp_db_path)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    # Reset any global variables in the modules
    from dlt_logger.dlt import pipeline

    pipeline._pipeline = None

    yield

    # Clean up after test
    pipeline._pipeline = None
