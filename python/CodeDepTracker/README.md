# CodeDepTracker - Code Deprecation Tracker

Track usage of deprecated APIs in codebase.

## Usage
```python
from CodeDepTracker import CodeDepTracker
tracker = CodeDepTracker()
tracker.mark_deprecated('old_func', '1.0', 'new_func')
tracker.record_usage('old_func', 'file.py:10')
```
