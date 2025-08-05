# dlt-logger Development Instructions

## Project Overview
dlt-logger is a Python library for structured logging with DuckDB storage via DLT Hub. It provides simple decorator-based logging with built-in analytics capabilities.

## Development Environment

### Language & Tools
- **Language**: Python 3.9+
- **Package Manager**: uv (preferred over pip)
- **Code Quality**: ruff for linting and formatting
- **Testing**: pytest with coverage
- **Type Checking**: Built-in with Pydantic models

### Essential uv Commands
```bash
# Install dependencies
uv sync

# Run commands in virtual environment
uv run python main.py
uv run pytest tests/
uv run ruff check .
uv run ruff format .

# Add new dependencies
uv add package_name
uv add --dev package_name  # For development dependencies

# Build package
uv build

# Update dependencies
uv sync --upgrade
```

## Project Structure
```
dlt_logger/                  # Main package
├── __init__.py            # Package exports
├── config.py              # Configuration management
├── core.py                # DLT-based logging implementation
└── models.py              # Pydantic data models

tests/                     # Test suite (38 tests)
├── test_config.py         # Configuration tests
├── test_core.py           # Core functionality tests
├── test_models.py         # Data model tests
└── conftest.py            # Test fixtures

main.py                    # Usage example
README.md                  # User documentation
PRD.md                     # Product requirements
```

## Code Quality Standards

### Before Committing
Always run these commands:
```bash
uv run ruff check .        # Lint code
uv run ruff format .       # Format code
uv run pytest tests/       # Run all tests
```

### Testing Requirements
- **Coverage**: Maintain >90% test coverage
- **All tests must pass**: 38/38 tests should pass
- **Test types**: Unit tests for all public APIs
- **Fixtures**: Use conftest.py for shared test setup

### Code Style
- **Imports**: Follow PEP 8 import ordering
- **Type hints**: Use type hints for all public APIs
- **Docstrings**: Document all public functions/classes
- **Pydantic**: Use Pydantic models for data validation

## Key Technologies

### Core Dependencies
- **dlt[duckdb]**: Data pipeline framework for log storage
- **loguru**: Beautiful console logging
- **pydantic**: Data validation and serialization
- **duckdb**: Embedded analytical database

### Architecture Principles
- **DLT Hub**: Use DLT for all data pipeline operations
- **Pydantic Models**: Ensure type safety with structured data
- **Decorator Pattern**: Provide `@log_execution` for easy function logging
- **Configuration**: Centralized config management in `config.py`

## Development Workflow

### Adding New Features
1. **Write tests first** in appropriate `test_*.py` file
2. **Implement feature** in relevant module
3. **Update documentation** in README.md if user-facing
4. **Run quality checks**: ruff + pytest
5. **Test example usage** in main.py

### Making Changes
- **Breaking changes**: Update version in pyproject.toml
- **New parameters**: Add to LoggerConfig with defaults
- **API changes**: Update __init__.py exports
- **Schema changes**: Update LogEntry model carefully

## Common Tasks

### Adding New Log Fields
1. Update `LogEntry` model in `models.py`
2. Update DLT resource schema in `core.py`
3. Add tests in `test_models.py`
4. Update documentation examples

### Performance Optimization
- Profile with `uv run python -m cProfile main.py`
- Check DuckDB query performance
- Monitor DLT pipeline efficiency
- Test with large log volumes

### Debugging
- Use `console_logging=True` for development
- Check database contents: `duckdb logs/app.duckdb "SELECT * FROM dlt_logger_logs.job_logs"`
- Enable debug logging: `log_level="DEBUG"`

## Release Process

1. **Update version** in pyproject.toml
2. **Run full test suite**: `uv run pytest tests/ --cov=dlt_logger`
3. **Build package**: `uv build`
4. **Test installation**: `pip install dist/dlt_logger-*.whl`
5. **Commit changes** with version tag

## Important Notes

### What NOT to Change
- **Database schema**: LogEntry model structure (breaking change)
- **Public API**: Function signatures in __init__.py exports
- **Default behavior**: Existing configuration defaults

### Performance Considerations
- **Batch logging**: DLT handles batching automatically
- **Database size**: Monitor .duckdb file growth
- **Memory usage**: Large context objects can impact memory

### Security
- **No PII**: Never log sensitive personal information
- **Local storage**: All data stays local by default
- **File permissions**: Ensure proper database file permissions

## Troubleshooting

### Common Issues
- **Import errors**: Check `uv sync` completed successfully
- **Test failures**: Ensure clean environment with `uv run pytest --cache-clear`
- **DLT errors**: Check DuckDB file permissions and disk space
- **Type errors**: Run `uv run python -m mypy dlt_logger/` if available

### Getting Help
- **Documentation**: README.md for user guide
- **Examples**: main.py for usage patterns
- **Tests**: tests/ directory for API examples
- **Architecture**: PRD.md for design decisions