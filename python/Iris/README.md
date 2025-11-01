# Iris - Threat modeling

Security tool for Python development.

## Description

Iris provides functionality to model threats.

## Usage

```python
from Iris import Iris

tool = Iris()
tool.process('item')
results = tool.get_results()
```

## Features

- Process items efficiently
- Track statistics
- Get results

## API Reference

- `__init__()` - Initialize tool
- `process(item)` - Process an item
- `get_results()` - Get processing results
- `get_statistics()` - Get statistics

## Testing

```bash
python test_Iris.py
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
