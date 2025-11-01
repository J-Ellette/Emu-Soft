# APICon - API Contract Testing

Test API contracts between services.

## Usage
```python
from APICon import APICon
api = APICon()
api.add_contract('/users', 'POST', {'required': ['name']}, {})
valid = api.validate_request('/users', 'POST', {'name': 'John'})
```
