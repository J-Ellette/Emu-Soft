# RealLoad - Realistic Load Pattern Generator

Generate realistic load patterns for testing.

## Usage
```python
from RealLoad import RealLoad
load = RealLoad()
load.add_pattern('peak_hours', 100, 60)
traffic = load.generate_traffic('peak_hours')
```
