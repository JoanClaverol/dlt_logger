"""Tests for tp_logger.models module."""

import json
from datetime import datetime
from uuid import UUID, uuid4
import pytest

from tp_logger.models import LogEntry


class TestLogEntry:
    """Test LogEntry model."""
    
    def test_default_log_entry(self):
        """Test creating a log entry with required fields only."""
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4()
        )
        
        assert entry.project_name == "test_project"
        assert isinstance(entry.run_id, UUID)
        assert isinstance(entry.id, UUID)
        assert isinstance(entry.timestamp, datetime)
        assert entry.level == "INFO"
        assert entry.context == {}
    
    def test_full_log_entry(self):
        """Test creating a log entry with all fields."""
        run_id = uuid4()
        entry_id = uuid4()
        now = datetime.now()
        
        entry = LogEntry(
            id=entry_id,
            project_name="test_project",
            module_name="test_module",
            function_name="test_function",
            run_id=run_id,
            timestamp=now,
            level="ERROR",
            action="test_action",
            message="Test message",
            success=False,
            status_code=500,
            duration_ms=1500,
            request_method="POST",
            context={"error": "test error", "retry_count": 3}
        )
        
        assert entry.id == entry_id
        assert entry.project_name == "test_project"
        assert entry.module_name == "test_module"
        assert entry.function_name == "test_function"
        assert entry.run_id == run_id
        assert entry.timestamp == now
        assert entry.level == "ERROR"
        assert entry.action == "test_action"
        assert entry.message == "Test message"
        assert entry.success is False
        assert entry.status_code == 500
        assert entry.duration_ms == 1500
        assert entry.request_method == "POST"
        assert entry.context == {"error": "test error", "retry_count": 3}
    
    def test_level_validation(self):
        """Test that level field validates allowed values."""
        # Valid levels should work
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            entry = LogEntry(
                project_name="test_project",
                run_id=uuid4(),
                level=level
            )
            assert entry.level == level
        
        # Invalid level should raise validation error
        with pytest.raises(ValueError):
            LogEntry(
                project_name="test_project",
                run_id=uuid4(),
                level="INVALID"
            )
    
    def test_context_validation_dict(self):
        """Test context validation with dictionary input."""
        context_dict = {"key1": "value1", "key2": 123, "nested": {"inner": "value"}}
        
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4(),
            context=context_dict
        )
        
        assert entry.context == context_dict
    
    def test_context_validation_json_string(self):
        """Test context validation with JSON string input."""
        context_dict = {"key": "value", "number": 42}
        json_string = json.dumps(context_dict)
        
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4(),
            context=json_string
        )
        
        assert entry.context == context_dict
    
    def test_context_validation_invalid_json(self):
        """Test context validation with invalid JSON string."""
        invalid_json = "not valid json"
        
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4(),
            context=invalid_json
        )
        
        # Should wrap in raw key
        assert entry.context == {"raw": invalid_json}
    
    def test_context_validation_empty(self):
        """Test context validation with None/empty values."""
        # None should become empty dict
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4(),
            context=None
        )
        assert entry.context == {}
        
        # Empty string should become empty dict
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4(),
            context=""
        )
        assert entry.context == {}
    
    def test_model_dump(self):
        """Test model serialization."""
        run_id = uuid4()
        entry = LogEntry(
            project_name="test_project",
            module_name="test_module",
            run_id=run_id,
            level="INFO",
            message="Test message",
            context={"key": "value"}
        )
        
        data = entry.model_dump()
        
        assert isinstance(data, dict)
        assert data["project_name"] == "test_project"
        assert data["module_name"] == "test_module"
        assert str(data["run_id"]) == str(run_id)  # Compare string representations
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["context"] == {"key": "value"}
        assert "id" in data
        assert "timestamp" in data
    
    def test_json_serialization(self):
        """Test JSON serialization with custom encoders."""
        entry = LogEntry(
            project_name="test_project",
            run_id=uuid4()
        )
        
        # Should be able to serialize to JSON
        json_str = entry.model_dump_json()
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        data = json.loads(json_str)
        assert data["project_name"] == "test_project"
        assert "id" in data
        assert "timestamp" in data