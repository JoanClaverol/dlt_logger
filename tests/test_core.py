"""Tests for dlt_logger.core module."""

import time
import pytest
from unittest.mock import patch, MagicMock

from dlt_logger import (
    setup_logging,
    get_logger,
    log_execution,
    timed_operation,
    TPLogger,
)
from dlt_logger.dlt import get_pipeline, transfer_to_athena
from dlt_logger.setup import get_config


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_with_kwargs(self, temp_db_path):
        """Test setup logging with keyword arguments."""
        setup_logging(
            project_name="test_project",
            db_path=temp_db_path,
            log_level="DEBUG",
            console_logging=False,
            dataset_name="test_dataset",
        )

        config = get_config()
        assert config.project_name == "test_project"
        assert config.db_path == temp_db_path
        assert config.log_level == "DEBUG"
        assert config.console_logging is False
        assert config.dataset_name == "test_dataset"

    def test_setup_logging_defaults(self):
        """Test setup logging with default values."""
        setup_logging(project_name="minimal_test")

        config = get_config()
        assert config.project_name == "minimal_test"
        assert config.log_level == "INFO"
        assert config.console_logging is True

    @patch("tp_logger.logger.setup_console_logging")
    def test_setup_logging_console_enabled(self, mock_setup_console, temp_db_path):
        """Test that console logging is setup when enabled."""
        setup_logging(project_name="test_project", console_logging=True)

        mock_setup_console.assert_called_once()

    @patch("tp_logger.logger.setup_console_logging")
    def test_setup_logging_console_disabled(self, mock_setup_console, temp_db_path):
        """Test that console logging is not setup when disabled."""
        setup_logging(project_name="test_project", console_logging=False)

        mock_setup_console.assert_not_called()


class TestTPLogger:
    """Test TPLogger class."""

    def test_logger_creation(self, setup_test_logging):
        """Test creating a TPLogger instance."""
        logger = TPLogger("test_module")

        assert logger.module_name == "test_module"
        assert logger.config.project_name == "test_project"

    def test_basic_logging_methods(self, setup_test_logging):
        """Test basic logging methods."""
        logger = TPLogger("test_module")

        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_action(self, setup_test_logging, mock_dlt_pipeline):
        """Test log_action method."""
        logger = TPLogger("test_module")

        logger.log_action(
            action="test_action",
            message="Test message",
            success=True,
            duration_ms=100,
            context={"key": "value"},
        )

        # Verify pipeline was called (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_log_exception(self, setup_test_logging, mock_dlt_pipeline):
        """Test log_exception method."""
        logger = TPLogger("test_module")

        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.log_exception("test_action", e)

        # Verify pipeline was called (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_create_log_entry(self, setup_test_logging):
        """Test _create_log_entry method."""
        logger = TPLogger("test_module")

        entry = logger._create_log_entry(
            level="INFO", message="Test message", action="test_action", success=True
        )

        assert entry.project_name == "test_project"
        assert entry.module_name == "test_module"
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.action == "test_action"
        assert entry.success is True


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger(self, setup_test_logging):
        """Test get_logger returns TPLogger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, TPLogger)
        assert logger.module_name == "test_module"


class TestLogExecutionDecorator:
    """Test log_execution decorator."""

    def test_log_execution_default_action(self, setup_test_logging, mock_dlt_pipeline):
        """Test log_execution decorator with default action name."""

        @log_execution()
        def test_function():
            return "success"

        result = test_function()

        assert result == "success"

        # Verify logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_log_execution_custom_action(self, setup_test_logging, mock_dlt_pipeline):
        """Test log_execution decorator with custom action name."""

        @log_execution("custom_action")
        def test_function():
            time.sleep(0.01)  # Small delay to test timing
            return "success"

        result = test_function()

        assert result == "success"

        # Verify logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_log_execution_with_exception(self, setup_test_logging, mock_dlt_pipeline):
        """Test log_execution decorator when function raises exception."""

        @log_execution("error_action")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Verify error logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_log_execution_with_args_kwargs(
        self, setup_test_logging, mock_dlt_pipeline
    ):
        """Test log_execution decorator preserves function arguments."""

        @log_execution()
        def function_with_args(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = function_with_args("a", "b", kwarg1="c")

        assert result == "a-b-c"


class TestTimedOperation:
    """Test timed_operation context manager."""

    def test_timed_operation_success(self, setup_test_logging, mock_dlt_pipeline):
        """Test timed_operation context manager with successful operation."""
        logger = TPLogger("test_module")

        with timed_operation(logger, "test_operation"):
            time.sleep(0.01)  # Small delay

        # Verify logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_timed_operation_with_exception(
        self, setup_test_logging, mock_dlt_pipeline
    ):
        """Test timed_operation context manager when operation raises exception."""
        logger = TPLogger("test_module")

        with pytest.raises(ValueError, match="Test error"):
            with timed_operation(logger, "failing_operation"):
                raise ValueError("Test error")

        # Verify error logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0

    def test_timed_operation_with_kwargs(self, setup_test_logging, mock_dlt_pipeline):
        """Test timed_operation with additional keyword arguments."""
        logger = TPLogger("test_module")

        with timed_operation(logger, "test_operation", context={"key": "value"}):
            pass

        # Verify logging occurred (mocked)
        pipeline = get_pipeline()
        assert len(pipeline.runs) > 0


class TestPipelineIntegration:
    """Test DLT pipeline integration."""

    def test_get_pipeline(self, setup_test_logging):
        """Test get_pipeline creates pipeline with correct configuration."""
        pipeline = get_pipeline()

        assert pipeline is not None
        # Just verify pipeline was created successfully
        assert hasattr(pipeline, "run")

    def test_pipeline_singleton(self, setup_test_logging):
        """Test that get_pipeline returns the same instance."""
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()

        assert pipeline1 is pipeline2


class TestIntegration:
    """Integration tests."""

    def test_full_logging_workflow(self, temp_db_path, mock_dlt_pipeline):
        """Test complete logging workflow from setup to logging."""
        # Setup logging
        setup_logging(
            project_name="integration_test",
            db_path=temp_db_path,
            log_level="INFO",
            console_logging=False,
        )

        # Get logger and log some actions
        logger = get_logger("integration_module")

        logger.info("Integration test started")
        logger.log_action(
            action="integration_action",
            message="Integration test action",
            success=True,
            context={"test": "integration"},
        )

        # Use decorator
        @log_execution("integration_function")
        def test_integration_function():
            return "integration_success"

        result = test_integration_function()
        assert result == "integration_success"

        # Use context manager
        with timed_operation(logger, "integration_operation"):
            time.sleep(0.001)

        # Verify all logging occurred
        pipeline = get_pipeline()
        assert len(pipeline.runs) >= 4  # At least 4 logging operations


class TestTransferToAthena:
    """Test transfer_to_athena function."""

    def test_transfer_to_athena_athena_destination_false(self, setup_test_logging):
        """Test transfer_to_athena when athena_destination is False."""
        config = get_config()
        config.athena_destination = False

        with pytest.raises(ValueError, match="athena_destination must be True"):
            transfer_to_athena()

    def test_transfer_to_athena_missing_aws_region(self, setup_test_logging):
        """Test transfer_to_athena when aws_region is missing."""
        config = get_config()
        config.athena_destination = True
        config.aws_region = None
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = "test-bucket"

        with pytest.raises(
            ValueError,
            match="aws_region, athena_database, and athena_s3_staging_bucket are required",
        ):
            transfer_to_athena()

    def test_transfer_to_athena_missing_athena_database(self, setup_test_logging):
        """Test transfer_to_athena when athena_database is missing."""
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = None
        config.athena_s3_staging_bucket = "test-bucket"

        with pytest.raises(
            ValueError,
            match="aws_region, athena_database, and athena_s3_staging_bucket are required",
        ):
            transfer_to_athena()

    def test_transfer_to_athena_missing_s3_staging_bucket(self, setup_test_logging):
        """Test transfer_to_athena when athena_s3_staging_bucket is missing."""
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = None

        with pytest.raises(
            ValueError,
            match="aws_region, athena_database, and athena_s3_staging_bucket are required",
        ):
            transfer_to_athena()

    @patch("tp_logger.athena.dlt.pipeline")
    @patch("tp_logger.athena.dlt.destinations.athena")
    @patch("tp_logger.athena.dlt.destinations.duckdb")
    def test_transfer_to_athena_success(
        self, mock_duckdb_dest, mock_athena_dest, mock_pipeline, setup_test_logging
    ):
        """Test successful transfer_to_athena execution."""
        # Setup config
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = "test-bucket"

        # Mock pipeline instances
        mock_duckdb_pipeline = MagicMock()
        mock_athena_pipeline = MagicMock()
        mock_pipeline.side_effect = [mock_duckdb_pipeline, mock_athena_pipeline]

        # Mock dataset and tables
        mock_dataset = MagicMock()
        mock_dataset.schema.tables.keys.return_value = ["job_logs"]
        mock_dataset.__getitem__.return_value.arrow.return_value = MagicMock()
        mock_duckdb_pipeline.dataset.return_value = mock_dataset

        # Mock destinations
        mock_athena_dest.return_value = MagicMock()
        mock_duckdb_dest.return_value = MagicMock()

        result = transfer_to_athena()

        assert result is True
        assert mock_pipeline.call_count == 2
        mock_athena_pipeline.run.assert_called_once()

    @patch("tp_logger.athena.dlt.pipeline")
    def test_transfer_to_athena_pipeline_error(self, mock_pipeline, setup_test_logging):
        """Test transfer_to_athena when pipeline creation fails."""
        # Setup config
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = "test-bucket"

        # Mock pipeline to raise an exception
        mock_pipeline.side_effect = Exception("Pipeline creation failed")

        result = transfer_to_athena()

        assert result is False

    @patch("tp_logger.athena.dlt.pipeline")
    @patch("tp_logger.athena.dlt.destinations.athena")
    @patch("tp_logger.athena.dlt.destinations.duckdb")
    def test_transfer_to_athena_upload_error(
        self, mock_duckdb_dest, mock_athena_dest, mock_pipeline, setup_test_logging
    ):
        """Test transfer_to_athena when table upload fails."""
        # Setup config
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = "test-bucket"

        # Mock pipeline instances
        mock_duckdb_pipeline = MagicMock()
        mock_athena_pipeline = MagicMock()
        mock_pipeline.side_effect = [mock_duckdb_pipeline, mock_athena_pipeline]

        # Mock dataset and tables
        mock_dataset = MagicMock()
        mock_dataset.schema.tables.keys.return_value = ["job_logs"]
        mock_dataset.__getitem__.return_value.arrow.return_value = MagicMock()
        mock_duckdb_pipeline.dataset.return_value = mock_dataset

        # Mock destinations
        mock_athena_dest.return_value = MagicMock()
        mock_duckdb_dest.return_value = MagicMock()

        # Mock athena pipeline run to fail
        mock_athena_pipeline.run.side_effect = Exception("Upload failed")

        result = transfer_to_athena()

        assert result is False

    @patch("tp_logger.athena.dlt.pipeline")
    @patch("tp_logger.athena.dlt.destinations.athena")
    @patch("tp_logger.athena.dlt.destinations.duckdb")
    def test_transfer_to_athena_skips_dlt_tables(
        self, mock_duckdb_dest, mock_athena_dest, mock_pipeline, setup_test_logging
    ):
        """Test transfer_to_athena skips DLT internal tables."""
        # Setup config
        config = get_config()
        config.athena_destination = True
        config.aws_region = "us-east-1"
        config.athena_database = "test_db"
        config.athena_s3_staging_bucket = "test-bucket"

        # Mock pipeline instances
        mock_duckdb_pipeline = MagicMock()
        mock_athena_pipeline = MagicMock()
        mock_pipeline.side_effect = [mock_duckdb_pipeline, mock_athena_pipeline]

        # Mock dataset with DLT internal table and regular table
        mock_dataset = MagicMock()
        mock_dataset.schema.tables.keys.return_value = [
            "job_logs",
            "_dlt_loads",
        ]
        mock_dataset.__getitem__.return_value.arrow.return_value = MagicMock()
        mock_duckdb_pipeline.dataset.return_value = mock_dataset

        # Mock destinations
        mock_athena_dest.return_value = MagicMock()
        mock_duckdb_dest.return_value = MagicMock()

        result = transfer_to_athena()

        assert result is True
        # Should only call run once for the regular table, not the DLT table
        mock_athena_pipeline.run.assert_called_once()
