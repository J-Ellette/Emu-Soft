# DataMig - Database Migration Rollback Safety Checker

Check if database migrations are safely reversible.

## Usage
```python
from DataMig import DataMig
mig = DataMig()
mig.add_migration('001', 'CREATE TABLE', 'DROP TABLE')
safety = mig.check_rollback_safety()
```
