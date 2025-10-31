"""
Tests for Gunicorn Emulator
"""

import unittest
import io
from WSGIServer import WSGIRequest, WSGIResponse, GunicornEmulator


class TestWSGIRequest(unittest.TestCase):
    """Test WSGI request parsing"""
    
    def test_simple_get_request(self):
        """Test parsing a simple GET request"""
        raw = b"GET /hello HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.path, '/hello')
        self.assertEqual(request.query_string, '')
        self.assertEqual(request.headers['host'], 'localhost')
    
    def test_get_with_query_string(self):
        """Test parsing GET request with query string"""
        raw = b"GET /search?q=test&page=1 HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.path, '/search')
        self.assertEqual(request.query_string, 'q=test&page=1')
    
    def test_post_with_body(self):
        """Test parsing POST request with body"""
        body = b'{"key":"value"}'
        raw = b"POST /api HTTP/1.1\r\n"
        raw += b"Host: localhost\r\n"
        raw += b"Content-Type: application/json\r\n"
        raw += b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        raw += b"\r\n"
        raw += body
        
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.path, '/api')
        self.assertEqual(request.headers['content-type'], 'application/json')
        self.assertEqual(request.headers['content-length'], str(len(body)))
        self.assertEqual(request.body, body)
    
    def test_to_wsgi_environ(self):
        """Test conversion to WSGI environ"""
        raw = b"GET /path?q=test HTTP/1.1\r\n"
        raw += b"Host: example.com\r\n"
        raw += b"User-Agent: TestAgent\r\n"
        raw += b"\r\n"
        
        request = WSGIRequest(raw, ('192.168.1.1', 54321), ('127.0.0.1', 8000))
        environ = request.to_wsgi_environ()
        
        self.assertEqual(environ['REQUEST_METHOD'], 'GET')
        self.assertEqual(environ['PATH_INFO'], '/path')
        self.assertEqual(environ['QUERY_STRING'], 'q=test')
        self.assertEqual(environ['SERVER_NAME'], '127.0.0.1')
        self.assertEqual(environ['SERVER_PORT'], '8000')
        self.assertEqual(environ['REMOTE_ADDR'], '192.168.1.1')
        self.assertEqual(environ['HTTP_HOST'], 'example.com')
        self.assertEqual(environ['HTTP_USER_AGENT'], 'TestAgent')
        self.assertEqual(environ['wsgi.version'], (1, 0))
        self.assertIn('wsgi.input', environ)
    
    def test_wsgi_input_stream(self):
        """Test wsgi.input is a file-like object"""
        raw = b"POST /api HTTP/1.1\r\n"
        raw += b"Content-Length: 5\r\n"
        raw += b"\r\n"
        raw += b"hello"
        
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        environ = request.to_wsgi_environ()
        
        wsgi_input = environ['wsgi.input']
        self.assertIsInstance(wsgi_input, io.BytesIO)
        self.assertEqual(wsgi_input.read(), b'hello')


class TestWSGIResponse(unittest.TestCase):
    """Test WSGI response building"""
    
    def test_start_response(self):
        """Test start_response callable"""
        response = WSGIResponse()
        
        write = response.start_response(
            '200 OK',
            [('Content-Type', 'text/plain')]
        )
        
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.headers, [('Content-Type', 'text/plain')])
        self.assertIsNotNone(write)
    
    def test_write_method(self):
        """Test write method for response body"""
        response = WSGIResponse()
        response.start_response('200 OK', [])
        
        response.write(b'Hello, ')
        response.write(b'World!')
        
        self.assertEqual(response.body_parts, [b'Hello, ', b'World!'])
    
    def test_to_http_response(self):
        """Test conversion to HTTP response"""
        response = WSGIResponse()
        response.start_response(
            '200 OK',
            [
                ('Content-Type', 'text/html'),
                ('Content-Length', '12')
            ]
        )
        response.body_parts = [b'Hello, World!']
        
        http_response = response.to_http_response()
        
        self.assertIn(b'HTTP/1.1 200 OK', http_response)
        self.assertIn(b'Content-Type: text/html', http_response)
        self.assertIn(b'Content-Length: 12', http_response)
        self.assertIn(b'Hello, World!', http_response)
    
    def test_custom_status_code(self):
        """Test custom status codes"""
        response = WSGIResponse()
        response.start_response('404 Not Found', [])
        
        http_response = response.to_http_response()
        self.assertIn(b'HTTP/1.1 404 Not Found', http_response)


class TestWSGIApplication(unittest.TestCase):
    """Test WSGI application integration"""
    
    def test_simple_wsgi_app(self):
        """Test a simple WSGI application"""
        def simple_app(environ, start_response):
            status = '200 OK'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b'Hello from WSGI!']
        
        # Simulate request
        raw = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        response = WSGIResponse()
        
        environ = request.to_wsgi_environ()
        result = simple_app(environ, response.start_response)
        
        # Collect response
        for data in result:
            response.body_parts.append(data)
        
        http_response = response.to_http_response()
        
        self.assertIn(b'200 OK', http_response)
        self.assertIn(b'text/plain', http_response)
        self.assertIn(b'Hello from WSGI!', http_response)
    
    def test_wsgi_app_with_environ(self):
        """Test WSGI app can access environ"""
        def app_with_environ(environ, start_response):
            path = environ.get('PATH_INFO', '/')
            method = environ.get('REQUEST_METHOD', 'GET')
            
            status = '200 OK'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            
            body = f"Method: {method}, Path: {path}"
            return [body.encode('utf-8')]
        
        # Simulate request
        raw = b"POST /api/users HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        response = WSGIResponse()
        
        environ = request.to_wsgi_environ()
        result = app_with_environ(environ, response.start_response)
        
        # Collect response
        for data in result:
            response.body_parts.append(data)
        
        http_response = response.to_http_response()
        
        self.assertIn(b'Method: POST, Path: /api/users', http_response)
    
    def test_wsgi_app_read_body(self):
        """Test WSGI app can read request body"""
        def app_read_body(environ, start_response):
            # Read body from wsgi.input
            wsgi_input = environ['wsgi.input']
            body = wsgi_input.read()
            
            status = '200 OK'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            
            return [b'Received: ' + body]
        
        # Simulate request with body
        raw = b"POST /echo HTTP/1.1\r\n"
        raw += b"Content-Length: 11\r\n"
        raw += b"\r\n"
        raw += b"test body!"
        
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        response = WSGIResponse()
        
        environ = request.to_wsgi_environ()
        result = app_read_body(environ, response.start_response)
        
        # Collect response
        for data in result:
            response.body_parts.append(data)
        
        http_response = response.to_http_response()
        
        self.assertIn(b'Received: test body!', http_response)


class TestGunicornEmulatorHelpers(unittest.TestCase):
    """Test helper functionality"""
    
    def test_url_decoding(self):
        """Test URL decoding in path"""
        raw = b"GET /hello%20world HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        environ = request.to_wsgi_environ()
        
        # PATH_INFO should be decoded
        self.assertEqual(environ['PATH_INFO'], '/hello world')
    
    def test_multiple_headers(self):
        """Test multiple headers"""
        raw = b"GET / HTTP/1.1\r\n"
        raw += b"Host: localhost\r\n"
        raw += b"Accept: text/html\r\n"
        raw += b"Accept-Encoding: gzip\r\n"
        raw += b"\r\n"
        
        request = WSGIRequest(raw, ('127.0.0.1', 12345), ('127.0.0.1', 8000))
        environ = request.to_wsgi_environ()
        
        self.assertEqual(environ['HTTP_HOST'], 'localhost')
        self.assertEqual(environ['HTTP_ACCEPT'], 'text/html')
        self.assertEqual(environ['HTTP_ACCEPT_ENCODING'], 'gzip')


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
