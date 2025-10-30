"""
Comprehensive tests for pytest emulator functionality.
Tests the test discovery, fixtures, and execution features.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_tools.pytest_emulator import (
    PyTestEmulator,
    fixture,
    skip,
    TestOutcome,
    FixtureDefinition,
    FixtureManager,
)


def test_basic_pytest_emulator():
    """Test basic pytest emulator initialization."""
    pytest_emu = PyTestEmulator()
    assert pytest_emu is not None
    assert pytest_emu.fixture_manager is not None
    assert pytest_emu.collector is not None
    assert pytest_emu.runner is not None
    print("✓ Basic pytest emulator initialization works")


def test_fixture_decorator():
    """Test fixture decorator functionality."""
    pytest_emu = PyTestEmulator()
    
    @pytest_emu.fixture
    def sample_fixture():
        return "fixture_value"
    
    assert hasattr(sample_fixture, '_pytest_fixture')
    assert sample_fixture._pytest_fixture.name == "sample_fixture"
    print("✓ Fixture decorator works")


def test_fixture_with_scope():
    """Test fixture with different scopes."""
    pytest_emu = PyTestEmulator()
    
    @pytest_emu.fixture(scope="module")
    def module_fixture():
        return "module_value"
    
    assert module_fixture._pytest_fixture.scope == "module"
    print("✓ Fixture with scope works")


def test_fixture_manager():
    """Test fixture manager functionality."""
    manager = FixtureManager()
    
    def simple_fixture():
        return 42
    
    fixture_def = FixtureDefinition(
        name="simple_fixture",
        func=simple_fixture,
        scope="function"
    )
    
    manager.register_fixture(fixture_def)
    value = manager.get_fixture_value("simple_fixture", "test_scope")
    
    assert value == 42
    print("✓ Fixture manager works")


def test_fixture_with_dependencies():
    """Test fixtures with dependencies."""
    manager = FixtureManager()
    
    def base_fixture():
        return 10
    
    def dependent_fixture(base_fixture):
        return base_fixture * 2
    
    base_def = FixtureDefinition(
        name="base_fixture",
        func=base_fixture,
        scope="function"
    )
    
    dep_def = FixtureDefinition(
        name="dependent_fixture",
        func=dependent_fixture,
        scope="function",
        dependencies=["base_fixture"]
    )
    
    manager.register_fixture(base_def)
    manager.register_fixture(dep_def)
    
    value = manager.get_fixture_value("dependent_fixture", "test_scope")
    assert value == 20
    print("✓ Fixture dependencies work")


def test_test_collection_from_module():
    """Test collecting tests from a module."""
    pytest_emu = PyTestEmulator()
    
    # Create a simple test module in memory
    import types
    test_module = types.ModuleType("test_module")
    test_module.__name__ = "test_module"
    
    def test_example():
        assert True
    
    test_module.test_example = test_example
    
    pytest_emu.collector.collect_from_module(test_module)
    
    assert len(pytest_emu.collector.collected_tests) == 1
    print("✓ Test collection from module works")


def test_test_runner_basic():
    """Test basic test runner functionality."""
    pytest_emu = PyTestEmulator()
    
    # Add a simple test
    def test_passing():
        assert 1 + 1 == 2
    
    pytest_emu.collector.collected_tests.append(
        (test_passing, "test_module::test_passing", [])
    )
    
    results = pytest_emu.runner.run_tests(pytest_emu.collector.collected_tests)
    
    assert len(results) == 1
    assert results[0].outcome == TestOutcome.PASSED
    print("✓ Test runner basic execution works")


def test_test_runner_failing_test():
    """Test runner with failing test."""
    pytest_emu = PyTestEmulator()
    
    def test_failing():
        assert 1 + 1 == 3
    
    pytest_emu.collector.collected_tests.append(
        (test_failing, "test_module::test_failing", [])
    )
    
    results = pytest_emu.runner.run_tests(pytest_emu.collector.collected_tests)
    
    assert len(results) == 1
    assert results[0].outcome == TestOutcome.FAILED
    assert results[0].error_message is not None
    print("✓ Test runner failing test works")


def test_test_runner_with_fixtures():
    """Test runner with fixture injection."""
    pytest_emu = PyTestEmulator()
    
    # Register a fixture
    def value_fixture():
        return 42
    
    fixture_def = FixtureDefinition(
        name="value_fixture",
        func=value_fixture,
        scope="function"
    )
    pytest_emu.fixture_manager.register_fixture(fixture_def)
    
    # Define test that uses fixture
    def test_with_fixture(value_fixture):
        assert value_fixture == 42
    
    pytest_emu.collector.collected_tests.append(
        (test_with_fixture, "test_module::test_with_fixture", ["value_fixture"])
    )
    
    results = pytest_emu.runner.run_tests(pytest_emu.collector.collected_tests)
    
    assert len(results) == 1
    assert results[0].outcome == TestOutcome.PASSED
    print("✓ Test runner with fixtures works")


def test_summary_generation():
    """Test test summary generation."""
    pytest_emu = PyTestEmulator()
    
    # Add various test results
    def test_pass1():
        assert True
    
    def test_pass2():
        assert True
    
    def test_fail():
        assert False
    
    pytest_emu.collector.collected_tests.extend([
        (test_pass1, "test::pass1", []),
        (test_pass2, "test::pass2", []),
        (test_fail, "test::fail", []),
    ])
    
    pytest_emu.runner.run_tests(pytest_emu.collector.collected_tests)
    summary = pytest_emu.runner.get_summary()
    
    assert summary['total'] == 3
    assert summary['passed'] == 2
    assert summary['failed'] == 1
    assert summary['success_rate'] > 0
    print("✓ Test summary generation works")


def test_global_fixture_decorator():
    """Test global fixture decorator."""
    @fixture
    def global_test_fixture():
        return "global_value"
    
    assert hasattr(global_test_fixture, '_pytest_fixture')
    print("✓ Global fixture decorator works")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Testing pytest emulator functionality")
    print("="*70 + "\n")
    
    test_basic_pytest_emulator()
    test_fixture_decorator()
    test_fixture_with_scope()
    test_fixture_manager()
    test_fixture_with_dependencies()
    test_test_collection_from_module()
    test_test_runner_basic()
    test_test_runner_failing_test()
    test_test_runner_with_fixtures()
    test_summary_generation()
    test_global_fixture_decorator()
    
    print("\n" + "="*70)
    print("✓ All pytest emulator tests passed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
