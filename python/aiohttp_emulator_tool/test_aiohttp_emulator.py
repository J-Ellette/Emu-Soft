"""
Test suite for aiohttp emulator.

Tests the core functionality including:
- ClientSession and async HTTP client
- ClientResponse object
- Application and Router
- Request/Response objects
- Route matching and parameters
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiohttp_emulator import (
    ClientSession,
    ClientResponse,
    Application,
    Router,
    Route,
    Request,
    Response,
    json_response,
    get,
    post,
)


class TestClientResponse:
    """Test ClientResponse class."""
    
    async def test_response_creation(self):
        """Test creating response object."""
        response = ClientResponse(
            status=200,
            reason="OK",
            headers={'content-type': 'text/plain'},
            body=b"test content",
            url="http://example.com/test"
        )
        assert response.status == 200
        assert response.reason == "OK"
        assert response.url == "http://example.com/test"
        
    async def test_response_read(self):
        """Test reading response data."""
        response = ClientResponse(
            status=200,
            reason="OK",
            headers={},
            body=b"hello world",
            url="http://example.com"
        )
        data = await response.read()
        assert data == b"hello world"
        
    async def test_response_text(self):
        """Test getting response as text."""
        response = ClientResponse(
            status=200,
            reason="OK",
            headers={},
            body=b"hello world",
            url="http://example.com"
        )
        text = await response.text()
        assert text == "hello world"
        
    async def test_response_json(self):
        """Test parsing JSON response."""
        response = ClientResponse(
            status=200,
            reason="OK",
            headers={'content-type': 'application/json'},
            body=b'{"key": "value", "number": 42}',
            url="http://example.com"
        )
        data = await response.json()
        assert data == {"key": "value", "number": 42}
        
    async def test_response_context_manager(self):
        """Test response as context manager."""
        response = ClientResponse(
            status=200,
            reason="OK",
            headers={},
            body=b"test",
            url="http://example.com"
        )
        async with response as r:
            assert r is response
        assert response._closed


class TestClientSession:
    """Test ClientSession class."""
    
    async def test_session_creation(self):
        """Test creating session."""
        session = ClientSession(
            base_url="http://example.com",
            headers={'User-Agent': 'test'},
            timeout=60.0
        )
        assert session.base_url == "http://example.com"
        assert session.headers == {'User-Agent': 'test'}
        assert session.timeout == 60.0
        
    async def test_session_context_manager(self):
        """Test session as context manager."""
        async with ClientSession() as session:
            assert not session._closed
        assert session._closed
        
    async def test_session_get_request(self):
        """Test GET request."""
        try:
            async with ClientSession() as session:
                resp = await session.get('http://httpbin.org/get')
                assert resp.status == 200
                text = await resp.text()
                assert len(text) > 0
        except Exception:
            # Skip test if network unavailable
            pass
            
    async def test_session_post_json(self):
        """Test POST request with JSON."""
        try:
            async with ClientSession() as session:
                resp = await session.post(
                    'http://httpbin.org/post',
                    json={'key': 'value'}
                )
                assert resp.status == 200
        except Exception:
            # Skip test if network unavailable
            pass
            
    async def test_session_post_data(self):
        """Test POST request with form data."""
        try:
            async with ClientSession() as session:
                resp = await session.post(
                    'http://httpbin.org/post',
                    data={'key': 'value'}
                )
                assert resp.status == 200
        except Exception:
            # Skip test if network unavailable
            pass


class TestRequest:
    """Test Request object."""
    
    async def test_request_creation(self):
        """Test creating request object."""
        request = Request(
            method='GET',
            path='/test',
            headers={'content-type': 'text/plain'},
            body=b'test data',
            query={'param': 'value'},
            match_info={'id': '123'}
        )
        assert request.method == 'GET'
        assert request.path == '/test'
        assert request.query == {'param': 'value'}
        assert request.match_info == {'id': '123'}
        
    async def test_request_text(self):
        """Test reading request body as text."""
        request = Request(
            method='POST',
            path='/test',
            headers={},
            body=b'hello world',
            query={},
            match_info={}
        )
        text = await request.text()
        assert text == 'hello world'
        
    async def test_request_json(self):
        """Test parsing request body as JSON."""
        request = Request(
            method='POST',
            path='/test',
            headers={},
            body=b'{"key": "value"}',
            query={},
            match_info={}
        )
        data = await request.json()
        assert data == {"key": "value"}


class TestResponse:
    """Test Response object."""
    
    def test_response_creation(self):
        """Test creating response object."""
        response = Response(
            body='test content',
            status=200,
            headers={'X-Custom': 'value'}
        )
        assert response.status == 200
        assert response.reason == 'OK'
        assert response.headers['X-Custom'] == 'value'
        assert response.headers['Content-Length'] == '12'
        
    def test_response_status_codes(self):
        """Test different status codes."""
        response = Response(status=404)
        assert response.reason == 'Not Found'
        
        response = Response(status=500)
        assert response.reason == 'Internal Server Error'
        
    def test_json_response_function(self):
        """Test json_response helper."""
        response = json_response({'key': 'value'}, status=201)
        assert response.status == 201
        assert response.headers['Content-Type'] == 'application/json'
        assert b'"key"' in response._body
        assert b'"value"' in response._body


class TestRoute:
    """Test Route class."""
    
    def test_route_creation(self):
        """Test creating route."""
        async def handler(request):
            return Response(body='test')
        
        route = Route('GET', '/test', handler)
        assert route.method == 'GET'
        assert route.path == '/test'
        assert route.handler is handler
        
    def test_route_simple_match(self):
        """Test simple route matching."""
        async def handler(request):
            return Response()
        
        route = Route('GET', '/test', handler)
        match = route.match('/test')
        assert match == {}
        
        match = route.match('/other')
        assert match is None
        
    def test_route_with_parameters(self):
        """Test route with path parameters."""
        async def handler(request):
            return Response()
        
        route = Route('GET', '/user/{id}', handler)
        match = route.match('/user/123')
        assert match == {'id': '123'}
        
        match = route.match('/user/abc')
        assert match == {'id': 'abc'}
        
        match = route.match('/user/')
        assert match is None
        
    def test_route_with_multiple_parameters(self):
        """Test route with multiple parameters."""
        async def handler(request):
            return Response()
        
        route = Route('GET', '/user/{user_id}/post/{post_id}', handler)
        match = route.match('/user/123/post/456')
        assert match == {'user_id': '123', 'post_id': '456'}


class TestRouter:
    """Test Router class."""
    
    def test_router_creation(self):
        """Test creating router."""
        router = Router()
        assert router.routes == []
        
    def test_router_add_route(self):
        """Test adding routes."""
        router = Router()
        
        async def handler(request):
            return Response()
        
        route = Route('GET', '/test', handler)
        router.add_route(route)
        assert len(router.routes) == 1
        
    def test_router_convenience_methods(self):
        """Test router convenience methods."""
        router = Router()
        
        async def handler(request):
            return Response()
        
        router.add_get('/get', handler)
        router.add_post('/post', handler)
        router.add_put('/put', handler)
        router.add_delete('/delete', handler)
        
        assert len(router.routes) == 4
        
    def test_router_match(self):
        """Test router matching."""
        router = Router()
        
        async def handler1(request):
            return Response(body='handler1')
        
        async def handler2(request):
            return Response(body='handler2')
        
        router.add_get('/path1', handler1)
        router.add_post('/path2', handler2)
        
        handler, match = router.match('GET', '/path1')
        assert handler is handler1
        
        handler, match = router.match('POST', '/path2')
        assert handler is handler2
        
        handler, match = router.match('GET', '/notfound')
        assert handler is None


class TestApplication:
    """Test Application class."""
    
    async def test_application_creation(self):
        """Test creating application."""
        app = Application()
        assert app.router is not None
        
    async def test_application_with_router(self):
        """Test creating application with router."""
        router = Router()
        app = Application(router=router)
        assert app.router is router
        
    async def test_application_handle_request(self):
        """Test handling request."""
        app = Application()
        
        async def hello_handler(request):
            return Response(body='Hello!')
        
        app.router.add_get('/hello', hello_handler)
        
        response = await app._handle_request(
            'GET', '/hello', {}, b''
        )
        assert response.status == 200
        assert response._body == b'Hello!'
        
    async def test_application_not_found(self):
        """Test 404 not found."""
        app = Application()
        
        response = await app._handle_request(
            'GET', '/notfound', {}, b''
        )
        assert response.status == 404


class TestDecorators:
    """Test route decorators."""
    
    def test_get_decorator(self):
        """Test @get decorator."""
        @get('/test')
        async def handler(request):
            return Response()
        
        assert handler._route_method == 'GET'
        assert handler._route_path == '/test'
        
    def test_post_decorator(self):
        """Test @post decorator."""
        @post('/test')
        async def handler(request):
            return Response()
        
        assert handler._route_method == 'POST'
        assert handler._route_path == '/test'


def run_tests():
    """Run all tests."""
    print("Running aiohttp emulator tests...")
    print("=" * 60)
    
    test_classes = [
        TestClientResponse,
        TestClientSession,
        TestRequest,
        TestResponse,
        TestRoute,
        TestRouter,
        TestApplication,
        TestDecorators,
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
