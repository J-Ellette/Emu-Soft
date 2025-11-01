"""
Developed by PowerShield, as an alternative to RQ
"""

"""
Tests for RQ (Redis Queue) emulator.
"""

import time
from datetime import timedelta
from SimpleQueue import Job, Queue, Worker, JobStatus


# Test functions
def simple_job(x, y):
    """Simple job that adds two numbers."""
    return x + y


def slow_job(duration):
    """Job that takes some time to complete."""
    time.sleep(duration)
    return f"Completed after {duration}s"


def failing_job():
    """Job that always fails."""
    raise ValueError("This job always fails")


def test_job_creation():
    """Test creating a job."""
    job = Job(simple_job, args=(1, 2))
    assert job.func == simple_job
    assert job.args == (1, 2)
    assert job.status == JobStatus.QUEUED
    assert job.is_queued()
    print("✓ Job creation test passed")


def test_queue_enqueue():
    """Test enqueueing jobs."""
    queue = Queue("test")
    job = queue.enqueue(simple_job, 5, 10)

    assert job.id is not None
    assert job.func == simple_job
    assert job.args == (5, 10)
    assert queue.count() == 1
    print("✓ Queue enqueue test passed")


def test_worker_execution():
    """Test worker executing jobs."""
    queue = Queue("test")
    job = queue.enqueue(simple_job, 3, 7)

    worker = Worker([queue])
    worker.start(burst=True)
    time.sleep(0.5)  # Give worker time to process
    worker.stop()

    assert job.is_finished()
    assert job.result == 10
    print("✓ Worker execution test passed")


def test_job_result():
    """Test getting job results."""
    queue = Queue("test")
    job = queue.enqueue(simple_job, 10, 20)

    worker = Worker([queue])
    worker.start(burst=True)

    result = job.get_result(timeout=2)
    assert result == 30
    worker.stop()
    print("✓ Job result test passed")


def test_failed_job():
    """Test handling failed jobs."""
    queue = Queue("test")
    job = queue.enqueue(failing_job)

    worker = Worker([queue])
    worker.start(burst=True)
    time.sleep(0.5)
    worker.stop()

    assert job.is_failed()
    assert job.exc_info is not None
    print("✓ Failed job test passed")


def test_multiple_queues():
    """Test worker processing multiple queues."""
    queue1 = Queue("high_priority")
    queue2 = Queue("low_priority")

    job1 = queue1.enqueue(simple_job, 1, 2)
    job2 = queue2.enqueue(simple_job, 3, 4)

    worker = Worker([queue1, queue2])
    worker.start(burst=True)
    time.sleep(0.5)
    worker.stop()

    assert job1.is_finished()
    assert job2.is_finished()
    assert job1.result == 3
    assert job2.result == 7
    print("✓ Multiple queues test passed")


def test_fetch_job():
    """Test fetching jobs by ID."""
    queue = Queue("test")
    job = queue.enqueue(simple_job, 5, 5)

    fetched_job = queue.fetch_job(job.id)
    assert fetched_job is not None
    assert fetched_job.id == job.id
    assert fetched_job.func == simple_job
    print("✓ Fetch job test passed")


def test_queue_operations():
    """Test various queue operations."""
    queue = Queue("test")

    # Initially empty
    assert queue.empty()
    assert queue.count() == 0

    # Add jobs
    job1 = queue.enqueue(simple_job, 1, 1)
    job2 = queue.enqueue(simple_job, 2, 2)

    assert queue.count() == 2
    assert not queue.empty()

    # Get job IDs
    job_ids = queue.get_job_ids()
    assert len(job_ids) == 2
    assert job1.id in job_ids
    assert job2.id in job_ids

    # Get jobs
    jobs = queue.get_jobs()
    assert len(jobs) == 2
    print("✓ Queue operations test passed")


def test_job_status_transitions():
    """Test job status transitions."""
    queue = Queue("test")
    job = queue.enqueue(slow_job, 0.2)

    # Initially queued
    assert job.is_queued()
    assert not job.is_started()
    assert not job.is_finished()

    worker = Worker([queue])
    worker.start(burst=False)

    # Wait for job to start
    time.sleep(0.1)
    assert job.is_started() or job.is_finished()

    # Wait for job to finish
    time.sleep(0.3)
    assert job.is_finished()
    assert job.started_at is not None
    assert job.ended_at is not None

    worker.stop()
    print("✓ Job status transitions test passed")


def test_job_with_kwargs():
    """Test jobs with keyword arguments."""
    def job_with_kwargs(a, b=10):
        return a + b

    queue = Queue("test")
    job = queue.enqueue(job_with_kwargs, 5, b=15)

    worker = Worker([queue])
    worker.start(burst=True)
    time.sleep(0.5)
    worker.stop()

    assert job.is_finished()
    assert job.result == 20
    print("✓ Job with kwargs test passed")


def test_scheduled_job():
    """Test scheduled jobs."""
    queue = Queue("test")
    scheduled_time = timedelta(seconds=5)
    job = queue.enqueue_in(scheduled_time, simple_job, 10, 10)

    assert job.status == JobStatus.SCHEDULED
    print("✓ Scheduled job test passed")


def test_job_to_dict():
    """Test converting job to dictionary."""
    queue = Queue("test")
    job = queue.enqueue(simple_job, 1, 2, description="Test job")

    job_dict = job.to_dict()
    assert job_dict["id"] == job.id
    assert job_dict["func_name"] == f"{simple_job.__module__}.{simple_job.__name__}"
    assert job_dict["description"] == "Test job"
    assert job_dict["status"] == "queued"
    print("✓ Job to_dict test passed")


def test_concurrent_jobs():
    """Test processing multiple concurrent jobs."""
    queue = Queue("test")

    # Enqueue multiple jobs
    jobs = []
    for i in range(10):
        job = queue.enqueue(simple_job, i, i)
        jobs.append(job)

    worker = Worker([queue])
    worker.start(burst=True)
    time.sleep(1)
    worker.stop()

    # All jobs should be finished
    for i, job in enumerate(jobs):
        assert job.is_finished()
        assert job.result == i + i
    print("✓ Concurrent jobs test passed")


if __name__ == "__main__":
    print("Running RQ Emulator Tests...\n")

    test_job_creation()
    test_queue_enqueue()
    test_worker_execution()
    test_job_result()
    test_failed_job()
    test_multiple_queues()
    test_fetch_job()
    test_queue_operations()
    test_job_status_transitions()
    test_job_with_kwargs()
    test_scheduled_job()
    test_job_to_dict()
    test_concurrent_jobs()

    print("\n✅ All RQ Emulator tests passed!")
