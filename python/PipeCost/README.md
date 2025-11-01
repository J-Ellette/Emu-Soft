# PipeCost - Pipeline Cost Analyzer

Analyze CI/CD pipeline costs.

## Usage
```python
from PipeCost import PipeCost
cost = PipeCost()
cost.add_run('build', 10, 0.5)  # 10 min at $0.5/min
total = cost.get_total_cost()
```
