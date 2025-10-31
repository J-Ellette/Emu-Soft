#!/usr/bin/env python3
"""
Demo script showing the new emulators in action
"""

import tempfile
import os

def demo_mypy():
    """Demonstrate MyPy emulator"""
    print("=" * 60)
    print("TypeChecker (MyPy) Emulator Demo - Type Checking")
    print("=" * 60)
    
    from TypeChecker.TypeChecker import MypyEmulator
    
    # Create a test file with type errors
    code = """
# Good type annotations
x: int = 5
y: str = "hello"

def add(a: int, b: int) -> int:
    return a + b

# Type error - wrong assignment
z: int = "this is wrong"

result = add(1, 2)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        emulator = MypyEmulator(strict=False, verbose=True)
        results = emulator.check_files([temp_file])
        report = emulator.generate_report(results)
        
        print(f"\nType Checking Summary:")
        print(f"  Files checked: {report['total_files']}")
        print(f"  Errors found: {report['total_errors']}")
        print(f"  Warnings: {report['total_warnings']}")
    finally:
        os.unlink(temp_file)
    
    print()


def demo_flake8():
    """Demonstrate Flake8 emulator"""
    print("=" * 60)
    print("CodeLinter (Flake8) Emulator Demo - Linting")
    print("=" * 60)
    
    from CodeLinter.CodeLinter import Flake8Emulator
    
    # Create a test file with linting issues
    code = """
import os
import sys

def bad_function(  ):  # E201 - whitespace after (
    unused_var = 42
    this_is_a_very_long_line_that_exceeds_the_maximum_allowed_length_of_79_characters = 1
    return 0

x = 1   
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        emulator = Flake8Emulator(verbose=True)
        results = emulator.check_files([temp_file])
        report = emulator.generate_report(results)
        
        print(f"\nLinting Summary:")
        print(f"  Files checked: {report['total_files']}")
        print(f"  Total issues: {report['total_issues']}")
        print(f"  Errors: {report['total_errors']}")
        print(f"  Warnings: {report['total_warnings']}")
    finally:
        os.unlink(temp_file)
    
    print()


def demo_uvicorn():
    """Demonstrate Uvicorn emulator components"""
    print("=" * 60)
    print("ASGIServer (Uvicorn) Emulator Demo - ASGI Server")
    print("=" * 60)
    
    from ASGIServer.ASGIServer import ASGIRequest, ASGIResponse
    
    # Demo request parsing
    raw_request = b"GET /api/users?limit=10 HTTP/1.1\r\nHost: localhost:8000\r\n\r\n"
    request = ASGIRequest(raw_request, ('127.0.0.1', 12345))
    
    print(f"\nRequest Parsing:")
    print(f"  Method: {request.method}")
    print(f"  Path: {request.path}")
    print(f"  Query: {request.query_string.decode('utf-8')}")
    
    # Demo response building
    response = ASGIResponse()
    response.add_start_event({
        'status': 200,
        'headers': [(b'content-type', b'application/json')]
    })
    response.add_body_event({
        'body': b'{"message": "Hello from ASGI!"}'
    })
    
    print(f"\nResponse Building:")
    print(f"  Status Code: {response.status_code}")
    print(f"  Body: {response.body.decode('utf-8')}")
    
    print(f"\nTo run ASGI server:")
    print(f"  python ASGIServer.py main:app")
    print(f"  python ASGIServer.py main:app --reload")
    print()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("EMU-SOFT New Emulators Demo")
    print("="*60 + "\n")
    
    demo_mypy()
    demo_flake8()
    demo_uvicorn()
    
    print("="*60)
    print("Demo Complete!")
    print("="*60)
