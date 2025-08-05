"""Workflow orchestration for tp-logger end-to-end operations."""

import time
from datetime import datetime
from typing import Any, Optional

from ..dlt import transfer_to_athena
from ..logging import get_logger, setup_logging
from ..setup import LoggerConfig, get_config, set_config
from ..utils import (
    ensure_directory_exists,
    format_duration,
    generate_sample_log_data,
    get_database_info_from_config,
)


class WorkflowManager:
    """Manages the complete tp-logger workflow from setup to transfer."""

    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize the workflow manager with optional custom config."""
        if config:
            set_config(config)

        self.config = get_config()
        self.logger = get_logger("workflow")
        self.start_time = datetime.now()

    def step_1_setup_configuration(self) -> bool:
        """Step 1: Setup and validate configuration."""
        try:
            self.logger.info("=== STEP 1: Configuration Setup ===")
            self.logger.info(f"Project: {self.config.project_name}")
            self.logger.info(f"Database Path: {self.config.db_path}")
            self.logger.info(f"Dataset Name: {self.config.dataset_name}")
            self.logger.info(f"Pipeline Name: {self.config.pipeline_name}")
            self.logger.info(f"Console Logging: {self.config.console_logging}")

            # Ensure database directory exists
            ensure_directory_exists(self.config.db_path)

            # Setup logging infrastructure with full config
            setup_logging(
                project_name=self.config.project_name,
                db_path=self.config.db_path,
                console_logging=self.config.console_logging,
                log_level=self.config.log_level,
                pipeline_name=self.config.pipeline_name,
                dataset_name=self.config.dataset_name,
                athena_destination=self.config.athena_destination,
                aws_region=self.config.aws_region,
                athena_database=self.config.athena_database,
                athena_s3_staging_bucket=self.config.athena_s3_staging_bucket,
            )

            self.logger.info("✅ Configuration setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Configuration setup failed: {str(e)}")
            return False

    def step_2_generate_sample_logs(self, count: int = 10) -> bool:
        """Step 2: Generate and store sample log entries."""
        try:
            self.logger.info("=== STEP 2: Sample Log Generation ===")

            # Generate sample data
            sample_data = generate_sample_log_data(count)
            self.logger.info(f"Generated {len(sample_data)} sample log entries")

            # Create logger instances and log the sample data
            test_modules = ["user_service", "api_handler", "data_processor"]

            for i, data in enumerate(sample_data):
                module_name = test_modules[i % len(test_modules)]
                module_logger = get_logger(module_name)

                # Log the sample entry
                module_logger.log_action(
                    action=data["action"],
                    message=data["message"],
                    success=data["success"],
                    level=data["level"],
                    duration_ms=data["duration_ms"],
                    context=data["context"],
                )

                # Small delay to show real-time logging
                time.sleep(0.1)

            self.logger.info("✅ Sample log generation completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Sample log generation failed: {str(e)}")
            return False

    def step_3_verify_duckdb_storage(self) -> bool:
        """Step 3: Verify logs are stored in DuckDB."""
        try:
            self.logger.info("=== STEP 3: DuckDB Storage Verification ===")

            # Get database info
            db_info = get_database_info_from_config()

            self.logger.info(f"Database exists: {db_info['exists']}")
            self.logger.info(f"File size: {db_info['file_size_mb']} MB")
            self.logger.info(f"Dataset: {db_info['dataset_name']}")
            self.logger.info(f"Tables: {db_info.get('tables', [])}")

            if "total_logs" in db_info:
                self.logger.info(f"Total log entries: {db_info['total_logs']}")

            if "error" in db_info:
                self.logger.warning(f"Database warning: {db_info['error']}")
                return False

            if not db_info["exists"]:
                self.logger.error("Database file does not exist")
                return False

            self.logger.info("✅ DuckDB storage verification completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ DuckDB storage verification failed: {str(e)}")
            return False

    def step_4_transfer_to_athena(self) -> bool:
        """Step 4: Transfer logs to AWS Athena (if configured)."""
        try:
            self.logger.info("=== STEP 4: Athena Transfer ===")

            if not self.config.athena_destination:
                self.logger.info(
                    "ℹ️  Athena transfer skipped (athena_destination=False)"
                )
                return True

            self.logger.info("Starting transfer to AWS Athena...")
            self.logger.info(f"AWS Region: {self.config.aws_region}")
            self.logger.info(f"Athena Database: {self.config.athena_database}")
            self.logger.info(
                f"S3 Staging Bucket: {self.config.athena_s3_staging_bucket}"
            )

            # Debug current config state
            current_config = get_config()
            self.logger.info(
                f"[WORKFLOW] Current global config - athena_destination: {current_config.athena_destination}"
            )
            self.logger.info(
                f"[WORKFLOW] Current global config - db_path: {current_config.db_path}"
            )
            self.logger.info(
                f"[WORKFLOW] Current global config - dataset_name: {current_config.dataset_name}"
            )

            # Check if database exists
            import os

            if os.path.exists(current_config.db_path):
                self.logger.info(
                    f"[WORKFLOW] Database file exists: {current_config.db_path} ({os.path.getsize(current_config.db_path)} bytes)"
                )
            else:
                self.logger.error(
                    f"[WORKFLOW] Database file missing: {current_config.db_path}"
                )
                return False

            # Perform the transfer
            self.logger.info("[WORKFLOW] Calling transfer_to_athena()...")
            success = transfer_to_athena()

            if success:
                self.logger.info("✅ Athena transfer completed successfully")
            else:
                self.logger.error("❌ Athena transfer failed")

            return success

        except Exception as e:
            self.logger.error(
                f"❌ Athena transfer failed: {type(e).__name__}: {str(e)}"
            )
            self.logger.error(f"[WORKFLOW] Exception details: {repr(e)}")
            return False

    def run_complete_workflow(self, sample_log_count: int = 10) -> dict[str, Any]:
        """Run the complete workflow from setup to transfer."""
        workflow_start = time.time()
        results = {
            "workflow_start_time": self.start_time.isoformat(),
            "steps": {},
            "overall_success": False,
            "total_duration_ms": 0,
        }

        self.logger.info("🚀 Starting complete tp-logger workflow")
        self.logger.info("=" * 60)

        # Step 1: Configuration Setup
        step_start = time.time()
        results["steps"]["1_configuration"] = {
            "success": self.step_1_setup_configuration(),
            "duration_ms": int((time.time() - step_start) * 1000),
        }

        if not results["steps"]["1_configuration"]["success"]:
            self.logger.error("🛑 Workflow stopped: Configuration setup failed")
            return results

        # Step 2: Sample Log Generation
        step_start = time.time()
        results["steps"]["2_sample_logs"] = {
            "success": self.step_2_generate_sample_logs(sample_log_count),
            "duration_ms": int((time.time() - step_start) * 1000),
            "log_count": sample_log_count,
        }

        if not results["steps"]["2_sample_logs"]["success"]:
            self.logger.error("🛑 Workflow stopped: Sample log generation failed")
            return results

        # Step 3: DuckDB Verification
        step_start = time.time()
        results["steps"]["3_duckdb_verification"] = {
            "success": self.step_3_verify_duckdb_storage(),
            "duration_ms": int((time.time() - step_start) * 1000),
        }

        if not results["steps"]["3_duckdb_verification"]["success"]:
            self.logger.error("🛑 Workflow stopped: DuckDB verification failed")
            return results

        # Step 4: Athena Transfer
        step_start = time.time()
        results["steps"]["4_athena_transfer"] = {
            "success": self.step_4_transfer_to_athena(),
            "duration_ms": int((time.time() - step_start) * 1000),
        }

        # Calculate total duration
        total_duration = time.time() - workflow_start
        results["total_duration_ms"] = int(total_duration * 1000)
        results["overall_success"] = all(
            step["success"] for step in results["steps"].values()
        )

        # Final summary
        self.logger.info("=" * 60)
        if results["overall_success"]:
            self.logger.info("🎉 Complete workflow executed successfully!")
        else:
            self.logger.error("❌ Workflow completed with errors")

        self.logger.info(
            f"Total duration: {format_duration(results['total_duration_ms'])}"
        )
        self.logger.info("=" * 60)

        return results

    def get_workflow_summary(self) -> dict[str, Any]:
        """Get a summary of the current workflow configuration."""
        return {
            "project_name": self.config.project_name,
            "database_path": self.config.db_path,
            "dataset_name": self.config.dataset_name,
            "pipeline_name": self.config.pipeline_name,
            "athena_enabled": self.config.athena_destination,
            "console_logging": self.config.console_logging,
            "log_level": self.config.log_level,
            "workflow_manager_created": self.start_time.isoformat(),
        }
