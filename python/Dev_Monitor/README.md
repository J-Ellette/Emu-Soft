# Live Reload Development Server

File watching and automatic reload capabilities for development.

## What This Emulates

**Emulates:** uvicorn --reload, webpack-dev-server, nodemon
**Similar to:** Live reload functionality in modern development tools

## Features

- File system watching for changes
- Automatic application reload on file modifications
- Configurable file extensions to monitor
- Debouncing to prevent multiple reloads
- Event-driven architecture
- Integration with development servers

## Core Components

- **live_reload.py**: Main implementation
  - `FileChangeHandler`: Handles file system events
  - File pattern matching
  - Debounce logic to prevent rapid reloads
  - Callback system for custom reload actions

## Dependencies

This module uses `watchdog` for cross-platform file system monitoring.

## Usage

```python
from live_reload import FileChangeHandler
from watchdog.observers import Observer

def on_file_change(filepath):
    print(f"File changed: {filepath}")
    # Reload your application here
    
# Create handler
handler = FileChangeHandler(
    callback=on_file_change,
    extensions={'.py', '.html', '.css', '.js'}
)

# Set up observer
observer = Observer()
observer.schedule(handler, path=".", recursive=True)
observer.start()

# Observer runs in background
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

## Configuration

- `extensions`: Set of file extensions to watch (e.g., `{'.py', '.html'}`)
- `debounce_time`: Time in seconds to wait before triggering callback (default: 0.5s)
- `callback`: Function called when files change

## Use Cases

- Development server auto-reload
- Template file monitoring
- Static asset recompilation
- Test runner automation
- Documentation regeneration

## Implementation Notes

- Uses `watchdog` library for cross-platform compatibility
- Implements debouncing to handle multiple rapid changes
- Ignores directory events (only tracks files)
- Tracks last modified times to prevent duplicate events

## Why This Was Created

This module was created as part of the CIV-ARCOS project to provide development workflow automation, improving developer productivity with automatic reloading during development.
