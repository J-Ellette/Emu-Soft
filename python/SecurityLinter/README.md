# Bandit Emulator

A lightweight emulation of Bandit's Python security linting functionality for detecting common security vulnerabilities in Python code.

## Features

- **Security Scanning**: Detect common security issues and vulnerabilities
- **CWE Mapping**: Issues mapped to Common Weakness Enumeration (CWE) IDs
- **Severity Levels**: HIGH, MEDIUM, LOW severity classifications
- **Confidence Levels**: HIGH, MEDIUM, LOW confidence in findings
- **Multiple File Support**: Scan single files or entire directories
- **Comprehensive Tests**: 22+ security test rules implemented
- **AST-Based Analysis**: Deep code analysis using Python's AST module

## What It Emulates

This tool emulates core functionality of [Bandit](https://github.com/PyCQA/bandit), the popular Python security linter developed by the PyCQA project for finding common security issues in Python code.

### Security Tests Implemented

#### B1XX Series - Code Injection

- **B101**: Use of assert detected
- **B102**: Use of exec detected
- **B103**: chmod setting a permissive mask (0o777, etc.)
- **B104**: Possible binding to all network interfaces (0.0.0.0)
- **B105**: Possible hardcoded password string
- **B106**: Hardcoded password in function argument

#### B2XX Series - Application Configuration

- **B201**: Flask app run with debug=True

#### B3XX Series - Serialization & Cryptography

- **B301**: Use of pickle detected (deserialization vulnerability)
- **B302**: Use of marshal detected (deserialization vulnerability)
- **B303**: Use of insecure MD5 or SHA1 hash function
- **B304**: Use of insecure cipher (DES, RC4, Blowfish)
- **B305**: Use of insecure cipher mode (ECB)
- **B306**: Use of insecure tempfile.mktemp()
- **B307**: Use of eval() detected
- **B308**: Use of mark_safe() on potentially untrusted input

#### B4XX Series - Insecure Protocols

- **B401**: Import of telnetlib (insecure protocol)
- **B402**: Import of ftplib (insecure protocol)

#### B5XX Series - SSL/TLS Issues

- **B501**: Request with verify=False (disabled certificate validation)
- **B502**: SSL/TLS with insecure version (SSLv2, SSLv3, TLSv1)

#### B6XX Series - Injection Vulnerabilities

- **B601**: Use of shell=True with subprocess
- **B602**: subprocess.Popen with shell=True
- **B608**: Possible SQL injection via string formatting

## Usage

### As a Module

```python
from bandit_emulator import BanditEmulator

# Create emulator instance
emulator = BanditEmulator(verbose=True)

# Scan single file
result = emulator.check_file('my_script.py')
print(f"Found {len(result.issues)} issues")

for issue in result.issues:
    print(f"{issue.severity.value}: {issue.message} (Line {issue.line_number})")

# Scan multiple files
results = emulator.check_files(['file1.py', 'file2.py', 'file3.py'])

# Scan entire directory
results = emulator.check_directory('src/', pattern='*.py')

# Generate report
report = emulator.generate_report(results)
print(f"Total issues: {report['total_issues']}")
print(f"High severity: {report['severity_breakdown']['HIGH']}")
print(f"Medium severity: {report['severity_breakdown']['MEDIUM']}")
print(f"Low severity: {report['severity_breakdown']['LOW']}")
```

### Command Line

```bash
# Scan single file
python bandit_emulator.py script.py

# Scan directory
python bandit_emulator.py src/

# Verbose output
python bandit_emulator.py -v script.py
python bandit_emulator.py --verbose src/
```

## Examples

### Hardcoded Password Detection (B105)

```python
# Bad: Hardcoded password detected
password = "mysecretpassword123"
db_password = "admin123"

# Good: Password from environment or config
import os
password = os.environ.get('DB_PASSWORD')
```

### Exec/Eval Usage (B102, B307)

```python
# Bad: Dangerous code execution
user_input = input("Enter code: ")
exec(user_input)  # B102: HIGH severity
result = eval(user_input)  # B307: HIGH severity

# Good: Use safer alternatives
import ast
result = ast.literal_eval(user_input)  # Only evaluates literals
```

### Shell Injection (B601, B602)

```python
# Bad: Shell injection vulnerability
import subprocess
subprocess.call(user_command, shell=True)  # B601: HIGH severity

# Good: Use list of arguments without shell
subprocess.call(['ls', '-l', directory])
```

### SQL Injection (B608)

```python
# Bad: SQL injection via string formatting
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE name = '%s'" % user_name)

# Good: Use parameterized queries
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
cursor.execute("SELECT * FROM users WHERE name = %s", (user_name,))
```

### Insecure Deserialization (B301, B302)

```python
# Bad: Pickle can execute arbitrary code
import pickle
data = pickle.loads(untrusted_data)  # B301: MEDIUM severity

# Good: Use JSON for untrusted data
import json
data = json.loads(untrusted_data)
```

### Flask Debug Mode (B201)

```python
# Bad: Debug mode in production
from flask import Flask
app = Flask(__name__)
app.run(debug=True)  # B201: HIGH severity

# Good: Debug only in development
app.run(debug=False)  # or omit debug parameter
```

### Insecure Hash Functions (B303)

```python
# Bad: MD5 and SHA1 are cryptographically broken
import hashlib
hash1 = hashlib.md5(data)  # B303: MEDIUM severity
hash2 = hashlib.sha1(data)  # B303: MEDIUM severity

# Good: Use SHA256 or better
hash = hashlib.sha256(data)
hash = hashlib.sha512(data)
```

### SSL Certificate Validation (B501)

```python
# Bad: Disabled certificate verification
import requests
response = requests.get('https://example.com', verify=False)  # B501: HIGH

# Good: Verify certificates (default)
response = requests.get('https://example.com')
response = requests.get('https://example.com', verify=True)
```

### Insecure Protocols (B401, B402)

```python
# Bad: Telnet and FTP transmit credentials in plaintext
import telnetlib  # B401: HIGH severity
import ftplib     # B402: HIGH severity

# Good: Use secure alternatives
import paramiko  # SSH
import ftplib; ftp = ftplib.FTP_TLS()  # FTPS
```

## API Reference

### BanditEmulator

Main interface for security scanning.

**Constructor:**
- `verbose` (bool): Enable verbose output

**Methods:**
- `check_file(file_path: str) -> ScanResult`: Scan a single file
- `check_files(file_paths: List[str]) -> List[ScanResult]`: Scan multiple files
- `check_directory(directory: str, pattern: str = "*.py") -> List[ScanResult]`: Scan directory
- `generate_report(results: List[ScanResult]) -> Dict`: Generate summary report

### ScanResult

Result of scanning a file.

**Attributes:**
- `file_path` (str): Path to scanned file
- `issues` (List[SecurityIssue]): Security issues found
- `lines_scanned` (int): Number of lines scanned

**Methods:**
- `add_issue(issue: SecurityIssue)`: Add a security issue

### SecurityIssue

Represents a security vulnerability.

**Attributes:**
- `test_id` (str): Test identifier (e.g., "B101")
- `test_name` (str): Test name (e.g., "assert_used")
- `severity` (Severity): Severity level (HIGH, MEDIUM, LOW)
- `confidence` (Confidence): Confidence level (HIGH, MEDIUM, LOW)
- `file_path` (str): File containing the issue
- `line_number` (int): Line number
- `code` (str): Code snippet
- `message` (str): Issue description
- `cwe_id` (Optional[int]): CWE identifier

### Severity Enum

- `Severity.HIGH`: Critical security issues requiring immediate attention
- `Severity.MEDIUM`: Moderate security issues that should be addressed
- `Severity.LOW`: Minor security issues or best practice violations

### Confidence Enum

- `Confidence.HIGH`: High confidence in finding (true positive)
- `Confidence.MEDIUM`: Medium confidence (may be false positive)
- `Confidence.LOW`: Low confidence (likely requires review)

## Security Test Categories

### Code Injection
Tests that detect arbitrary code execution vulnerabilities (exec, eval, assert).

### Application Configuration
Tests for dangerous application settings (Flask debug mode, binding to all interfaces).

### Serialization & Cryptography
Tests for insecure deserialization (pickle, marshal) and weak cryptography (MD5, SHA1, weak ciphers).

### Insecure Protocols
Tests for protocols that transmit data insecurely (Telnet, FTP).

### SSL/TLS Issues
Tests for disabled certificate validation and insecure SSL/TLS versions.

### Injection Vulnerabilities
Tests for command injection (shell=True) and SQL injection.

## Testing

Run the test suite:

```bash
python test_bandit_emulator.py
```

Tests cover:
- All 22 security test rules
- Directory scanning
- Report generation
- Multiple issues in same file
- Clean files (no issues)
- Error handling (syntax errors, non-Python files)
- SecurityIssue and ScanResult classes

## Complexity

**Implementation Complexity**: Medium-High

This emulator involves:
- AST parsing for code analysis
- Pattern recognition for security issues
- Understanding of security vulnerabilities
- CWE mapping and classification
- Severity and confidence assessment

The security scanner requires understanding common security vulnerabilities, Python's AST structure, and security best practices.

## Dependencies

- Python 3.7+ (uses built-in `ast` module)
- No external dependencies required

## Integration

Can be integrated into:
- Pre-commit hooks for security scanning
- CI/CD pipelines for continuous security testing
- IDE security linting tools
- Code review automation
- Security audits

## Limitations

This is an educational emulation with some limitations:

1. **Limited Rule Set**: Implements 22 common rules, while real Bandit has 100+ tests
2. **Simplified Analysis**: Some complex vulnerability patterns may not be detected
3. **No Plugins**: Doesn't support custom security tests or plugins
4. **No Config Files**: Doesn't read .bandit or setup.cfg configuration
5. **Context Awareness**: May have false positives without full context analysis

## Common Weakness Enumeration (CWE) Coverage

The emulator maps issues to CWE IDs for standardized vulnerability classification:

- **CWE-78**: OS Command Injection (shell=True)
- **CWE-79**: Cross-site Scripting (mark_safe)
- **CWE-89**: SQL Injection (string formatting in queries)
- **CWE-94**: Code Injection (exec, eval)
- **CWE-259**: Hard-coded Password
- **CWE-295**: Improper Certificate Validation
- **CWE-319**: Cleartext Transmission (Telnet, FTP)
- **CWE-327**: Use of Broken Crypto (MD5, SHA1, weak ciphers)
- **CWE-377**: Insecure Temporary File
- **CWE-489**: Active Debug Code
- **CWE-502**: Deserialization of Untrusted Data (pickle, marshal)
- **CWE-605**: Multiple Binds to Same Port
- **CWE-703**: Improper Check or Handling of Exceptional Conditions
- **CWE-732**: Incorrect Permission Assignment

## Best Practices

1. **Run Early**: Scan code during development, not just before deployment
2. **Review Results**: Not all findings are vulnerabilities; review each one
3. **Fix High Severity**: Prioritize HIGH severity issues first
4. **Understand Context**: Some warnings may be false positives in specific contexts
5. **Continuous Scanning**: Integrate into CI/CD for ongoing security checks

## License

Part of the Emu-Soft project - see main repository LICENSE.
