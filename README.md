# tp-logger

Simple logging library with DuckDB storage via DLT Hub for structured logging and easy data analysis.

## Features

- **Easy Setup**: One function call to configure logging
- **Structured Logging**: All logs stored in DuckDB with consistent schema
- **Decorator Support**: `@log_execution` decorator for automatic function logging
- **DLT Integration**: Uses DLT Hub for robust data pipeline management
- **Type Safety**: Pydantic models ensure data consistency
- **Console + Database**: Logs to both console (via loguru) and database

## Installation

```bash
pip install tp-logger
```

Or with uv:

```bash
uv add tp-logger
```

## Quick Start

### 1. Setup in your main.py

```python
from tp_logger import setup_logging

# Initialize logging (call this once at app startup)
setup_logging(
    project_name="my_app",
    db_path="./logs/my_app.duckdb",  # Optional, defaults to ./logs/app.duckdb
    log_level="INFO",               # Optional, defaults to INFO
    console_logging=True            # Optional, defaults to True
)
```

### 2. Use in your modules

```python
from tp_logger import get_logger, log_execution

# Get a logger instance
logger = get_logger(__name__)

# Basic logging
logger.info("Application started")
logger.error("Something went wrong")

# Structured logging with metadata
logger.log_action(
    action="data_processing",
    message="Processed 100 records",
    success=True,
    duration_ms=1500,
    context={"records_count": 100}
)

# Decorator for automatic function logging
@log_execution("user_registration")
def register_user(email: str):
    # Function automatically gets logged with timing
    print(f"Registering {email}")
    return {"user_id": 123}
```

## Database Schema

Logs are stored in a `job_logs` table with this structure:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Unique log entry ID |
| project_name | TEXT | Your project name |
| module_name | TEXT | Python module name |
| function_name | TEXT | Function name (for decorators) |
| run_id | UUID | Session run ID |
| timestamp | TIMESTAMPTZ | When the log was created |
| level | TEXT | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| action | TEXT | Action being performed |
| message | TEXT | Log message |
| success | BOOLEAN | Whether the action succeeded |
| status_code | INT | HTTP status code (if applicable) |
| duration_ms | BIGINT | Duration in milliseconds |
| request_method | TEXT | HTTP method (if applicable) |
| context | JSON | Additional context data |

## Advanced Usage

### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    logger.log_exception("risky_operation", e)
```

### Context Manager for Timing

```python
from tp_logger import timed_operation

logger = get_logger(__name__)

with timed_operation(logger, "database_backup"):
    # Operation automatically timed and logged
    backup_database()
```

### Querying Your Logs

Since logs are stored in DuckDB, you can easily analyze them:

```python
import duckdb

# Connect to your log database
conn = duckdb.connect("./logs/my_app.duckdb")

# Query examples
results = conn.execute("""
    SELECT action, COUNT(*) as count, AVG(duration_ms) as avg_duration
    FROM tp_logger_logs.job_logs 
    WHERE success = true
    GROUP BY action
    ORDER BY avg_duration DESC
""").fetchall()

print(results)
```

## Configuration Options

The `setup_logging()` function accepts these parameters:

- `project_name` (str): Name of your project (default: "tp_logger_app")
- `db_path` (str): Path to DuckDB file (default: "./logs/app.duckdb")
- `log_level` (str): Minimum log level (default: "INFO")
- `console_logging` (bool): Enable console output (default: True)

## Environment Variables

You can also configure tp-logger using environment variables:

- `TP_LOGGER_PROJECT_NAME`: Override project name
- `TP_LOGGER_DB_PATH`: Override database path
- `TP_LOGGER_LOG_LEVEL`: Override log level
- `TP_LOGGER_CONSOLE_LOGGING`: Override console logging (true/false)

## Use Cases

- **Application Monitoring**: Track function performance and errors
- **Data Pipeline Logging**: Log ETL processes with structured metadata
- **API Request Logging**: Log HTTP requests with status codes and timing
- **Business Process Tracking**: Log business events with custom context
- **Debugging**: Rich structured logs for troubleshooting

## Why tp-logger?

- **Simple**: Minimal setup, maximum functionality
- **Structured**: Consistent schema for all log data
- **Queryable**: Easy to analyze logs with SQL
- **Reliable**: Built on DLT Hub for robust data handling
- **Type-safe**: Pydantic models prevent data inconsistencies
- **Performant**: Efficient batch writes to DuckDB

## Future Features

- S3/Athena sync for cloud analytics
- Built-in dashboard for log visualization  
- Automatic schema evolution
- Custom exporters for other databases

## Development

This package is built with modern Python tooling:

- **Package Management**: uv
- **Data Pipeline**: DLT Hub
- **Database**: DuckDB
- **Validation**: Pydantic
- **Logging**: loguru

## License

MIT License