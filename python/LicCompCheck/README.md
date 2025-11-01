# LicCompCheck - License Compliance Checker

Check license compliance with policy.

## Usage
```python
from LicCompCheck import LicCompCheck
checker = LicCompCheck()
checker.set_policy(allowed=['MIT', 'Apache-2.0'])
result = checker.check_compliance()
```
