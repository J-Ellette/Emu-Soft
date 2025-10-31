# isort Emulator

A pure Python implementation that emulates the core functionality of isort for automatically organizing Python import statements without external dependencies.

## Overview

This module provides automatic import sorting and organization according to PEP 8 guidelines. It groups imports into sections (standard library, third-party, first-party) and sorts them alphabetically within each section.

## Features

- **Automatic Import Sorting**
  - Alphabetical sorting within sections
  - Separate sections for different import types
  - Sort both `import` and `from ... import` statements

- **Import Classification**
  - Standard library imports
  - Third-party package imports
  - First-party (local project) imports
  - Configurable classification rules

- **Preservation**
  - Preserve docstrings
  - Preserve comments (inline and standalone)
  - Preserve code structure after imports

- **Multi-line Import Support**
  - Handle imports with parentheses
  - Preserve multi-line formatting

- **File Operations**
  - Sort single files
  - Sort entire directories recursively
  - Check mode (verify without modifying)
  - Skip specific directories (`.git`, `__pycache__`, etc.)

- **Configuration**
  - Load configuration from files
  - Specify known first-party and third-party modules
  - Customizable line length and profiles

## Usage

### Basic Import Sorting

```python
from isort_emulator import sort_imports

code = """
import sys
import requests
import os
from myapp.models import User
from typing import List
"""

sorted_code = sort_imports(code,
    known_first_party={'myapp'},
    known_third_party={'requests'})

print(sorted_code)
```

Output:
```python
import os
import sys
from typing import List

import requests

from myapp.models import User
```

### Sort a File

```python
from isort_emulator import sort_file

# Sort and modify file
changed = sort_file('mymodule.py')
if changed:
    print("File was modified")

# Check without modifying
is_sorted = sort_file('mymodule.py', check_only=True)
if not is_sorted:
    print("File needs sorting")
```

### Sort a Directory

```python
from isort_emulator import sort_directory

# Sort all Python files in directory
modified, total = sort_directory('src/',
    known_first_party={'myapp'},
    known_third_party={'requests', 'django'})

print(f"Modified {modified} of {total} files")
```

### Custom Classification

```python
from isort_emulator import sort_imports

code = """
import requests
from myapp import utils
import django
"""

# Specify which modules belong to which category
sorted_code = sort_imports(code,
    known_first_party={'myapp'},
    known_third_party={'requests', 'django'})
```

### Configuration File

Create a `.isort.cfg` file:

```ini
known_first_party = myapp, mylib
known_third_party = requests, numpy, django
line_length = 100
profile = black
```

Load and use configuration:

```python
from isort_emulator import Config, sort_imports

config = Config.from_file('.isort.cfg')

code = "import sys\nimport requests"
sorted_code = sort_imports(code,
    known_first_party=config.known_first_party,
    known_third_party=config.known_third_party)
```

## Import Sections

Imports are organized into three sections, in this order:

1. **Standard Library** - Python built-in modules (os, sys, json, etc.)
2. **Third-Party** - Installed packages (requests, numpy, django, etc.)
3. **First-Party** - Your project's modules

Each section is separated by a blank line.

### Example

Before sorting:
```python
from myapp.models import User
import requests
import os
from typing import List
import sys
```

After sorting:
```python
import os
import sys
from typing import List

import requests

from myapp.models import User
```

## Import Ordering Within Sections

Within each section, imports are sorted as follows:

1. Regular `import` statements come before `from ... import` statements
2. Imports are sorted alphabetically by module name
3. Items in `from ... import` statements are sorted alphabetically

### Example

```python
# Regular imports first, alphabetically
import json
import os
import sys

# Then from imports, alphabetically
from pathlib import Path
from typing import Dict, List, Optional
```

## Command-Line Usage

You can run the emulator as a script:

```bash
# Sort a single file
python isort_emulator.py myfile.py

# Sort a directory
python isort_emulator.py src/

# Check without modifying
python isort_emulator.py --check myfile.py
```

## Advanced Features

### Preserving Docstrings

Module docstrings are automatically preserved at the top of the file:

```python
"""
This is my module.

It does important things.
"""
import os
import sys
```

### Preserving Comments

Comments are preserved with their associated imports:

```python
import os  # Operating system interface
import sys  # System-specific parameters
```

### Handling Relative Imports

Relative imports are automatically classified as first-party:

```python
from . import models
from .. import utils
from ...config import settings
```

### Multi-line Imports

Multi-line imports with parentheses are handled:

```python
from typing import (
    Dict,
    List,
    Optional,
    Union,
)
```

## Classification Logic

The emulator uses the following logic to classify imports:

1. **Known First-Party**: If module is in `known_first_party` set → first-party
2. **Known Third-Party**: If module is in `known_third_party` set → third-party
3. **Standard Library**: If module is in Python standard library → stdlib
4. **Relative Import**: If module starts with `.` → first-party
5. **Default**: Everything else → third-party

## Testing

Run the test suite:

```bash
python test_isort_emulator.py
```

The test suite includes:
- Import statement parsing (6 tests)
- Import section management (3 tests)
- Import classification (5 tests)
- Import sorting functionality (8 tests)
- File operations (4 tests)
- Configuration (2 tests)
- Edge cases (3 tests)

## Use Cases

This emulator is ideal for:
- **Code Formatting**: Automatically organize imports in your codebase
- **Code Review**: Ensure consistent import organization
- **CI/CD Pipelines**: Check import order in automated tests
- **Pre-commit Hooks**: Sort imports before committing
- **Legacy Code**: Clean up messy import sections
- **Project Templates**: Maintain clean imports from the start
- **Team Standards**: Enforce consistent import style

## Comparison with Manual Sorting

### Manual Sorting (Error-Prone)

```python
# Messy, inconsistent
import sys
from typing import List
import os
from myapp.models import User
import requests
from typing import Dict
```

### With isort Emulator (Clean, Consistent)

```python
# Clean, organized, consistent
import os
import sys
from typing import Dict, List

import requests

from myapp.models import User
```

## Configuration Options

### Config Class Properties

```python
config = Config()
config.known_first_party = {'myapp', 'mylib'}  # Set of first-party modules
config.known_third_party = {'requests', 'numpy'}  # Set of third-party modules
config.line_length = 88  # Maximum line length (not enforced yet)
config.profile = 'black'  # Style profile (not enforced yet)
config.skip_dirs = {'.git', 'venv', '__pycache__'}  # Directories to skip
```

### Profiles

While profiles are accepted, they don't currently change behavior. Supported profile names:
- `black` - Compatible with Black formatter (default)
- `django` - Django project style
- `pep8` - Standard PEP 8 style

## Implementation Details

### Standard Library Detection

The emulator includes a comprehensive list of Python 3.6+ standard library modules. This list is used to automatically classify imports without configuration.

### Parsing Strategy

1. Extract docstrings and preserve them
2. Identify all import statements (including multi-line)
3. Parse each import to extract module and items
4. Classify each import into appropriate section
5. Sort imports within each section
6. Reconstruct file with sorted imports
7. Preserve code after imports

### Thread Safety

The emulator is thread-safe for reading and sorting. File operations should be synchronized externally if multiple threads/processes modify the same files.

## Limitations

Compared to the full isort library:
- No custom section definitions beyond the three main sections
- Simplified multi-line import handling
- No automatic wrapping of long import lines
- No star import (*) handling
- No __future__ import special handling
- Simplified comment preservation
- No integration with version control systems

These limitations keep the implementation simple while covering the most common use cases.

## Best Practices

### 1. Configure Known Modules

Always specify your project's modules:

```python
known_first_party = {'myapp', 'mylib', 'mytools'}
```

### 2. Run in CI/CD

Add to your CI pipeline:

```bash
python isort_emulator.py --check src/
if [ $? -ne 0 ]; then
    echo "Imports are not sorted!"
    exit 1
fi
```

### 3. Use Pre-commit Hooks

Automatically sort imports before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit
python isort_emulator.py src/
git add -u
```

### 4. Skip Generated Code

Configure skip directories for generated or vendor code:

```python
skip_dirs = {'.git', 'vendor', 'generated', '__pycache__'}
```

## Performance

- **Fast Parsing**: Uses regular expressions and string operations
- **Minimal Memory**: Processes files one at a time
- **Efficient Sorting**: O(n log n) sorting complexity
- **Skip Optimization**: Automatically skips non-Python files and configured directories

## Examples

### Example 1: Django Project

```python
# Before
from django.views import View
import os
from .models import User
from django.conf import settings
import sys

# After
import os
import sys

from django.conf import settings
from django.views import View

from .models import User
```

### Example 2: Data Science Project

```python
# Before
import pandas as pd
import sys
import numpy as np
from myproject.utils import helper
import os

# After (with configuration)
import os
import sys

import numpy as np
import pandas as pd

from myproject.utils import helper
```

### Example 3: API Project

```python
# Before
from fastapi import FastAPI
from .database import get_db
import os
from typing import List
from pydantic import BaseModel

# After
import os
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from .database import get_db
```

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
