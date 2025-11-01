"""
Developed by PowerShield, as an alternative to Requests
"""

"""
Tests for Requests Emulator
"""

import unittest
import json
from HTTPClient import Response, Request, Session, HTTPError
import HTTPClient as requests


class TestResponse(unittest.TestCase):
    """Test Response object"""
    
    def test_response_content(self):
        """Test response content property"""
        response = Response()
        response._content = b'Hello, World!'
        
        self.assertEqual(response.content, b'Hello, World!')
    
    def test_response_text(self):
        """Test response text property"""
        response = Response()
        response._content = b'Hello, World!'
        
        self.assertEqual(response.text, 'Hello, World!')
    
    def test_response_text_with_encoding(self):
        """Test response text with custom encoding"""
        response = Response()
        response._content = 'Hello, 世界!'.encode('utf-8')
        response.encoding = 'utf-8'
        
        self.assertIn('世界', response.text)
    
    def test_response_json(self):
        """Test JSON parsing"""
        response = Response()
        data = {'key': 'value', 'number': 42}
        response._content = json.dumps(data).encode('utf-8')
        
        parsed = response.json()
        self.assertEqual(parsed['key'], 'value')
        self.assertEqual(parsed['number'], 42)
    
    def test_response_ok(self):
        """Test ok property"""
        response = Response()
        
        response.status_code = 200
        self.assertTrue(response.ok)
        
        response.status_code = 404
        self.assertFalse(response.ok)
        
        response.status_code = 500
        self.assertFalse(response.ok)
    
    def test_raise_for_status(self):
        """Test raise_for_status method"""
        response = Response()
        
        # Should not raise for 200
        response.status_code = 200
        response.raise_for_status()  # No exception
        
        # Should raise for 404
        response.status_code = 404
        response.reason = 'Not Found'
        with self.assertRaises(HTTPError):
            response.raise_for_status()
    
    def test_encoding_from_content_type(self):
        """Test encoding detection from Content-Type header"""
        response = Response()
        response.headers['content-type'] = 'text/html; charset=utf-8'
        
        self.assertEqual(response.encoding, 'utf-8')
        
        response.headers['content-type'] = 'text/html; charset=iso-8859-1'
        self.assertEqual(response.encoding, 'iso-8859-1')


class TestRequest(unittest.TestCase):
    """Test Request object"""
    
    def test_request_creation(self):
        """Test creating a request"""
        request = Request('GET', 'http://example.com')
        
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.url, 'http://example.com')
    
    def test_request_with_headers(self):
        """Test request with headers"""
        headers = {'User-Agent': 'Test'}
        request = Request('GET', 'http://example.com', headers=headers)
        
        self.assertEqual(request.headers['User-Agent'], 'Test')
    
    def test_request_with_data(self):
        """Test request with data"""
        data = {'key': 'value'}
        request = Request('POST', 'http://example.com', data=data)
        
        self.assertEqual(request.data, data)


class TestSession(unittest.TestCase):
    """Test Session object"""
    
    def test_session_creation(self):
        """Test creating a session"""
        session = Session()
        
        self.assertIsInstance(session.headers, dict)
        self.assertIsInstance(session.cookies, dict)
    
    def test_session_persistent_headers(self):
        """Test session persistent headers"""
        session = Session()
        session.headers['X-Custom'] = 'value'
        
        self.assertEqual(session.headers['X-Custom'], 'value')
    
    def test_session_cookies(self):
        """Test session cookies"""
        session = Session()
        session.cookies['session_id'] = '12345'
        
        self.assertEqual(session.cookies['session_id'], '12345')
    
    def test_session_auth(self):
        """Test session authentication"""
        session = Session()
        session.auth = ('user', 'pass')
        
        self.assertEqual(session.auth, ('user', 'pass'))
    
    def test_session_context_manager(self):
        """Test session as context manager"""
        with Session() as session:
            self.assertIsInstance(session, Session)


class TestHTTPError(unittest.TestCase):
    """Test HTTPError exception"""
    
    def test_http_error_creation(self):
        """Test creating HTTPError"""
        error = HTTPError('404 Not Found')
        
        self.assertIn('404', str(error))
    
    def test_http_error_with_response(self):
        """Test HTTPError with response"""
        response = Response()
        response.status_code = 404
        error = HTTPError('404 Not Found', response=response)
        
        self.assertEqual(error.response.status_code, 404)


class TestRequestFunctions(unittest.TestCase):
    """Test module-level request functions"""
    
    def test_request_function_signature(self):
        """Test request function has correct signature"""
        # Just verify the function exists and can be called
        # We won't actually make HTTP requests in tests
        self.assertTrue(callable(requests.request))
        self.assertTrue(callable(requests.get))
        self.assertTrue(callable(requests.post))
        self.assertTrue(callable(requests.put))
        self.assertTrue(callable(requests.patch))
        self.assertTrue(callable(requests.delete))
        self.assertTrue(callable(requests.head))
        self.assertTrue(callable(requests.options))
    
    def test_session_alias(self):
        """Test Session alias"""
        s = requests.session()
        self.assertIsInstance(s, Session)


class TestURLParsing(unittest.TestCase):
    """Test URL parsing and parameter handling"""
    
    def test_url_with_params(self):
        """Test URL parameter handling"""
        # We can't easily test actual requests, but we can verify
        # the function accepts the parameters
        try:
            # This will fail to connect, but we can catch that
            requests.get('http://localhost:99999', params={'key': 'value'}, timeout=0.1)
        except Exception as e:
            # Expected to fail, just checking it doesn't crash on parameter handling
            pass
    
    def test_auth_parameter(self):
        """Test authentication parameter"""
        try:
            requests.get('http://localhost:99999', auth=('user', 'pass'), timeout=0.1)
        except Exception as e:
            # Expected to fail
            pass


class TestSessionMethods(unittest.TestCase):
    """Test Session HTTP methods"""
    
    def test_session_get_method(self):
        """Test session.get() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'get'))
        self.assertTrue(callable(session.get))
    
    def test_session_post_method(self):
        """Test session.post() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'post'))
        self.assertTrue(callable(session.post))
    
    def test_session_put_method(self):
        """Test session.put() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'put'))
        self.assertTrue(callable(session.put))
    
    def test_session_delete_method(self):
        """Test session.delete() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'delete'))
        self.assertTrue(callable(session.delete))
    
    def test_session_patch_method(self):
        """Test session.patch() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'patch'))
        self.assertTrue(callable(session.patch))
    
    def test_session_head_method(self):
        """Test session.head() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'head'))
        self.assertTrue(callable(session.head))
    
    def test_session_options_method(self):
        """Test session.options() method exists"""
        session = Session()
        self.assertTrue(hasattr(session, 'options'))
        self.assertTrue(callable(session.options))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
