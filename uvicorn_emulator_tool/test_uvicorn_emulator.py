"""
Tests for Uvicorn Emulator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from uvicorn_emulator import ASGIRequest, ASGIResponse, FileWatcher
import tempfile
import asyncio
from pathlib import Path
import time


def test_request_parsing():
    """Test HTTP request parsing"""
    raw_request = b"GET /test?key=value HTTP/1.1\r\nHost: localhost\r\nUser-Agent: test\r\n\r\n"
    
    request = ASGIRequest(raw_request, ('127.0.0.1', 12345))
    
    assert request.method == "GET"
    assert request.path == "/test"
    assert request.query_string == b"key=value"
    assert "host" in request.headers
    assert request.headers["host"] == "localhost"
    
    print("✓ Request parsing works")


def test_request_to_asgi_scope():
    """Test conversion to ASGI scope"""
    raw_request = b"POST /api/data HTTP/1.1\r\nContent-Type: application/json\r\n\r\n"
    
    request = ASGIRequest(raw_request, ('127.0.0.1', 12345))
    scope = request.to_asgi_scope()
    
    assert scope['type'] == 'http'
    assert scope['method'] == 'POST'
    assert scope['path'] == '/api/data'
    assert 'headers' in scope
    
    print("✓ ASGI scope conversion works")


def test_response_building():
    """Test HTTP response building"""
    response = ASGIResponse()
    
    # Add start event
    response.add_start_event({
        'status': 200,
        'headers': [(b'content-type', b'text/plain')]
    })
    
    # Add body
    response.add_body_event({
        'body': b'Hello, World!'
    })
    
    http_response = response.to_http_response()
    
    assert b'HTTP/1.1 200 OK' in http_response
    assert b'content-type: text/plain' in http_response
    assert b'Hello, World!' in http_response
    
    print("✓ Response building works")


def test_file_watcher():
    """Test file watching for auto-reload"""
    # Create temp directory with a file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("# test")
        
        watcher = FileWatcher([tmpdir])
        
        # No changes initially
        assert not watcher.check_changes()
        
        # Modify file
        time.sleep(0.1)  # Ensure different mtime
        test_file.write_text("# modified")
        
        # Should detect change
        assert watcher.check_changes()
    
    print("✓ File watcher works")


def test_asgi_app_integration():
    """Test calling an ASGI app"""
    # Create a simple ASGI app
    async def simple_app(scope, receive, send):
        assert scope['type'] == 'http'
        
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/plain')],
        })
        
        await send({
            'type': 'http.response.body',
            'body': b'Hello from ASGI!',
        })
    
    # Test the integration
    async def run_test():
        from uvicorn_emulator import ASGIServer
        
        server = ASGIServer(simple_app, host='127.0.0.1', port=8001)
        
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'query_string': b'',
            'headers': [],
        }
        
        response = await server._call_asgi_app(scope, b'')
        
        assert response.status_code == 200
        assert response.body == b'Hello from ASGI!'
    
    asyncio.run(run_test())
    
    print("✓ ASGI app integration works")


def test_request_with_body():
    """Test request with POST body"""
    raw_request = (
        b"POST /api HTTP/1.1\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 13\r\n"
        b"\r\n"
        b'{"key":"value"}'
    )
    
    request = ASGIRequest(raw_request, ('127.0.0.1', 12345))
    
    assert request.method == "POST"
    assert request.body == b'{"key":"value"}'
    
    print("✓ Request with body parsing works")


def test_response_with_multiple_body_chunks():
    """Test response with multiple body chunks"""
    response = ASGIResponse()
    
    response.add_start_event({
        'status': 200,
        'headers': [(b'content-type', b'text/plain')]
    })
    
    # Add multiple body chunks
    response.add_body_event({'body': b'Hello, '})
    response.add_body_event({'body': b'World!'})
    
    http_response = response.to_http_response()
    
    assert b'Hello, World!' in http_response
    
    print("✓ Multiple body chunks work")


def test_query_string_parsing():
    """Test query string parsing"""
    raw_request = b"GET /search?q=python&limit=10 HTTP/1.1\r\n\r\n"
    
    request = ASGIRequest(raw_request, ('127.0.0.1', 12345))
    
    assert request.path == "/search"
    assert request.query_string == b"q=python&limit=10"
    
    print("✓ Query string parsing works")


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Uvicorn Emulator Tests")
    print("="*60)
    
    tests = [
        test_request_parsing,
        test_request_to_asgi_scope,
        test_response_building,
        test_file_watcher,
        test_asgi_app_integration,
        test_request_with_body,
        test_response_with_multiple_body_chunks,
        test_query_string_parsing,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("="*60)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
