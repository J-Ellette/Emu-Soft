# PyYAML Emulator - YAML Parser and Emitter

This module emulates the **PyYAML** library, which provides YAML parsing and emission capabilities for Python.

## What is PyYAML?

PyYAML is a YAML parser and emitter for Python. YAML (YAML Ain't Markup Language) is a human-friendly data serialization format commonly used for:
- Configuration files
- Data exchange between languages
- Application settings
- CI/CD pipelines (GitHub Actions, GitLab CI, etc.)
- Docker Compose files
- Kubernetes manifests

## Features

This emulator implements core PyYAML functionality:

### Parsing (Loading)
- **Scalars** - strings, integers, floats, booleans, null
- **Mappings** - dictionaries with key-value pairs
- **Sequences** - lists/arrays
- **Nested structures** - deeply nested combinations
- **Inline flow style** - `{key: value}` and `[item1, item2]`
- **Comments** - full line and inline comments
- **Multi-line strings** - quoted strings with escapes

### Emitting (Dumping)
- Convert Python objects to YAML format
- Proper indentation and formatting
- Automatic quoting when needed
- Nested structure support
- List and dictionary emission

### Functions
- `load(stream)` - Parse YAML from string or file
- `safe_load(stream)` - Safely parse YAML (alias for load)
- `dump(data, stream=None)` - Serialize to YAML
- `safe_dump(data, stream=None)` - Safely serialize (alias for dump)

## Usage Examples

### Loading YAML

```python
from pyyaml_emulator import load

# Simple mapping
yaml = """
name: Alice
age: 30
active: true
"""
data = load(yaml)
print(data)
# {'name': 'Alice', 'age': 30, 'active': True}

# List
yaml = """
- apple
- banana
- cherry
"""
data = load(yaml)
print(data)
# ['apple', 'banana', 'cherry']
```

### Nested Structures

```python
yaml = """
user:
  name: Alice
  email: alice@example.com
  roles:
    - admin
    - developer
"""
data = load(yaml)
print(data)
# {
#     'user': {
#         'name': 'Alice',
#         'email': 'alice@example.com',
#         'roles': ['admin', 'developer']
#     }
# }
```

### List of Mappings

```python
yaml = """
users:
  - name: Alice
    email: alice@example.com
    age: 30
  - name: Bob
    email: bob@example.com
    age: 25
"""
data = load(yaml)
print(data['users'])
# [
#     {'name': 'Alice', 'email': 'alice@example.com', 'age': 30},
#     {'name': 'Bob', 'email': 'bob@example.com', 'age': 25}
# ]
```

### Inline/Flow Style

```python
# Inline list
yaml = "colors: [red, green, blue]"
data = load(yaml)
# {'colors': ['red', 'green', 'blue']}

# Inline mapping
yaml = "person: {name: Alice, age: 30}"
data = load(yaml)
# {'person': {'name': 'Alice', 'age': 30}}
```

### Comments

```python
yaml = """
# Application configuration
name: MyApp  # Application name
version: 1.0  # Current version

# Database settings
database:
  host: localhost
  port: 5432
"""
data = load(yaml)
# {'name': 'MyApp', 'version': 1.0, 'database': {'host': 'localhost', 'port': 5432}}
```

### Dumping YAML

```python
from pyyaml_emulator import dump

# Simple dump
data = {
    'name': 'Alice',
    'age': 30,
    'active': True
}
yaml = dump(data)
print(yaml)
# name: Alice
# age: 30
# active: true

# Nested structures
data = {
    'user': {
        'name': 'Alice',
        'roles': ['admin', 'developer']
    }
}
yaml = dump(data)
print(yaml)
# user:
#   name: Alice
#   roles:
#     - admin
#     - developer
```

### File I/O

```python
from pyyaml_emulator import load, dump
from io import StringIO

# Load from file-like object
yaml_str = "name: Alice\nage: 30"
stream = StringIO(yaml_str)
data = load(stream)

# Dump to file-like object
output = StringIO()
dump(data, output)
result = output.getvalue()
```

### Safe Functions

```python
from pyyaml_emulator import safe_load, safe_dump

# Safe load (alias for load in this implementation)
data = safe_load("name: Alice")

# Safe dump (alias for dump in this implementation)
yaml = safe_dump({'name': 'Alice'})
```

### Configuration File Example

```python
# config.yaml
yaml_config = """
application:
  name: MyWebApp
  version: 1.0.0
  debug: false

database:
  host: localhost
  port: 5432
  name: mydb
  credentials:
    username: admin
    password: secret123

features:
  - authentication
  - logging
  - caching

limits:
  max_connections: 100
  timeout: 30
"""

config = load(yaml_config)

# Access configuration
print(config['application']['name'])  # MyWebApp
print(config['database']['port'])  # 5432
print(config['features'])  # ['authentication', 'logging', 'caching']
```

### Docker Compose Example

```python
yaml_compose = """
version: '3.8'

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    environment:
      - ENV=production
    volumes:
      - ./html:/usr/share/nginx/html

  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: mydb
"""

compose = load(yaml_compose)
print(compose['services']['web']['ports'])
# ['80:80', '443:443']
```

### GitHub Actions Example

```python
yaml_workflow = """
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
"""

workflow = load(yaml_workflow)
print(workflow['jobs']['build']['runs-on'])
# ubuntu-latest
```

## Type Conversions

The emulator automatically converts between YAML and Python types:

| YAML | Python |
|------|--------|
| string | str |
| integer | int |
| float | float |
| true/false | bool |
| null/~ | None |
| mapping | dict |
| sequence | list |

## Testing

Run the comprehensive test suite:

```bash
python test_pyyaml_emulator.py
```

Tests cover:
- Scalar parsing (strings, numbers, booleans, null)
- Mapping/dictionary parsing
- List/sequence parsing
- Complex nested structures
- Comment handling
- Inline/flow style
- YAML dumping
- Round-trip conversions
- File I/O
- Edge cases

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for PyYAML:

```python
# Instead of:
# import yaml
# data = yaml.load(stream)
# yaml.dump(data)

# Use:
from pyyaml_emulator import load, dump
data = load(stream)
dump(data)
```

## Use Cases

Perfect for:
- **Configuration Management**: Parse and generate config files
- **CI/CD**: Parse workflow definitions
- **Infrastructure as Code**: Read Kubernetes, Docker Compose files
- **Testing**: Test YAML parsing without external dependencies
- **Data Serialization**: Exchange data between systems
- **Documentation**: Generate YAML documentation

## Supported YAML Features

- ✅ Scalars (strings, numbers, booleans, null)
- ✅ Mappings (key-value pairs)
- ✅ Sequences (lists)
- ✅ Nested structures
- ✅ Inline/flow style
- ✅ Comments
- ✅ Quoted strings
- ✅ Multi-line values
- ✅ Custom indentation

## Limitations

This emulator implements the most commonly used YAML features. Some advanced features not included:
- Anchors and aliases (`&anchor`, `*alias`)
- Multi-document streams (`---`)
- Complex keys
- Block scalars (`|`, `>`)
- Tags and custom types
- Binary data

For most configuration and data serialization use cases, the implemented features provide comprehensive YAML support.

## Compatibility

Emulates core features of:
- PyYAML 5.x/6.x API
- Common YAML 1.2 constructs
- Standard load/dump interface

## License

Part of the Emu-Soft project. See main repository LICENSE.
