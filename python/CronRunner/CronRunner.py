"""
Developed by PowerShield, as an alternative to APScheduler


APScheduler (Advanced Python Scheduler) Emulator.

APScheduler is a Python library that lets you schedule Python code to be executed
later, either just once or periodically. It provides cron-like scheduling,
interval-based scheduling, and one-time scheduled execution.

This emulator provides APScheduler's core functionality without external dependencies.
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from threading import Thread, Lock, Event
from enum import Enum
import heapq


class JobState(Enum):
    """Job execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    REMOVED = "removed"


class TriggerType(Enum):
    """Types of triggers for job scheduling."""
    DATE = "date"          # Run once at a specific date/time
    INTERVAL = "interval"  # Run at fixed intervals
    CRON = "cron"          # Run at specific times (cron-like)


class Job:
    """
    Represents a scheduled job.
    """

    def __init__(
        self,
        job_id: str,
        func: Callable,
        trigger_type: TriggerType,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        name: Optional[str] = None,
        next_run_time: Optional[datetime] = None,
    ):
        """
        Initialize a job.

        Args:
            job_id: Unique job identifier
            func: Function to execute
            trigger_type: Type of trigger
            args: Positional arguments
            kwargs: Keyword arguments
            name: Job name
            next_run_time: Next scheduled run time
        """
        self.id = job_id
        self.func = func
        self.trigger_type = trigger_type
        self.args = args
        self.kwargs = kwargs or {}
        self.name = name or f"{func.__module__}.{func.__name__}"
        self.next_run_time = next_run_time
        self.state = JobState.PENDING
        self.last_run_time: Optional[datetime] = None
        self.run_count = 0

        # Trigger-specific data
        self.trigger_data: Dict[str, Any] = {}

    def __lt__(self, other):
        """Compare jobs by next run time (for heap queue)."""
        if self.next_run_time is None:
            return False
        if other.next_run_time is None:
            return True
        return self.next_run_time < other.next_run_time

    def execute(self):
        """Execute the job."""
        self.state = JobState.RUNNING
        self.last_run_time = datetime.now()
        self.run_count += 1

        try:
            result = self.func(*self.args, **self.kwargs)
            return result
        finally:
            self.state = JobState.PENDING

    def pause(self):
        """Pause the job."""
        self.state = JobState.PAUSED

    def resume(self):
        """Resume the job."""
        self.state = JobState.PENDING

    def remove(self):
        """Mark job for removal."""
        self.state = JobState.REMOVED


class BackgroundScheduler:
    """
    Background scheduler that runs in a separate thread.
    Emulates APScheduler's BackgroundScheduler.
    """

    def __init__(self, timezone=None):
        """
        Initialize the scheduler.

        Args:
            timezone: Timezone for scheduling (not fully implemented)
        """
        self.timezone = timezone
        self._jobs: Dict[str, Job] = {}
        self._job_heap: List[Job] = []
        self._lock = Lock()
        self._thread: Optional[Thread] = None
        self._shutdown_event = Event()
        self._running = False

    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler.

        Args:
            wait: Whether to wait for the thread to finish
        """
        self._running = False
        self._shutdown_event.set()

        if wait and self._thread:
            self._thread.join(timeout=5)

    def add_job(
        self,
        func: Callable,
        trigger: Optional[str] = None,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        **trigger_args,
    ) -> Job:
        """
        Add a job to the scheduler.

        Args:
            func: Function to execute
            trigger: Trigger type ('date', 'interval', or 'cron')
            args: Positional arguments
            kwargs: Keyword arguments
            id: Job ID (auto-generated if not provided)
            name: Job name
            **trigger_args: Trigger-specific arguments

        Returns:
            Job object
        """
        job_id = id or str(uuid.uuid4())

        # Determine trigger type
        if trigger == "date":
            trigger_type = TriggerType.DATE
            next_run = self._parse_date_trigger(**trigger_args)
        elif trigger == "interval":
            trigger_type = TriggerType.INTERVAL
            next_run = self._parse_interval_trigger(**trigger_args)
        elif trigger == "cron":
            trigger_type = TriggerType.CRON
            next_run = self._parse_cron_trigger(**trigger_args)
        else:
            # Default to immediate execution
            trigger_type = TriggerType.DATE
            next_run = datetime.now()

        job = Job(
            job_id=job_id,
            func=func,
            trigger_type=trigger_type,
            args=args,
            kwargs=kwargs,
            name=name,
            next_run_time=next_run,
        )
        job.trigger_data = trigger_args

        with self._lock:
            self._jobs[job_id] = job
            heapq.heappush(self._job_heap, job)

        return job

    def remove_job(self, job_id: str):
        """
        Remove a job from the scheduler.

        Args:
            job_id: Job identifier
        """
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.remove()
                del self._jobs[job_id]
                # Rebuild heap without the removed job
                self._job_heap = [j for j in self._job_heap if j.id != job_id]
                heapq.heapify(self._job_heap)

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None
        """
        with self._lock:
            return self._jobs.get(job_id)

    def get_jobs(self) -> List[Job]:
        """Get all jobs."""
        with self._lock:
            return list(self._jobs.values())

    def pause_job(self, job_id: str):
        """Pause a job."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].pause()

    def resume_job(self, job_id: str):
        """Resume a job."""
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.resume()
                # If job is not in heap, add it back
                if job not in self._job_heap:
                    heapq.heappush(self._job_heap, job)

    def _run(self):
        """Main scheduler loop."""
        while self._running and not self._shutdown_event.is_set():
            now = datetime.now()

            with self._lock:
                # Get jobs that are due
                due_jobs = []
                while self._job_heap and self._job_heap[0].next_run_time <= now:
                    job = heapq.heappop(self._job_heap)
                    if job.state == JobState.PENDING:
                        due_jobs.append(job)
                    elif job.state == JobState.PAUSED:
                        # Don't execute, but don't lose the job either
                        # It will be re-added when resumed
                        pass

            # Execute due jobs
            for job in due_jobs:
                if job.state == JobState.PENDING:
                    try:
                        job.execute()
                    except Exception as e:
                        # In production, this would be logged
                        pass

                    # Reschedule if needed
                    self._reschedule_job(job)

            # Sleep for a short time
            self._shutdown_event.wait(timeout=0.1)

    def _reschedule_job(self, job: Job):
        """
        Reschedule a job based on its trigger type.

        Args:
            job: Job to reschedule
        """
        with self._lock:
            if job.trigger_type == TriggerType.INTERVAL:
                # Reschedule for next interval
                interval_data = job.trigger_data
                next_run = self._parse_interval_trigger(**interval_data)
                job.next_run_time = next_run
                heapq.heappush(self._job_heap, job)

            elif job.trigger_type == TriggerType.CRON:
                # Calculate next cron run time
                next_run = self._parse_cron_trigger(**job.trigger_data)
                job.next_run_time = next_run
                heapq.heappush(self._job_heap, job)

            # DATE trigger jobs run once and are not rescheduled

    def _parse_date_trigger(
        self,
        run_date: Optional[Union[datetime, str]] = None,
        **kwargs,
    ) -> datetime:
        """Parse date trigger arguments."""
        if run_date is None:
            return datetime.now()
        if isinstance(run_date, str):
            # Simple ISO format parsing
            return datetime.fromisoformat(run_date)
        return run_date

    def _parse_interval_trigger(
        self,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        start_date: Optional[datetime] = None,
        **kwargs,
    ) -> datetime:
        """Parse interval trigger arguments."""
        interval = timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

        if start_date:
            base = start_date if start_date > datetime.now() else datetime.now()
        else:
            base = datetime.now()

        return base + interval

    def _parse_cron_trigger(
        self,
        year: Optional[Union[int, str]] = None,
        month: Optional[Union[int, str]] = None,
        day: Optional[Union[int, str]] = None,
        week: Optional[Union[int, str]] = None,
        day_of_week: Optional[Union[int, str]] = None,
        hour: Optional[Union[int, str]] = None,
        minute: Optional[Union[int, str]] = None,
        second: Optional[Union[int, str]] = None,
        **kwargs,
    ) -> datetime:
        """
        Parse cron trigger arguments (simplified implementation).

        This is a basic implementation. For full cron support,
        a more sophisticated parser would be needed.
        """
        now = datetime.now()

        # If specific values provided, use them
        target_hour = int(hour) if hour is not None else now.hour
        target_minute = int(minute) if minute is not None else now.minute
        target_second = int(second) if second is not None else now.second

        # Calculate next run time
        next_run = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=target_second,
            microsecond=0,
        )

        # If the time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run


# Decorator for scheduled functions
def scheduled_job(scheduler, trigger, **trigger_args):
    """
    Decorator to schedule a function.

    Args:
        scheduler: BackgroundScheduler instance
        trigger: Trigger type
        **trigger_args: Trigger-specific arguments

    Returns:
        Decorator function
    """
    def decorator(func):
        scheduler.add_job(func, trigger, **trigger_args)
        return func
    return decorator
