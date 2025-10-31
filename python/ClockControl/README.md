# freezegun Emulator

A pure Python implementation that emulates freezegun functionality for mocking time without external dependencies.

## What This Emulates

**Emulates:** freezegun (Time mocking library)
**Original:** https://github.com/spulec/freezegun

## Overview

This module allows you to "freeze" time in your tests, making time-dependent code deterministic and testable. Instead of relying on the current time (which changes every test run), you can set a specific point in time and optionally move forward through time in controlled increments.

## Features

- **Time Freezing**
  - Freeze `datetime.datetime.now()`
  - Freeze `datetime.date.today()`
  - Freeze `datetime.datetime.utcnow()`
  - Freeze `time.time()`

- **Time Manipulation**
  - Move to different times
  - Tick time forward by seconds or timedeltas
  - Jump to any point in time

- **Flexible Usage**
  - Context manager
  - Decorator
  - Manual start/stop

- **Time Formats**
  - ISO format strings
  - datetime objects
  - date objects

## Usage

### Basic Time Freezing

```python
from freezegun_emulator_tool.freezegun_emulator import freeze_time
import datetime

# Freeze time to a specific date
with freeze_time("2023-01-15 10:30:00"):
    now = datetime.datetime.now()
    print(now)  # 2023-01-15 10:30:00
    
    # Multiple calls return the same time
    later = datetime.datetime.now()
    assert now == later
```

### Using as Decorator

```python
from freezegun_emulator_tool.freezegun_emulator import freeze_time_decorator
import datetime

@freeze_time_decorator("2023-12-25 00:00:00")
def test_christmas_greeting():
    now = datetime.datetime.now()
    if now.month == 12 and now.day == 25:
        return "Merry Christmas!"
    return "Hello!"

result = test_christmas_greeting()
print(result)  # "Merry Christmas!"
```

### Moving Through Time

```python
with freeze_time("2023-01-01 00:00:00") as frozen:
    print(datetime.datetime.now())  # 2023-01-01 00:00:00
    
    # Jump to a different time
    frozen.move_to("2023-06-15 14:30:00")
    print(datetime.datetime.now())  # 2023-06-15 14:30:00
    
    # Move to a date
    frozen.move_to(datetime.date(2024, 1, 1))
    print(datetime.datetime.now())  # 2024-01-01 00:00:00
```

### Ticking Time Forward

```python
with freeze_time("2023-01-15 10:00:00") as frozen:
    print(datetime.datetime.now())  # 2023-01-15 10:00:00
    
    # Tick forward by 1 second (default)
    frozen.tick()
    print(datetime.datetime.now())  # 2023-01-15 10:00:01
    
    # Tick forward by seconds
    frozen.tick(delta=60)
    print(datetime.datetime.now())  # 2023-01-15 10:01:01
    
    # Tick forward by timedelta
    frozen.tick(delta=datetime.timedelta(hours=2, minutes=30))
    print(datetime.datetime.now())  # 2023-01-15 12:31:01
```

### Freezing date.today()

```python
with freeze_time("2023-07-04"):
    today = datetime.date.today()
    print(today)  # 2023-07-04
```

### Freezing time.time()

```python
import time

with freeze_time("2023-01-01 00:00:00"):
    timestamp = time.time()
    print(timestamp)  # Unix timestamp for 2023-01-01
```

### Manual Start/Stop

```python
frozen = freeze_time("2023-01-15 10:00:00")

# Start freezing
frozen.start()
print(datetime.datetime.now())  # 2023-01-15 10:00:00

# Do something...

# Stop freezing
frozen.stop()
print(datetime.datetime.now())  # Current real time
```

### Different Time Formats

```python
# ISO format string (date only)
with freeze_time("2023-01-15"):
    print(datetime.datetime.now())  # 2023-01-15 00:00:00

# ISO format string (date and time with space)
with freeze_time("2023-01-15 14:30:00"):
    print(datetime.datetime.now())  # 2023-01-15 14:30:00

# ISO format string (date and time with T)
with freeze_time("2023-01-15T14:30:00"):
    print(datetime.datetime.now())  # 2023-01-15 14:30:00

# datetime object
target = datetime.datetime(2024, 3, 15, 10, 30)
with freeze_time(target):
    print(datetime.datetime.now())  # 2024-03-15 10:30:00

# date object
target = datetime.date(2024, 6, 1)
with freeze_time(target):
    print(datetime.datetime.now())  # 2024-06-01 00:00:00
```

## Common Use Cases

### Testing Time-Dependent Logic

```python
from freezegun_emulator_tool.freezegun_emulator import freeze_time_decorator
import datetime

def is_weekend():
    """Check if today is a weekend."""
    today = datetime.date.today()
    return today.weekday() >= 5  # Saturday=5, Sunday=6

@freeze_time_decorator("2023-01-14")  # Saturday
def test_weekend():
    assert is_weekend() is True

@freeze_time_decorator("2023-01-16")  # Monday
def test_weekday():
    assert is_weekend() is False

test_weekend()
test_weekday()
```

### Testing Expiration Logic

```python
def is_expired(created_at, lifetime_days=30):
    """Check if something has expired."""
    expiry = created_at + datetime.timedelta(days=lifetime_days)
    return datetime.datetime.now() > expiry

# Test not expired
with freeze_time("2023-01-15"):
    created = datetime.datetime.now()

with freeze_time("2023-01-20"):  # 5 days later
    assert is_expired(created, lifetime_days=30) is False

# Test expired
with freeze_time("2023-02-20"):  # 36 days later
    assert is_expired(created, lifetime_days=30) is True
```

### Testing Scheduled Tasks

```python
def should_run_task():
    """Task should run at 3 AM every day."""
    now = datetime.datetime.now()
    return now.hour == 3

# Test at 3 AM - should run
with freeze_time("2023-01-15 03:00:00"):
    assert should_run_task() is True

# Test at other times - should not run
with freeze_time("2023-01-15 10:00:00"):
    assert should_run_task() is False
```

### Testing Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def allow_request(self):
        now = time.time()
        # Remove old requests outside the window
        cutoff = now - self.window_seconds
        self.requests = [r for r in self.requests if r > cutoff]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

with freeze_time("2023-01-15 10:00:00") as frozen:
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # First 3 requests succeed
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    
    # 4th request fails (rate limited)
    assert limiter.allow_request() is False
    
    # Tick forward 61 seconds (past the window)
    frozen.tick(delta=61)
    
    # New requests succeed
    assert limiter.allow_request() is True
```

### Testing Business Hours

```python
def is_business_hours():
    """Check if current time is during business hours (9 AM - 5 PM)."""
    now = datetime.datetime.now()
    return 9 <= now.hour < 17 and now.weekday() < 5

# Test during business hours
with freeze_time("2023-01-16 10:00:00"):  # Monday 10 AM
    assert is_business_hours() is True

# Test after hours
with freeze_time("2023-01-16 18:00:00"):  # Monday 6 PM
    assert is_business_hours() is False

# Test weekend
with freeze_time("2023-01-14 10:00:00"):  # Saturday 10 AM
    assert is_business_hours() is False
```

### Testing Retry Logic with Timeouts

```python
def retry_with_timeout(func, timeout_seconds=5, retry_delay=1):
    """Retry a function until it succeeds or timeout."""
    import time
    start_time = time.time()
    
    while True:
        try:
            return func()
        except Exception:
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError("Operation timed out")
            time.sleep(retry_delay)

# Mock a function that fails 3 times then succeeds
attempt_count = 0

def flaky_function():
    global attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise ValueError("Not ready yet")
    return "success"

with freeze_time("2023-01-15 10:00:00") as frozen:
    attempt_count = 0
    
    # In a real test, you'd mock time.sleep or use tick()
    result = retry_with_timeout(flaky_function, timeout_seconds=10)
    assert result == "success"
```

## Implementation Details

### Pure Python Implementation

This emulator is implemented using only Python standard library:
- No external dependencies required
- Monkey-patches `datetime` and `time` modules
- Properly restores original functions on exit

### What Gets Frozen

- `datetime.datetime.now()`
- `datetime.datetime.utcnow()`
- `datetime.datetime.today()`
- `datetime.date.today()`
- `time.time()`

### Differences from freezegun

This is a simplified emulator. Some features are not implemented:
- No `time.monotonic()` freezing
- No timezone-aware datetime full support
- No `time.sleep()` auto-tick
- No ignore lists
- No tick on method call
- Simplified nested context handling

For production use cases requiring these features, use the official freezegun library.

## Testing

Run the included tests:

```bash
python freezegun_emulator_tool/test_freezegun_emulator.py
```

## Best Practices

### Always Use Context Managers or Decorators

```python
# Good - automatic cleanup
with freeze_time("2023-01-15"):
    do_something()

# Avoid - manual cleanup required
frozen = freeze_time("2023-01-15")
frozen.start()
do_something()
frozen.stop()  # Easy to forget!
```

### Test Both Sides of Time Boundaries

```python
# Test just before midnight
with freeze_time("2023-01-15 23:59:59"):
    assert datetime.date.today() == datetime.date(2023, 1, 15)

# Test just after midnight
with freeze_time("2023-01-16 00:00:00"):
    assert datetime.date.today() == datetime.date(2023, 1, 16)
```

### Use Descriptive Times

```python
# Good - clear what's being tested
with freeze_time("2023-01-14"):  # Saturday
    assert is_weekend() is True

# Avoid - unclear without checking calendar
with freeze_time("2023-01-15"):
    assert is_weekend() is False
```

## License

See LICENSE file in the repository root.
