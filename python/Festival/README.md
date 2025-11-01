# Festival - MANIFEST.in handler

Manifest manager for Python development.

## Description

Festival provides functionality to include files in dist.

## Usage

```python
from Festival import Festival

tool = Festival()
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
python test_Festival.py
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
