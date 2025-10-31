# pre-commit Emulator

A pure Python implementation that emulates the core functionality of pre-commit for managing and running Git hooks without external dependencies.

## Overview

This module provides a framework for managing Git hooks that run automatically before commits, pushes, and other Git operations. It enables running linters, formatters, and validators to enforce code quality standards.

## Features

- **Git Hook Management**
  - Install and uninstall Git hooks
  - Support for multiple hook types (pre-commit, pre-push, commit-msg, etc.)
  - Automatic hook script generation
  - Hook lifecycle management

- **Hook Configuration**
  - YAML-based configuration (`.pre-commit-config.yaml`)
  - Multiple hooks per repository
  - File pattern matching (regex)
  - File type filtering (python, javascript, json, etc.)
  - Exclude patterns for skipping files

- **Hook Execution**
  - Run hooks on staged files or all files
  - Parallel hook execution support
  - Pass/fail result tracking
  - Skip specific hooks
  - Fail-fast mode
  - Verbose output mode

- **File Filtering**
  - Match files by regex patterns
  - Match files by type (python, json, yaml, etc.)
  - Exclude patterns
  - Automatic staged file detection

- **Result Reporting**
  - Clear pass/fail indicators
  - Execution time tracking
  - File count reporting
  - Detailed error messages
  - Summary statistics

## Usage

### Installation

Install pre-commit hooks in a Git repository:

```python
from precommit_emulator import PreCommitFramework

framework = PreCommitFramework()
framework.install()  # Installs pre-commit hook
```

Or from command line:

```bash
python -m precommit_emulator_tool.precommit_emulator install
```

### Configuration

Create a `.pre-commit-config.yaml` file in your repository root:

```yaml
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      - id: check-yaml
        name: Check YAML
        entry: python -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"
        language: system
        types: [yaml]
      
      - id: trailing-whitespace
        name: Trim Trailing Whitespace
        entry: sed -i 's/[[:space:]]*$//'
        language: system
        types: [text]
      
      - id: python-syntax
        name: Check Python Syntax
        entry: python -m py_compile
        language: system
        types: [python]
```

### Running Hooks

Run hooks manually:

```python
from precommit_emulator import PreCommitFramework

framework = PreCommitFramework()
success = framework.run(hook_stage='pre-commit')

if success:
    print("All hooks passed!")
else:
    print("Some hooks failed!")
```

Or from command line:

```bash
# Run on staged files
python -m precommit_emulator_tool.precommit_emulator run

# Run on all files
python -m precommit_emulator_tool.precommit_emulator run --all-files

# Run with verbose output
python -m precommit_emulator_tool.precommit_emulator run --verbose

# Skip specific hooks
python -m precommit_emulator_tool.precommit_emulator run --skip check-yaml --skip trailing-whitespace
```

### Uninstallation

Uninstall hooks:

```python
framework = PreCommitFramework()
framework.uninstall()
```

Or from command line:

```bash
python -m precommit_emulator_tool.precommit_emulator uninstall
```

## Hook Configuration

### Hook Definition

Each hook has the following properties:

- **id**: Unique identifier for the hook
- **name**: Human-readable name
- **entry**: Command to execute
- **language**: Language/runtime (default: `system`)
- **files**: Regex pattern for files to check (default: `.*`)
- **exclude**: Regex pattern for files to exclude
- **types**: List of file types (python, json, yaml, etc.)
- **stages**: List of hook stages (pre-commit, pre-push, etc.)
- **pass_filenames**: Pass matching filenames to command (default: `true`)
- **always_run**: Run even if no files match (default: `false`)
- **verbose**: Show command output (default: `false`)

### Example Configuration

```yaml
repos:
  - repo: local
    rev: v1.0.0
    hooks:
      # Check JSON syntax
      - id: check-json
        name: Check JSON Files
        entry: python -m json.tool
        language: system
        types: [json]
      
      # Check Python syntax
      - id: check-python
        name: Check Python Syntax
        entry: python -m py_compile
        language: system
        types: [python]
        
      # Run custom script
      - id: custom-check
        name: Custom Check
        entry: ./scripts/check.sh
        language: system
        files: \.py$
        exclude: test_.*\.py$
        
      # Always run regardless of files
      - id: notify
        name: Notify
        entry: echo "Running pre-commit checks..."
        language: system
        always_run: true
        pass_filenames: false

# Global configuration
fail_fast: false
default_stages: [commit, push]
```

## Hook Stages

Supported Git hook stages:

- **pre-commit**: Before creating a commit
- **pre-push**: Before pushing to remote
- **commit-msg**: After commit message is entered
- **pre-merge-commit**: Before merge commit
- **post-commit**: After commit is created
- **post-checkout**: After checkout
- **post-merge**: After merge

## File Type Detection

Built-in file type mappings:

- **python**: `.py`
- **javascript**: `.js`, `.jsx`
- **typescript**: `.ts`, `.tsx`
- **json**: `.json`
- **yaml**: `.yaml`, `.yml`
- **markdown**: `.md`
- **text**: `.txt`

## Common Hook Examples

### Check YAML Syntax

```yaml
- id: check-yaml
  name: Check YAML
  entry: python -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"
  language: system
  types: [yaml]
```

### Check JSON Syntax

```yaml
- id: check-json
  name: Check JSON
  entry: python -m json.tool
  language: system
  types: [json]
```

### Trim Trailing Whitespace

```yaml
- id: trailing-whitespace
  name: Trim Trailing Whitespace
  entry: sed -i 's/[[:space:]]*$//'
  language: system
  types: [text]
```

### Check Python Syntax

```yaml
- id: python-syntax
  name: Check Python Syntax
  entry: python -m py_compile
  language: system
  types: [python]
```

### Check for Large Files

```yaml
- id: check-large-files
  name: Check for Large Files
  entry: python -c "import sys, os; exit(0 if os.path.getsize(sys.argv[1]) < 500000 else 1)"
  language: system
```

### Run Black Formatter

```yaml
- id: black
  name: Format with Black
  entry: black
  language: system
  types: [python]
```

### Run isort

```yaml
- id: isort
  name: Sort Imports
  entry: isort
  language: system
  types: [python]
```

### Run Flake8

```yaml
- id: flake8
  name: Lint with Flake8
  entry: flake8
  language: system
  types: [python]
```

## Command-Line Interface

### Install Hooks

```bash
# Install pre-commit hook
python -m precommit_emulator_tool.precommit_emulator install

# Install multiple hook types
python -m precommit_emulator_tool.precommit_emulator install -t pre-commit -t pre-push
```

### Run Hooks

```bash
# Run pre-commit hooks on staged files
python -m precommit_emulator_tool.precommit_emulator run

# Run on all files
python -m precommit_emulator_tool.precommit_emulator run --all-files

# Run specific hook stage
python -m precommit_emulator_tool.precommit_emulator run --hook-stage pre-push

# Run with verbose output
python -m precommit_emulator_tool.precommit_emulator run --verbose

# Skip specific hooks
python -m precommit_emulator_tool.precommit_emulator run --skip check-yaml
```

### Uninstall Hooks

```bash
# Uninstall pre-commit hook
python -m precommit_emulator_tool.precommit_emulator uninstall

# Uninstall multiple hook types
python -m precommit_emulator_tool.precommit_emulator uninstall -t pre-commit -t pre-push
```

### Generate Sample Configuration

```bash
python -m precommit_emulator_tool.precommit_emulator sample-config > .pre-commit-config.yaml
```

## Python API

### Basic Usage

```python
from precommit_emulator import PreCommitFramework

# Create framework
framework = PreCommitFramework()

# Install hooks
framework.install()

# Run hooks
success = framework.run(hook_stage='pre-commit')

# Uninstall hooks
framework.uninstall()
```

### Advanced Usage

```python
from precommit_emulator import PreCommitFramework, Hook, HookResult

# Create framework with specific repo root
framework = PreCommitFramework(repo_root='/path/to/repo')

# Load configuration
config = framework.load_config()

# Get hooks for a stage
hooks = config.get_hooks('pre-commit')

# Run individual hook
result = framework.run_hook(hooks[0], files=['file1.py', 'file2.py'])

if result.result == HookResult.PASSED:
    print(f"Hook passed! Processed {result.files_processed} files in {result.duration:.2f}s")
else:
    print(f"Hook failed: {result.output}")
```

### Custom Hook Creation

```python
from precommit_emulator import Hook

hook = Hook(
    id='my-custom-hook',
    name='My Custom Hook',
    entry='./my-script.sh',
    language='system',
    files=r'.*\.py$',
    exclude=r'test_.*\.py$',
    types=['python'],
    stages=['pre-commit'],
    pass_filenames=True,
    always_run=False,
    verbose=True
)
```

## Testing

Run the test suite:

```bash
python test_precommit_emulator.py
```

The test suite includes:
- Hook class tests (5 tests)
- PreCommitConfig tests (3 tests)
- PreCommitFramework tests (10 tests)
- HookExecution tests (1 test)
- HookStage tests (1 test)
- Integration tests (1 test)

## Use Cases

This emulator is ideal for:

- **Code Quality**: Enforce code quality standards before commits
- **Formatting**: Automatically format code before commits
- **Linting**: Run linters to catch errors early
- **Testing**: Run quick tests before commits
- **Security**: Check for security issues before commits
- **CI/CD**: Validate code before it enters the pipeline
- **Team Standards**: Enforce team coding standards
- **Documentation**: Ensure documentation is up to date

## Benefits

### Consistency

Ensures all team members run the same checks before committing, maintaining consistent code quality.

### Early Detection

Catches issues early in the development process, before code review or CI/CD.

### Automation

Automatically runs checks without manual intervention, reducing human error.

### Flexibility

Highly configurable to match your project's specific needs and workflows.

### Speed

Runs checks locally, providing immediate feedback without waiting for CI/CD.

## Best Practices

### 1. Keep Hooks Fast

Hooks should complete quickly to avoid slowing down the development workflow. Use `--all-files` mode for comprehensive checks in CI/CD.

### 2. Use Fail-Fast Strategically

Set `fail_fast: true` in configuration to stop on first failure, or `false` to see all failures.

### 3. Skip Hooks When Needed

Use `--skip` to bypass specific hooks when you need to commit quickly (e.g., work in progress).

### 4. Test Configuration

Test your hook configuration with `--all-files` before committing the configuration file.

### 5. Document Custom Hooks

Add comments to your configuration file explaining what custom hooks do.

### 6. Version Configuration

Commit your `.pre-commit-config.yaml` to version control so all team members use the same hooks.

### 7. Update Regularly

Keep your hook configuration up to date with project needs and new tools.

## Limitations

Compared to the full pre-commit framework:

- No remote repository support (all hooks must be local)
- Simplified YAML parsing (complex YAML features may not work)
- No virtual environment management for hooks
- No automatic hook updates
- Simplified language support (mainly `system` language)
- No hook caching or memoization

These limitations keep the implementation simple while covering common use cases.

## Performance

- **Fast Hook Execution**: Runs hooks in subprocess with minimal overhead
- **Selective File Processing**: Only processes relevant files based on patterns
- **Skip Optimization**: Automatically skips hooks with no matching files
- **Timeout Protection**: 5-minute timeout per hook prevents hanging

## Integration Examples

### With pytest Emulator

```yaml
- id: pytest
  name: Run Tests
  entry: python -m pytest_emulator_tool.pytest_emulator
  language: system
  types: [python]
  pass_filenames: false
  always_run: true
```

### With Black Emulator

```yaml
- id: black
  name: Format Code
  entry: python -m code_formatter_tool.formatter
  language: system
  types: [python]
```

### With isort Emulator

```yaml
- id: isort
  name: Sort Imports
  entry: python -m isort_emulator_tool.isort_emulator
  language: system
  types: [python]
```

### With Flake8 Emulator

```yaml
- id: flake8
  name: Lint Code
  entry: python -m flake8_emulator_tool.flake8_emulator
  language: system
  types: [python]
```

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
