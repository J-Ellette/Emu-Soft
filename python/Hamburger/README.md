# Hamburger - HMAC generator

Signature creator for Python development.

## Description

Hamburger provides functionality to sign data.

## Usage

```python
from Hamburger import Hamburger

tool = Hamburger()
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
python test_Hamburger.py
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
