"""
Developed by PowerShield, as an alternative to RQ


RQ (Redis Queue) Emulator - Simple Python job queue.

RQ is a simple Python library for queueing jobs and processing them in the background
with workers. It is backed by Redis and is designed to have a low barrier to entry.

This emulator provides RQ's core functionality without external Redis dependency.
"""

import uuid
import time
import pickle
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from threading import Thread, Lock
from queue import Queue as ThreadQueue, Empty
from enum import Enum


class JobStatus(Enum):
    """Job status states (matches RQ's JobStatus)."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    DEFERRED = "deferred"
    SCHEDULED = "scheduled"


class Job:
    """
    Represents a job in the queue.
    Emulates RQ's Job class with core functionality.
    """

    def __init__(
        self,
        func: Callable,
        args: Tuple = (),
        kwargs: Dict[str, Any] = None,
        result_ttl: int = 500,
        timeout: Optional[int] = None,
        job_id: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize a job.

        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            result_ttl: Time-to-live for the result (in seconds)
            timeout: Maximum execution time (in seconds)
            job_id: Optional custom job ID
            description: Optional job description
        """
        self.id = job_id or str(uuid.uuid4())
        self.func = func
        self.func_name = f"{func.__module__}.{func.__name__}"
        self.args = args
        self.kwargs = kwargs or {}
        self.result_ttl = result_ttl
        self.timeout = timeout
        self.description = description or self.func_name

        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.status = JobStatus.QUEUED
        self.result: Any = None
        self.exc_info: Optional[str] = None
        self.meta: Dict[str, Any] = {}

    def get_status(self) -> str:
        """Get the current job status."""
        return self.status.value

    def is_finished(self) -> bool:
        """Check if the job is finished."""
        return self.status == JobStatus.FINISHED

    def is_failed(self) -> bool:
        """Check if the job failed."""
        return self.status == JobStatus.FAILED

    def is_started(self) -> bool:
        """Check if the job has started."""
        return self.status == JobStatus.STARTED

    def is_queued(self) -> bool:
        """Check if the job is queued."""
        return self.status == JobStatus.QUEUED

    def get_result(self, timeout: Optional[int] = None) -> Any:
        """
        Get the job result, waiting if necessary.

        Args:
            timeout: Maximum time to wait for result (in seconds)

        Returns:
            The job result

        Raises:
            Exception: If the job failed
        """
        if timeout:
            start = time.time()
            while not self.is_finished() and not self.is_failed():
                if time.time() - start > timeout:
                    raise TimeoutError(f"Job {self.id} did not complete within {timeout}s")
                time.sleep(0.1)

        if self.is_failed():
            raise Exception(f"Job failed: {self.exc_info}")

        return self.result

    def refresh(self):
        """Refresh job data (no-op in this emulator)."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "func_name": self.func_name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "result": str(self.result) if self.result is not None else None,
            "exc_info": self.exc_info,
            "meta": self.meta,
        }


class Queue:
    """
    Job queue implementation.
    Emulates RQ's Queue class.
    """

    def __init__(self, name: str = "default", is_async: bool = True):
        """
        Initialize a queue.

        Args:
            name: Queue name
            is_async: Whether to execute jobs asynchronously
        """
        self.name = name
        self.is_async = is_async
        self._jobs: Dict[str, Job] = {}
        self._job_queue: ThreadQueue = ThreadQueue()
        self._lock = Lock()

    def enqueue(
        self,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        timeout: Optional[int] = None,
        result_ttl: int = 500,
        description: Optional[str] = None,
        **kwargs,
    ) -> Job:
        """
        Enqueue a job for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            job_id: Optional custom job ID
            timeout: Maximum execution time
            result_ttl: Time-to-live for result
            description: Job description
            **kwargs: Keyword arguments

        Returns:
            Job object
        """
        job = Job(
            func=func,
            args=args,
            kwargs=kwargs,
            result_ttl=result_ttl,
            timeout=timeout,
            job_id=job_id,
            description=description,
        )

        with self._lock:
            self._jobs[job.id] = job
            self._job_queue.put(job)

        return job

    def enqueue_at(self, datetime: datetime, func: Callable, *args, **kwargs) -> Job:
        """
        Schedule a job to run at a specific time.

        Args:
            datetime: When to run the job
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Job object
        """
        job = self.enqueue(func, *args, **kwargs)
        job.status = JobStatus.SCHEDULED
        # In a real implementation, this would schedule the job
        # For simplicity, we'll just mark it as scheduled
        return job

    def enqueue_in(self, time_delta: timedelta, func: Callable, *args, **kwargs) -> Job:
        """
        Schedule a job to run after a time delta.

        Args:
            time_delta: Time to wait before running
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Job object
        """
        scheduled_time = datetime.utcnow() + time_delta
        return self.enqueue_at(scheduled_time, func, *args, **kwargs)

    def fetch_job(self, job_id: str) -> Optional[Job]:
        """
        Fetch a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)

    def get_jobs(self) -> List[Job]:
        """Get all jobs in the queue."""
        with self._lock:
            return list(self._jobs.values())

    def get_job_ids(self) -> List[str]:
        """Get all job IDs."""
        with self._lock:
            return list(self._jobs.keys())

    def count(self) -> int:
        """Get the number of jobs in the queue."""
        return self._job_queue.qsize()

    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._job_queue.empty()


class Worker:
    """
    Worker that processes jobs from queues.
    Emulates RQ's Worker class.
    """

    def __init__(
        self,
        queues: List[Queue],
        name: Optional[str] = None,
    ):
        """
        Initialize a worker.

        Args:
            queues: List of queues to process
            name: Worker name
        """
        self.queues = queues if isinstance(queues, list) else [queues]
        self.name = name or f"worker-{uuid.uuid4()}"
        self._shutdown = False
        self._thread: Optional[Thread] = None

    def work(self, burst: bool = False):
        """
        Start processing jobs.

        Args:
            burst: If True, quit after all jobs are processed
        """
        while not self._shutdown:
            job = self._dequeue_job()

            if job is None:
                if burst:
                    break
                time.sleep(0.1)
                continue

            self._execute_job(job)

            if burst:
                # Check if all queues are empty
                if all(q.empty() for q in self.queues):
                    break

    def start(self, burst: bool = False):
        """
        Start the worker in a background thread.

        Args:
            burst: If True, quit after all jobs are processed
        """
        self._thread = Thread(target=self.work, args=(burst,), daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the worker gracefully."""
        self._shutdown = True
        if self._thread:
            self._thread.join(timeout=5)

    def _dequeue_job(self) -> Optional[Job]:
        """Dequeue a job from any queue."""
        for queue in self.queues:
            try:
                job = queue._job_queue.get_nowait()
                return job
            except Empty:
                continue
        return None

    def _execute_job(self, job: Job):
        """
        Execute a job.

        Args:
            job: Job to execute
        """
        job.status = JobStatus.STARTED
        job.started_at = datetime.utcnow()

        try:
            # Execute the job function
            result = job.func(*job.args, **job.kwargs)

            job.status = JobStatus.FINISHED
            job.result = result
            job.ended_at = datetime.utcnow()

        except Exception as e:
            job.status = JobStatus.FAILED
            job.exc_info = str(e)
            job.ended_at = datetime.utcnow()


# Convenience functions (matching RQ's API)
_default_queue = None


def get_current_job() -> Optional[Job]:
    """Get the currently executing job (not implemented in this simple version)."""
    return None


def push_connection(conn):
    """Push a connection onto the stack (no-op in this emulator)."""
    pass


def pop_connection():
    """Pop a connection from the stack (no-op in this emulator)."""
    pass


def use_connection(conn):
    """Use a connection (no-op in this emulator)."""
    pass
