"""
Main demonstration script for dlt-logger: Complete workflow from setup to Athena transfer.

This script tells the complete story of dlt-logger:
1. Setup: Configuration and initialization
2. Logging: Generate sample logs and store in DuckDB
3. Storage: Verify DuckDB storage
4. Transfer: Move data to AWS Athena (if configured)
5. Orchestration: Coordinate the entire workflow

Run this script to see dlt-logger in action from start to finish.
"""

import sys
from typing import Dict, Any

# Import from dlt_logger package
from dlt_logger.setup import LoggerConfig
from dlt_logger.orchestrator import WorkflowManager
from dlt_logger.utils import get_database_info_from_config


def create_basic_config() -> LoggerConfig:
    """Create a basic configuration for demonstration."""
    return LoggerConfig(
        project_name="dlt_logger_demo",
        log_level="INFO",
        pipeline_name="demo_pipeline",
        dataset_name="demo_logs",
        table_name="application_logs",
        db_path="./logs/demo.duckdb",
        console_logging=True,
        # Athena is disabled by default - enable if you have AWS credentials
        athena_destination=False,
        # Uncomment and configure if you want to test Athena transfer:
        # athena_destination=True,
        # aws_region="us-east-1",
        # athena_database="dlt_logger_db",
        # athena_s3_staging_bucket="your-s3-bucket"
    )


def create_athena_config() -> LoggerConfig:
    """Create a configuration with Athena enabled (requires AWS setup)."""
    return LoggerConfig(
        project_name="dlt_logger_athena_demo",
        log_level="INFO",
        pipeline_name="athena_demo_pipeline",
        dataset_name="athena_demo_logs",
        table_name="production_logs",
        db_path="./logs/athena_demo.duckdb",
        console_logging=True,
        # Athena configuration
        athena_destination=True,
        aws_region="eu-west-3",
        athena_database="dlt_logger_test_db",
        athena_s3_staging_bucket="dlt-logger-test-bucket",
    )


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)


def print_workflow_results(results: Dict[str, Any]) -> None:
    """Print detailed workflow results."""
    print_section_header("Workflow Results Summary")

    print(f"Overall Success: {'✅ YES' if results['overall_success'] else '❌ NO'}")
    print(f"Total Duration: {results['total_duration_ms']} ms")
    print(f"Started: {results['workflow_start_time']}")

    print("\nStep-by-Step Results:")
    for step_name, step_data in results["steps"].items():
        status = "✅ PASS" if step_data["success"] else "❌ FAIL"
        duration = step_data["duration_ms"]
        print(f"  {step_name}: {status} ({duration} ms)")

        if "log_count" in step_data:
            print(f"    └─ Generated {step_data['log_count']} log entries")


def demonstrate_basic_workflow():
    """Demonstrate the basic dlt-logger workflow without Athena."""
    print_section_header("TP-Logger Basic Workflow Demonstration")

    print("🚀 This demonstration will show you dlt-logger's complete workflow:")
    print("   1. Configuration Setup")
    print("   2. Sample Log Generation")
    print("   3. DuckDB Storage")
    print("   4. Workflow Orchestration")
    print("\n📝 Note: Athena transfer is disabled in this demo")

    # Create basic configuration
    print_section_header("Step 1: Configuration Setup")
    config = create_basic_config()
    print("✅ Created basic configuration:")
    print(f"   Project: {config.project_name}")
    print(f"   Database: {config.db_path}")
    print(f"   Dataset: {config.dataset_name}")
    print(f"   Console Logging: {config.console_logging}")

    # Initialize workflow manager
    print_section_header("Step 2: Initialize Workflow Manager")
    workflow = WorkflowManager(config)

    summary = workflow.get_workflow_summary()
    print("✅ Workflow manager initialized:")
    for key, value in summary.items():
        print(f"   {key}: {value}")

    # Run complete workflow
    print_section_header("Step 3: Execute Complete Workflow")
    print("🔄 Running end-to-end workflow with 15 sample log entries...")

    results = workflow.run_complete_workflow(sample_log_count=15)

    # Show results
    print_workflow_results(results)

    # Show database info
    print_section_header("Step 4: Database Verification")
    try:
        db_info = get_database_info_from_config()
        print("📊 Database Information:")
        for key, value in db_info.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Error getting database info: {e}")

    return results


def demonstrate_athena_workflow():
    """Demonstrate the complete workflow including Athena transfer."""
    print_section_header("TP-Logger Complete Workflow with Athena")

    print("🚀 This demonstration includes AWS Athena transfer:")
    print("   1. Configuration Setup (with Athena)")
    print("   2. Sample Log Generation")
    print("   3. DuckDB Storage")
    print("   4. AWS Athena Transfer")
    print("   5. Complete Orchestration")

    print("\n⚠️  WARNING: This requires valid AWS credentials and configuration!")
    print("   Make sure you have:")
    print(
        "   - AWS credentials configured (AWS CLI, environment variables, or IAM role)"
    )
    print("   - An existing Athena database")
    print("   - An S3 bucket for staging")
    print("   - Proper IAM permissions for Athena and S3")

    # Create Athena configuration
    print_section_header("Step 1: Athena Configuration Setup")
    config = create_athena_config()

    print("⚠️  Please update the Athena configuration in create_athena_config():")
    print(f"   AWS Region: {config.aws_region}")
    print(f"   Athena Database: {config.athena_database}")
    print(f"   S3 Staging Bucket: {config.athena_s3_staging_bucket}")

    response = input("\nDo you want to continue with Athena demo? (y/N): ")
    if response.lower() not in ["y", "yes"]:
        print("❌ Athena demo cancelled. Run demonstrate_basic_workflow() instead.")
        return None

    # Initialize workflow manager
    workflow = WorkflowManager(config)

    # Run complete workflow with Athena
    print_section_header("Step 2: Execute Complete Workflow with Athena")
    print("🔄 Running end-to-end workflow with Athena transfer...")

    results = workflow.run_complete_workflow(sample_log_count=20)

    # Show results
    print_workflow_results(results)

    return results


def main():
    """Main entry point for dlt-logger demonstration."""
    print_section_header("Welcome to TP-Logger Complete Demonstration")

    print("Choose a demonstration mode:")
    print("1. Basic Workflow (Local DuckDB only)")
    print("2. Complete Workflow (DuckDB + AWS Athena)")
    print("3. Exit")

    results = None
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                results = demonstrate_basic_workflow()
                break
            elif choice == "2":
                results = demonstrate_athena_workflow()
                break
            elif choice == "3":
                print("👋 Thanks for trying dlt-logger!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for trying dlt-logger!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    print_section_header("Demonstration Complete")
    print("🎉 dlt-logger demonstration finished!")
    print("\nNext steps:")
    print("1. Check your logs directory for the generated DuckDB file")
    print("2. Explore the dlt-logger API for your own applications")
    print("3. Configure Athena settings for production use")
    print("4. Review the workflow results above for any issues")

    return results


if __name__ == "__main__":
    main()
