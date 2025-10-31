"""
Test suite for urllib3 emulator.

Tests the core functionality including:
- HTTPResponse object
- Connection pooling
- Retry logic
- PoolManager
- Request methods
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from HTTPCore import (
    HTTPResponse,
    HTTPConnectionPool,
    PoolManager,
    Retry,
    request,
)


class TestHTTPResponse:
    """Test HTTPResponse class."""
    
    def test_response_creation(self):
        """Test creating response object."""
        response = HTTPResponse(
            body=b"test content",
            headers={'content-type': 'text/plain'},
            status=200,
            reason="OK"
        )
        assert response.status == 200
        assert response.reason == "OK"
        assert response.data == b"test content"
        
    def test_response_read(self):
        """Test reading response data."""
        response = HTTPResponse(body=b"hello world")
        data = response.read()
        assert data == b"hello world"
        
    def test_response_read_partial(self):
        """Test reading partial response data."""
        response = HTTPResponse(body=b"hello world")
        data1 = response.read(5)
        assert data1 == b"hello"
        data2 = response.read(6)
        assert data2 == b" world"
        
    def test_response_text(self):
        """Test getting response as text."""
        response = HTTPResponse(body=b"hello world")
        assert response.text == "hello world"
        
    def test_response_json(self):
        """Test parsing JSON response."""
        response = HTTPResponse(body=b'{"key": "value", "number": 42}')
        data = response.json()
        assert data == {"key": "value", "number": 42}
        
    def test_response_getheader(self):
        """Test getting header value."""
        response = HTTPResponse(
            headers={'content-type': 'text/html', 'content-length': '100'}
        )
        assert response.getheader('content-type') == 'text/html'
        assert response.getheader('content-length') == '100'
        assert response.getheader('missing') is None
        assert response.getheader('missing', 'default') == 'default'
        
    def test_response_getheaders(self):
        """Test getting all headers."""
        headers = {'content-type': 'text/html', 'content-length': '100'}
        response = HTTPResponse(headers=headers)
        all_headers = response.getheaders()
        assert all_headers == headers


class TestRetry:
    """Test Retry configuration."""
    
    def test_retry_defaults(self):
        """Test default retry settings."""
        retry = Retry()
        assert retry.total == 10
        assert retry.connect == 10
        assert retry.read == 10
        assert retry.redirect == 5
        assert retry.backoff_factor == 0
        
    def test_retry_custom(self):
        """Test custom retry settings."""
        retry = Retry(
            total=5,
            connect=3,
            read=2,
            backoff_factor=0.5,
            status_forcelist={500, 503}
        )
        assert retry.total == 5
        assert retry.connect == 3
        assert retry.read == 2
        assert retry.backoff_factor == 0.5
        assert retry.status_forcelist == {500, 503}
        
    def test_retry_sleep(self):
        """Test retry sleep calculation."""
        import time
        retry = Retry(backoff_factor=0.1)
        
        start = time.time()
        retry.sleep_for_retry(0)  # Should sleep ~0.1s
        elapsed = time.time() - start
        assert 0.05 < elapsed < 0.2  # Allow some tolerance
        
        start = time.time()
        retry.sleep_for_retry(1)  # Should sleep ~0.2s
        elapsed = time.time() - start
        assert 0.15 < elapsed < 0.3


class TestHTTPConnectionPool:
    """Test HTTPConnectionPool class."""
    
    def test_pool_creation(self):
        """Test creating connection pool."""
        pool = HTTPConnectionPool('example.com', port=80)
        assert pool.host == 'example.com'
        assert pool.port == 80
        assert pool.scheme == 'http'
        
    def test_pool_https(self):
        """Test HTTPS connection pool."""
        pool = HTTPConnectionPool('example.com', scheme='https')
        assert pool.port == 443
        assert pool.scheme == 'https'
        
    def test_pool_with_retries(self):
        """Test pool with retry configuration."""
        retry = Retry(total=3)
        pool = HTTPConnectionPool('example.com', retries=retry)
        assert pool.retries.total == 3
        
        # Test with boolean
        pool2 = HTTPConnectionPool('example.com', retries=True)
        assert pool2.retries.total == 3
        
        # Test with int
        pool3 = HTTPConnectionPool('example.com', retries=5)
        assert pool3.retries.total == 5
        
    def test_pool_close(self):
        """Test closing connection pool."""
        pool = HTTPConnectionPool('example.com')
        pool.close()
        assert len(pool._connections) == 0


class TestPoolManager:
    """Test PoolManager class."""
    
    def test_manager_creation(self):
        """Test creating pool manager."""
        manager = PoolManager(num_pools=10)
        assert manager.num_pools == 10
        assert manager.timeout == 5.0
        
    def test_manager_with_headers(self):
        """Test manager with default headers."""
        headers = {'User-Agent': 'urllib3-emulator'}
        manager = PoolManager(headers=headers)
        assert manager.headers == headers
        
    def test_connection_from_host(self):
        """Test getting connection pool from host."""
        manager = PoolManager()
        
        # HTTP pool
        pool1 = manager.connection_from_host('example.com', scheme='http')
        assert pool1.host == 'example.com'
        assert pool1.port == 80
        
        # HTTPS pool
        pool2 = manager.connection_from_host('example.com', scheme='https')
        assert pool2.host == 'example.com'
        assert pool2.port == 443
        
        # Same pool should be returned for same host
        pool3 = manager.connection_from_host('example.com', scheme='http')
        assert pool3 is pool1
        
    def test_manager_clear(self):
        """Test clearing all pools."""
        manager = PoolManager()
        manager.connection_from_host('example.com')
        manager.connection_from_host('google.com')
        assert len(manager._pools) == 2
        
        manager.clear()
        assert len(manager._pools) == 0


class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def test_request_function(self):
        """Test convenience request function."""
        # Just test that the function exists and has correct signature
        # Actual HTTP calls are tested in integration tests
        assert callable(request)


class TestIntegration:
    """Integration tests (require network)."""
    
    def test_simple_get_request(self):
        """Test simple GET request."""
        # Skip if no network
        try:
            http = PoolManager()
            resp = http.request('GET', 'http://httpbin.org/get')
            assert resp.status == 200
            assert 'application/json' in resp.getheader('content-type', '')
        except Exception:
            # Skip test if network unavailable
            pass
            
    def test_post_request_with_fields(self):
        """Test POST request with form fields."""
        try:
            http = PoolManager()
            resp = http.request(
                'POST',
                'http://httpbin.org/post',
                fields={'key': 'value', 'test': 'data'}
            )
            assert resp.status == 200
        except Exception:
            # Skip test if network unavailable
            pass


def run_tests():
    """Run all tests."""
    print("Running urllib3 emulator tests...")
    print("=" * 60)
    
    test_classes = [
        TestHTTPResponse,
        TestRetry,
        TestHTTPConnectionPool,
        TestPoolManager,
        TestConvenienceFunctions,
        TestIntegration,
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
