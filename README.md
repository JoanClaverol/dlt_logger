# dlt-logger

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, structured logging library for Python with DuckDB storage and optional AWS Athena integration. Built for analytics, debugging, and production monitoring.

## ✨ Key Features

- **📊 Structured Logging**: All logs stored in DuckDB with consistent schema
- **🎯 Easy Integration**: Simple decorator `@log_execution` for automatic function logging
- **⚡ High Performance**: Built on DLT Hub for robust data pipeline management
- **🔒 Type Safety**: Pydantic models ensure data consistency
- **🖥️ Dual Output**: Console logging (via loguru) + database storage
- **☁️ Cloud Ready**: Optional AWS Athena integration for analytics at scale
- **🔧 Explicit Config**: Clear, required configuration for better maintainability

## 🚀 Quick Start

### Installation

#### From GitHub (Latest Development Version)

```bash
# Install directly from GitHub
pip install git+https://github.com/JoanClaverol/dlt_logger.git

# Or install with uv (recommended)
uv add git+https://github.com/JoanClaverol/dlt_logger.git
```

#### From PyPI (When Available)

```bash
# Standard installation
pip install dlt-logger

# Or with uv
uv add dlt-logger
```

#### Development Installation

```bash
# Clone the repository
git clone https://github.com/JoanClaverol/dlt_logger.git
cd dlt_logger

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Basic Usage

```python
import dlt_logger

# 1. Setup (call once at application startup)
dlt_logger.setup_logging(
    project_name="my_app",
    log_level="INFO",
    pipeline_name="my_app_pipeline",
    dataset_name="my_app_logs",
    table_name="application_logs",
    db_path="./logs/app.duckdb"
)

# 2. Get a logger
logger = dlt_logger.get_logger(__name__)

# 3. Start logging
logger.info("Application started")
logger.error("Something went wrong")

# 4. Structured logging with metadata
logger.log_action(
    action="user_registration",
    message="New user registered",
    success=True,
    duration_ms=150,
)
```

### Automatic Function Logging

```python
import dlt_logger

dlt_logger.setup_logging(
    project_name="my_app",
    log_level="INFO",
    pipeline_name="my_app_pipeline",
    dataset_name="my_app_logs",
    table_name="application_logs"
)

@dlt_logger.log_execution("data_processing")
def process_data(user_id: int):
    # Function automatically logged with timing
    return {"processed": True, "user_id": user_id}

# Logs generated automatically:
# - Function start
# - Function completion with duration
# - Any exceptions with stack traces
```

## 📚 Complete API Reference

### Core Functions

#### `setup_logging(**kwargs)`

Initialize the logging system. Call once at application startup.

```python
dlt_logger.setup_logging(
    project_name="my_app",                    # Required: Your project name
    log_level="INFO",                        # Required: Log level
    pipeline_name="my_pipeline",             # Required: DLT pipeline name
    dataset_name="my_logs",                  # Required: Database schema name
    table_name="application_logs",           # Required: Table name
    db_path="./logs/app.duckdb",             # Optional: Database path
    console_logging=True,                    # Optional: Enable console output
)
```

#### `get_logger(name: str) -> TPLogger`

Get a logger instance for a specific module or component.

```python
logger = dlt_logger.get_logger(__name__)
logger = dlt_logger.get_logger("api_service")
```

#### `@log_execution(action: str = None)`

Decorator for automatic function logging with timing.

```python
@dlt_logger.log_execution("api_call")
def fetch_user(user_id: int):
    return {"user": user_id}

@dlt_logger.log_execution()  # Uses function name
def process_payment():
    return {"status": "paid"}
```

### Logger Methods

#### Basic Logging

```python
logger = dlt_logger.get_logger("my_service")

logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical system error")
```

#### Structured Action Logging

```python
logger.log_action(
    action="database_query",           # Action identifier
    message="User data retrieved",     # Human-readable message
    success=True,                      # Success/failure status
    duration_ms=250,                   # Optional: Duration in milliseconds
    status_code=200,                   # Optional: HTTP status code
)
```

#### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    logger.log_exception("risky_operation", e)
```

### Context Manager for Timing

```python
from dlt_logger import get_logger, timed_operation

logger = get_logger(__name__)

with timed_operation(logger, "database_backup"):
    # Operation automatically timed and logged
    perform_backup()
```

## ☁️ AWS Athena Integration

Upload your logs to AWS Athena for cloud-scale analytics.

### Setup

```python
dlt_logger.setup_logging(
    project_name="production_app",
    log_level="INFO",
    pipeline_name="production_pipeline",
    dataset_name="production_logs",
    table_name="application_events",
    # Enable Athena
    athena_destination=True,
    aws_region="us-east-1",
    athena_database="logs_db",
    athena_s3_staging_bucket="my-staging-bucket"
)
```

### Transfer Data

```python
from dlt_logger.dlt import transfer_logs_to_athena

# Transfer logs to Athena
success = transfer_logs_to_athena()
if success:
    print("✅ Logs uploaded to Athena")
```

### AWS Configuration

Create `.dlt/secrets.toml` in your project:

```toml
[destination.athena.credentials]
aws_access_key_id = "your_access_key"
aws_secret_access_key = "your_secret_key"
```

Or use environment variables:
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

## 🛠️ Advanced Usage

### Workflow Management

For complex operations, use the WorkflowManager:

```python
from dlt_logger import WorkflowManager, LoggerConfig

config = LoggerConfig(
    project_name="data_pipeline",
    log_level="INFO",
    pipeline_name="data_processing_pipeline",
    dataset_name="analytics_logs",
    table_name="workflow_events",
    athena_destination=True,
    aws_region="us-west-2"
)

workflow = WorkflowManager(config)
results = workflow.run_complete_workflow(sample_log_count=100)

print(f"Success: {results['overall_success']}")
print(f"Duration: {results['total_duration_ms']}ms")
```

### Custom Configuration

```python
from dlt_logger.setup import LoggerConfig

config = LoggerConfig(
    project_name="custom_app",
    log_level="DEBUG",
    pipeline_name="custom_pipeline",
    dataset_name="custom_logs",
    table_name="debug_events",
    db_path="./data/custom.duckdb",
    console_logging=False,
    athena_destination=True,
    aws_region="eu-west-1"
)

dlt_logger.setup_logging(**config.__dict__)
```

### Project Root Detection

**New in v0.1.0**: dlt-logger automatically detects your project's root directory and creates all files relative to it, ensuring clean project organization when installed as a dependency.

**How it works:**
- Automatically detects project root by looking for `pyproject.toml`, `setup.py`, `.git`, or other project indicators
- Creates database files and DLT pipeline directories relative to your project root
- Works seamlessly when installed via `pip install git+https://github.com/...`

**Path Resolution Examples:**
```python
# All paths are resolved relative to your project root
dlt_logger.setup_logging(
    project_name="my_app",
    log_level="INFO",
    pipeline_name="my_app_pipeline",
    dataset_name="my_app_logs",
    table_name="application_logs",
    db_path="./logs/app.duckdb"  # Creates: /your/project/logs/app.duckdb
)

# Manual project root override (if needed)
dlt_logger.setup_logging(
    project_name="my_app",
    log_level="INFO",
    pipeline_name="my_app_pipeline",
    dataset_name="my_app_logs",
    table_name="application_logs",
    db_path="./logs/app.duckdb",
    project_root="/custom/project/path"
)

# Test project root detection
project_root = dlt_logger.detect_project_root()
print(f"Detected project root: {project_root}")
```

**What gets created in your project:**
- `./logs/` - Database files (configurable path)
- `./.dlt_pipeline/` - DLT pipeline state and configuration
- No more files scattered in unexpected locations!

### Environment Variables

Override settings with environment variables:

```bash
export TP_LOGGER_PROJECT_NAME="production_app"
export TP_LOGGER_LOG_LEVEL="WARNING"
export TP_LOGGER_ATHENA_DESTINATION="true"
export TP_LOGGER_AWS_REGION="us-east-1"
```

## 📊 Database Schema

Logs are stored with this structure:

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

## 🔍 Querying Your Logs

### Local DuckDB

```python
import duckdb

conn = duckdb.connect("./logs/app.duckdb")

# Performance analysis
perf_query = """
    SELECT action, 
           COUNT(*) as calls,
           AVG(duration_ms) as avg_duration,
           MAX(duration_ms) as max_duration
    FROM dlt_logger_logs.job_logs 
    WHERE success = true AND duration_ms IS NOT NULL
    GROUP BY action
    ORDER BY avg_duration DESC
"""
results = conn.execute(perf_query).fetchdf()
print(results)
```

### AWS Athena

```sql
-- Query in Athena console
SELECT action, 
       DATE_TRUNC('hour', timestamp) as hour,
       COUNT(*) as log_count,
       AVG(duration_ms) as avg_duration
FROM your_database.job_logs
WHERE project_name = 'production_app'
  AND timestamp >= current_timestamp - interval '24' hour
GROUP BY action, DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;
```

## 🎯 Real-World Example

```python
import dlt_logger
import time

# Setup
dlt_logger.setup_logging(
    project_name="ecommerce_api",
    log_level="INFO",
    pipeline_name="ecommerce_pipeline",
    dataset_name="ecommerce_logs",
    table_name="order_events",
    athena_destination=True,
    aws_region="us-east-1"
)

logger = dlt_logger.get_logger(__name__)

class OrderProcessor:
    def __init__(self):
        self.logger = dlt_logger.get_logger(self.__class__.__name__)
    
    @dlt_logger.log_execution("order_processing")
    def process_order(self, order_id: str, items: list):
        """Process order with automatic logging."""
        
        # Log order received
        self.logger.log_action(
            action="order_received",
            message=f"Processing order {order_id}",
            success=True,
        )
        
        # Validate
        if not self._validate_order(items):
            return False
        
        # Process payment with timing
        with dlt_logger.timed_operation(self.logger, "payment_processing"):
            if not self._process_payment(order_id):
                return False
        
        # Complete order
        self.logger.log_action(
            action="order_completed",
            message=f"Order {order_id} completed",
            success=True
        )
        
        return True
    
    def _validate_order(self, items: list) -> bool:
        success = len(items) > 0
        self.logger.log_action(
            action="order_validation",
            message="Order validation " + ("passed" if success else "failed"),
            success=success
        )
        return success
    
    def _process_payment(self, order_id: str) -> bool:
        time.sleep(0.1)  # Simulate payment processing
        
        success = True  # Assume success
        self.logger.log_action(
            action="payment_processing",
            message="Payment processed",
            success=success,
            status_code=200 if success else 402
        )
        return success

# Usage
processor = OrderProcessor()
success = processor.process_order("ORD-001", [{"price": 29.99}])
logger.info(f"Order result: {'SUCCESS' if success else 'FAILED'}")
```

## 🔧 Troubleshooting

### Common Issues

**Import Error**
```python
# ❌ Wrong
from dlt_logger.core import setup_logging

# ✅ Correct
import dlt_logger
dlt_logger.setup_logging(...)
```

**DLT Pipeline Issues**
```python
# Check pipeline status
from dlt_logger.dlt import get_pipeline
pipeline = get_pipeline()
print(f"Pipeline working dir: {pipeline.working_dir}")
```

**Athena Upload Failures**
```python
# Validate configuration
from dlt_logger.setup import get_config
config = get_config()

if not all([config.athena_destination, config.aws_region, 
           config.athena_database, config.athena_s3_staging_bucket]):
    print("❌ Missing Athena configuration")
```

### Debug Mode

```python
dlt_logger.setup_logging(
    project_name="debug_app",
    log_level="DEBUG",
    pipeline_name="debug_pipeline",
    dataset_name="debug_logs",
    table_name="debug_events",
    console_logging=True
)
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for better logging and observability.**