# Testing Guide

This document explains how to run and work with tests in the diary application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_todo_integration.py # Integration tests for Todo API
├── test_utils.py           # Test utilities and helper functions
└── README_TESTS.md         # This file
```

## Installation

First, install the test dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Quick Start

Run all tests:
```bash
python -m pytest
```

### Using the Test Runner Script

The `run_tests.py` script provides convenient options:

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run with coverage report
python run_tests.py --coverage

# Run integration tests only
python run_tests.py --integration

# Run specific test file
python run_tests.py test_todo_integration.py
```

### Manual pytest Commands

```bash
# Run all tests with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_todo_integration.py

# Run specific test method
python -m pytest tests/test_todo_integration.py::TestTodoIntegration::test_create_todo_success

# Run with coverage
python -m pytest --cov=app --cov-report=html --cov-report=term

# Run integration tests only
python -m pytest -m integration

# Run with detailed output
python -m pytest -v --tb=long
```

## Test Categories

### Integration Tests
- Test complete API workflows
- Use real database (in-memory SQLite for tests)
- Test HTTP endpoints end-to-end
- Located in `test_todo_integration.py`

### Test Fixtures

The `conftest.py` file provides several useful fixtures:

- `session`: Test database session with in-memory SQLite
- `client`: FastAPI test client with dependency overrides
- `sample_todo_data`: Sample todo data for testing
- `sample_todo_create_data`: Sample todo creation data

## Test Utilities

The `test_utils.py` module provides helper functions:

- `create_test_todo()`: Create a test todo and return response data
- `assert_todo_matches()`: Assert todo data matches expectations
- `create_multiple_todos()`: Create multiple test todos

## Test Coverage

The integration tests cover:

✅ **CRUD Operations**
- Create todo (successful and validation errors)
- Read todo (existing and non-existent)
- Update todo (full and partial updates)
- Delete todo (existing and non-existent)
- List todos (empty and with data)

✅ **Error Handling**
- 404 errors for non-existent todos
- 422 validation errors for invalid data

✅ **Workflows**
- Complete CRUD workflow
- Partial updates
- Data persistence verification

✅ **API Features**
- CORS middleware configuration
- Proper HTTP status codes
- JSON response formats

## Adding New Tests

### Integration Tests

Add new test methods to `TestTodoIntegration` class in `test_todo_integration.py`:

```python
def test_new_feature(self, client: TestClient):
    """Test description."""
    response = client.post("/api/v1/todo/", json={"title": "Test"})
    assert response.status_code == 200
```

### Test Fixtures

Add new fixtures to `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    """Custom fixture description."""
    return {"custom": "data"}
```

## Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Use fixtures** for common test data and setup
3. **Test both success and failure cases**
4. **Use helper functions** for common operations
5. **Assert specific expectations** rather than general ones
6. **Clean up after tests** (handled automatically by fixtures)

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running tests from the project root
2. **Database errors**: Tests use in-memory SQLite, no setup required
3. **Missing dependencies**: Run `pip install -r requirements.txt`

### Running Tests in Development

For development, run tests frequently:

```bash
# Quick test run
python -m pytest tests/test_todo_integration.py -v

# With coverage to see what's missing
python run_tests.py --coverage
```

## CI/CD Integration

These tests are designed to run in CI/CD environments. Example GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    python -m pytest --cov=app --cov-report=xml
``` 