# Development Tools

Original location of development tool emulators. Scripts have been reorganized into individual folders at the repository root.

## New Organization

Development tools have been moved to separate folders:

- **pytest_emulator_tool/** - pytest testing framework emulator
- **coverage_emulator_tool/** - Coverage.py code coverage emulator
- **code_formatter_tool/** - Black code formatter emulator
- **live_reload_tool/** - Live reload development server
- **cms_cli_tool/** - CMS scaffolding CLI tool

## What's Still Here

This folder contains the original implementations that are imported by the root-level entry points.

### Scripts

- **pytest_emulator.py** - Main pytest emulator implementation
- **coverage_emulator.py** - Coverage tracking implementation
- **formatter.py** - Code formatter implementation
- **live_reload.py** - File watching and auto-reload
- **cli.py** - CMS scaffolding tool implementation

### Tests

- **test_pytest_emulator.py** - Tests for pytest emulator
- **test_coverage_emulator.py** - Tests for coverage emulator
- **test_formatter.py** - Tests for code formatter

## Usage

Import from dev_tools or use the new individual folders:

```python
# Original way
from dev_tools.pytest_emulator import PyTestEmulator
from dev_tools.coverage_emulator import Coverage
from dev_tools.formatter import Black

# New way (from individual folders)
from pytest_emulator_tool.pytest_emulator import PyTestEmulator
from coverage_emulator_tool.coverage_emulator import Coverage
from code_formatter_tool.formatter import Black
```

## See Also

Refer to the README files in the individual tool folders for detailed documentation:
- [pytest_emulator_tool/README.md](../pytest_emulator_tool/README.md)
- [coverage_emulator_tool/README.md](../coverage_emulator_tool/README.md)
- [code_formatter_tool/README.md](../code_formatter_tool/README.md)
- [live_reload_tool/README.md](../live_reload_tool/README.md)
- [cms_cli_tool/README.md](../cms_cli_tool/README.md)
