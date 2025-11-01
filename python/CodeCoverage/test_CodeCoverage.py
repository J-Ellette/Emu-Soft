"""
Developed by PowerShield, as an alternative to coverage
"""

"""
Comprehensive tests for coverage emulator functionality.
Tests line coverage tracking, branch coverage, and reporting.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_tools.coverage_emulator import (
    Coverage,
    CoverageData,
    CoverageAnalyzer,
    CoverageTracer,
    FileCoverage,
    LineCoverage,
)


def test_basic_coverage_initialization():
    """Test basic coverage initialization."""
    cov = Coverage()
    assert cov is not None
    assert cov.data is not None
    assert cov.tracer is not None
    print("✓ Basic coverage initialization works")


def test_line_coverage_tracking():
    """Test that line coverage tracks execution."""
    # Create a simple file to test coverage
    test_code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

result = add(2, 3)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        cov = Coverage()
        cov.start()
        
        # Execute the code
        with open(temp_file, 'r') as f:
            code = compile(f.read(), temp_file, 'exec')
            exec(code)
        
        cov.stop()
        
        # Check that some coverage was recorded
        assert len(cov.data.files) > 0
        print("✓ Line coverage tracking works")
        
    finally:
        os.unlink(temp_file)


def test_coverage_percentage_calculation():
    """Test coverage percentage calculation."""
    file_cov = FileCoverage(filename="test.py")
    
    # Add executable lines
    file_cov.add_line(1)
    file_cov.add_line(2)
    file_cov.add_line(3)
    file_cov.add_line(4)
    
    # Mark some as executed
    file_cov.mark_executed(1)
    file_cov.mark_executed(2)
    
    percentage = file_cov.get_coverage_percentage()
    assert percentage == 50.0
    print("✓ Coverage percentage calculation works")


def test_missed_lines_tracking():
    """Test missed lines tracking."""
    file_cov = FileCoverage(filename="test.py")
    
    file_cov.add_line(1)
    file_cov.add_line(2)
    file_cov.add_line(3)
    
    file_cov.mark_executed(1)
    file_cov.mark_executed(3)
    
    missed = file_cov.get_missed_lines()
    assert missed == [2]
    print("✓ Missed lines tracking works")


def test_executed_lines_tracking():
    """Test executed lines tracking."""
    file_cov = FileCoverage(filename="test.py")
    
    file_cov.add_line(1)
    file_cov.add_line(2)
    file_cov.add_line(3)
    
    file_cov.mark_executed(1)
    file_cov.mark_executed(2)
    
    executed = file_cov.get_executed_lines()
    assert executed == [1, 2]
    print("✓ Executed lines tracking works")


def test_coverage_analyzer():
    """Test AST-based coverage analyzer."""
    test_code = """
def example():
    x = 1
    y = 2
    return x + y

if True:
    pass
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        executable_lines, branch_points = CoverageAnalyzer.analyze_file(temp_file)
        
        assert len(executable_lines) > 0
        assert len(branch_points) > 0  # Should detect the 'if' statement
        print("✓ Coverage analyzer works")
        
    finally:
        os.unlink(temp_file)


def test_coverage_data_summary():
    """Test coverage data summary generation."""
    data = CoverageData()
    
    # Add file coverage
    file_cov = FileCoverage(filename="test.py")
    file_cov.add_line(1)
    file_cov.add_line(2)
    file_cov.add_line(3)
    file_cov.mark_executed(1)
    file_cov.mark_executed(2)
    
    data.files["test.py"] = file_cov
    
    summary = data.get_summary()
    
    assert summary['total_files'] == 1
    assert summary['total_lines'] == 3
    assert summary['executed_lines'] == 2
    assert summary['missed_lines'] == 1
    assert summary['coverage_percentage'] > 0
    print("✓ Coverage data summary works")


def test_coverage_context_manager():
    """Test coverage as context manager."""
    with Coverage() as cov:
        # Execute some code
        x = 1 + 1
    
    # Coverage should have stopped automatically
    assert not cov.tracer.active
    print("✓ Coverage context manager works")


def test_should_trace_file():
    """Test file filtering for tracing."""
    data = CoverageData()
    
    # Should not trace standard library
    assert not data.should_trace_file('/usr/lib/python3/site-packages/module.py')
    
    # Should trace local files
    assert data.should_trace_file('/home/user/project/app.py')
    print("✓ File filtering for tracing works")


def test_coverage_omit_patterns():
    """Test omitting files by pattern."""
    cov = Coverage(omit=['test_*', '*_test.py'])
    
    # These should be omitted
    assert not cov.data.should_trace_file('/home/user/test_file.py')
    assert not cov.data.should_trace_file('/home/user/file_test.py')
    
    # This should not be omitted
    assert cov.data.should_trace_file('/home/user/app.py')
    print("✓ Coverage omit patterns work")


def test_coverage_include_patterns():
    """Test including only specific files."""
    cov = Coverage(include=['/home/user/project'])
    
    # Only files matching include pattern should be traced
    assert cov.data.should_trace_file('/home/user/project/app.py')
    assert not cov.data.should_trace_file('/home/other/app.py')
    print("✓ Coverage include patterns work")


def test_coverage_erase():
    """Test erasing coverage data."""
    cov = Coverage()
    
    # Add some data
    cov.data.files['test.py'] = FileCoverage(filename="test.py")
    assert len(cov.data.files) > 0
    
    # Erase
    cov.erase()
    assert len(cov.data.files) == 0
    print("✓ Coverage erase works")


def test_execution_count_tracking():
    """Test execution count tracking for lines."""
    file_cov = FileCoverage(filename="test.py")
    
    file_cov.add_line(1)
    file_cov.mark_executed(1)
    file_cov.mark_executed(1)
    file_cov.mark_executed(1)
    
    assert file_cov.lines[1].execution_count == 3
    print("✓ Execution count tracking works")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Testing coverage emulator functionality")
    print("="*70 + "\n")
    
    test_basic_coverage_initialization()
    test_line_coverage_tracking()
    test_coverage_percentage_calculation()
    test_missed_lines_tracking()
    test_executed_lines_tracking()
    test_coverage_analyzer()
    test_coverage_data_summary()
    test_coverage_context_manager()
    test_should_trace_file()
    test_coverage_omit_patterns()
    test_coverage_include_patterns()
    test_coverage_erase()
    test_execution_count_tracking()
    
    print("\n" + "="*70)
    print("✓ All coverage emulator tests passed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
