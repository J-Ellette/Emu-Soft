# Chaos - Chaos Engineering Scenarios

Chaos engineering for local testing.

## Usage
```python
from Chaos import Chaos
chaos = Chaos()
chaos.add_scenario('network_delay', 'Add delay', lambda: time.sleep(1))
chaos.enable()
chaos.inject_chaos('network_delay')
```
