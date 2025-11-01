# MultiRepRef - Multi-Repo Refactoring Coordinator

Coordinate refactoring tasks across multiple repositories.

## Usage
```python
from MultiRepRef import MultiRepRef
ref = MultiRepRef()
ref.add_task('repo1', 'file.py', 'rename function')
progress = ref.get_progress()
```
