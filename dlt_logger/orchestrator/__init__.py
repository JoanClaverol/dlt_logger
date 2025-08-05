"""Workflow orchestration for dlt-logger.

This module provides WorkflowManager for end-to-end dlt-logger operations:
- Configuration setup and validation
- Sample log generation for testing
- DuckDB storage verification
- AWS Athena transfer (when configured)

Usage Example:
    >>> from dlt_logger.orchestrator import WorkflowManager
    >>> from dlt_logger.setup import LoggerConfig
    >>>
    >>> # Create configuration
    >>> config = LoggerConfig(
    ...     project_name="production_app",
    ...     db_path="./logs/prod.duckdb",
    ...     athena_destination=True,
    ...     aws_region="us-west-2",
    ...     athena_database="analytics_db"
    ... )
    >>>
    >>> # Run complete workflow
    >>> workflow = WorkflowManager(config)
    >>> results = workflow.run_complete_workflow(sample_log_count=100)
    >>>
    >>> # Check results
    >>> if results['overall_success']:
    ...     print(f"Workflow completed in {results['total_duration_ms']}ms")
"""

from .workflow import WorkflowManager

__all__ = ["WorkflowManager"]
