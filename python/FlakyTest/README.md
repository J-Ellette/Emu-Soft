# FlakyTest - Flaky Test Detector

Detect flaky tests with root cause analysis.

## Usage
```python
from FlakyTest import FlakyTest
detector = FlakyTest()
detector.record_result('test1', True, 1)
detector.record_result('test1', False, 2)
flaky = detector.detect_flaky()
```
