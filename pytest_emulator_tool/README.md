# pytest Emulator

A pure Python implementation of pytest functionality without external dependencies.

## What This Emulates

**Emulates:** pytest (Python testing framework)
**Original:** https://pytest.org/

## Features

- Test discovery with pattern matching (`test_*.py` and `*_test.py`)
- Fixture management system with scope support
- Assertion introspection for better error messages
- Test runner with detailed results
- Plugin architecture support
- Test outcome tracking (passed, failed, skipped, error)

## Core Components

- **pytest_emulator.py**: Main implementation
  - `TestOutcome`: Enumeration for test results
  - `TestResult`: Test execution results dataclass
  - `Fixture`: Fixture definition and management
  - `TestCollector`: Test discovery and collection
  - `TestRunner`: Test execution engine
  - `PyTestEmulator`: Main API class

## Usage

```python
from pytest_emulator import PyTestEmulator

# Create emulator instance
pytest_emu = PyTestEmulator()

# Discover and run tests
results = pytest_emu.run_tests("tests/")

# Check results
for result in results:
    print(f"{result.test_name}: {result.outcome.value}")
```

## Testing

Run the test suite:

```bash
python test_pytest_emulator.py
```

## Implementation Notes

- Uses Python's AST module for test discovery
- Implements fixture dependency injection
- Captures stdout/stderr during test execution
- Provides detailed error messages with tracebacks
- No external dependencies required

## Why This Was Created

This emulator was created as part of the CIV-ARCOS project to provide testing capabilities without external dependencies, ensuring a self-contained civilian version of military-grade software assurance tools.
