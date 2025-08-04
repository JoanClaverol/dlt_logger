# tp-logger

A modern, modular Python logging library with DuckDB storage and AWS Athena integration via DLT Hub. Designed for structured logging, data analysis, and cloud-scale log analytics.

## ✨ Features

- **🏗️ Modular Architecture**: Clean separation of concerns across focused modules
- **📊 Structured Logging**: All logs stored in DuckDB with consistent schema
- **🎯 Decorator Support**: `@log_execution` decorator for automatic function logging
- **⚡ DLT Integration**: Built on DLT Hub for robust data pipeline management
- **🔒 Type Safety**: Pydantic models ensure data consistency
- **🖥️ Dual Output**: Logs to both console (via loguru) and database
- **☁️ Cloud Ready**: Upload logs to AWS Athena for analytics at scale
- **🔧 Easy Setup**: One function call to configure everything

## 🏗️ Architecture

tp-logger is built with a modular architecture for maintainability and flexibility:

```
tp_logger/
├── core.py          # Main entry point - imports & re-exports all APIs
├── logger.py        # TPLogger class and setup functions
├── decorators.py    # @log_execution decorator and context managers
├── pipeline.py      # DLT pipeline management 
├── handlers.py      # Console logging handlers
├── athena.py        # AWS Athena upload functionality
├── models.py        # Pydantic data models
└── config.py        # Configuration management
```

Each module has a single responsibility, making the codebase easy to understand and extend.

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install tp-logger
```

Or with uv (recommended):

```bash
uv add tp-logger
```

### From GitHub Repository

```bash
# Using uv (recommended)
uv add git+https://github.com/JoanClaverol/tp_logger.git

# Using pip
pip install git+https://github.com/JoanClaverol/tp_logger.git
```

### For Development

```bash
git clone https://github.com/JoanClaverol/tp_logger.git
cd tp_logger
uv sync  # Install with uv
```

## 🚀 Quick Start

### 1. Basic Setup (Local DuckDB)

```python
from tp_logger import setup_logging, get_logger, log_execution

# Initialize logging (call once at app startup)
setup_logging(
    project_name="my_awesome_app",
    db_path="./logs/my_app.duckdb",  # Optional, defaults to ./logs/app.duckdb
    log_level="INFO",               # Optional, defaults to INFO
    console_logging=True            # Optional, defaults to True
)

# Get a logger instance
logger = get_logger(__name__)

# Basic logging
logger.info("Application started successfully")
logger.error("Something went wrong", context={"error_code": 500})

# Structured logging with metadata
logger.log_action(
    action="user_registration",
    message="New user registered",
    success=True,
    duration_ms=150,
    context={"user_id": 12345, "email": "user@example.com"}
)

# Decorator for automatic function logging with timing
@log_execution("data_processing")
def process_user_data(user_id: int):
    # Function automatically gets logged with timing
    return {"processed": True, "user_id": user_id}
```

### 2. Advanced Setup with AWS Athena Integration

```python
from tp_logger import setup_logging, upload_to_athena

# Setup with Athena configuration
setup_logging(
    project_name="my_production_app",
    db_path="./logs/app.duckdb",
    log_level="INFO",
    console_logging=True,
    # Athena configuration
    athena_destination=True,
    aws_region="us-east-1",
    athena_database="my_logs_database", 
    athena_s3_staging_bucket="my-athena-staging-bucket"
)

# Later, upload logs to Athena
success = upload_to_athena()
if success:
    print("✅ Logs successfully uploaded to Athena")
else:
    print("❌ Failed to upload logs to Athena")
```

## ⚙️ AWS Athena Configuration

To use the Athena integration, you need to set up DLT configuration files and AWS credentials.

### Step 1: Create DLT Configuration Directory

Create a `.dlt` directory in your project root:

```bash
mkdir .dlt
```

### Step 2: Configure DLT Settings (`.dlt/config.toml`)

Create `.dlt/config.toml`:

```toml
[sources]
tp_logger_pipeline = "tp_logger"

[destination.athena]
aws_region = "us-east-1"
athena_database = "your_logs_database"
s3_staging_bucket = "your-athena-staging-bucket"
table_format = "iceberg"  # Optional: Use Iceberg format for better performance

[destination.athena.credentials]
# AWS credentials will be loaded from secrets.toml

[pipeline]
# Optional pipeline settings
progress = "enlighten"  # Show progress bars
staging = "filesystem"  # Use filesystem for staging
```

### Step 3: Configure AWS Credentials (`.dlt/secrets.toml`)

Create `.dlt/secrets.toml` (⚠️ **Never commit this file**):

```toml
[destination.athena.credentials]
aws_access_key_id = "YOUR_AWS_ACCESS_KEY_ID"
aws_secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"
# Optional: For assumed roles
# aws_session_token = "YOUR_SESSION_TOKEN"
# region_name = "us-east-1"  # Override default region if needed
```

### Step 4: Set Up AWS Resources

#### S3 Staging Bucket
```bash
# Create S3 bucket for Athena staging
aws s3 mb s3://your-athena-staging-bucket --region us-east-1
```

#### Athena Database
```sql
-- Create Athena database
CREATE DATABASE IF NOT EXISTS your_logs_database;
```

#### IAM Permissions
Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "athena:*",
                "glue:CreateDatabase",
                "glue:CreateTable", 
                "glue:GetDatabase",
                "glue:GetTable",
                "glue:GetTables",
                "glue:UpdateTable",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:athena:*:*:workgroup/*",
                "arn:aws:glue:*:*:catalog",
                "arn:aws:glue:*:*:database/your_logs_database",
                "arn:aws:glue:*:*:table/your_logs_database/*",
                "arn:aws:s3:::your-athena-staging-bucket",
                "arn:aws:s3:::your-athena-staging-bucket/*"
            ]
        }
    ]
}
```

### Step 5: Environment Variables (Alternative)

Instead of `.dlt/secrets.toml`, you can use environment variables:

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# tp-logger specific
export TP_LOGGER_PROJECT_NAME="my_production_app"
export TP_LOGGER_ATHENA_DESTINATION="true"
export TP_LOGGER_AWS_REGION="us-east-1"
export TP_LOGGER_ATHENA_DATABASE="your_logs_database"
export TP_LOGGER_ATHENA_S3_STAGING_BUCKET="your-athena-staging-bucket"
```

## 📚 Module Usage Examples

### Core Logging (`tp_logger.logger`)

```python
from tp_logger.logger import TPLogger, setup_logging, get_logger

# Setup logging first
setup_logging(project_name="my_app")

# Get logger instance
logger = get_logger("my_module")

# Different log levels
logger.debug("Debug information", context={"debug_data": "value"})
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", context={"error_code": "E001"})
logger.critical("Critical system error")

# Action logging with metadata
logger.log_action(
    action="database_query",
    message="User query executed",
    success=True,
    duration_ms=250,
    status_code=200,
    context={"query": "SELECT * FROM users", "rows_returned": 50}
)

# Exception logging
try:
    risky_operation()
except Exception as e:
    logger.log_exception("risky_operation", e)
```

### Decorators (`tp_logger.decorators`)

```python
from tp_logger.decorators import log_execution, timed_operation
from tp_logger import get_logger

logger = get_logger(__name__)

# Automatic function logging with timing
@log_execution("user_authentication")
def authenticate_user(username: str, password: str):
    # Function execution is automatically logged with timing
    if username == "admin" and password == "secret":
        return {"authenticated": True, "user_id": 1}
    raise ValueError("Invalid credentials")

@log_execution()  # Uses function name as action
def process_payment(amount: float):
    # Custom processing logic
    return {"transaction_id": "txn_123", "amount": amount}

# Context manager for timing operations
def backup_database():
    with timed_operation(logger, "database_backup"):
        # Operation is automatically timed and logged
        time.sleep(2)  # Simulate backup process
        logger.info("Database backup completed")
```

### Pipeline Management (`tp_logger.pipeline`)

```python
from tp_logger.pipeline import get_pipeline, job_logs, RUN_ID
from tp_logger.models import LogEntry

# Get the current pipeline instance
pipeline = get_pipeline()

# Create custom log entries
log_entry = LogEntry(
    project_name="my_app",
    module_name="custom_module", 
    level="INFO",
    message="Custom log entry",
    success=True,
    context={"custom_field": "value"}
)

# Use the job_logs resource directly
pipeline.run(job_logs([log_entry]))

# Access current run ID
print(f"Current run ID: {RUN_ID}")
```

### Athena Upload (`tp_logger.athena`)

```python
from tp_logger.athena import upload_to_athena
from tp_logger import setup_logging

# Setup with Athena configuration
setup_logging(
    project_name="production_app",
    athena_destination=True,
    aws_region="us-east-1",
    athena_database="logs_db",
    athena_s3_staging_bucket="my-staging-bucket"
)

# Upload logs to Athena
try:
    success = upload_to_athena()
    if success:
        print("✅ Successfully uploaded logs to Athena")
    else:
        print("❌ Failed to upload logs")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Upload error: {e}")
```

## 📋 Database Schema

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

## 🔍 Querying Your Logs

### Local DuckDB Queries

```python
import duckdb

# Connect to your log database
conn = duckdb.connect("./logs/my_app.duckdb")

# Performance analysis
performance_query = """
    SELECT action, 
           COUNT(*) as total_calls,
           AVG(duration_ms) as avg_duration,
           MAX(duration_ms) as max_duration,
           MIN(duration_ms) as min_duration
    FROM tp_logger_logs.job_logs 
    WHERE success = true AND duration_ms IS NOT NULL
    GROUP BY action
    ORDER BY avg_duration DESC
"""
results = conn.execute(performance_query).fetchdf()
print(results)

# Error analysis
error_query = """
    SELECT DATE_TRUNC('hour', timestamp) as hour,
           level,
           COUNT(*) as error_count
    FROM tp_logger_logs.job_logs 
    WHERE success = false
    GROUP BY hour, level
    ORDER BY hour DESC, error_count DESC
"""
errors = conn.execute(error_query).fetchdf()
print(errors)

conn.close()
```

### AWS Athena Queries

```sql
-- Query logs in Athena
SELECT action, 
       DATE_TRUNC('hour', timestamp) as hour,
       COUNT(*) as log_count,
       AVG(duration_ms) as avg_duration
FROM your_logs_database.job_logs
WHERE project_name = 'production_app'
  AND timestamp >= current_timestamp - interval '24' hour
GROUP BY action, DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC, avg_duration DESC;

-- Error tracking
SELECT level,
       COUNT(*) as error_count,
       ARRAY_AGG(DISTINCT action) as affected_actions
FROM your_logs_database.job_logs
WHERE success = false
  AND timestamp >= current_timestamp - interval '7' day
GROUP BY level
ORDER BY error_count DESC;
```

## ⚙️ Configuration Reference

### LoggerConfig Parameters

```python
from tp_logger import setup_logging

setup_logging(
    # Basic configuration
    project_name="my_app",                    # Project identifier
    db_path="./logs/app.duckdb",             # Local DuckDB path
    log_level="INFO",                        # DEBUG, INFO, WARNING, ERROR, CRITICAL
    console_logging=True,                    # Enable console output
    
    # DLT configuration
    pipeline_name="tp_logger_pipeline",      # DLT pipeline name
    dataset_name="tp_logger_logs",           # DLT dataset name
    
    # AWS Athena configuration
    athena_destination=False,                # Enable Athena upload
    aws_region="us-east-1",                  # AWS region
    athena_database="logs_database",         # Athena database name
    athena_s3_staging_bucket="staging-bucket", # S3 staging bucket
    
    # S3 sync (future feature)
    sync_to_s3=False,                        # Enable S3 sync
    aws_s3_bucket="logs-bucket",             # S3 bucket for logs
    aws_s3_key_prefix="logs/",               # S3 key prefix
    sync_interval_minutes=60                 # Sync interval
)
```

### Environment Variables

Override configuration with environment variables:

```bash
# Basic settings
export TP_LOGGER_PROJECT_NAME="production_app"
export TP_LOGGER_DB_PATH="./logs/prod.duckdb"
export TP_LOGGER_LOG_LEVEL="INFO"
export TP_LOGGER_CONSOLE_LOGGING="true"

# Athena settings
export TP_LOGGER_ATHENA_DESTINATION="true"
export TP_LOGGER_AWS_REGION="us-west-2"
export TP_LOGGER_ATHENA_DATABASE="production_logs"
export TP_LOGGER_ATHENA_S3_STAGING_BUCKET="prod-athena-staging"

# DLT settings
export TP_LOGGER_PIPELINE_NAME="production_pipeline"
export TP_LOGGER_DATASET_NAME="production_logs"
```

## 🎯 Complete Example: E-commerce Order Processing

```python
from tp_logger import setup_logging, get_logger, log_execution, timed_operation
import time
import random

# Setup logging with Athena integration
setup_logging(
    project_name="ecommerce_platform",
    log_level="INFO", 
    console_logging=True,
    athena_destination=True,
    aws_region="us-east-1",
    athena_database="ecommerce_logs",
    athena_s3_staging_bucket="ecommerce-athena-staging"
)

logger = get_logger(__name__)

class OrderProcessor:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    @log_execution("order_processing")
    def process_order(self, order_id: str, customer_id: str, items: list):
        """Process a customer order with full tracking."""
        
        self.logger.log_action(
            action="order_received",
            message=f"Processing order {order_id}",
            success=True,
            context={
                "order_id": order_id,
                "customer_id": customer_id,
                "item_count": len(items),
                "order_value": sum(item.get("price", 0) for item in items)
            }
        )
        
        # Validate order
        if not self._validate_order(order_id, items):
            return False
        
        # Process payment
        with timed_operation(self.logger, "payment_processing"):
            payment_success = self._process_payment(order_id, customer_id)
            if not payment_success:
                return False
        
        # Ship order
        self._ship_order(order_id, items)
        
        self.logger.log_action(
            action="order_completed",
            message=f"Order {order_id} completed successfully",
            success=True,
            context={"order_id": order_id, "final_status": "shipped"}
        )
        return True
    
    def _validate_order(self, order_id: str, items: list) -> bool:
        if not items:
            self.logger.log_action(
                action="order_validation",
                message="Order validation failed: no items",
                success=False,
                context={"order_id": order_id, "reason": "empty_cart"}
            )
            return False
        
        self.logger.log_action(
            action="order_validation", 
            message=f"Order {order_id} validation passed",
            success=True,
            context={"order_id": order_id, "items_count": len(items)}
        )
        return True
    
    def _process_payment(self, order_id: str, customer_id: str) -> bool:
        # Simulate payment processing
        time.sleep(0.2)
        success = not customer_id.startswith("bad_")
        
        self.logger.log_action(
            action="payment_processing",
            message=f"Payment {'succeeded' if success else 'failed'} for order {order_id}",
            success=success,
            status_code=200 if success else 402,
            context={
                "order_id": order_id,
                "customer_id": customer_id,
                "payment_method": "credit_card"
            }
        )
        return success
    
    def _ship_order(self, order_id: str, items: list):
        with timed_operation(self.logger, "shipping"):
            time.sleep(0.1)  # Simulate shipping process
            
            tracking_number = f"TRK{order_id[-6:].upper()}"
            self.logger.log_action(
                action="order_shipped",
                message=f"Order {order_id} shipped",
                success=True,
                context={
                    "order_id": order_id,
                    "tracking_number": tracking_number,
                    "items_shipped": len(items)
                }
            )

# Usage
if __name__ == "__main__":
    processor = OrderProcessor()
    
    # Process successful order
    success = processor.process_order(
        order_id="ORD001",
        customer_id="CUST123", 
        items=[
            {"id": "WIDGET001", "price": 29.99},
            {"id": "GADGET002", "price": 49.99}
        ]
    )
    
    logger.info(f"Order processing result: {'SUCCESS' if success else 'FAILED'}")
    
    # Upload logs to Athena (optional)
    from tp_logger import upload_to_athena
    upload_success = upload_to_athena()
    logger.info(f"Athena upload: {'SUCCESS' if upload_success else 'FAILED'}")
```

## 🔧 Troubleshooting

### Common Issues

**DLT Pipeline Errors**
```python
# Check DLT pipeline status
from tp_logger.pipeline import get_pipeline
pipeline = get_pipeline()
print(f"Pipeline state: {pipeline.state}")
```

**Athena Upload Failures**
```python
# Validate Athena configuration
from tp_logger.config import get_config
config = get_config()

required_settings = [
    config.athena_destination,
    config.aws_region,
    config.athena_database,
    config.athena_s3_staging_bucket
]

if not all(required_settings):
    print("❌ Missing required Athena configuration")
else:
    print("✅ Athena configuration looks good")
```

**Environment Variables**
```bash
# Check environment variables
env | grep TP_LOGGER

# Check AWS credentials
aws sts get-caller-identity
```

### Debug Mode

```python
# Enable debug logging
setup_logging(
    project_name="debug_app",
    log_level="DEBUG",
    console_logging=True
)

# Check configuration
from tp_logger.config import get_config
config = get_config()
print(f"Configuration: {vars(config)}")
```

## 🚀 Use Cases

- **📊 Application Monitoring**: Track function performance and errors
- **🔄 Data Pipeline Logging**: Log ETL processes with structured metadata  
- **🌐 API Request Logging**: Log HTTP requests with status codes and timing
- **💼 Business Process Tracking**: Log business events with custom context
- **🐛 Debugging**: Rich structured logs for troubleshooting
- **📈 Analytics**: Query logs with SQL for insights and reporting

## 🏆 Why tp-logger?

- **🎯 Simple**: Minimal setup, maximum functionality
- **📊 Structured**: Consistent schema for all log data
- **🔍 Queryable**: Easy to analyze logs with SQL
- **🛡️ Reliable**: Built on DLT Hub for robust data handling
- **🔒 Type-safe**: Pydantic models prevent data inconsistencies
- **⚡ Performant**: Efficient batch writes to DuckDB
- **☁️ Scalable**: Upload to Athena for cloud-scale analytics
- **🏗️ Modular**: Clean architecture for easy maintenance

## 🛠️ Development

Built with modern Python tooling:

- **📦 Package Management**: uv
- **🔄 Data Pipeline**: DLT Hub  
- **💾 Database**: DuckDB
- **✅ Validation**: Pydantic
- **📝 Logging**: loguru
- **☁️ Cloud**: AWS Athena
- **🧪 Testing**: pytest

## 📄 License

MIT License - see LICENSE file for details.

---

Made with ❤️ for better logging and observability.