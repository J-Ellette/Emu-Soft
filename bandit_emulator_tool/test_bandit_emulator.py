"""
Test suite for Bandit Emulator
"""

import unittest
import tempfile
import os
from pathlib import Path
from bandit_emulator import (
    BanditEmulator,
    Severity,
    Confidence,
    SecurityIssue,
    ScanResult
)


class TestBanditEmulator(unittest.TestCase):
    """Test cases for Bandit security scanner emulator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.emulator = BanditEmulator(verbose=False)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_file(self, filename: str, content: str) -> str:
        """Create a temporary test file"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_assert_usage_detection(self):
        """Test B101: Assert usage detection"""
        code = """
def test_function(x):
    assert x > 0, "x must be positive"
    return x * 2
"""
        file_path = self._create_test_file('test_assert.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B101']
        self.assertGreater(len(issues), 0, "Should detect assert usage")
        self.assertEqual(issues[0].severity, Severity.LOW)
    
    def test_exec_usage_detection(self):
        """Test B102: Exec usage detection"""
        code = """
user_input = "print('hello')"
exec(user_input)
"""
        file_path = self._create_test_file('test_exec.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B102']
        self.assertGreater(len(issues), 0, "Should detect exec usage")
        self.assertEqual(issues[0].severity, Severity.MEDIUM)
    
    def test_bad_file_permissions(self):
        """Test B103: Bad file permissions"""
        code = """
import os
os.chmod('/tmp/test', 0o777)
"""
        file_path = self._create_test_file('test_chmod.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B103']
        self.assertGreater(len(issues), 0, "Should detect bad file permissions")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_hardcoded_password_string(self):
        """Test B105: Hardcoded password string"""
        code = """
password = "mysecretpassword123"
db_password = "admin123"
"""
        file_path = self._create_test_file('test_password.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B105']
        self.assertGreater(len(issues), 0, "Should detect hardcoded passwords")
        self.assertEqual(issues[0].severity, Severity.LOW)
    
    def test_hardcoded_password_funcarg(self):
        """Test B106: Hardcoded password in function argument"""
        code = """
def connect_db():
    conn = connect(username='admin', password='password123')
    return conn
"""
        file_path = self._create_test_file('test_password_arg.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B106']
        self.assertGreater(len(issues), 0, "Should detect hardcoded password in argument")
    
    def test_flask_debug_true(self):
        """Test B201: Flask debug mode enabled"""
        code = """
from flask import Flask
app = Flask(__name__)
app.run(debug=True)
"""
        file_path = self._create_test_file('test_flask.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B201']
        self.assertGreater(len(issues), 0, "Should detect Flask debug=True")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_pickle_usage(self):
        """Test B301: Pickle usage"""
        code = """
import pickle
data = pickle.loads(user_input)
"""
        file_path = self._create_test_file('test_pickle.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B301']
        self.assertGreater(len(issues), 0, "Should detect pickle usage")
        self.assertEqual(issues[0].severity, Severity.MEDIUM)
    
    def test_marshal_usage(self):
        """Test B302: Marshal usage"""
        code = """
import marshal
data = marshal.loads(user_data)
"""
        file_path = self._create_test_file('test_marshal.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B302']
        self.assertGreater(len(issues), 0, "Should detect marshal usage")
    
    def test_md5_sha1_usage(self):
        """Test B303: MD5/SHA1 usage"""
        code = """
import hashlib
hash1 = hashlib.md5(data)
hash2 = hashlib.sha1(data)
"""
        file_path = self._create_test_file('test_hash.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B303']
        self.assertGreater(len(issues), 0, "Should detect insecure hash functions")
        self.assertEqual(issues[0].severity, Severity.MEDIUM)
    
    def test_tempfile_mktemp(self):
        """Test B306: Insecure tempfile usage"""
        code = """
import tempfile
temp = tempfile.mktemp()
"""
        file_path = self._create_test_file('test_tempfile.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B306']
        self.assertGreater(len(issues), 0, "Should detect insecure tempfile usage")
    
    def test_eval_usage(self):
        """Test B307: Eval usage"""
        code = """
user_code = input("Enter code: ")
result = eval(user_code)
"""
        file_path = self._create_test_file('test_eval.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B307']
        self.assertGreater(len(issues), 0, "Should detect eval usage")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_mark_safe_usage(self):
        """Test B308: mark_safe usage"""
        code = """
from django.utils.safestring import mark_safe
html = mark_safe(user_input)
"""
        file_path = self._create_test_file('test_mark_safe.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B308']
        self.assertGreater(len(issues), 0, "Should detect mark_safe usage")
    
    def test_telnetlib_import(self):
        """Test B401: Telnetlib import"""
        code = """
import telnetlib
tn = telnetlib.Telnet('example.com')
"""
        file_path = self._create_test_file('test_telnet.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B401']
        self.assertGreater(len(issues), 0, "Should detect telnetlib import")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_ftplib_import(self):
        """Test B402: FTPlib import"""
        code = """
import ftplib
ftp = ftplib.FTP('ftp.example.com')
"""
        file_path = self._create_test_file('test_ftp.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B402']
        self.assertGreater(len(issues), 0, "Should detect ftplib import")
    
    def test_request_without_cert_validation(self):
        """Test B501: Request with verify=False"""
        code = """
import requests
response = requests.get('https://example.com', verify=False)
"""
        file_path = self._create_test_file('test_verify.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B501']
        self.assertGreater(len(issues), 0, "Should detect verify=False")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_shell_true_detection(self):
        """Test B601: shell=True in subprocess"""
        code = """
import subprocess
subprocess.call(user_command, shell=True)
"""
        file_path = self._create_test_file('test_shell.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B601']
        self.assertGreater(len(issues), 0, "Should detect shell=True")
        self.assertEqual(issues[0].severity, Severity.HIGH)
    
    def test_sql_injection_detection(self):
        """Test B608: SQL injection"""
        code = """
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""
        file_path = self._create_test_file('test_sql.py', code)
        result = self.emulator.check_file(file_path)
        
        issues = [i for i in result.issues if i.test_id == 'B608']
        self.assertGreater(len(issues), 0, "Should detect SQL injection")
    
    def test_clean_file(self):
        """Test scanning a clean file with no issues"""
        code = """
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
"""
        file_path = self._create_test_file('test_clean.py', code)
        result = self.emulator.check_file(file_path)
        
        self.assertEqual(len(result.issues), 0, "Clean file should have no issues")
    
    def test_directory_scanning(self):
        """Test scanning multiple files in a directory"""
        # Create multiple test files
        self._create_test_file('file1.py', 'exec("test")')
        self._create_test_file('file2.py', 'eval("test")')
        self._create_test_file('file3.py', 'def clean(): pass')
        
        results = self.emulator.check_directory(self.temp_dir)
        
        self.assertEqual(len(results), 3, "Should scan all files")
        total_issues = sum(len(r.issues) for r in results)
        self.assertGreater(total_issues, 0, "Should find issues in directory")
    
    def test_report_generation(self):
        """Test report generation"""
        # Create test files with different issues
        self._create_test_file('file1.py', 'exec("test")')
        self._create_test_file('file2.py', 'eval("test")')
        
        results = self.emulator.check_directory(self.temp_dir)
        report = self.emulator.generate_report(results)
        
        self.assertIn('total_files', report)
        self.assertIn('total_issues', report)
        self.assertIn('severity_breakdown', report)
        self.assertIn('confidence_breakdown', report)
        self.assertGreater(report['total_issues'], 0)
    
    def test_multiple_issues_same_file(self):
        """Test file with multiple security issues"""
        code = """
exec(user_input)
eval(user_code)
password = "hardcoded123"
"""
        file_path = self._create_test_file('test_multiple.py', code)
        result = self.emulator.check_file(file_path)
        
        self.assertGreater(len(result.issues), 2, "Should detect multiple issues")
    
    def test_security_issue_attributes(self):
        """Test SecurityIssue attributes"""
        code = 'exec("test")'
        file_path = self._create_test_file('test_attrs.py', code)
        result = self.emulator.check_file(file_path)
        
        self.assertGreater(len(result.issues), 0)
        issue = result.issues[0]
        
        self.assertIsNotNone(issue.test_id)
        self.assertIsNotNone(issue.test_name)
        self.assertIsInstance(issue.severity, Severity)
        self.assertIsInstance(issue.confidence, Confidence)
        self.assertEqual(issue.file_path, file_path)
        self.assertGreater(issue.line_number, 0)
    
    def test_nonexistent_file(self):
        """Test scanning nonexistent file"""
        result = self.emulator.check_file('/nonexistent/file.py')
        self.assertEqual(len(result.issues), 0)
    
    def test_non_python_file(self):
        """Test scanning non-Python file"""
        file_path = self._create_test_file('test.txt', 'not python code')
        result = self.emulator.check_file(file_path)
        self.assertEqual(len(result.issues), 0)
    
    def test_syntax_error_file(self):
        """Test scanning file with syntax errors"""
        code = """
def broken_syntax(
    pass
"""
        file_path = self._create_test_file('test_syntax.py', code)
        result = self.emulator.check_file(file_path)
        # Should not crash, just return empty or partial results
        self.assertIsInstance(result, ScanResult)


class TestSecurityIssue(unittest.TestCase):
    """Test SecurityIssue class"""
    
    def test_security_issue_creation(self):
        """Test creating a SecurityIssue"""
        issue = SecurityIssue(
            test_id='B101',
            test_name='assert_used',
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            file_path='test.py',
            line_number=10,
            code='assert x > 0',
            message='Assert detected',
            cwe_id=703
        )
        
        self.assertEqual(issue.test_id, 'B101')
        self.assertEqual(issue.severity, Severity.LOW)
        self.assertEqual(issue.confidence, Confidence.HIGH)
        self.assertEqual(issue.cwe_id, 703)
    
    def test_security_issue_string_representation(self):
        """Test SecurityIssue __str__ method"""
        issue = SecurityIssue(
            test_id='B101',
            test_name='assert_used',
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            file_path='test.py',
            line_number=10,
            code='assert x > 0',
            message='Assert detected'
        )
        
        str_repr = str(issue)
        self.assertIn('test.py', str_repr)
        self.assertIn('10', str_repr)
        self.assertIn('B101', str_repr)
        self.assertIn('LOW', str_repr)


class TestScanResult(unittest.TestCase):
    """Test ScanResult class"""
    
    def test_scan_result_creation(self):
        """Test creating a ScanResult"""
        result = ScanResult(file_path='test.py')
        self.assertEqual(result.file_path, 'test.py')
        self.assertEqual(len(result.issues), 0)
    
    def test_adding_issues(self):
        """Test adding issues to ScanResult"""
        result = ScanResult(file_path='test.py')
        
        issue = SecurityIssue(
            test_id='B101',
            test_name='assert_used',
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            file_path='test.py',
            line_number=10,
            code='assert x > 0',
            message='Assert detected'
        )
        
        result.add_issue(issue)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].test_id, 'B101')


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    unittest.main()
