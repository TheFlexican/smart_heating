# Smart Heating Unit Tests

Comprehensive unit test suite for the Smart Heating Home Assistant integration using pytest.

## Overview

This test suite provides extensive coverage of the Smart Heating integration with the goal of achieving **at least 85% code coverage**. Tests follow Home Assistant best practices and use pytest with async support.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Common fixtures and test configuration
├── unit/
│   ├── __init__.py
│   ├── const.py               # Test constants
│   ├── test_area_manager.py  # Area Manager tests
│   ├── test_coordinator.py   # Data Coordinator tests
│   ├── test_climate.py       # Climate platform tests
│   ├── test_scheduler.py     # Schedule Executor tests
│   ├── test_safety_monitor.py # Safety Monitor tests
│   ├── test_vacation_manager.py # Vacation Manager tests
│   ├── test_models_area.py   # Area model tests
│   ├── test_switch.py        # Switch platform tests
│   ├── test_utils.py         # Utility functions tests
│   └── test_history.py       # History tracker tests (database migration)
├── e2e/                       # Playwright end-to-end tests
│   ├── tests/                 # E2E test files
│   ├── playwright.config.ts   # Playwright configuration
│   └── package.json           # E2E dependencies
└── README.md
```

## Requirements

Install test dependencies:

```bash
pip install -r requirements_test.txt
```

Key dependencies:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-homeassistant-custom-component` - HA test helpers
- `homeassistant` - Home Assistant core

## Running Tests

### Quick Run

Use the provided test runner script:

```bash
./run_tests.sh
```

This script will:
1. Create/activate virtual environment
2. Install dependencies
3. Run all tests with coverage
4. Generate HTML coverage report
5. Check if coverage meets 85% threshold

### Manual Run

#### Run all tests:
```bash
pytest tests/unit -v
```

#### Run with coverage:
```bash
pytest tests/unit --cov=smart_heating --cov-report=term-missing -v
```

#### Run specific test file:
```bash
pytest tests/unit/test_area_manager.py -v
```

#### Run specific test class:
```bash
pytest tests/unit/test_area_manager.py::TestAreaManagerInitialization -v
```

#### Run specific test:
```bash
pytest tests/unit/test_area_manager.py::TestAreaManagerInitialization::test_init -v
```

## Coverage Reports

### Terminal Report
```bash
pytest tests/unit --cov=smart_heating --cov-report=term-missing
```

### HTML Report
```bash
pytest tests/unit --cov=smart_heating --cov-report=html
# Open coverage_html/index.html in browser
```

### XML Report (for CI/CD)
```bash
pytest tests/unit --cov=smart_heating --cov-report=xml
```

## Test Structure

### Fixtures (`conftest.py`)

Common fixtures available in all tests:

- `mock_config_entry` - Mock Home Assistant config entry
- `mock_area_manager` - Mock AreaManager instance
- `mock_coordinator` - Mock DataUpdateCoordinator
- `mock_area_data` - Mock area data dictionary
- `mock_climate_device` - Mock climate device state
- `mock_sensor_state` - Mock sensor state
- `mock_schedule_entry` - Mock schedule entry
- `mock_learning_data` - Mock learning engine data

### Test Organization

Tests are organized by module/component:

1. **Core Module Tests**
   - `test_area_manager.py` - Area management (create, update, delete, settings)
   - `test_coordinator.py` - Data coordination and updates
   - `test_models_area.py` - Area model functionality
   - `test_history.py` - History tracker (database migration, dual storage backends)

2. **Platform Tests**
   - `test_climate.py` - Climate entity (temperature, presets, HVAC modes)
   - `test_switch.py` - Switch entity (enable/disable areas)

3. **Manager Tests**
   - `test_scheduler.py` - Schedule execution
   - `test_safety_monitor.py` - Safety monitoring (smoke, CO detection)
   - `test_vacation_manager.py` - Vacation mode management

4. **Utility Tests**
   - `test_utils.py` - Validators and response builders

5. **End-to-End Tests** (`tests/e2e/`)
   - Browser-based testing with Playwright
   - Full user workflow validation
   - Run: `cd tests/e2e && npm test`

### Test Patterns

#### Testing Async Functions
```python
async def test_async_function(hass: HomeAssistant):
    """Test an async function."""
    result = await some_async_function()
    assert result is True
```

#### Mocking Service Calls
```python
async def test_service_call(hass: HomeAssistant):
    """Test Home Assistant service calls."""
    hass.services.async_call = AsyncMock()
    await entity.async_set_temperature(temperature=22.0)
    hass.services.async_call.assert_called_once()
```

#### Testing State Changes
```python
def test_state_change(mock_coordinator, mock_area_data):
    """Test entity state based on coordinator data."""
    mock_coordinator.data = {"areas": {TEST_AREA_ID: mock_area_data}}
    assert entity.current_temperature == mock_area_data["current_temperature"]
```

## Coverage Goals

Target coverage by module:

| Module | Target Coverage |
|--------|----------------|
| area_manager.py | 90%+ |
| coordinator.py | 85%+ |
| climate.py | 85%+ |
| scheduler.py | 85%+ |
| safety_monitor.py | 85%+ |
| vacation_manager.py | 85%+ |
| history.py | 85%+ |
| models/area.py | 90%+ |
| utils/* | 90%+ |
| **Overall** | **85%+** |

## Test Coverage Highlights

### History Tracker Tests (`test_history.py`)

Comprehensive testing of dual storage backend system:

**Database Migration Tests:**
- JSON → Database migration with data preservation
- Database → JSON migration with data preservation
- Backend preference persistence across restarts
- Migration validation (checks database availability)
- Error handling for unsupported databases (SQLite)

**Database Validation Tests:**
- Automatic MariaDB/MySQL/PostgreSQL detection
- Fallback to JSON for SQLite or unavailable databases
- Table creation with optimized schema
- Database engine initialization

**Storage Backend Tests:**
- JSON storage read/write operations
- Database storage read/write operations
- In-memory cache management (1000 entries per area)
- Retention period enforcement (1-365 days)
- Automatic cleanup of old entries

**API Tests:**
- Storage info endpoint
- Database stats endpoint
- Migration endpoint
- Configuration endpoint
- Cleanup endpoint

## Writing New Tests

### 1. Create Test File

Create `test_<module_name>.py` in `tests/unit/`:

```python
"""Tests for <Module Name>."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.smart_heating.<module> import YourClass


@pytest.fixture
def your_fixture():
    """Create test fixture."""
    return YourClass()


class TestYourClassInitialization:
    """Test class initialization."""
    
    def test_init(self, your_fixture):
        """Test initialization."""
        assert your_fixture is not None
```

### 2. Use Existing Fixtures

Leverage fixtures from `conftest.py`:

```python
async def test_with_fixtures(
    hass: HomeAssistant,
    mock_area_manager,
    mock_coordinator,
    mock_area_data
):
    """Test using common fixtures."""
    # Your test code
    pass
```

### 3. Follow Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>` (e.g., `TestAreaManagement`)
- Test functions: `test_<what_it_tests>` (e.g., `test_create_area`)

### 4. Test Organization

Group related tests in classes:

```python
class TestAreaCreation:
    """Test area creation functionality."""
    
    async def test_create_area_success(self):
        """Test successful area creation."""
        pass
    
    async def test_create_area_duplicate(self):
        """Test creating duplicate area."""
        pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements_test.txt
      - name: Run tests
        run: pytest tests/unit --cov=smart_heating --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run with verbose output:
```bash
pytest tests/unit -vv
```

### Run with print statements:
```bash
pytest tests/unit -s
```

### Run last failed tests:
```bash
pytest tests/unit --lf
```

### Run with pdb debugger:
```bash
pytest tests/unit --pdb
```

## Best Practices

1. **Test One Thing** - Each test should verify one specific behavior
2. **Use Descriptive Names** - Test names should clearly describe what they test
3. **Arrange-Act-Assert** - Structure tests with setup, execution, and verification
4. **Use Fixtures** - Leverage pytest fixtures for test data and mocks
5. **Mock External Dependencies** - Use mocks for HA services, state, etc.
6. **Test Edge Cases** - Include tests for error conditions and boundary values
7. **Keep Tests Fast** - Avoid unnecessary delays or complex setups
8. **Maintain Independence** - Tests should not depend on each other

## Home Assistant Testing Guidelines

Follow HA testing best practices from:
https://developers.home-assistant.io/docs/development_testing/

Key points:
- Use `MockConfigEntry` for config entries
- Test via HA core interfaces (states, services, registries)
- Use `async_setup_entry` and `async_unload_entry`
- Mock device/entity registries when needed
- Use snapshot testing for complex outputs

## Troubleshooting

### Import Errors
Ensure `custom_components` is in the Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Warnings
Make sure `pytest-asyncio` is installed and tests use `async def`.

### Coverage Too Low
Run with `--cov-report=term-missing` to see untested lines:
```bash
pytest tests/unit --cov=smart_heating --cov-report=term-missing
```

## Contributing

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure tests pass: `./run_tests.sh`
3. Check coverage meets 85% threshold
4. Update this README if adding new test patterns

## License

Same as Smart Heating integration - see main project LICENSE.
