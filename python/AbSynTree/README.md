# AbSynTree - AST parser

Code analyzer for Python development.

## Description

AbSynTree provides functionality to parse AST.

## Usage

```python
from AbSynTree import AbSynTree

tool = AbSynTree()
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
python test_AbSynTree.py
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
