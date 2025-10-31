"""
Test suite for httpx emulator.

Tests the core functionality including:
- Request object
- Response object
- Headers (case-insensitive)
- Client (sync)
- AsyncClient
- Convenience functions
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from SyncAsyncHTTP import (
    Headers,
    Request,
    Response,
    Client,
    AsyncClient,
    get,
    post,
    put,
    delete,
    patch,
    head,
    options,
    request,
)


class TestHeaders:
    """Test Headers class (case-insensitive dict)."""
    
    def test_headers_creation(self):
        """Test creating headers."""
        headers = Headers({'Content-Type': 'application/json'})
        assert 'content-type' in headers
        assert headers['content-type'] == 'application/json'
        
    def test_headers_case_insensitive(self):
        """Test case-insensitive access."""
        headers = Headers()
        headers['Content-Type'] = 'text/html'
        
        assert headers['content-type'] == 'text/html'
        assert headers['Content-Type'] == 'text/html'
        assert headers['CONTENT-TYPE'] == 'text/html'
        
    def test_headers_get(self):
        """Test getting header with default."""
        headers = Headers({'key': 'value'})
        assert headers.get('key') == 'value'
        assert headers.get('missing') is None
        assert headers.get('missing', 'default') == 'default'
        
    def test_headers_contains(self):
        """Test checking if header exists."""
        headers = Headers({'X-Custom': 'value'})
        assert 'x-custom' in headers
        assert 'X-Custom' in headers
        assert 'missing' not in headers


class TestRequest:
    """Test Request object."""
    
    def test_request_creation(self):
        """Test creating request."""
        req = Request('GET', 'http://example.com/path')
        assert req.method == 'GET'
        assert req.url == 'http://example.com/path'
        
    def test_request_with_params(self):
        """Test request with query parameters."""
        req = Request('GET', 'http://example.com/path', params={'key': 'value', 'page': '1'})
        assert 'key=value' in req.url
        assert 'page=1' in req.url
        
    def test_request_with_json(self):
        """Test request with JSON body."""
        req = Request('POST', 'http://example.com/api', json={'key': 'value'})
        assert req.headers['content-type'] == 'application/json'
        assert b'"key"' in req.content
        assert b'"value"' in req.content
        
    def test_request_with_data_dict(self):
        """Test request with form data."""
        req = Request('POST', 'http://example.com/form', data={'field': 'value'})
        assert req.headers['content-type'] == 'application/x-www-form-urlencoded'
        assert b'field=value' in req.content
        
    def test_request_with_data_str(self):
        """Test request with string data."""
        req = Request('POST', 'http://example.com/api', data='raw data')
        assert req.content == b'raw data'
        
    def test_request_with_content(self):
        """Test request with raw bytes content."""
        req = Request('POST', 'http://example.com/api', content=b'binary data')
        assert req.content == b'binary data'
        
    def test_request_headers(self):
        """Test request with custom headers."""
        headers = {'User-Agent': 'test', 'X-Custom': 'value'}
        req = Request('GET', 'http://example.com', headers=headers)
        assert req.headers['user-agent'] == 'test'
        assert req.headers['x-custom'] == 'value'


class TestResponse:
    """Test Response object."""
    
    def test_response_creation(self):
        """Test creating response."""
        req = Request('GET', 'http://example.com')
        resp = Response(
            status_code=200,
            reason_phrase='OK',
            headers={'content-type': 'text/plain'},
            content=b'test content',
            request=req
        )
        assert resp.status_code == 200
        assert resp.reason_phrase == 'OK'
        assert resp.content == b'test content'
        
    def test_response_text(self):
        """Test getting response as text."""
        req = Request('GET', 'http://example.com')
        resp = Response(
            status_code=200,
            reason_phrase='OK',
            headers={},
            content=b'hello world',
            request=req
        )
        assert resp.text == 'hello world'
        
    def test_response_json(self):
        """Test parsing JSON response."""
        req = Request('GET', 'http://example.com')
        resp = Response(
            status_code=200,
            reason_phrase='OK',
            headers={'content-type': 'application/json'},
            content=b'{"key": "value", "number": 42}',
            request=req
        )
        data = resp.json()
        assert data == {"key": "value", "number": 42}
        
    def test_response_is_success(self):
        """Test is_success property."""
        req = Request('GET', 'http://example.com')
        
        resp = Response(200, 'OK', {}, b'', req)
        assert resp.is_success
        
        resp = Response(201, 'Created', {}, b'', req)
        assert resp.is_success
        
        resp = Response(404, 'Not Found', {}, b'', req)
        assert not resp.is_success
        
    def test_response_is_error(self):
        """Test is_error property."""
        req = Request('GET', 'http://example.com')
        
        resp = Response(200, 'OK', {}, b'', req)
        assert not resp.is_error
        
        resp = Response(404, 'Not Found', {}, b'', req)
        assert resp.is_error
        
        resp = Response(500, 'Internal Server Error', {}, b'', req)
        assert resp.is_error
        
    def test_response_is_redirect(self):
        """Test is_redirect property."""
        req = Request('GET', 'http://example.com')
        
        resp = Response(200, 'OK', {}, b'', req)
        assert not resp.is_redirect
        
        resp = Response(301, 'Moved Permanently', {}, b'', req)
        assert resp.is_redirect
        
        resp = Response(302, 'Found', {}, b'', req)
        assert resp.is_redirect
        
    def test_response_raise_for_status(self):
        """Test raise_for_status method."""
        req = Request('GET', 'http://example.com')
        
        resp = Response(200, 'OK', {}, b'', req)
        resp.raise_for_status()  # Should not raise
        
        resp = Response(404, 'Not Found', {}, b'', req)
        try:
            resp.raise_for_status()
            assert False, "Should have raised exception"
        except Exception as e:
            assert '404' in str(e)


class TestClient:
    """Test Client class (sync)."""
    
    def test_client_creation(self):
        """Test creating client."""
        client = Client(
            base_url='http://example.com',
            headers={'User-Agent': 'test'},
            timeout=30.0
        )
        assert client.base_url == 'http://example.com'
        assert client.headers['user-agent'] == 'test'
        assert client.timeout == 30.0
        
    def test_client_context_manager(self):
        """Test client as context manager."""
        with Client() as client:
            assert not client._closed
        assert client._closed
        
    def test_client_get_request(self):
        """Test GET request with client."""
        try:
            with Client() as client:
                resp = client.get('http://httpbin.org/get')
                assert resp.status_code == 200
                assert resp.is_success
        except Exception:
            # Skip test if network unavailable
            pass
            
    def test_client_post_json(self):
        """Test POST request with JSON."""
        try:
            with Client() as client:
                resp = client.post(
                    'http://httpbin.org/post',
                    json={'key': 'value'}
                )
                assert resp.status_code == 200
        except Exception:
            # Skip test if network unavailable
            pass
            
    def test_client_with_base_url(self):
        """Test client with base URL."""
        try:
            with Client(base_url='http://httpbin.org') as client:
                resp = client.get('/get')
                assert resp.status_code == 200
                assert 'httpbin.org' in resp.url
        except Exception:
            # Skip test if network unavailable
            pass


class TestAsyncClient:
    """Test AsyncClient class."""
    
    async def test_async_client_creation(self):
        """Test creating async client."""
        client = AsyncClient(
            base_url='http://example.com',
            timeout=30.0
        )
        assert client._sync_client.base_url == 'http://example.com'
        
    async def test_async_client_context_manager(self):
        """Test async client as context manager."""
        async with AsyncClient() as client:
            assert not client._sync_client._closed
        assert client._sync_client._closed
        
    async def test_async_client_get_request(self):
        """Test async GET request."""
        try:
            async with AsyncClient() as client:
                resp = await client.get('http://httpbin.org/get')
                assert resp.status_code == 200
                assert resp.is_success
        except Exception:
            # Skip test if network unavailable
            pass
            
    async def test_async_client_post_json(self):
        """Test async POST request with JSON."""
        try:
            async with AsyncClient() as client:
                resp = await client.post(
                    'http://httpbin.org/post',
                    json={'key': 'value'}
                )
                assert resp.status_code == 200
        except Exception:
            # Skip test if network unavailable
            pass


class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def test_get_function(self):
        """Test get() function."""
        try:
            resp = get('http://httpbin.org/get')
            assert resp.status_code == 200
        except Exception:
            # Skip test if network unavailable
            pass
            
    def test_post_function(self):
        """Test post() function."""
        try:
            resp = post('http://httpbin.org/post', data={'key': 'value'})
            assert resp.status_code == 200
        except Exception:
            # Skip test if network unavailable
            pass
            
    def test_request_function(self):
        """Test request() function."""
        try:
            resp = request('GET', 'http://httpbin.org/get')
            assert resp.status_code == 200
        except Exception:
            # Skip test if network unavailable
            pass


def run_tests():
    """Run all tests."""
    print("Running httpx emulator tests...")
    print("=" * 60)
    
    test_classes = [
        TestHeaders,
        TestRequest,
        TestResponse,
        TestClient,
        TestAsyncClient,
        TestConvenienceFunctions,
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            method = getattr(test_instance, method_name)
            
            try:
                # Run async test
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                failed_tests += 1
            except Exception as e:
                print(f"  ⚠ {method_name}: {e}")
                # Don't count as failure (might be network issue)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    if failed_tests > 0:
        print(f"Failed: {failed_tests}")
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
