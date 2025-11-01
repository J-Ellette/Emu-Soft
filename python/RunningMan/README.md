# RunningMan - Runtime monitor

Performance monitor for Python development.

## Description

RunningMan provides functionality to track metrics.

## Usage

```python
from RunningMan import RunningMan

tool = RunningMan()
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
python test_RunningMan.py
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
