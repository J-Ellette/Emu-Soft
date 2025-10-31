"""
Developed by PowerShield, as an alternative to bandit


Bandit Emulator - Python Security Linter
Emulates Bandit functionality for security vulnerability detection in Python code
"""

import ast
import re
import hashlib
import json
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class Severity(Enum):
    """Security issue severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Confidence(Enum):
    """Confidence levels for security findings"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability finding"""
    test_id: str
    test_name: str
    severity: Severity
    confidence: Confidence
    file_path: str
    line_number: int
    code: str
    message: str
    cwe_id: Optional[int] = None
    
    def __str__(self):
        return (f"{self.file_path}:{self.line_number}: "
                f"[{self.severity.value}:{self.confidence.value}] "
                f"{self.test_id}: {self.message}")


@dataclass
class ScanResult:
    """Result of security scan"""
    file_path: str
    issues: List[SecurityIssue] = field(default_factory=list)
    lines_scanned: int = 0
    
    def add_issue(self, issue: SecurityIssue):
        """Add a security issue to the result"""
        self.issues.append(issue)


class BanditTest:
    """Base class for security tests"""
    
    def __init__(self, test_id: str, test_name: str):
        self.test_id = test_id
        self.test_name = test_name
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check a node for security issues"""
        return []


class B101_AssertUsedTest(BanditTest):
    """B101: Use of assert detected"""
    
    def __init__(self):
        super().__init__("B101", "assert_used")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for assert statements"""
        issues = []
        if isinstance(node, ast.Assert):
            issues.append(SecurityIssue(
                test_id=self.test_id,
                test_name=self.test_name,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                file_path=file_path,
                line_number=node.lineno,
                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                message="Use of assert detected. The enclosed code will be removed when compiling to optimised byte code.",
                cwe_id=703
            ))
        return issues


class B102_ExecUsedTest(BanditTest):
    """B102: Use of exec detected"""
    
    def __init__(self):
        super().__init__("B102", "exec_used")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for exec usage"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'exec':
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Use of exec detected. This is dangerous as it allows execution of arbitrary code.",
                    cwe_id=94
                ))
        return issues


class B103_SetBadFilePerm(BanditTest):
    """B103: chmod setting a permissive mask"""
    
    def __init__(self):
        super().__init__("B103", "set_bad_file_permissions")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for bad file permissions"""
        issues = []
        if isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Attribute) and 
                node.func.attr == 'chmod' and len(node.args) >= 2):
                # Check if permission is too open (e.g., 0o777)
                if isinstance(node.args[1], ast.Constant):
                    perm = node.args[1].value
                    if isinstance(perm, int) and perm >= 0o777:
                        issues.append(SecurityIssue(
                            test_id=self.test_id,
                            test_name=self.test_name,
                            severity=Severity.HIGH,
                            confidence=Confidence.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                            message=f"chmod setting a permissive mask {oct(perm)} on file.",
                            cwe_id=732
                        ))
        return issues


class B104_HardcodedBindAllInterfacesTest(BanditTest):
    """B104: Possible binding to all interfaces"""
    
    def __init__(self):
        super().__init__("B104", "hardcoded_bind_all_interfaces")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for binding to all network interfaces"""
        issues = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and 'host' in target.id.lower():
                    if isinstance(node.value, ast.Constant):
                        if node.value.value in ['0.0.0.0', '::']:
                            issues.append(SecurityIssue(
                                test_id=self.test_id,
                                test_name=self.test_name,
                                severity=Severity.MEDIUM,
                                confidence=Confidence.MEDIUM,
                                file_path=file_path,
                                line_number=node.lineno,
                                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                message=f"Possible binding to all interfaces. Consider binding to specific interface.",
                                cwe_id=605
                            ))
        return issues


class B105_HardcodedPasswordString(BanditTest):
    """B105: Possible hardcoded password"""
    
    def __init__(self):
        super().__init__("B105", "hardcoded_password_string")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for hardcoded passwords"""
        issues = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(keyword in var_name for keyword in ['password', 'passwd', 'pwd', 'secret', 'token']):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            if len(node.value.value) > 3:  # Ignore short values
                                issues.append(SecurityIssue(
                                    test_id=self.test_id,
                                    test_name=self.test_name,
                                    severity=Severity.LOW,
                                    confidence=Confidence.MEDIUM,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                    message="Possible hardcoded password detected.",
                                    cwe_id=259
                                ))
        return issues


class B106_HardcodedPasswordFuncArg(BanditTest):
    """B106: Hardcoded password in function call"""
    
    def __init__(self):
        super().__init__("B106", "hardcoded_password_funcarg")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for hardcoded passwords in function arguments"""
        issues = []
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg and any(pwd in keyword.arg.lower() for pwd in ['password', 'passwd', 'pwd']):
                    if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                        if len(keyword.value.value) > 3:
                            issues.append(SecurityIssue(
                                test_id=self.test_id,
                                test_name=self.test_name,
                                severity=Severity.LOW,
                                confidence=Confidence.MEDIUM,
                                file_path=file_path,
                                line_number=node.lineno,
                                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                message="Possible hardcoded password in function call.",
                                cwe_id=259
                            ))
        return issues


class B201_FlaskDebugTrue(BanditTest):
    """B201: Flask app run with debug=True"""
    
    def __init__(self):
        super().__init__("B201", "flask_debug_true")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for Flask debug mode enabled"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'run':
                for keyword in node.keywords:
                    if keyword.arg == 'debug':
                        if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            issues.append(SecurityIssue(
                                test_id=self.test_id,
                                test_name=self.test_name,
                                severity=Severity.HIGH,
                                confidence=Confidence.HIGH,
                                file_path=file_path,
                                line_number=node.lineno,
                                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                message="A Flask app appears to be run with debug=True, which exposes the Werkzeug debugger.",
                                cwe_id=489
                            ))
        return issues


class B301_PickleUsage(BanditTest):
    """B301: Use of pickle detected"""
    
    def __init__(self):
        super().__init__("B301", "pickle")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for pickle usage"""
        issues = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'pickle' in alias.name:
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message="Pickle library appears to be in use, possible security issue.",
                        cwe_id=502
                    ))
        elif isinstance(node, ast.ImportFrom):
            if node.module and 'pickle' in node.module:
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Pickle library appears to be in use, possible security issue.",
                    cwe_id=502
                ))
        return issues


class B302_MarshalUsage(BanditTest):
    """B302: Use of marshal detected"""
    
    def __init__(self):
        super().__init__("B302", "marshal")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for marshal usage"""
        issues = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'marshal' in alias.name:
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message="Deserialization with the marshal module is possibly dangerous.",
                        cwe_id=502
                    ))
        return issues


class B303_MD5SHA1Usage(BanditTest):
    """B303: Use of insecure MD5 or SHA1 hash function"""
    
    def __init__(self):
        super().__init__("B303", "md5_sha1")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for MD5/SHA1 usage"""
        issues = []
        if isinstance(node, ast.Call):
            # Check hashlib.md5() or hashlib.sha1()
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ['md5', 'sha1']:
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message=f"Use of insecure {node.func.attr.upper()} hash function detected.",
                        cwe_id=327
                    ))
        return issues


class B304_InsecureCipherUsage(BanditTest):
    """B304: Use of insecure cipher"""
    
    def __init__(self):
        super().__init__("B304", "insecure_cipher")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for insecure cipher usage"""
        issues = []
        insecure_ciphers = ['DES', 'RC4', 'Blowfish', 'ARC2', 'ARC4']
        
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if any(cipher in str(node.func.attr) for cipher in insecure_ciphers):
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message="Use of insecure cipher detected. Consider using AES.",
                        cwe_id=327
                    ))
        return issues


class B305_InsecureCipherMode(BanditTest):
    """B305: Use of insecure cipher mode"""
    
    def __init__(self):
        super().__init__("B305", "insecure_cipher_mode")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for insecure cipher modes"""
        issues = []
        if isinstance(node, ast.Attribute):
            if node.attr in ['MODE_ECB', 'ECB']:
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Use of insecure cipher mode ECB detected. Use CBC or GCM instead.",
                    cwe_id=327
                ))
        return issues


class B306_TempfileNotSecure(BanditTest):
    """B306: Use of insecure tempfile function"""
    
    def __init__(self):
        super().__init__("B306", "tempfile_mktemp")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for insecure tempfile usage"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'mktemp':
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Use of insecure tempfile.mktemp() detected. Use tempfile.mkstemp() instead.",
                    cwe_id=377
                ))
        return issues


class B307_EvalUsage(BanditTest):
    """B307: Use of eval detected"""
    
    def __init__(self):
        super().__init__("B307", "eval")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for eval usage"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Use of eval() detected. This is extremely dangerous.",
                    cwe_id=94
                ))
        return issues


class B308_MarkSafeUsage(BanditTest):
    """B308: Use of mark_safe on potentially untrusted input"""
    
    def __init__(self):
        super().__init__("B308", "mark_safe")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for mark_safe usage"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'mark_safe':
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message="Use of mark_safe() may expose XSS vulnerabilities.",
                    cwe_id=79
                ))
        return issues


class B401_ImportTelnetlib(BanditTest):
    """B401: Import of telnetlib"""
    
    def __init__(self):
        super().__init__("B401", "import_telnetlib")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for telnetlib import"""
        issues = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'telnetlib' in alias.name:
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message="Telnet is considered insecure. Use SSH instead.",
                        cwe_id=319
                    ))
        return issues


class B402_ImportFTPLib(BanditTest):
    """B402: Import of ftplib"""
    
    def __init__(self):
        super().__init__("B402", "import_ftplib")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for ftplib import"""
        issues = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'ftplib' in alias.name:
                    issues.append(SecurityIssue(
                        test_id=self.test_id,
                        test_name=self.test_name,
                        severity=Severity.HIGH,
                        confidence=Confidence.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                        message="FTP is considered insecure. Use SFTP or FTPS instead.",
                        cwe_id=319
                    ))
        return issues


class B501_RequestWithoutCertValidation(BanditTest):
    """B501: Request with verify=False"""
    
    def __init__(self):
        super().__init__("B501", "request_without_cert_validation")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for requests with disabled certificate validation"""
        issues = []
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == 'verify':
                    if isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                        issues.append(SecurityIssue(
                            test_id=self.test_id,
                            test_name=self.test_name,
                            severity=Severity.HIGH,
                            confidence=Confidence.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                            message="Request with verify=False disables SSL certificate verification.",
                            cwe_id=295
                        ))
        return issues


class B502_SSLWithBadVersion(BanditTest):
    """B502: SSL/TLS with insecure version"""
    
    def __init__(self):
        super().__init__("B502", "ssl_with_bad_version")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for insecure SSL/TLS versions"""
        issues = []
        insecure_versions = ['PROTOCOL_SSLv2', 'PROTOCOL_SSLv3', 'PROTOCOL_TLSv1', 'SSLv2', 'SSLv3', 'TLSv1']
        
        if isinstance(node, ast.Attribute):
            if node.attr in insecure_versions:
                issues.append(SecurityIssue(
                    test_id=self.test_id,
                    test_name=self.test_name,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=node.lineno,
                    code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                    message=f"Use of insecure SSL/TLS version {node.attr} detected. Use TLS 1.2 or higher.",
                    cwe_id=327
                ))
        return issues


class B601_ShellTrueParamEscape(BanditTest):
    """B601: Use of shell=True with user input"""
    
    def __init__(self):
        super().__init__("B601", "paramiko_calls")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for subprocess with shell=True"""
        issues = []
        if isinstance(node, ast.Call):
            # Check for subprocess calls with shell=True
            if isinstance(node.func, ast.Attribute) and node.func.attr in ['call', 'run', 'Popen']:
                for keyword in node.keywords:
                    if keyword.arg == 'shell':
                        if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            issues.append(SecurityIssue(
                                test_id=self.test_id,
                                test_name=self.test_name,
                                severity=Severity.HIGH,
                                confidence=Confidence.HIGH,
                                file_path=file_path,
                                line_number=node.lineno,
                                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                message="Use of shell=True can lead to shell injection vulnerabilities.",
                                cwe_id=78
                            ))
        return issues


class B602_SubprocessWithoutShellEquals(BanditTest):
    """B602: subprocess call with shell=True"""
    
    def __init__(self):
        super().__init__("B602", "subprocess_popen_with_shell_equals_true")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for Popen with shell=True"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'Popen':
                for keyword in node.keywords:
                    if keyword.arg == 'shell':
                        if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            issues.append(SecurityIssue(
                                test_id=self.test_id,
                                test_name=self.test_name,
                                severity=Severity.HIGH,
                                confidence=Confidence.HIGH,
                                file_path=file_path,
                                line_number=node.lineno,
                                code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                                message="subprocess.Popen with shell=True is dangerous.",
                                cwe_id=78
                            ))
        return issues


class B608_SQLInjection(BanditTest):
    """B608: Possible SQL injection"""
    
    def __init__(self):
        super().__init__("B608", "hardcoded_sql_expressions")
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for SQL injection vulnerabilities"""
        issues = []
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'execute':
                # Check if SQL query uses string formatting
                if node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.JoinedStr):  # f-string
                        issues.append(SecurityIssue(
                            test_id=self.test_id,
                            test_name=self.test_name,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                            message="Possible SQL injection via string formatting in query.",
                            cwe_id=89
                        ))
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):  # % formatting
                        issues.append(SecurityIssue(
                            test_id=self.test_id,
                            test_name=self.test_name,
                            severity=Severity.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            code=source_lines[node.lineno - 1].strip() if node.lineno <= len(source_lines) else "",
                            message="Possible SQL injection via % formatting in query.",
                            cwe_id=89
                        ))
        return issues


class BanditEmulator:
    """
    Main Bandit security scanner emulator.
    Scans Python code for common security vulnerabilities.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize Bandit emulator.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.tests = self._initialize_tests()
    
    def _initialize_tests(self) -> List[BanditTest]:
        """Initialize all security tests"""
        return [
            B101_AssertUsedTest(),
            B102_ExecUsedTest(),
            B103_SetBadFilePerm(),
            B104_HardcodedBindAllInterfacesTest(),
            B105_HardcodedPasswordString(),
            B106_HardcodedPasswordFuncArg(),
            B201_FlaskDebugTrue(),
            B301_PickleUsage(),
            B302_MarshalUsage(),
            B303_MD5SHA1Usage(),
            B304_InsecureCipherUsage(),
            B305_InsecureCipherMode(),
            B306_TempfileNotSecure(),
            B307_EvalUsage(),
            B308_MarkSafeUsage(),
            B401_ImportTelnetlib(),
            B402_ImportFTPLib(),
            B501_RequestWithoutCertValidation(),
            B502_SSLWithBadVersion(),
            B601_ShellTrueParamEscape(),
            B602_SubprocessWithoutShellEquals(),
            B608_SQLInjection(),
        ]
    
    def check_file(self, file_path: str) -> ScanResult:
        """
        Scan a single Python file for security issues.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            ScanResult with security issues found
        """
        path = Path(file_path)
        result = ScanResult(file_path=str(path))
        
        if not path.exists():
            return result
        
        if path.suffix != '.py':
            return result
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            source_lines = source_code.splitlines()
            result.lines_scanned = len(source_lines)
            
            # Parse AST
            try:
                tree = ast.parse(source_code, filename=str(path))
            except SyntaxError:
                return result
            
            # Run all tests on all AST nodes
            for node in ast.walk(tree):
                for test in self.tests:
                    issues = test.check(node, source_lines, str(path))
                    for issue in issues:
                        result.add_issue(issue)
            
            if self.verbose and result.issues:
                print(f"Found {len(result.issues)} issues in {path}")
            
        except Exception as e:
            if self.verbose:
                print(f"Error scanning {path}: {e}")
        
        return result
    
    def check_files(self, file_paths: List[str]) -> List[ScanResult]:
        """
        Scan multiple Python files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of ScanResult objects
        """
        results = []
        for file_path in file_paths:
            result = self.check_file(file_path)
            results.append(result)
        return results
    
    def check_directory(self, directory: str, pattern: str = "*.py") -> List[ScanResult]:
        """
        Scan all Python files in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern (default: "*.py")
            
        Returns:
            List of ScanResult objects
        """
        results = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return results
        
        for py_file in dir_path.rglob(pattern):
            if '__pycache__' in str(py_file):
                continue
            result = self.check_file(str(py_file))
            results.append(result)
        
        return results
    
    def generate_report(self, results: List[ScanResult]) -> Dict[str, Any]:
        """
        Generate summary report from scan results.
        
        Args:
            results: List of ScanResult objects
            
        Returns:
            Dictionary with summary statistics
        """
        total_issues = sum(len(r.issues) for r in results)
        files_with_issues = sum(1 for r in results if r.issues)
        total_files = len(results)
        
        severity_counts = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        confidence_counts = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        test_counts = {}
        
        for result in results:
            for issue in result.issues:
                severity_counts[issue.severity.value] += 1
                confidence_counts[issue.confidence.value] += 1
                test_counts[issue.test_id] = test_counts.get(issue.test_id, 0) + 1
        
        return {
            'total_files': total_files,
            'files_with_issues': files_with_issues,
            'clean_files': total_files - files_with_issues,
            'total_issues': total_issues,
            'severity_breakdown': severity_counts,
            'confidence_breakdown': confidence_counts,
            'test_breakdown': test_counts,
            'lines_scanned': sum(r.lines_scanned for r in results)
        }


def main():
    """Command-line interface for Bandit emulator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bandit_emulator.py <file_or_directory> [-v]")
        sys.exit(1)
    
    target = sys.argv[1]
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    emulator = BanditEmulator(verbose=verbose)
    
    path = Path(target)
    if path.is_file():
        results = [emulator.check_file(target)]
    elif path.is_dir():
        results = emulator.check_directory(target)
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)
    
    # Print results
    for result in results:
        if result.issues:
            print(f"\n{result.file_path}")
            print("-" * 80)
            for issue in result.issues:
                print(issue)
    
    # Print summary
    report = emulator.generate_report(results)
    print("\n" + "=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)
    print(f"Total files scanned: {report['total_files']}")
    print(f"Total issues found: {report['total_issues']}")
    print(f"Files with issues: {report['files_with_issues']}")
    print(f"Clean files: {report['clean_files']}")
    print(f"\nSeverity breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  {severity}: {count}")
    print(f"\nConfidence breakdown:")
    for confidence, count in report['confidence_breakdown'].items():
        print(f"  {confidence}: {count}")


if __name__ == '__main__':
    main()
