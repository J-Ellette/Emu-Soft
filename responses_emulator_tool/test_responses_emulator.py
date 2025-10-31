#!/usr/bin/env python3
"""
Tests for responses emulator
"""

import sys
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from responses_emulator_tool.responses_emulator import (
    RequestsMock, Response, activate, add, reset,
    GET, POST, PUT, PATCH, DELETE
)


def test_basic_response():
    """Test basic response creation."""
    print("Testing basic response...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    
    assert len(mock._responses) == 1
    response = mock._responses[0]
    assert response.method == 'GET'
    assert response.status == 200
    print("  ✓ Basic response creation works")


def test_response_matching():
    """Test URL matching."""
    print("Testing response matching...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    
    response = mock._responses[0]
    assert response.matches('GET', 'https://api.example.com/users') is True
    assert response.matches('POST', 'https://api.example.com/users') is False
    assert response.matches('GET', 'https://api.example.com/posts') is False
    print("  ✓ URL matching works")


def test_response_with_query_string():
    """Test query string handling."""
    print("Testing query string handling...")
    mock = RequestsMock()
    
    # Without match_querystring, should match base URL
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    response = mock._responses[0]
    assert response.matches('GET', 'https://api.example.com/users?page=1') is True
    
    # With match_querystring, should require exact match
    mock.reset()
    mock.add(method='GET', url='https://api.example.com/users?page=1', json={'users': []}, match_querystring=True)
    response = mock._responses[0]
    assert response.matches('GET', 'https://api.example.com/users?page=1') is True
    assert response.matches('GET', 'https://api.example.com/users?page=2') is False
    print("  ✓ Query string handling works")


def test_regex_url_matching():
    """Test regex URL matching."""
    print("Testing regex URL matching...")
    mock = RequestsMock()
    pattern = re.compile(r'https://api\.example\.com/users/\d+')
    mock.add(method='GET', url=pattern, json={'user': {'id': 1}})
    
    response = mock._responses[0]
    assert response.matches('GET', 'https://api.example.com/users/123') is True
    assert response.matches('GET', 'https://api.example.com/users/456') is True
    assert response.matches('GET', 'https://api.example.com/users/abc') is False
    print("  ✓ Regex URL matching works")


def test_json_response():
    """Test JSON response body."""
    print("Testing JSON response...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': [{'id': 1, 'name': 'John'}]})
    
    response = mock._responses[0]
    body = response.get_response()
    assert b'"users"' in body
    assert b'"name"' in body
    assert b'"John"' in body
    print("  ✓ JSON response works")


def test_text_response():
    """Test text response body."""
    print("Testing text response...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/text', body='Hello, World!')
    
    response = mock._responses[0]
    body = response.get_response()
    assert body == b'Hello, World!'
    print("  ✓ Text response works")


def test_status_codes():
    """Test different status codes."""
    print("Testing status codes...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/ok', status=200)
    mock.add(method='GET', url='https://api.example.com/created', status=201)
    mock.add(method='GET', url='https://api.example.com/notfound', status=404)
    mock.add(method='GET', url='https://api.example.com/error', status=500)
    
    assert mock._responses[0].status == 200
    assert mock._responses[1].status == 201
    assert mock._responses[2].status == 404
    assert mock._responses[3].status == 500
    print("  ✓ Status codes work")


def test_headers():
    """Test custom headers."""
    print("Testing headers...")
    mock = RequestsMock()
    mock.add(
        method='GET',
        url='https://api.example.com/users',
        json={'users': []},
        headers={'X-Custom-Header': 'value', 'X-Another': 'test'}
    )
    
    response = mock._responses[0]
    assert 'X-Custom-Header' in response.headers
    assert response.headers['X-Custom-Header'] == 'value'
    assert response.headers['Content-Type'] == 'application/json'
    print("  ✓ Headers work")


def test_callback_response():
    """Test callback-based responses."""
    print("Testing callback responses...")
    
    def custom_callback(request):
        return json.dumps({'method': request.method, 'url': request.url})
    
    import json
    mock = RequestsMock()
    mock.add_callback(method='GET', url='https://api.example.com/callback', callback=custom_callback)
    
    response = mock._responses[0]
    assert callable(response._body)
    print("  ✓ Callback responses work")


def test_multiple_methods():
    """Test different HTTP methods."""
    print("Testing multiple HTTP methods...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/resource', json={'method': 'GET'})
    mock.add(method='POST', url='https://api.example.com/resource', json={'method': 'POST'})
    mock.add(method='PUT', url='https://api.example.com/resource', json={'method': 'PUT'})
    mock.add(method='PATCH', url='https://api.example.com/resource', json={'method': 'PATCH'})
    mock.add(method='DELETE', url='https://api.example.com/resource', json={'method': 'DELETE'})
    
    assert len(mock._responses) == 5
    assert mock._responses[0].method == 'GET'
    assert mock._responses[1].method == 'POST'
    assert mock._responses[2].method == 'PUT'
    assert mock._responses[3].method == 'PATCH'
    assert mock._responses[4].method == 'DELETE'
    print("  ✓ Multiple HTTP methods work")


def test_reset():
    """Test resetting mocks."""
    print("Testing reset...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    mock.add(method='POST', url='https://api.example.com/users', json={'id': 1})
    
    assert len(mock._responses) == 2
    
    mock.reset()
    assert len(mock._responses) == 0
    assert len(mock.calls) == 0
    print("  ✓ Reset works")


def test_call_count():
    """Test tracking call count."""
    print("Testing call count...")
    mock = RequestsMock()
    response = mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    
    assert response.call_count == 0
    response.get_response()
    assert response.call_count == 1
    response.get_response()
    assert response.call_count == 2
    print("  ✓ Call count tracking works")


def test_context_manager():
    """Test context manager usage."""
    print("Testing context manager...")
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
    
    assert mock._is_started is False
    
    with mock:
        assert mock._is_started is True
    
    assert mock._is_started is False
    print("  ✓ Context manager works")


# Test with actual requests library if available
def test_with_requests_library():
    """Test integration with requests library."""
    print("Testing with requests library...")
    
    try:
        import requests
        
        mock = RequestsMock()
        mock.add(method='GET', url='https://api.example.com/users', json={'users': ['Alice', 'Bob']}, status=200)
        mock.add(method='POST', url='https://api.example.com/users', json={'id': 1, 'name': 'Charlie'}, status=201)
        
        with mock:
            # Test GET
            resp = requests.get('https://api.example.com/users')
            assert resp.status_code == 200
            data = resp.json()
            assert 'users' in data
            assert 'Alice' in data['users']
            
            # Test POST
            resp = requests.post('https://api.example.com/users', json={'name': 'Charlie'})
            assert resp.status_code == 201
            data = resp.json()
            assert data['id'] == 1
            assert data['name'] == 'Charlie'
            
            # Test calls were recorded
            assert len(mock.calls) == 2
            assert mock.calls[0].request.method == 'GET'
            assert mock.calls[1].request.method == 'POST'
        
        print("  ✓ Integration with requests library works")
        return True
        
    except ImportError:
        print("  ⊘ requests library not available, skipping")
        return False


def test_decorator():
    """Test decorator usage."""
    print("Testing decorator...")
    
    try:
        import requests
        
        @activate
        def make_request():
            add(method='GET', url='https://api.example.com/test', json={'success': True})
            resp = requests.get('https://api.example.com/test')
            return resp.json()
        
        result = make_request()
        assert result['success'] is True
        print("  ✓ Decorator works")
        return True
        
    except ImportError:
        print("  ⊘ requests library not available, skipping")
        return False


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing responses Emulator")
    print("=" * 60)
    
    tests = [
        test_basic_response,
        test_response_matching,
        test_response_with_query_string,
        test_regex_url_matching,
        test_json_response,
        test_text_response,
        test_status_codes,
        test_headers,
        test_callback_response,
        test_multiple_methods,
        test_reset,
        test_call_count,
        test_context_manager,
        test_with_requests_library,
        test_decorator,
    ]
    
    passed = 0
    skipped = 0
    
    for test in tests:
        try:
            result = test()
            if result is False:
                skipped += 1
            else:
                passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            raise
        except Exception as e:
            print(f"  ✗ {test.__name__} error: {e}")
            raise
    
    print("\n" + "=" * 60)
    print(f"✓ {passed} TESTS PASSED")
    if skipped > 0:
        print(f"⊘ {skipped} TESTS SKIPPED (requests library not available)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
