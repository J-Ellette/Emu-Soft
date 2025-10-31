"""Live reload development server.

Provides file watching and automatic reload capabilities for development,
similar to uvicorn --reload but with custom implementation.


Developed by PowerShield
"""

import asyncio
import sys
import os
import time
from typing import Optional, Set, Callable, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import logging


logger = logging.getLogger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system changes."""

    def __init__(
        self,
        callback: Callable[[str], None],
        extensions: Optional[Set[str]] = None,
    ) -> None:
        """Initialize file change handler.
        
        Args:
            callback: Function to call when files change
            extensions: Set of file extensions to watch (e.g., {'.py', '.html'})
        """
        super().__init__()
        self.callback = callback
        self.extensions = extensions or {".py", ".html", ".css", ".js"}
        self.last_modified: dict[str, float] = {}
        self.debounce_time = 0.5  # 500ms debounce

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any file system event.
        
        Args:
            event: File system event
        """
        # Ignore directory events
        if event.is_directory:
            return
        
        # Check if file extension is watched
        file_path = event.src_path
        _, ext = os.path.splitext(file_path)
        
        if ext not in self.extensions:
            return
        
        # Debounce: ignore rapid consecutive changes
        current_time = time.time()
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_time:
                return
        
        self.last_modified[file_path] = current_time
        
        # Call the callback
        try:
            self.callback(file_path)
        except Exception as e:
            logger.error(f"Error in file change callback: {e}")


class LiveReloadServer:
    """Development server with live reload capability.
    
    This provides automatic reloading when files change, similar to
    uvicorn --reload or webpack-dev-server.
    """

    def __init__(
        self,
        app: Any,
        watch_dirs: Optional[list[str]] = None,
        watch_extensions: Optional[Set[str]] = None,
        port: int = 8000,
        host: str = "127.0.0.1",
    ) -> None:
        """Initialize live reload server.
        
        Args:
            app: ASGI application to serve
            watch_dirs: Directories to watch for changes
            watch_extensions: File extensions to watch
            port: Port to serve on
            host: Host to bind to
        """
        self.app = app
        self.watch_dirs = watch_dirs or [os.getcwd()]
        self.watch_extensions = watch_extensions or {".py", ".html", ".css", ".js"}
        self.port = port
        self.host = host
        self.observer: Optional[Observer] = None
        self.should_reload = False
        self.server_process: Optional[asyncio.subprocess.Process] = None

    def start(self) -> None:
        """Start the live reload server."""
        logger.info(f"Starting live reload server on {self.host}:{self.port}")
        logger.info(f"Watching directories: {self.watch_dirs}")
        logger.info(f"Watching extensions: {self.watch_extensions}")
        
        # Start file watcher
        self._start_watcher()
        
        # Start server
        try:
            self._run_server()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self._stop_watcher()

    def _start_watcher(self) -> None:
        """Start watching files for changes."""
        self.observer = Observer()
        
        handler = FileChangeHandler(
            callback=self._on_file_change,
            extensions=self.watch_extensions,
        )
        
        for watch_dir in self.watch_dirs:
            if os.path.exists(watch_dir):
                self.observer.schedule(handler, watch_dir, recursive=True)
                logger.info(f"Watching: {watch_dir}")
        
        self.observer.start()

    def _stop_watcher(self) -> None:
        """Stop watching files."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def _on_file_change(self, file_path: str) -> None:
        """Handle file change event.
        
        Args:
            file_path: Path to changed file
        """
        logger.info(f"File changed: {file_path}")
        logger.info("Reloading server...")
        self.should_reload = True

    def _run_server(self) -> None:
        """Run the server with automatic reload."""
        while True:
            self.should_reload = False
            
            try:
                # Import uvicorn here to avoid hard dependency
                import uvicorn
                
                # Run server in a way that can be interrupted
                config = uvicorn.Config(
                    app=self.app,
                    host=self.host,
                    port=self.port,
                    log_level="info",
                )
                server = uvicorn.Server(config)
                
                # Run until reload is needed
                asyncio.run(self._run_until_reload(server))
                
                if not self.should_reload:
                    break
                    
            except ImportError:
                logger.error(
                    "uvicorn not installed. Install with: pip install uvicorn"
                )
                break
            except Exception as e:
                logger.error(f"Server error: {e}")
                if not self.should_reload:
                    break
            
            # Small delay before restarting
            time.sleep(0.5)

    async def _run_until_reload(self, server) -> None:
        """Run server until reload is needed.
        
        Args:
            server: Uvicorn server instance
        """
        # Start server in background
        server_task = asyncio.create_task(server.serve())
        
        # Wait for reload signal
        while not self.should_reload:
            await asyncio.sleep(0.1)
        
        # Stop server
        server.should_exit = True
        await server_task


class HotModuleReloader:
    """Hot module replacement for Python modules.
    
    This provides HMR-like functionality for Python code, allowing
    modules to be reloaded without full server restart.
    """

    def __init__(self) -> None:
        """Initialize hot module reloader."""
        self.watched_modules: Set[str] = set()
        self.module_timestamps: dict[str, float] = {}

    def watch_module(self, module_name: str) -> None:
        """Add a module to watch for changes.
        
        Args:
            module_name: Name of module to watch
        """
        self.watched_modules.add(module_name)
        
        # Get initial timestamp
        if module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, "__file__") and module.__file__:
                self.module_timestamps[module_name] = os.path.getmtime(
                    module.__file__
                )

    def check_and_reload(self) -> list[str]:
        """Check for changed modules and reload them.
        
        Returns:
            List of reloaded module names
        """
        reloaded = []
        
        for module_name in self.watched_modules:
            if module_name not in sys.modules:
                continue
            
            module = sys.modules[module_name]
            if not hasattr(module, "__file__") or not module.__file__:
                continue
            
            file_path = module.__file__
            if not os.path.exists(file_path):
                continue
            
            current_mtime = os.path.getmtime(file_path)
            last_mtime = self.module_timestamps.get(module_name, 0)
            
            if current_mtime > last_mtime:
                try:
                    # Reload the module
                    import importlib
                    importlib.reload(module)
                    
                    self.module_timestamps[module_name] = current_mtime
                    reloaded.append(module_name)
                    logger.info(f"Hot reloaded module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to reload {module_name}: {e}")
        
        return reloaded

    def auto_watch_project(self, root_dir: str, package_name: str) -> None:
        """Automatically watch all modules in a project.
        
        Args:
            root_dir: Root directory of project
            package_name: Name of main package
        """
        root_path = Path(root_dir)
        package_path = root_path / package_name
        
        if not package_path.exists():
            return
        
        # Find all Python files
        for py_file in package_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            # Convert file path to module name
            relative = py_file.relative_to(root_path)
            module_parts = list(relative.parts)
            module_parts[-1] = module_parts[-1][:-3]  # Remove .py
            module_name = ".".join(module_parts)
            
            self.watch_module(module_name)


# Convenience function
def serve_with_reload(
    app: Any,
    watch_dirs: Optional[list[str]] = None,
    port: int = 8000,
    host: str = "127.0.0.1",
) -> None:
    """Start development server with live reload.
    
    Args:
        app: ASGI application to serve
        watch_dirs: Directories to watch
        port: Port to serve on
        host: Host to bind to
    """
    server = LiveReloadServer(
        app=app,
        watch_dirs=watch_dirs,
        port=port,
        host=host,
    )
    server.start()
