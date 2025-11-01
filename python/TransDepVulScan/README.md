# TransDepVulScan - Transitive Dependency Vulnerability Scanner

Scan for vulnerabilities in transitive dependencies.

## Usage
```python
from TransDepVulScan import TransDepVulScan
scanner = TransDepVulScan()
scanner.add_dependency('myapp', ['requests'])
vulns = scanner.scan('myapp')
```
