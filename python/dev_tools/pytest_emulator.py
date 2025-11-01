"""
Developed by PowerShield, as an alternative to Development Tools
"""

"""
pytest emulator - Test discovery, fixtures, and assertion rewriting.
Emulates pytest functionality without external dependencies.

Core features:
- Test discovery with pattern matching
- Fixture management system
- Assertion introspection
- Test runner with detailed results
- Plugin architecture support
"""

import ast
import inspect
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class TestOutcome(Enum):
    """Test execution outcome."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Represents the result of a single test execution."""
    test_id: str
    test_name: str
    outcome: TestOutcome
    duration: float = 0.0
    error_message: Optional[str] = None
    traceback_info: Optional[str] = None
    captured_output: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "outcome": self.outcome.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "traceback_info": self.traceback_info,
            "captured_output": self.captured_output,
        }


@dataclass
class FixtureDefinition:
    """Defines a test fixture."""
    name: str
    func: Callable
    scope: str = "function"  # function, class, module, session
    params: List[Any] = field(default_factory=list)
    autouse: bool = False
    dependencies: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.name)


class FixtureManager:
    """Manages fixture lifecycle and dependency resolution."""
    
    def __init__(self):
        self.fixtures: Dict[str, FixtureDefinition] = {}
        self._cache: Dict[Tuple[str, str], Any] = {}  # (fixture_name, scope_key) -> value
        self._active_scopes: Dict[str, str] = {}  # scope -> current key
        
    def register_fixture(self, fixture: FixtureDefinition) -> None:
        """Register a fixture definition."""
        self.fixtures[fixture.name] = fixture
        
    def get_fixture_value(self, name: str, scope_key: str) -> Any:
        """Get or create fixture value for given scope."""
        cache_key = (name, scope_key)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        if name not in self.fixtures:
            raise ValueError(f"Fixture '{name}' not found")
            
        fixture = self.fixtures[name]
        
        # Resolve dependencies first
        kwargs = {}
        for dep_name in fixture.dependencies:
            kwargs[dep_name] = self.get_fixture_value(dep_name, scope_key)
        
        # Execute fixture function
        value = fixture.func(**kwargs)
        
        # Cache based on scope
        if fixture.scope != "function":
            self._cache[cache_key] = value
            
        return value
    
    def teardown_scope(self, scope: str) -> None:
        """Teardown fixtures for a given scope."""
        # Remove cached values for this scope
        keys_to_remove = [k for k in self._cache if k[1].startswith(scope)]
        for key in keys_to_remove:
            del self._cache[key]


class AssertionRewriter(ast.NodeTransformer):
    """
    Rewrites assert statements to provide detailed failure messages.
    Similar to pytest's assertion introspection.
    """
    
    def visit_Assert(self, node: ast.Assert) -> ast.Assert:
        """Rewrite assert to capture intermediate values."""
        # For simplicity, we keep the original assert but could expand
        # this to capture sub-expression values
        self.generic_visit(node)
        return node
    
    @staticmethod
    def format_assertion_error(test_node: ast.Assert, locals_dict: Dict) -> str:
        """Format a detailed assertion error message."""
        try:
            # Try to provide helpful assertion message
            test_src = ast.unparse(test_node.test)
            msg = f"AssertionError: assert {test_src}"
            
            if test_node.msg:
                msg_src = ast.unparse(test_node.msg)
                msg += f"\n  {msg_src}"
                
            return msg
        except Exception:
            return "AssertionError"


class TestCollector:
    """Collects tests from Python modules and files."""
    
    def __init__(self, fixture_manager: FixtureManager):
        self.fixture_manager = fixture_manager
        self.collected_tests: List[Tuple[Callable, str, List[str]]] = []  # (func, test_id, fixture_names)
        
    def collect_from_path(self, path: Path, pattern: str = "test_*.py") -> None:
        """Collect tests from a file or directory."""
        if path.is_file():
            if self._matches_pattern(path.name, pattern):
                self._collect_from_file(path)
        elif path.is_dir():
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    self._collect_from_file(file_path)
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches test pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filename, "*_test.py")
    
    def _collect_from_file(self, file_path: Path) -> None:
        """Collect tests from a single file."""
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(file_path))
            
            # Import the module to get actual function objects
            import importlib.util
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[file_path.stem] = module
                spec.loader.exec_module(module)
                
                # Collect test functions and fixtures
                for name in dir(module):
                    obj = getattr(module, name)
                    
                    # Check if it's a test function
                    if callable(obj) and (name.startswith('test_') or name.endswith('_test')):
                        # Get fixture dependencies from function signature
                        sig = inspect.signature(obj)
                        fixture_names = list(sig.parameters.keys())
                        
                        test_id = f"{file_path.stem}::{name}"
                        self.collected_tests.append((obj, test_id, fixture_names))
                    
                    # Check if it's a fixture
                    if callable(obj) and hasattr(obj, '_pytest_fixture'):
                        fixture_def = obj._pytest_fixture
                        self.fixture_manager.register_fixture(fixture_def)
                        
        except Exception as e:
            print(f"Error collecting from {file_path}: {e}")
    
    def collect_from_module(self, module: Any) -> None:
        """Collect tests from an imported module."""
        for name in dir(module):
            obj = getattr(module, name)
            
            if callable(obj) and (name.startswith('test_') or name.endswith('_test')):
                sig = inspect.signature(obj)
                fixture_names = list(sig.parameters.keys())
                
                test_id = f"{module.__name__}::{name}"
                self.collected_tests.append((obj, test_id, fixture_names))
            
            if callable(obj) and hasattr(obj, '_pytest_fixture'):
                fixture_def = obj._pytest_fixture
                self.fixture_manager.register_fixture(fixture_def)


class TestRunner:
    """Executes collected tests with fixture support."""
    
    def __init__(self, fixture_manager: FixtureManager):
        self.fixture_manager = fixture_manager
        self.results: List[TestResult] = []
        
    def run_tests(self, tests: List[Tuple[Callable, str, List[str]]]) -> List[TestResult]:
        """Run all collected tests."""
        import time
        
        for test_func, test_id, fixture_names in tests:
            start_time = time.time()
            
            try:
                # Prepare fixtures
                kwargs = {}
                for fixture_name in fixture_names:
                    kwargs[fixture_name] = self.fixture_manager.get_fixture_value(
                        fixture_name, 
                        scope_key=test_id
                    )
                
                # Run the test
                test_func(**kwargs)
                
                # Test passed
                duration = time.time() - start_time
                result = TestResult(
                    test_id=test_id,
                    test_name=test_func.__name__,
                    outcome=TestOutcome.PASSED,
                    duration=duration
                )
                
            except AssertionError as e:
                duration = time.time() - start_time
                result = TestResult(
                    test_id=test_id,
                    test_name=test_func.__name__,
                    outcome=TestOutcome.FAILED,
                    duration=duration,
                    error_message=str(e),
                    traceback_info=traceback.format_exc()
                )
                
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    test_id=test_id,
                    test_name=test_func.__name__,
                    outcome=TestOutcome.ERROR,
                    duration=duration,
                    error_message=str(e),
                    traceback_info=traceback.format_exc()
                )
            
            self.results.append(result)
            
            # Teardown function-scoped fixtures
            self.fixture_manager.teardown_scope(test_id)
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test execution summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.outcome == TestOutcome.PASSED)
        failed = sum(1 for r in self.results if r.outcome == TestOutcome.FAILED)
        errors = sum(1 for r in self.results if r.outcome == TestOutcome.ERROR)
        skipped = sum(1 for r in self.results if r.outcome == TestOutcome.SKIPPED)
        total_duration = sum(r.duration for r in self.results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "duration": total_duration,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }


class PyTestEmulator:
    """
    Main pytest emulator class.
    Provides test discovery, fixture management, and test execution.
    """
    
    def __init__(self):
        self.fixture_manager = FixtureManager()
        self.collector = TestCollector(self.fixture_manager)
        self.runner = TestRunner(self.fixture_manager)
        self._plugins: List[Any] = []
        
    def register_plugin(self, plugin: Any) -> None:
        """Register a pytest plugin."""
        self._plugins.append(plugin)
    
    def fixture(
        self,
        func: Optional[Callable] = None,
        *,
        scope: str = "function",
        params: List[Any] = None,
        autouse: bool = False
    ) -> Callable:
        """
        Decorator to mark a function as a fixture.
        
        Args:
            func: Function to decorate
            scope: Fixture scope (function, class, module, session)
            params: Parametrize fixture with these values
            autouse: Automatically use this fixture
            
        Returns:
            Decorated function
        """
        def decorator(f: Callable) -> Callable:
            # Extract dependencies from function signature
            sig = inspect.signature(f)
            dependencies = list(sig.parameters.keys())
            
            fixture_def = FixtureDefinition(
                name=f.__name__,
                func=f,
                scope=scope,
                params=params or [],
                autouse=autouse,
                dependencies=dependencies
            )
            
            # Store fixture definition on function
            f._pytest_fixture = fixture_def
            
            return f
        
        if func is not None:
            return decorator(func)
        return decorator
    
    def mark_skip(self, reason: str = "") -> Callable:
        """Decorator to skip a test."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                raise SkipTest(reason)
            return wrapper
        return decorator
    
    def collect(self, path: Union[str, Path], pattern: str = "test_*.py") -> int:
        """
        Collect tests from path.
        
        Args:
            path: File or directory path
            pattern: Test file pattern
            
        Returns:
            Number of tests collected
        """
        path_obj = Path(path) if isinstance(path, str) else path
        self.collector.collect_from_path(path_obj, pattern)
        return len(self.collector.collected_tests)
    
    def run(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Run collected tests.
        
        Args:
            verbose: Print detailed output
            
        Returns:
            Test execution summary
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Running {len(self.collector.collected_tests)} tests...")
            print(f"{'='*70}\n")
        
        results = self.runner.run_tests(self.collector.collected_tests)
        
        if verbose:
            self._print_results(results)
        
        return self.runner.get_summary()
    
    def _print_results(self, results: List[TestResult]) -> None:
        """Print test results in pytest-like format."""
        for result in results:
            status_symbol = {
                TestOutcome.PASSED: "✓",
                TestOutcome.FAILED: "✗",
                TestOutcome.ERROR: "E",
                TestOutcome.SKIPPED: "s"
            }[result.outcome]
            
            print(f"{status_symbol} {result.test_id} ({result.duration:.3f}s)")
            
            if result.outcome in (TestOutcome.FAILED, TestOutcome.ERROR):
                print(f"  Error: {result.error_message}")
                if result.traceback_info:
                    # Print last few lines of traceback
                    lines = result.traceback_info.split('\n')
                    for line in lines[-5:]:
                        if line.strip():
                            print(f"    {line}")
                print()
        
        # Print summary
        summary = self.runner.get_summary()
        print(f"\n{'='*70}")
        print(f"Test Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Duration: {summary['duration']:.2f}s")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"{'='*70}\n")


class SkipTest(Exception):
    """Exception to skip a test."""
    pass


# Global pytest instance for convenient access
pytest = PyTestEmulator()


# Convenience decorators
def fixture(
    func: Optional[Callable] = None,
    *,
    scope: str = "function",
    params: List[Any] = None,
    autouse: bool = False
) -> Callable:
    """Decorator to mark a function as a fixture."""
    return pytest.fixture(func, scope=scope, params=params, autouse=autouse)


def skip(reason: str = "") -> Callable:
    """Decorator to skip a test."""
    return pytest.mark_skip(reason)


def main(path: str = ".", pattern: str = "test_*.py", verbose: bool = True) -> int:
    """
    Main entry point for running tests.
    
    Args:
        path: Directory or file to search for tests
        pattern: Test file pattern
        verbose: Print detailed output
        
    Returns:
        Exit code (0 for success, 1 for failures)
    """
    pytest_runner = PyTestEmulator()
    num_tests = pytest_runner.collect(path, pattern)
    
    if num_tests == 0:
        print(f"No tests collected from {path}")
        return 0
    
    summary = pytest_runner.run(verbose=verbose)
    
    # Return exit code
    return 0 if summary['failed'] == 0 and summary['errors'] == 0 else 1


if __name__ == "__main__":
    import sys
    
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    exit_code = main(path)
    sys.exit(exit_code)
