#!/usr/bin/env python3
"""
Jenkins Emulator - CI/CD Automation Server

This module emulates core Jenkins functionality including:
- Job configuration and execution
- Pipeline definitions
- Build triggers
- Build history and status
- Plugin system (basic)
- Workspace management
- Build artifacts
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import threading
import time


class BuildStatus(Enum):
    """Build status states"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNSTABLE = "UNSTABLE"
    ABORTED = "ABORTED"
    NOT_BUILT = "NOT_BUILT"
    IN_PROGRESS = "IN_PROGRESS"


class TriggerType(Enum):
    """Build trigger types"""
    MANUAL = "manual"
    SCM_POLL = "scm"
    CRON = "cron"
    WEBHOOK = "webhook"
    UPSTREAM = "upstream"


@dataclass
class BuildResult:
    """Result of a build execution"""
    build_number: int
    job_name: str
    status: BuildStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    console_output: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """Check if build was successful"""
        return self.status == BuildStatus.SUCCESS
    
    def is_failure(self) -> bool:
        """Check if build failed"""
        return self.status == BuildStatus.FAILURE
    
    def is_complete(self) -> bool:
        """Check if build is complete"""
        return self.status != BuildStatus.IN_PROGRESS


@dataclass
class Job:
    """Jenkins job configuration"""
    name: str
    description: str = ""
    script: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    triggers: List[TriggerType] = field(default_factory=list)
    builds: List[BuildResult] = field(default_factory=list)
    enabled: bool = True
    concurrent_builds: bool = False
    build_counter: int = 0
    workspace: str = ""
    
    def get_last_build(self) -> Optional[BuildResult]:
        """Get last build result"""
        return self.builds[-1] if self.builds else None
    
    def get_last_successful_build(self) -> Optional[BuildResult]:
        """Get last successful build"""
        for build in reversed(self.builds):
            if build.is_success():
                return build
        return None
    
    def get_build(self, build_number: int) -> Optional[BuildResult]:
        """Get specific build by number"""
        for build in self.builds:
            if build.build_number == build_number:
                return build
        return None


@dataclass
class Pipeline:
    """Jenkins pipeline configuration"""
    name: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    agent: str = "any"
    environment: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    post_actions: Dict[str, Callable] = field(default_factory=dict)
    
    def add_stage(self, name: str, steps: List[Callable]):
        """Add a stage to the pipeline"""
        self.stages.append({
            "name": name,
            "steps": steps
        })


class JenkinsEmulator:
    """Main Jenkins emulator class"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.pipelines: Dict[str, Pipeline] = {}
        self.running_builds: Dict[str, threading.Thread] = {}
        self.plugins: List[str] = []
        self.global_config: Dict[str, Any] = {}
        
    def create_job(self, name: str, description: str = "", 
                   script: Optional[Callable] = None) -> Job:
        """Create a new job"""
        job = Job(name=name, description=description, script=script)
        self.jobs[name] = job
        return job
    
    def get_job(self, name: str) -> Optional[Job]:
        """Get job by name"""
        return self.jobs.get(name)
    
    def delete_job(self, name: str) -> bool:
        """Delete a job"""
        if name in self.jobs:
            del self.jobs[name]
            return True
        return False
    
    def list_jobs(self) -> List[str]:
        """List all job names"""
        return list(self.jobs.keys())
    
    def build_job(self, job_name: str, parameters: Optional[Dict[str, Any]] = None,
                  wait: bool = False) -> Optional[BuildResult]:
        """Trigger a job build"""
        job = self.get_job(job_name)
        if not job:
            return None
        
        if not job.enabled:
            return None
        
        if not job.concurrent_builds and job_name in self.running_builds:
            return None
        
        # Create build result
        job.build_counter += 1
        build = BuildResult(
            build_number=job.build_counter,
            job_name=job_name,
            status=BuildStatus.IN_PROGRESS,
            start_time=datetime.now(),
            parameters=parameters or {}
        )
        job.builds.append(build)
        
        # Execute build in thread
        def run_build():
            try:
                build.console_output.append(f"[{datetime.now()}] Starting build #{build.build_number}")
                build.console_output.append(f"[{datetime.now()}] Building job: {job_name}")
                
                if job.script:
                    # Execute job script
                    result = job.script(build.parameters)
                    if result is False:
                        build.status = BuildStatus.FAILURE
                    else:
                        build.status = BuildStatus.SUCCESS
                else:
                    # Simulate build
                    time.sleep(0.5)
                    build.status = BuildStatus.SUCCESS
                
                build.console_output.append(f"[{datetime.now()}] Build finished: {build.status.value}")
                
            except Exception as e:
                build.status = BuildStatus.FAILURE
                build.console_output.append(f"[{datetime.now()}] Build failed: {str(e)}")
            
            finally:
                build.end_time = datetime.now()
                build.duration = (build.end_time - build.start_time).total_seconds()
                if job_name in self.running_builds:
                    del self.running_builds[job_name]
        
        thread = threading.Thread(target=run_build)
        self.running_builds[job_name] = thread
        thread.start()
        
        if wait:
            thread.join()
        
        return build
    
    def get_build_status(self, job_name: str, build_number: int) -> Optional[BuildStatus]:
        """Get status of a specific build"""
        job = self.get_job(job_name)
        if not job:
            return None
        
        build = job.get_build(build_number)
        return build.status if build else None
    
    def get_console_output(self, job_name: str, build_number: int) -> List[str]:
        """Get console output for a build"""
        job = self.get_job(job_name)
        if not job:
            return []
        
        build = job.get_build(build_number)
        return build.console_output if build else []
    
    def abort_build(self, job_name: str, build_number: int) -> bool:
        """Abort a running build"""
        job = self.get_job(job_name)
        if not job:
            return False
        
        build = job.get_build(build_number)
        if build and build.status == BuildStatus.IN_PROGRESS:
            build.status = BuildStatus.ABORTED
            build.end_time = datetime.now()
            build.duration = (build.end_time - build.start_time).total_seconds()
            return True
        
        return False
    
    def create_pipeline(self, name: str) -> Pipeline:
        """Create a new pipeline"""
        pipeline = Pipeline(name=name)
        self.pipelines[name] = pipeline
        return pipeline
    
    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get pipeline by name"""
        return self.pipelines.get(name)
    
    def execute_pipeline(self, name: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[BuildResult]:
        """Execute a pipeline"""
        pipeline = self.get_pipeline(name)
        if not pipeline:
            return None
        
        # Create a job for the pipeline
        job = self.create_job(f"pipeline_{name}", f"Pipeline: {name}")
        
        def pipeline_script(params):
            """Execute pipeline stages"""
            for stage in pipeline.stages:
                print(f"Stage: {stage['name']}")
                for step in stage['steps']:
                    step(params)
            return True
        
        job.script = pipeline_script
        
        # Build the pipeline job
        return self.build_job(job.name, parameters, wait=True)
    
    def install_plugin(self, plugin_name: str):
        """Install a plugin"""
        if plugin_name not in self.plugins:
            self.plugins.append(plugin_name)
    
    def get_installed_plugins(self) -> List[str]:
        """Get list of installed plugins"""
        return self.plugins.copy()
    
    def set_global_config(self, key: str, value: Any):
        """Set global configuration"""
        self.global_config[key] = value
    
    def get_global_config(self, key: str) -> Any:
        """Get global configuration"""
        return self.global_config.get(key)


# Helper functions
def create_job(jenkins: JenkinsEmulator, name: str, description: str = "") -> Job:
    """Helper to create a job"""
    return jenkins.create_job(name, description)


def create_pipeline(jenkins: JenkinsEmulator, name: str) -> Pipeline:
    """Helper to create a pipeline"""
    return jenkins.create_pipeline(name)


def build_job(jenkins: JenkinsEmulator, job_name: str, 
              parameters: Optional[Dict[str, Any]] = None, wait: bool = False) -> Optional[BuildResult]:
    """Helper to build a job"""
    return jenkins.build_job(job_name, parameters, wait)


if __name__ == "__main__":
    # Example usage
    jenkins = JenkinsEmulator()
    
    # Create a simple job
    def build_script(params):
        print(f"Building with params: {params}")
        return True
    
    job = jenkins.create_job("my-job", "My first job", build_script)
    
    # Trigger build
    build = jenkins.build_job("my-job", {"version": "1.0"}, wait=True)
    
    if build:
        print(f"Build #{build.build_number} status: {build.status.value}")
        print(f"Console output: {build.console_output}")
