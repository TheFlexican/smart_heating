# Quick Start Guide - Smart Heating Unit Tests

## Installation

### Step 1: Install Test Dependencies

```bash
cd /Users/ralf/git/smart_heating
pip3 install -r requirements_test.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
cd /Users/ralf/git/smart_heating

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements_test.txt
```

### Step 2: Run Tests

#### Option A: Use the automated runner (recommended)
```bash
./run_tests.sh
```

This will:
- Set up virtual environment (if needed)
- Install dependencies
- Run all tests
- Generate coverage report
- Check 85% threshold

#### Option B: Run manually
```bash
# Run all tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=smart_heating --cov-report=term-missing -v

# Run specific test file
pytest tests/unit/test_area_manager.py -v
```

### Step 3: View Coverage Report

After running tests, open the HTML coverage report:

```bash
open coverage_html/index.html
```

## What You Get

✅ **126+ unit tests** covering all major components  
✅ **85%+ coverage target** enforced  
✅ **Automated test runner** (run_tests.sh)  
✅ **Comprehensive documentation** (tests/README.md)  
✅ **CI/CD ready** (GitHub Actions example included)  

## Test Structure

```
tests/
├── conftest.py              # Common fixtures
├── unit/
│   ├── test_area_manager.py    # 19 tests
│   ├── test_models_area.py     # 20 tests
│   ├── test_coordinator.py     # 15 tests
│   ├── test_climate.py         # 14 tests
│   ├── test_scheduler.py       # 11 tests
│   ├── test_safety_monitor.py  # 10 tests
│   ├── test_vacation_manager.py# 10 tests
│   ├── test_switch.py          # 8 tests
│   ├── test_utils.py           # 8 tests
│   ├── test_config_flow.py     # 5 tests
│   └── test_init.py            # 6 tests
└── README.md               # Full testing documentation
```

## Common Commands

```bash
# Run all tests verbosely
pytest tests/unit -v

# Run tests for specific module
pytest tests/unit/test_area_manager.py -v

# Run with coverage and see missing lines
pytest tests/unit --cov=smart_heating --cov-report=term-missing

# Run tests matching a pattern
pytest tests/unit -k "test_init" -v

# Run last failed tests
pytest tests/unit --lf

# Run with debugging
pytest tests/unit -s --pdb
```

## Troubleshooting

### Import errors?
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/unit
```

### Module not found?
```bash
# Make sure you're in the project root
cd /Users/ralf/git/smart_heating

# Reinstall dependencies
pip install -r requirements_test.txt
```

### Tests fail?
```bash
# Run with verbose output
pytest tests/unit -vv

# Run with print statements visible
pytest tests/unit -s
```

## Next Steps

1. **Run tests**: `./run_tests.sh`
2. **Check coverage**: Open `coverage_html/index.html`
3. **Add more tests** for uncovered lines
4. **Integrate with CI/CD** (see tests/README.md)

For complete documentation, see:
- `tests/README.md` - Full testing guide
- `TESTING_SUMMARY.md` - Implementation summary
