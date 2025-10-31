#!/usr/bin/env python3
"""
Tests for freezegun emulator
"""

import sys
import datetime
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from freezegun_emulator_tool.freezegun_emulator import freeze_time, freeze_time_decorator


def test_basic_freezing():
    """Test basic time freezing."""
    print("Testing basic freezing...")
    
    with freeze_time("2023-01-15 10:30:00"):
        now = datetime.datetime.now()
        assert now.year == 2023
        assert now.month == 1
        assert now.day == 15
        assert now.hour == 10
        assert now.minute == 30
        assert now.second == 0
    
    # After context, time should be unfrozen
    now = datetime.datetime.now()
    assert now.year >= 2023
    
    print("  ✓ Basic freezing works")


def test_freeze_datetime_object():
    """Test freezing with datetime object."""
    print("Testing freeze with datetime object...")
    
    target = datetime.datetime(2024, 3, 15, 14, 30, 45)
    with freeze_time(target):
        now = datetime.datetime.now()
        assert now == target
    
    print("  ✓ Freezing with datetime object works")


def test_freeze_date_object():
    """Test freezing with date object."""
    print("Testing freeze with date object...")
    
    target = datetime.date(2024, 6, 1)
    with freeze_time(target):
        now = datetime.datetime.now()
        assert now.year == 2024
        assert now.month == 6
        assert now.day == 1
        assert now.hour == 0
        assert now.minute == 0
    
    print("  ✓ Freezing with date object works")


def test_date_today():
    """Test date.today() freezing."""
    print("Testing date.today()...")
    
    with freeze_time("2023-07-04"):
        today = datetime.date.today()
        assert today.year == 2023
        assert today.month == 7
        assert today.day == 4
    
    print("  ✓ date.today() freezing works")


def test_datetime_today():
    """Test datetime.today() freezing."""
    print("Testing datetime.today()...")
    
    with freeze_time("2023-12-25 15:30:00"):
        today = datetime.datetime.today()
        assert today.year == 2023
        assert today.month == 12
        assert today.day == 25
        # today() returns midnight
        assert today.hour == 0
        assert today.minute == 0
    
    print("  ✓ datetime.today() freezing works")


def test_datetime_utcnow():
    """Test datetime.utcnow() freezing."""
    print("Testing datetime.utcnow()...")
    
    with freeze_time("2023-01-01 00:00:00"):
        utcnow = datetime.datetime.utcnow()
        assert utcnow.year == 2023
        assert utcnow.month == 1
        assert utcnow.day == 1
    
    print("  ✓ datetime.utcnow() freezing works")


def test_time_time():
    """Test time.time() freezing."""
    print("Testing time.time()...")
    
    target = datetime.datetime(2023, 1, 1, 0, 0, 0)
    with freeze_time(target):
        frozen_timestamp = time.time()
        expected_timestamp = target.timestamp()
        # Should be very close (within 1 second due to conversion)
        assert abs(frozen_timestamp - expected_timestamp) < 1
    
    print("  ✓ time.time() freezing works")


def test_tick_timedelta():
    """Test ticking time forward with timedelta."""
    print("Testing tick with timedelta...")
    
    with freeze_time("2023-01-15 10:00:00") as frozen:
        start = datetime.datetime.now()
        assert start.hour == 10
        assert start.minute == 0
        
        frozen.tick(delta=datetime.timedelta(hours=2, minutes=30))
        now = datetime.datetime.now()
        assert now.hour == 12
        assert now.minute == 30
    
    print("  ✓ Tick with timedelta works")


def test_tick_seconds():
    """Test ticking time forward with seconds."""
    print("Testing tick with seconds...")
    
    with freeze_time("2023-01-15 10:00:00") as frozen:
        start = datetime.datetime.now()
        
        frozen.tick(delta=3600)  # 1 hour in seconds
        now = datetime.datetime.now()
        assert now.hour == 11
        
        frozen.tick(delta=60)  # 1 minute
        now = datetime.datetime.now()
        assert now.minute == 1
    
    print("  ✓ Tick with seconds works")


def test_tick_default():
    """Test ticking time forward with default (1 second)."""
    print("Testing tick with default...")
    
    with freeze_time("2023-01-15 10:00:00") as frozen:
        start = datetime.datetime.now()
        assert start.second == 0
        
        frozen.tick()  # Default: 1 second
        now = datetime.datetime.now()
        assert now.second == 1
        
        frozen.tick()
        now = datetime.datetime.now()
        assert now.second == 2
    
    print("  ✓ Tick with default works")


def test_move_to():
    """Test moving to different times."""
    print("Testing move_to...")
    
    with freeze_time("2023-01-15 10:00:00") as frozen:
        start = datetime.datetime.now()
        assert start.month == 1
        
        frozen.move_to("2023-06-15 14:30:00")
        now = datetime.datetime.now()
        assert now.month == 6
        assert now.day == 15
        assert now.hour == 14
        assert now.minute == 30
        
        frozen.move_to(datetime.date(2024, 1, 1))
        now = datetime.datetime.now()
        assert now.year == 2024
        assert now.month == 1
        assert now.day == 1
    
    print("  ✓ move_to works")


def test_decorator():
    """Test freeze_time as decorator."""
    print("Testing decorator...")
    
    @freeze_time_decorator("2023-12-25 00:00:00")
    def check_time():
        now = datetime.datetime.now()
        return now.year, now.month, now.day
    
    year, month, day = check_time()
    assert year == 2023
    assert month == 12
    assert day == 25
    
    # After function returns, time should be unfrozen
    now = datetime.datetime.now()
    assert now.year >= 2023
    
    print("  ✓ Decorator works")


def test_manual_start_stop():
    """Test manual start/stop."""
    print("Testing manual start/stop...")
    
    frozen = freeze_time("2023-01-15 10:00:00")
    
    # Not started yet
    now_before = datetime.datetime.now()
    assert now_before.year >= 2023
    
    # Start freezing
    frozen.start()
    now_frozen = datetime.datetime.now()
    assert now_frozen.year == 2023
    assert now_frozen.month == 1
    assert now_frozen.day == 15
    
    # Stop freezing
    frozen.stop()
    now_after = datetime.datetime.now()
    assert now_after.year >= 2023
    
    print("  ✓ Manual start/stop works")


def test_nested_freezing():
    """Test nested freeze_time contexts."""
    print("Testing nested freezing...")
    
    with freeze_time("2023-01-15"):
        outer = datetime.datetime.now()
        assert outer.month == 1
        assert outer.day == 15
        
        with freeze_time("2023-06-20"):
            inner = datetime.datetime.now()
            assert inner.month == 6
            assert inner.day == 20
        
        # Back to outer context
        back = datetime.datetime.now()
        assert back.month == 1
        assert back.day == 15
    
    print("  ✓ Nested freezing works")


def test_multiple_now_calls():
    """Test that multiple calls to now() return same time."""
    print("Testing multiple now() calls...")
    
    with freeze_time("2023-01-15 10:30:45"):
        now1 = datetime.datetime.now()
        now2 = datetime.datetime.now()
        now3 = datetime.datetime.now()
        
        assert now1 == now2
        assert now2 == now3
    
    print("  ✓ Multiple now() calls return same time")


def test_iso_format_parsing():
    """Test various ISO format strings."""
    print("Testing ISO format parsing...")
    
    # Date only
    with freeze_time("2023-01-15"):
        now = datetime.datetime.now()
        assert now.year == 2023
        assert now.month == 1
        assert now.day == 15
    
    # Date and time (space)
    with freeze_time("2023-01-15 14:30:00"):
        now = datetime.datetime.now()
        assert now.hour == 14
        assert now.minute == 30
    
    # Date and time (T separator)
    with freeze_time("2023-01-15T14:30:00"):
        now = datetime.datetime.now()
        assert now.hour == 14
        assert now.minute == 30
    
    print("  ✓ ISO format parsing works")


def test_time_dependent_code():
    """Test with time-dependent code."""
    print("Testing time-dependent code...")
    
    def is_business_hours():
        """Check if current time is during business hours (9-17)."""
        now = datetime.datetime.now()
        return 9 <= now.hour < 17
    
    # Morning - should be business hours
    with freeze_time("2023-01-15 10:00:00"):
        assert is_business_hours() is True
    
    # Evening - should not be business hours
    with freeze_time("2023-01-15 20:00:00"):
        assert is_business_hours() is False
    
    # Early morning - should not be business hours
    with freeze_time("2023-01-15 06:00:00"):
        assert is_business_hours() is False
    
    print("  ✓ Time-dependent code works")


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing freezegun Emulator")
    print("=" * 60)
    
    tests = [
        test_basic_freezing,
        test_freeze_datetime_object,
        test_freeze_date_object,
        test_date_today,
        test_datetime_today,
        test_datetime_utcnow,
        test_time_time,
        test_tick_timedelta,
        test_tick_seconds,
        test_tick_default,
        test_move_to,
        test_decorator,
        test_manual_start_stop,
        test_nested_freezing,
        test_multiple_now_calls,
        test_iso_format_parsing,
        test_time_dependent_code,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            raise
        except Exception as e:
            print(f"  ✗ {test.__name__} error: {e}")
            raise
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
