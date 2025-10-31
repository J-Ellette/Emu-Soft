#!/usr/bin/env python3
"""
Developed by PowerShield, as an alternative to freezegun

freezegun Emulator - Time Mocking

Emulates freezegun functionality for mocking datetime and time without external dependencies.
freezegun allows you to "freeze" time in your tests so that time-dependent code can be tested reliably.

Reference: https://github.com/spulec/freezegun
"""

import datetime
import time
import functools
from typing import Optional, Union
from contextlib import contextmanager


class FrozenTime:
    """Represents a frozen point in time."""
    
    def __init__(self, time_to_freeze: Union[str, datetime.datetime, datetime.date] = None):
        """
        Initialize frozen time.
        
        Args:
            time_to_freeze: The time to freeze at. Can be:
                - datetime object
                - date object
                - ISO format string (e.g., "2023-01-15 10:30:00")
                - None (uses current time)
        """
        self._frozen_time = self._parse_time(time_to_freeze)
        self._original_datetime = datetime.datetime
        self._original_date = datetime.date
        self._original_time_time = time.time
        self._original_time_monotonic = time.monotonic
        self._is_started = False
        self._time_offset = None
    
    def _parse_time(self, time_to_freeze) -> datetime.datetime:
        """Parse the input time to freeze."""
        if time_to_freeze is None:
            return datetime.datetime.now()
        elif isinstance(time_to_freeze, datetime.datetime):
            return time_to_freeze
        elif isinstance(time_to_freeze, datetime.date):
            return datetime.datetime.combine(time_to_freeze, datetime.time())
        elif isinstance(time_to_freeze, str):
            # Try to parse ISO format
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ]:
                try:
                    return datetime.datetime.strptime(time_to_freeze, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse time: {time_to_freeze}")
        else:
            raise TypeError(f"Unsupported type for time_to_freeze: {type(time_to_freeze)}")
    
    def start(self):
        """Start freezing time."""
        if self._is_started:
            return
        
        self._is_started = True
        
        # Calculate offset
        real_now = self._original_datetime.now()
        self._time_offset = (self._frozen_time - real_now).total_seconds()
        
        # Create frozen datetime class
        frozen_time_obj = self._frozen_time
        time_offset = self._time_offset
        original_datetime = self._original_datetime
        original_date = self._original_date
        
        class FrozenDatetime(datetime.datetime):
            """Frozen datetime that returns the frozen time."""
            
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return frozen_time_obj.replace(tzinfo=None)
                else:
                    # For timezone-aware datetime, apply the timezone
                    return frozen_time_obj.replace(tzinfo=tz)
            
            @classmethod
            def utcnow(cls):
                return frozen_time_obj.replace(tzinfo=None)
            
            @classmethod
            def today(cls):
                return frozen_time_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        
        class FrozenDate(datetime.date):
            """Frozen date that returns the frozen date."""
            
            @classmethod
            def today(cls):
                return frozen_time_obj.date()
        
        # Monkey-patch datetime module
        datetime.datetime = FrozenDatetime
        datetime.date = FrozenDate
        
        # Monkey-patch time module
        frozen_timestamp = frozen_time_obj.timestamp()
        original_time = self._original_time_time
        
        def frozen_time_time():
            """Return frozen timestamp."""
            return frozen_timestamp
        
        time.time = frozen_time_time
    
    def stop(self):
        """Stop freezing time and restore original functions."""
        if not self._is_started:
            return
        
        self._is_started = False
        
        # Restore original functions
        datetime.datetime = self._original_datetime
        datetime.date = self._original_date
        time.time = self._original_time_time
    
    def move_to(self, target_time: Union[str, datetime.datetime, datetime.date]):
        """Move the frozen time to a new point."""
        self._frozen_time = self._parse_time(target_time)
        if self._is_started:
            # Restart with new time
            self.stop()
            self.start()
    
    def tick(self, delta: Union[datetime.timedelta, int, float] = None):
        """
        Move time forward by a delta.
        
        Args:
            delta: Amount to move forward. Can be:
                - timedelta object
                - int/float (seconds)
                - None (moves forward by 1 second)
        """
        if delta is None:
            delta = datetime.timedelta(seconds=1)
        elif isinstance(delta, (int, float)):
            delta = datetime.timedelta(seconds=delta)
        elif not isinstance(delta, datetime.timedelta):
            raise TypeError(f"Unsupported type for delta: {type(delta)}")
        
        self._frozen_time += delta
        if self._is_started:
            # Restart with new time
            self.stop()
            self.start()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def freeze_time(time_to_freeze: Union[str, datetime.datetime, datetime.date] = None):
    """
    Freeze time at a specific point.
    
    Can be used as:
    - Context manager: with freeze_time("2023-01-15"):
    - Decorator: @freeze_time("2023-01-15")
    - Manual: freezer = freeze_time("2023-01-15"); freezer.start()
    
    Args:
        time_to_freeze: The time to freeze at
    
    Returns:
        FrozenTime instance
    """
    frozen_time_obj = FrozenTime(time_to_freeze)
    
    # If used as a decorator without arguments, time_to_freeze might be a function
    if callable(time_to_freeze):
        func = time_to_freeze
        frozen_time_obj = FrozenTime()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with frozen_time_obj:
                return func(*args, **kwargs)
        return wrapper
    
    return frozen_time_obj


def freeze_time_decorator(time_to_freeze: Union[str, datetime.datetime, datetime.date] = None):
    """
    Decorator version of freeze_time.
    
    Usage:
        @freeze_time_decorator("2023-01-15")
        def test_function():
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with freeze_time(time_to_freeze):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import datetime
    
    print("Testing freezegun emulator...")
    print()
    
    # Test 1: Basic freezing
    print("Test 1: Basic freezing")
    print(f"Current time: {datetime.datetime.now()}")
    
    with freeze_time("2023-01-15 10:30:00"):
        frozen_now = datetime.datetime.now()
        print(f"Frozen time: {frozen_now}")
        assert frozen_now.year == 2023
        assert frozen_now.month == 1
        assert frozen_now.day == 15
        assert frozen_now.hour == 10
        assert frozen_now.minute == 30
    
    print(f"After unfreezing: {datetime.datetime.now()}")
    print()
    
    # Test 2: Ticking time forward
    print("Test 2: Ticking time forward")
    with freeze_time("2023-01-15 10:00:00") as frozen_time:
        print(f"Start: {datetime.datetime.now()}")
        
        frozen_time.tick(delta=datetime.timedelta(hours=1))
        print(f"After 1 hour: {datetime.datetime.now()}")
        
        frozen_time.tick(delta=60)  # 60 seconds
        print(f"After 1 minute: {datetime.datetime.now()}")
        
        frozen_time.tick()  # 1 second by default
        print(f"After 1 second: {datetime.datetime.now()}")
    print()
    
    # Test 3: Moving to different times
    print("Test 3: Moving to different times")
    with freeze_time("2023-01-15") as frozen_time:
        print(f"Start: {datetime.datetime.now()}")
        
        frozen_time.move_to("2023-06-15")
        print(f"Moved to June: {datetime.datetime.now()}")
        
        frozen_time.move_to("2024-01-01 00:00:00")
        print(f"Moved to New Year: {datetime.datetime.now()}")
    print()
    
    # Test 4: Using as decorator
    print("Test 4: Using as decorator")
    
    @freeze_time_decorator("2023-12-25 00:00:00")
    def check_christmas():
        now = datetime.datetime.now()
        return now.month == 12 and now.day == 25
    
    result = check_christmas()
    print(f"Is it Christmas? {result}")
    assert result is True
    print()
    
    # Test 5: date.today()
    print("Test 5: date.today()")
    with freeze_time("2023-07-04"):
        today = datetime.date.today()
        print(f"Today: {today}")
        assert today.year == 2023
        assert today.month == 7
        assert today.day == 4
    print()
    
    # Test 6: time.time()
    print("Test 6: time.time()")
    import time
    with freeze_time("2023-01-01 00:00:00"):
        frozen_timestamp = time.time()
        print(f"Frozen timestamp: {frozen_timestamp}")
        expected_timestamp = datetime.datetime(2023, 1, 1).timestamp()
        print(f"Expected timestamp: {expected_timestamp}")
        assert abs(frozen_timestamp - expected_timestamp) < 1  # Within 1 second
    print()
    
    print("✓ All tests passed!")
    print("freezegun emulator working correctly!")
