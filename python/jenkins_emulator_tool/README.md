# Jenkins Emulator - CI/CD Automation Server

A lightweight emulation of **Jenkins**, the leading open-source automation server used for continuous integration and continuous delivery (CI/CD).

## Features

This emulator implements core Jenkins functionality:

### Job Management
- **Job Creation**: Define and configure jobs
- **Job Execution**: Run jobs with custom scripts
- **Build History**: Track all build executions
- **Build Parameters**: Pass parameters to jobs
- **Job Status**: Enable/disable jobs
- **Console Output**: Capture build logs

### Build System
- **Build Triggers**: Manual, SCM, cron, webhook, upstream
- **Build Status**: Success, failure, unstable, aborted
- **Build Numbers**: Sequential build numbering
- **Concurrent Builds**: Control parallel execution
- **Build Artifacts**: Track build outputs
- **Build Duration**: Measure execution time

### Pipeline Support
- **Pipeline Definition**: Create multi-stage pipelines
- **Stage Execution**: Define pipeline stages
- **Pipeline Parameters**: Parameterized pipelines
- **Agent Configuration**: Configure build agents
- **Post Actions**: Define post-build actions

### Plugin System
- **Plugin Installation**: Add plugins
- **Plugin Management**: List installed plugins
- **Extensibility**: Basic plugin framework

### Configuration
- **Global Configuration**: System-wide settings
- **Job Configuration**: Per-job settings
- **Build Environment**: Environment variables
- **Workspace Management**: Build workspaces

## What It Emulates

This tool emulates core functionality of [Jenkins](https://www.jenkins.io/), the most popular open-source automation server.

### Core Components Implemented

1. **Job System**
   - Job creation and management
   - Build execution
   - Build history
   - Console output capture

2. **Pipeline Framework**
   - Multi-stage pipelines
   - Stage definitions
   - Pipeline execution
   - Parameter support

3. **Build Management**
   - Build triggers
   - Build status tracking
   - Build artifacts
   - Build history

4. **Configuration**
   - Global settings
   - Job configuration
   - Plugin system
   - Environment variables

## Usage

### Basic Job Creation and Execution

```python
from jenkins_emulator import JenkinsEmulator

# Create Jenkins instance
jenkins = JenkinsEmulator()

# Create a simple job
job = jenkins.create_job("my-first-job", "My first Jenkins job")

# Trigger a build
build = jenkins.build_job("my-first-job", wait=True)

print(f"Build #{build.build_number} status: {build.status.value}")
```

### Job with Custom Script

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Define build script
def build_script(params):
    """Custom build logic"""
    print(f"Building version {params.get('version', '1.0')}")
    # Perform build steps
    return True  # Return True for success, False for failure

# Create job with script
job = jenkins.create_job(
    "build-project",
    "Build the project",
    script=build_script
)

# Build with parameters
build = jenkins.build_job(
    "build-project",
    parameters={"version": "2.0", "branch": "main"},
    wait=True
)

print(f"Build status: {build.status.value}")
print(f"Console output: {build.console_output}")
```

### Pipeline Creation

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Create pipeline
pipeline = jenkins.create_pipeline("my-pipeline")

# Define stages
def build_stage(params):
    print("Compiling source code...")

def test_stage(params):
    print("Running tests...")

def deploy_stage(params):
    print("Deploying application...")

# Add stages to pipeline
pipeline.add_stage("Build", [build_stage])
pipeline.add_stage("Test", [test_stage])
pipeline.add_stage("Deploy", [deploy_stage])

# Execute pipeline
build = jenkins.execute_pipeline("my-pipeline", parameters={"env": "prod"})

print(f"Pipeline status: {build.status.value}")
```

### Build History Management

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Create job
job = jenkins.create_job("test-job")

# Run multiple builds
for i in range(5):
    jenkins.build_job("test-job", parameters={"run": i}, wait=True)

# Get last build
last_build = job.get_last_build()
print(f"Last build: #{last_build.build_number}, status: {last_build.status.value}")

# Get last successful build
last_success = job.get_last_successful_build()
if last_success:
    print(f"Last successful build: #{last_success.build_number}")

# Get specific build
build_3 = job.get_build(3)
if build_3:
    print(f"Build #3 duration: {build_3.duration}s")
```

### Console Output Capture

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

def verbose_script(params):
    print("Step 1: Preparing environment")
    print("Step 2: Running tests")
    print("Step 3: Generating report")
    return True

job = jenkins.create_job("verbose-job", script=verbose_script)
build = jenkins.build_job("verbose-job", wait=True)

# Get console output
output = jenkins.get_console_output("verbose-job", build.build_number)
for line in output:
    print(line)
```

### Plugin Management

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Install plugins
jenkins.install_plugin("git")
jenkins.install_plugin("docker")
jenkins.install_plugin("kubernetes")

# List installed plugins
plugins = jenkins.get_installed_plugins()
print(f"Installed plugins: {plugins}")
```

### Global Configuration

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Set global configuration
jenkins.set_global_config("master_url", "http://jenkins.local:8080")
jenkins.set_global_config("num_executors", 4)
jenkins.set_global_config("admin_email", "admin@example.com")

# Get configuration
url = jenkins.get_global_config("master_url")
print(f"Jenkins URL: {url}")
```

### Advanced Build Control

```python
from jenkins_emulator import JenkinsEmulator, BuildStatus

jenkins = JenkinsEmulator()

# Create job
job = jenkins.create_job("long-running-job")

def long_running_script(params):
    import time
    for i in range(10):
        print(f"Processing step {i+1}/10")
        time.sleep(1)
    return True

job.script = long_running_script

# Start build without waiting
build = jenkins.build_job("long-running-job", wait=False)

# Check status later
import time
time.sleep(3)
status = jenkins.get_build_status("long-running-job", build.build_number)
print(f"Build status: {status.value}")

# Abort if needed
if status == BuildStatus.IN_PROGRESS:
    jenkins.abort_build("long-running-job", build.build_number)
    print("Build aborted")
```

### Job Management

```python
from jenkins_emulator import JenkinsEmulator

jenkins = JenkinsEmulator()

# Create multiple jobs
jenkins.create_job("frontend-build", "Build frontend")
jenkins.create_job("backend-build", "Build backend")
jenkins.create_job("integration-test", "Run integration tests")

# List all jobs
jobs = jenkins.list_jobs()
print(f"All jobs: {jobs}")

# Get specific job
job = jenkins.get_job("frontend-build")
print(f"Job: {job.name}, Description: {job.description}")

# Delete job
jenkins.delete_job("integration-test")
jobs = jenkins.list_jobs()
print(f"Remaining jobs: {jobs}")
```

## API Reference

### Main Classes

#### `JenkinsEmulator`
Main Jenkins server class.

**Methods:**
- `create_job(name, description, script)` - Create a new job
- `get_job(name)` - Get job by name
- `delete_job(name)` - Delete a job
- `list_jobs()` - List all job names
- `build_job(job_name, parameters, wait)` - Trigger job build
- `get_build_status(job_name, build_number)` - Get build status
- `get_console_output(job_name, build_number)` - Get console output
- `abort_build(job_name, build_number)` - Abort running build
- `create_pipeline(name)` - Create pipeline
- `execute_pipeline(name, parameters)` - Execute pipeline
- `install_plugin(plugin_name)` - Install plugin
- `get_installed_plugins()` - List plugins
- `set_global_config(key, value)` - Set config
- `get_global_config(key)` - Get config

#### `Job`
Job configuration.

**Attributes:**
- `name` (str) - Job name
- `description` (str) - Job description
- `script` (callable) - Build script
- `parameters` (dict) - Job parameters
- `builds` (list) - Build history
- `enabled` (bool) - Job enabled status
- `build_counter` (int) - Build counter

**Methods:**
- `get_last_build()` - Get last build
- `get_last_successful_build()` - Get last successful build
- `get_build(build_number)` - Get specific build

#### `BuildResult`
Build execution result.

**Attributes:**
- `build_number` (int) - Build number
- `job_name` (str) - Job name
- `status` (BuildStatus) - Build status
- `start_time` (datetime) - Start time
- `end_time` (datetime) - End time
- `duration` (float) - Duration in seconds
- `console_output` (list) - Console output lines
- `artifacts` (list) - Build artifacts
- `parameters` (dict) - Build parameters

**Methods:**
- `is_success()` - Check if successful
- `is_failure()` - Check if failed
- `is_complete()` - Check if complete

#### `Pipeline`
Pipeline configuration.

**Attributes:**
- `name` (str) - Pipeline name
- `stages` (list) - Pipeline stages
- `agent` (str) - Build agent
- `environment` (dict) - Environment variables
- `parameters` (dict) - Pipeline parameters

**Methods:**
- `add_stage(name, steps)` - Add pipeline stage

### Enums

**`BuildStatus`:**
- `SUCCESS` - Build succeeded
- `FAILURE` - Build failed
- `UNSTABLE` - Build unstable
- `ABORTED` - Build aborted
- `NOT_BUILT` - Not built
- `IN_PROGRESS` - Currently building

**`TriggerType`:**
- `MANUAL` - Manual trigger
- `SCM_POLL` - SCM polling
- `CRON` - Scheduled trigger
- `WEBHOOK` - Webhook trigger
- `UPSTREAM` - Upstream job trigger

## Testing

Run the test suite:

```bash
python test_jenkins_emulator.py
```

Tests cover:
- Job creation and management
- Build execution
- Pipeline execution
- Build status tracking
- Console output capture
- Plugin management
- Global configuration

## Limitations

This is an educational emulation with some limitations:

1. **No Distributed Builds**: Single instance only
2. **No Actual SCM Integration**: SCM triggers not implemented
3. **Simplified Plugin System**: Basic plugin management only
4. **No Authentication**: No user/security management
5. **No Web UI**: Command-line/API only
6. **No Workspace Persistence**: In-memory only
7. **No Build Queue**: Simplified queue management
8. **No Slave Nodes**: No distributed execution

## Real-World Jenkins

To use real Jenkins, see the [official documentation](https://www.jenkins.io/doc/).

## Use Cases

- Learning CI/CD concepts
- Understanding build automation
- Testing Jenkins integrations
- Prototyping build pipelines
- Educational purposes
- Development environments

## Complexity

**Implementation Complexity**: Medium

This emulator involves:
- Job management system
- Build execution framework
- Pipeline orchestration
- Threading for concurrent builds
- Build history tracking

## Dependencies

- Python 3.7+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
