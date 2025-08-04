"""Example usage of tp-logger library."""

import time
from tp_logger import setup_logging, get_logger, log_execution


def main():
    """Main function demonstrating tp-logger usage."""
    # Setup logging - this is what users will do in their main.py
    setup_logging(
        project_name="example_app",
        db_path="./logs/example_app.duckdb",
        log_level="INFO",
        console_logging=True,
    )

    # Get a logger instance
    logger = get_logger(__name__)

    # Basic logging
    logger.info("Application started")
    logger.debug("This is a debug message")
    logger.warning("This is a warning")

    # Log specific actions
    logger.log_action(
        action="initialization",
        message="App initialized successfully",
        success=True,
        duration_ms=150,
        context={"version": "1.0.0"},
    )

    # Test the decorator
    process_data()

    # Test exception logging
    try:
        risky_operation()
    except Exception as e:
        logger.log_exception("risky_operation", e)

    logger.info("Application finished")


@log_execution("data_processing")
def process_data():
    """Example function with logging decorator."""
    print("Processing data...")
    time.sleep(0.1)  # Simulate work
    return "Data processed successfully"


@log_execution()
def risky_operation():
    """Function that will throw an exception to test error logging."""
    raise ValueError("Something went wrong!")


if __name__ == "__main__":
    main()
