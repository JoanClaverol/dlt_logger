"""Tests for tp_logger.config module."""

import pytest
from tp_logger.config import LoggerConfig, get_config, set_config


class TestLoggerConfig:
    """Test LoggerConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LoggerConfig()

        assert config.project_name == "tp_logger_app"
        assert config.db_path == "./logs/app.duckdb"
        assert config.log_level == "INFO"
        assert config.console_logging is True
        assert config.dataset_name == "tp_logger_logs"
        assert config.pipeline_name == "tp_logger_pipeline"
        assert config.sync_to_s3 is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = LoggerConfig(
            project_name="custom_project",
            db_path="/custom/path.duckdb",
            log_level="debug",
            console_logging=False,
            dataset_name="custom_logs",
            pipeline_name="custom_pipeline",
        )

        assert config.project_name == "custom_project"
        assert config.db_path == "/custom/path.duckdb"
        assert config.log_level == "DEBUG"  # Should be uppercased
        assert config.console_logging is False
        assert config.dataset_name == "custom_logs"
        assert config.pipeline_name == "custom_pipeline"

    def test_db_path_default_handling(self):
        """Test db_path default handling when None is passed."""
        config = LoggerConfig(db_path=None)
        assert config.db_path == "./logs/app.duckdb"

    def test_log_level_uppercasing(self):
        """Test that log level is automatically uppercased."""
        config = LoggerConfig(log_level="debug")
        assert config.log_level == "DEBUG"

        config = LoggerConfig(log_level="warning")
        assert config.log_level == "WARNING"

    def test_s3_config_validation(self):
        """Test S3 configuration validation."""
        # Should not raise error when sync_to_s3 is False
        config = LoggerConfig(sync_to_s3=False, aws_s3_bucket=None)
        assert config.sync_to_s3 is False

        # Should raise error when sync_to_s3 is True but no bucket
        with pytest.raises(ValueError, match="aws_s3_bucket is required"):
            LoggerConfig(sync_to_s3=True, aws_s3_bucket=None)

        # Should work when both are provided
        config = LoggerConfig(sync_to_s3=True, aws_s3_bucket="my-bucket")
        assert config.sync_to_s3 is True
        assert config.aws_s3_bucket == "my-bucket"

    def test_get_setting_method(self):
        """Test the get_setting method."""
        config = LoggerConfig(project_name="test_project")

        # Test getting existing attribute
        assert config.get_setting("project_name") == "test_project"

        # Test getting non-existing attribute with default
        assert config.get_setting("non_existing", "default_value") == "default_value"

    def test_get_setting_with_env_var(self, monkeypatch):
        """Test get_setting with environment variables."""
        config = LoggerConfig(project_name="test_project")

        # Set environment variable
        monkeypatch.setenv("TP_LOGGER_PROJECT_NAME", "env_project")

        # Should return environment variable value
        assert config.get_setting("project_name") == "env_project"


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_get_config_default(self):
        """Test get_config returns default config."""
        # Reset global config
        import tp_logger.config

        tp_logger.config._config = None

        config = get_config()
        assert isinstance(config, LoggerConfig)
        assert config.project_name == "tp_logger_app"

    def test_set_and_get_config(self):
        """Test setting and getting custom config."""
        custom_config = LoggerConfig(project_name="custom_test", log_level="ERROR")

        set_config(custom_config)
        retrieved_config = get_config()

        assert retrieved_config is custom_config
        assert retrieved_config.project_name == "custom_test"
        assert retrieved_config.log_level == "ERROR"
