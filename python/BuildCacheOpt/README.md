# BuildCacheOpt - Build Cache Optimizer

Optimize build cache usage.

## Usage
```python
from BuildCacheOpt import BuildCacheOpt
cache = BuildCacheOpt(max_size_mb=1000)
cache.add_entry('build1', 100)
cache.record_hit('build1')
to_remove = cache.optimize()
```
