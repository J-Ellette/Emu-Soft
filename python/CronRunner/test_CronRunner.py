"""
Tests for APScheduler emulator.
"""

import time
from datetime import datetime, timedelta
from CronRunner import BackgroundScheduler, Job, JobState, scheduled_job


# Test functions
execution_log = []


def simple_job(message):
    """Simple job that logs a message."""
    execution_log.append(message)
    return message


def counter_job():
    """Job that increments a counter."""
    if not hasattr(counter_job, 'count'):
        counter_job.count = 0
    counter_job.count += 1
    return counter_job.count


def test_scheduler_creation():
    """Test creating a scheduler."""
    scheduler = BackgroundScheduler()
    assert scheduler is not None
    assert not scheduler._running
    print("✓ Scheduler creation test passed")


def test_date_trigger():
    """Test date-based (one-time) job scheduling."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Schedule job to run immediately
    run_time = datetime.now() + timedelta(seconds=0.5)
    job = scheduler.add_job(
        simple_job,
        trigger='date',
        args=('one-time job',),
        run_date=run_time
    )

    time.sleep(1)
    scheduler.shutdown()

    assert 'one-time job' in execution_log
    assert job.run_count == 1
    print("✓ Date trigger test passed")


def test_interval_trigger():
    """Test interval-based job scheduling."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Schedule job to run every 0.5 seconds
    job = scheduler.add_job(
        simple_job,
        trigger='interval',
        args=('interval job',),
        seconds=0.5
    )

    time.sleep(2)
    scheduler.shutdown()

    # Should have run multiple times
    assert len(execution_log) >= 3
    assert 'interval job' in execution_log
    print("✓ Interval trigger test passed")


def test_job_management():
    """Test adding, getting, and removing jobs."""
    scheduler = BackgroundScheduler()

    job1 = scheduler.add_job(simple_job, trigger='date', args=('job1',), id='job-1')
    job2 = scheduler.add_job(simple_job, trigger='date', args=('job2',), id='job-2')

    # Get job by ID
    fetched = scheduler.get_job('job-1')
    assert fetched is not None
    assert fetched.id == 'job-1'

    # Get all jobs
    jobs = scheduler.get_jobs()
    assert len(jobs) == 2

    # Remove job
    scheduler.remove_job('job-1')
    assert scheduler.get_job('job-1') is None
    assert len(scheduler.get_jobs()) == 1

    print("✓ Job management test passed")


def test_pause_resume():
    """Test pausing and resuming jobs."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    job = scheduler.add_job(
        simple_job,
        trigger='interval',
        args=('pausable job',),
        seconds=0.5,
        id='pausable'
    )

    time.sleep(1)

    # Pause job
    scheduler.pause_job('pausable')
    count_before_pause = len(execution_log)

    time.sleep(1)
    count_after_pause = len(execution_log)

    # Should not have executed while paused
    assert count_after_pause == count_before_pause

    # Resume job
    scheduler.resume_job('pausable')
    time.sleep(1)

    # Should execute again after resume
    assert len(execution_log) > count_after_pause

    scheduler.shutdown()
    print("✓ Pause/resume test passed")


def test_multiple_jobs():
    """Test running multiple jobs simultaneously."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    scheduler.add_job(simple_job, trigger='interval', args=('job-a',), seconds=0.5)
    scheduler.add_job(simple_job, trigger='interval', args=('job-b',), seconds=0.5)
    scheduler.add_job(simple_job, trigger='interval', args=('job-c',), seconds=0.5)

    time.sleep(2)
    scheduler.shutdown()

    # All jobs should have executed
    assert 'job-a' in execution_log
    assert 'job-b' in execution_log
    assert 'job-c' in execution_log
    print("✓ Multiple jobs test passed")


def test_job_with_kwargs():
    """Test jobs with keyword arguments."""
    global execution_log
    execution_log = []

    def job_with_kwargs(msg, prefix="INFO"):
        execution_log.append(f"{prefix}: {msg}")

    scheduler = BackgroundScheduler()
    scheduler.start()

    scheduler.add_job(
        job_with_kwargs,
        trigger='date',
        kwargs={'msg': 'test message', 'prefix': 'DEBUG'}
    )

    time.sleep(0.5)
    scheduler.shutdown()

    assert 'DEBUG: test message' in execution_log
    print("✓ Job with kwargs test passed")


def test_cron_trigger():
    """Test cron-like scheduling."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Schedule to run at a specific minute (next occurrence)
    now = datetime.now()
    next_minute = (now.minute + 1) % 60

    job = scheduler.add_job(
        simple_job,
        trigger='cron',
        args=('cron job',),
        minute=next_minute,
        second=0
    )

    # Wait a bit to see if it gets scheduled properly
    time.sleep(1)
    scheduler.shutdown()

    # Job should be scheduled for future
    assert job.next_run_time is not None
    print("✓ Cron trigger test passed")


def test_job_execution_count():
    """Test tracking job execution count."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    job = scheduler.add_job(
        counter_job,
        trigger='interval',
        seconds=0.3,
        id='counter'
    )

    time.sleep(1.5)
    scheduler.shutdown()

    # Job should have run multiple times
    assert job.run_count >= 4
    print("✓ Job execution count test passed")


def test_scheduler_decorator():
    """Test decorator-based job scheduling."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()

    @scheduled_job(scheduler, 'interval', seconds=0.5)
    def decorated_job():
        execution_log.append('decorated')

    scheduler.start()
    time.sleep(1.5)
    scheduler.shutdown()

    assert 'decorated' in execution_log
    print("✓ Scheduler decorator test passed")


def test_job_state_transitions():
    """Test job state transitions."""
    scheduler = BackgroundScheduler()

    job = scheduler.add_job(simple_job, trigger='date', args=('state test',))

    # Initially pending
    assert job.state == JobState.PENDING

    # Pause
    scheduler.pause_job(job.id)
    assert job.state == JobState.PAUSED

    # Resume
    scheduler.resume_job(job.id)
    assert job.state == JobState.PENDING

    # Remove
    scheduler.remove_job(job.id)
    assert scheduler.get_job(job.id) is None

    print("✓ Job state transitions test passed")


def test_interval_with_different_units():
    """Test interval trigger with different time units."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Test with seconds
    job1 = scheduler.add_job(
        simple_job,
        trigger='interval',
        args=('seconds',),
        seconds=1
    )

    # Test with minutes (use fractional for testing)
    job2 = scheduler.add_job(
        simple_job,
        trigger='interval',
        args=('minutes',),
        minutes=0.01  # 0.6 seconds
    )

    time.sleep(2)
    scheduler.shutdown()

    assert 'seconds' in execution_log
    assert 'minutes' in execution_log
    print("✓ Interval with different units test passed")


def test_start_date_interval():
    """Test interval trigger with start date."""
    global execution_log
    execution_log = []

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Start in the future
    start_time = datetime.now() + timedelta(seconds=0.5)
    job = scheduler.add_job(
        simple_job,
        trigger='interval',
        args=('delayed start',),
        seconds=0.5,
        start_date=start_time
    )

    # Check immediately - should not have run yet
    time.sleep(0.3)
    count_early = len(execution_log)

    # Wait for start time
    time.sleep(1)

    scheduler.shutdown()

    # Should have run after start time
    assert len(execution_log) > count_early
    print("✓ Start date interval test passed")


def test_named_jobs():
    """Test jobs with custom names."""
    scheduler = BackgroundScheduler()

    job = scheduler.add_job(
        simple_job,
        trigger='date',
        args=('named',),
        name='My Custom Job'
    )

    assert job.name == 'My Custom Job'
    print("✓ Named jobs test passed")


if __name__ == "__main__":
    print("Running APScheduler Emulator Tests...\n")

    test_scheduler_creation()
    test_date_trigger()
    test_interval_trigger()
    test_job_management()
    test_pause_resume()
    test_multiple_jobs()
    test_job_with_kwargs()
    test_cron_trigger()
    test_job_execution_count()
    test_scheduler_decorator()
    test_job_state_transitions()
    test_interval_with_different_units()
    test_start_date_interval()
    test_named_jobs()

    print("\n✅ All APScheduler Emulator tests passed!")
