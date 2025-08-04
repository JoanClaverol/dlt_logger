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

### From PyPI (Recommended)

```bash
pip install tp-logger
```

Or with uv:

```bash
uv add tp-logger
```

### From GitHub Repository

Install the latest development version directly from GitHub:

```bash
# Using pip
pip install git+https://github.com/JoanClaverol/tp_logger.git

# Using uv (recommended)
uv add git+https://github.com/JoanClaverol/tp_logger.git
```

#### Install Specific Version/Branch/Tag

```bash
# Install specific branch
uv add git+https://github.com/JoanClaverol/tp_logger.git@main
uv add git+https://github.com/JoanClaverol/tp_logger.git@development

# Install specific tag/release
uv add git+https://github.com/JoanClaverol/tp_logger.git@v0.1.0

# Install specific commit
uv add git+https://github.com/JoanClaverol/tp_logger.git@abc1234
```

#### For Development

If you want to contribute or modify the library:

```bash
# Clone the repository
git clone https://github.com/JoanClaverol/tp_logger.git
cd tp_logger

# Install in development mode with uv
uv sync

# Or install in editable mode with pip
pip install -e .
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

## More Examples

### Simple Function Logging

```python
from tp_logger import get_logger, log_execution
import time
import random

logger = get_logger(__name__)

@log_execution("data_processing")
def process_data_batch(batch_size: int = 100):
    """Process a batch of data with automatic timing."""
    print(f"Processing {batch_size} records...")
    time.sleep(0.2)  # Simulate work
    return f"Processed {batch_size} records"

@log_execution("file_operations") 
def save_results(data: str, filename: str):
    """Save results to file with logging."""
    logger.log_action(
        action="file_write",
        message=f"Saving data to {filename}",
        success=True,
        context={"filename": filename, "data_size": len(data)}
    )
    # Simulate file save
    time.sleep(0.1)
    return True

def calculate_metrics(values: list):
    """Calculate metrics with structured logging."""
    logger.info(f"Calculating metrics for {len(values)} values")
    
    try:
        result = {
            "mean": sum(values) / len(values),
            "max": max(values),
            "min": min(values)
        }
        
        logger.log_action(
            action="metrics_calculation",
            message="Successfully calculated metrics",
            success=True,
            context={
                "input_count": len(values),
                "mean": result["mean"],
                "range": result["max"] - result["min"]
            }
        )
        return result
        
    except Exception as e:
        logger.log_exception("metrics_calculation", e)
        raise

# Usage example
if __name__ == "__main__":
    # Process some data
    result = process_data_batch(250)
    
    # Save results  
    save_results(result, "output.txt")
    
    # Calculate metrics
    sample_data = [random.randint(1, 100) for _ in range(50)]
    metrics = calculate_metrics(sample_data)
    
    logger.info("All operations completed successfully")
```

### Error Handling and Recovery

```python
from tp_logger import get_logger, log_execution
import random
import time

logger = get_logger(__name__)

@log_execution("network_request")
def fetch_data_with_retry(url: str, max_retries: int = 3):
    """Fetch data with retry logic and comprehensive logging."""
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to fetch data from {url} (attempt {attempt + 1})")
            
            # Simulate network request that might fail
            if random.random() < 0.3:  # 30% chance of failure
                raise ConnectionError(f"Failed to connect to {url}")
            
            # Simulate successful response
            time.sleep(0.1)
            data = {"status": "success", "records": 42}
            
            logger.log_action(
                action="data_fetch_success",
                message=f"Successfully fetched data from {url}",
                success=True,
                status_code=200,
                context={
                    "url": url,
                    "attempt": attempt + 1,
                    "records_received": data["records"]
                }
            )
            return data
            
        except Exception as e:
            logger.log_action(
                action="data_fetch_failed",
                message=f"Failed to fetch data: {str(e)}",
                success=False,
                status_code=500,
                context={
                    "url": url,
                    "attempt": attempt + 1,
                    "error_type": type(e).__name__
                }
            )
            
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed for {url}")
                raise
            else:
                logger.warning(f"Retrying in 1 second... ({attempt + 1}/{max_retries})")
                time.sleep(1)

def validate_user_input(user_data: dict):
    """Validate user input with detailed logging."""
    logger.debug("Starting user input validation")
    
    errors = []
    
    # Check required fields
    required_fields = ["name", "email", "age"]
    for field in required_fields:
        if field not in user_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate email format
    if "email" in user_data and "@" not in user_data["email"]:
        errors.append("Invalid email format")
    
    # Validate age
    if "age" in user_data:
        try:
            age = int(user_data["age"])
            if age < 0 or age > 150:
                errors.append("Age must be between 0 and 150")
        except ValueError:
            errors.append("Age must be a number")
    
    if errors:
        logger.log_action(
            action="validation_failed",
            message=f"User input validation failed with {len(errors)} errors",
            success=False,
            context={
                "errors": errors,
                "provided_fields": list(user_data.keys())
            }
        )
        return False, errors
    else:
        logger.log_action(
            action="validation_success",
            message="User input validation passed",
            success=True,
            context={"validated_fields": list(user_data.keys())}
        )
        return True, []

# Example usage
if __name__ == "__main__":
    # Test network requests with retry
    try:
        data = fetch_data_with_retry("https://api.example.com/data")
        logger.info(f"Received data: {data}")
    except Exception as e:
        logger.error(f"Failed to fetch data after all retries: {e}")
    
    # Test validation
    test_users = [
        {"name": "John", "email": "john@example.com", "age": 30},
        {"name": "Jane", "email": "invalid-email", "age": "not-a-number"},
        {"email": "missing@name.com", "age": 25}
    ]
    
    for i, user in enumerate(test_users):
        logger.info(f"Validating user {i + 1}")
        is_valid, validation_errors = validate_user_input(user)
        if not is_valid:
            logger.warning(f"User {i + 1} validation failed: {validation_errors}")
```

### Business Process Tracking

```python
from tp_logger import get_logger, log_execution, timed_operation
import time
from datetime import datetime

logger = get_logger(__name__)

class OrderProcessor:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    @log_execution("order_processing")
    def process_order(self, order_id: str, customer_id: str, items: list):
        """Process a customer order with full tracking."""
        
        self.logger.log_action(
            action="order_received",
            message=f"New order received: {order_id}",
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
        
        # Check inventory
        if not self._check_inventory(items):
            return False
        
        # Process payment
        payment_success = self._process_payment(order_id, customer_id)
        if not payment_success:
            return False
        
        # Fulfill order
        self._fulfill_order(order_id, items)
        
        self.logger.log_action(
            action="order_completed",
            message=f"Order {order_id} completed successfully",
            success=True,
            context={
                "order_id": order_id,
                "processing_time": datetime.now().isoformat(),
                "final_status": "completed"
            }
        )
        return True
    
    def _validate_order(self, order_id: str, items: list) -> bool:
        """Validate order details."""
        self.logger.debug(f"Validating order {order_id}")
        
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
            context={"order_id": order_id, "items_validated": len(items)}
        )
        return True
    
    def _check_inventory(self, items: list) -> bool:
        """Check if items are in stock."""
        with timed_operation(self.logger, "inventory_check"):
            # Simulate inventory check
            time.sleep(0.1)
            
            out_of_stock = []
            for item in items:
                # Simulate random stock status
                if item.get("id", "").endswith("99"):  # Items ending in 99 are out of stock
                    out_of_stock.append(item["id"])
            
            if out_of_stock:
                self.logger.log_action(
                    action="inventory_insufficient",
                    message=f"{len(out_of_stock)} items out of stock",
                    success=False,
                    context={"out_of_stock_items": out_of_stock}
                )
                return False
            
            self.logger.log_action(
                action="inventory_confirmed",
                message="All items in stock",
                success=True,
                context={"items_checked": len(items)}
            )
            return True
    
    def _process_payment(self, order_id: str, customer_id: str) -> bool:
        """Process payment for the order."""
        with timed_operation(self.logger, "payment_processing"):
            # Simulate payment processing
            time.sleep(0.2)
            
            # Simulate payment success/failure
            payment_successful = not customer_id.startswith("bad_")
            
            if payment_successful:
                self.logger.log_action(
                    action="payment_success",
                    message=f"Payment processed for order {order_id}",
                    success=True,
                    context={
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "payment_method": "credit_card"
                    }
                )
            else:
                self.logger.log_action(
                    action="payment_failed",
                    message=f"Payment failed for order {order_id}",
                    success=False,
                    context={
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "failure_reason": "insufficient_funds"
                    }
                )
            
            return payment_successful
    
    def _fulfill_order(self, order_id: str, items: list):
        """Fulfill the order."""
        with timed_operation(self.logger, "order_fulfillment"):
            # Simulate fulfillment process
            time.sleep(0.15)
            
            self.logger.log_action(
                action="order_shipped",
                message=f"Order {order_id} has been shipped",
                success=True,
                context={
                    "order_id": order_id,
                    "items_shipped": len(items),
                    "tracking_number": f"TRK{order_id[-6:].upper()}"
                }
            )

# Example usage
if __name__ == "__main__":
    processor = OrderProcessor()
    
    # Test successful order
    success = processor.process_order(
        order_id="ORD123456",
        customer_id="CUST789",
        items=[
            {"id": "ITEM001", "name": "Widget", "price": 29.99},
            {"id": "ITEM002", "name": "Gadget", "price": 49.99}
        ]
    )
    
    if success:
        logger.info("Order processed successfully")
    else:
        logger.error("Order processing failed")
    
    # Test failed order (customer with bad credit)
    processor.process_order(
        order_id="ORD123457", 
        customer_id="bad_customer",
        items=[{"id": "ITEM003", "name": "Thing", "price": 19.99}]
    )
```

## Configuration Options

The `setup_logging()` function accepts these parameters:

- `project_name` (str): Name of your project (default: "tp_logger_app")
- `db_path` (str): Path to DuckDB file (default: "./logs/app.duckdb")
- `log_level` (str): Minimum log level (default: "INFO")
- `console_logging` (bool): Enable console output (default: True)
- `dataset_name` (str): DLT dataset name (default: "tp_logger_logs")
- `pipeline_name` (str): DLT pipeline name (default: "tp_logger_pipeline")

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