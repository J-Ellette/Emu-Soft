# AutoGenAPI - Auto-generate API Documentation

Auto-generate API documentation from actual traffic patterns.

## Usage

```python
from AutoGenAPI import AutoGenAPI

api = AutoGenAPI()
api.record_request('GET', '/users', response_body={'users': []})
docs = api.generate_markdown()
```

## License

Part of the Emu-Soft project.
