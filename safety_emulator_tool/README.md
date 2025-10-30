# Safety Emulator

A lightweight emulation of Safety's Python dependency vulnerability scanner functionality for checking Python packages for known security vulnerabilities.

## Features

- **Vulnerability Scanning**: Check dependencies for known security vulnerabilities
- **CVE Tracking**: Vulnerabilities mapped to CVE (Common Vulnerabilities and Exposures) IDs
- **Severity Classification**: CRITICAL, HIGH, MEDIUM, LOW severity levels
- **Requirements File Support**: Scan requirements.txt files
- **Package List Support**: Check specific package versions
- **Comprehensive Database**: Built-in vulnerability database with common Python packages
- **Extensible**: Load custom vulnerability databases from JSON files

## What It Emulates

This tool emulates core functionality of [Safety](https://github.com/pyupio/safety), the popular Python dependency vulnerability scanner developed by PyUp.io for checking Python dependencies against a database of known security vulnerabilities.

### Vulnerability Database

The emulator includes a curated database of known vulnerabilities for popular Python packages:

#### Covered Packages

- **Django** - Web framework
- **Flask** - Micro web framework
- **Requests** - HTTP library
- **urllib3** - HTTP client library
- **PyYAML** - YAML parser
- **Cryptography** - Cryptographic recipes
- **Pillow** - Image processing library
- **Jinja2** - Template engine
- **SQLAlchemy** - ORM and SQL toolkit
- **PyJWT** - JSON Web Token implementation
- **Werkzeug** - WSGI utility library
- **Certifi** - Root certificate bundle
- **NumPy** - Numerical computing
- **Setuptools** - Package installer
- **Tornado** - Async web framework

### Severity Levels

- **CRITICAL**: Vulnerabilities requiring immediate attention (e.g., arbitrary code execution)
- **HIGH**: Serious vulnerabilities that should be fixed promptly
- **MEDIUM**: Moderate vulnerabilities that should be addressed
- **LOW**: Minor vulnerabilities or informational findings

## Usage

### As a Module

```python
from safety_emulator import SafetyEmulator

# Create emulator instance
emulator = SafetyEmulator(verbose=True)

# Check requirements.txt file
result = emulator.check_requirements('requirements.txt')

if not result.is_safe:
    print(f"Found {result.total_vulnerabilities} vulnerabilities!")
    
    for pkg in result.vulnerable_packages:
        print(f"\n{pkg.package_name} {pkg.installed_version}")
        for vuln in pkg.vulnerabilities:
            print(f"  - {vuln.cve_id}: {vuln.advisory}")
            print(f"    Severity: {vuln.severity.value}")
            if vuln.fixed_in:
                print(f"    Fixed in: {vuln.fixed_in}")
else:
    print("All dependencies are safe!")

# Check specific packages
packages = [
    ('django', '2.2.0'),
    ('flask', '2.0.0'),
    ('requests', '2.31.0')
]
result = emulator.check_packages(packages)

# Generate report
report = emulator.generate_report(result)
print(f"Scanned: {report['scanned_packages']} packages")
print(f"Vulnerable: {report['vulnerable_packages']} packages")
print(f"Total vulnerabilities: {report['total_vulnerabilities']}")
print(f"Critical: {report['severity_breakdown']['CRITICAL']}")
print(f"High: {report['severity_breakdown']['HIGH']}")
```

### Command Line

```bash
# Check requirements.txt
python safety_emulator.py requirements.txt

# Alternative syntax
python safety_emulator.py check requirements.txt

# Verbose output
python safety_emulator.py -v requirements.txt
python safety_emulator.py --verbose requirements.txt
```

### Custom Vulnerability Database

```python
from safety_emulator import SafetyEmulator, VulnerabilityDatabase, Vulnerability, VulnerabilitySeverity

# Create custom database
db = VulnerabilityDatabase()

# Add custom vulnerability
custom_vuln = Vulnerability(
    package_name='mypackage',
    vulnerable_spec='<2.0.0',
    cve_id='CVE-2023-99999',
    advisory='Custom security issue in mypackage',
    severity=VulnerabilitySeverity.HIGH,
    fixed_in='2.0.0'
)
db.add_vulnerability(custom_vuln)

# Use custom database
emulator = SafetyEmulator(db=db)
result = emulator.check_requirements('requirements.txt')

# Save database to file
db.save_to_file('custom_vulns.json')

# Load database from file
db2 = VulnerabilityDatabase()
db2.load_from_file('custom_vulns.json')
```

## Examples

### Vulnerable Django

```txt
# requirements.txt
django==2.2.0
```

**Output:**
```
django 2.2.0 (2 vulnerabilities)
  -> CVE-2022-28346 - HIGH: SQL injection in QuerySet.annotate(), aggregate(), and extra() Fixed in: 2.2.28
  -> CVE-2022-28347 - HIGH: SQL injection via QuerySet.explain() on PostgreSQL Fixed in: 3.2.13
```

### Vulnerable PyYAML (Critical)

```txt
# requirements.txt
pyyaml==5.3
```

**Output:**
```
pyyaml 5.3 (1 vulnerability)
  -> CVE-2020-14343 - CRITICAL: Arbitrary code execution via python/object/new constructor Fixed in: 5.4
```

### Multiple Vulnerabilities

```txt
# requirements.txt
django==2.2.0
flask==2.0.0
requests==2.30.0
urllib3==1.26.0
```

**Output:**
```
VULNERABILITIES FOUND
================================================================================

django 2.2.0 (2 vulnerabilities)
  -> CVE-2022-28346 - HIGH: SQL injection in QuerySet.annotate(), aggregate(), and extra() Fixed in: 2.2.28
  -> CVE-2022-28347 - HIGH: SQL injection via QuerySet.explain() on PostgreSQL Fixed in: 3.2.13

flask 2.0.0 (1 vulnerability)
  -> CVE-2023-30861 - HIGH: Cookie parsing vulnerability allowing session fixation Fixed in: 2.2.5

requests 2.30.0 (1 vulnerability)
  -> CVE-2023-32681 - MEDIUM: Unintended leak of Proxy-Authorization header Fixed in: 2.31.0

urllib3 1.26.0 (2 vulnerabilities)
  -> CVE-2021-33503 - HIGH: HTTP request smuggling due to header injection Fixed in: 1.26.5
  -> CVE-2023-43804 - MEDIUM: Cookie request header is not stripped on cross-origin redirects Fixed in: 1.26.17

SCAN SUMMARY
================================================================================
Packages scanned: 4
Vulnerable packages: 4
Total vulnerabilities: 6

Severity breakdown:
  HIGH: 5
  MEDIUM: 1
```

### Clean Dependencies

```txt
# requirements.txt
safepackage==1.0.0
anotherpackage==2.0.0
```

**Output:**
```
================================================================================
✓ All dependencies are safe!
================================================================================
```

## API Reference

### SafetyEmulator

Main interface for vulnerability scanning.

**Constructor:**
- `db` (Optional[VulnerabilityDatabase]): Custom vulnerability database (creates default if None)
- `verbose` (bool): Enable verbose output

**Methods:**
- `check_requirements(requirements_file: str) -> ScanResult`: Scan requirements.txt file
- `check_packages(packages: List[Tuple[str, str]]) -> ScanResult`: Check list of (name, version) tuples
- `generate_report(result: ScanResult) -> Dict`: Generate summary report

### VulnerabilityDatabase

Database of known vulnerabilities.

**Methods:**
- `get_vulnerabilities(package_name: str) -> List[Vulnerability]`: Get vulnerabilities for package
- `add_vulnerability(vuln: Vulnerability)`: Add vulnerability to database
- `load_from_file(file_path: str)`: Load vulnerabilities from JSON file
- `save_to_file(file_path: str)`: Save vulnerabilities to JSON file

### ScanResult

Result of vulnerability scan.

**Attributes:**
- `scanned_packages` (int): Number of packages scanned
- `vulnerable_packages` (List[InsecurePackage]): Packages with vulnerabilities
- `total_vulnerabilities` (int): Total vulnerability count
- `is_safe` (bool): True if no vulnerabilities found

**Methods:**
- `add_vulnerable_package(pkg: InsecurePackage)`: Add vulnerable package

### InsecurePackage

Package with known vulnerabilities.

**Attributes:**
- `package_name` (str): Package name
- `installed_version` (str): Installed version
- `vulnerabilities` (List[Vulnerability]): List of vulnerabilities

**Methods:**
- `add_vulnerability(vuln: Vulnerability)`: Add vulnerability

### Vulnerability

Known security vulnerability.

**Attributes:**
- `package_name` (str): Package name
- `vulnerable_spec` (str): Vulnerable version specification (e.g., "<2.0.0")
- `cve_id` (Optional[str]): CVE identifier
- `advisory` (str): Vulnerability description
- `severity` (VulnerabilitySeverity): Severity level
- `fixed_in` (Optional[str]): Version that fixes the vulnerability

### VulnerabilitySeverity Enum

- `VulnerabilitySeverity.CRITICAL`: Critical vulnerabilities
- `VulnerabilitySeverity.HIGH`: High severity vulnerabilities
- `VulnerabilitySeverity.MEDIUM`: Medium severity vulnerabilities
- `VulnerabilitySeverity.LOW`: Low severity vulnerabilities
- `VulnerabilitySeverity.UNKNOWN`: Unknown severity

## Supported Requirements File Formats

The emulator supports standard requirements.txt syntax:

```txt
# Comments are supported
package==1.0.0          # Exact version
package>=1.0.0          # Minimum version
package<=2.0.0          # Maximum version
package~=1.0.0          # Compatible version
package>1.0.0           # Greater than
package<2.0.0           # Less than
package!=1.5.0          # Excluded version
package                 # Any version (treated as potentially vulnerable)
package[extra]==1.0.0   # With extras (extras are ignored)
```

## Testing

Run the test suite:

```bash
python test_safety_emulator.py
```

Tests cover:
- Vulnerability detection for multiple packages
- Requirements file parsing
- Version comparison logic
- Report generation
- Database save/load functionality
- Edge cases (empty files, missing files, etc.)

## Complexity

**Implementation Complexity**: Medium

This emulator involves:
- Vulnerability database management
- Version comparison and specification matching
- Requirements file parsing
- CVE tracking and severity classification

The scanner requires understanding dependency management, version specifications, and vulnerability databases.

## Dependencies

- Python 3.7+ (uses built-in modules)
- No external dependencies required

## Integration

Can be integrated into:
- Pre-commit hooks for dependency scanning
- CI/CD pipelines for continuous security monitoring
- Dependency update workflows
- Security audit processes
- Automated vulnerability alerts

## Limitations

This is an educational emulation with some limitations:

1. **Limited Database**: Includes subset of common vulnerabilities; real Safety uses comprehensive PyUp.io database
2. **Simplified Version Matching**: Basic version comparison; real Safety has more sophisticated matching
3. **No Auto-Updates**: Database is static; real Safety updates from PyUp.io regularly
4. **No API Integration**: Doesn't connect to external vulnerability databases
5. **Basic Parsing**: Simple requirements.txt parsing; may not handle all edge cases

## Extending the Database

You can extend the vulnerability database by:

1. **Adding vulnerabilities programmatically:**
```python
from safety_emulator import VulnerabilityDatabase, Vulnerability, VulnerabilitySeverity

db = VulnerabilityDatabase()
db.add_vulnerability(Vulnerability(
    package_name='mypackage',
    vulnerable_spec='<1.5.0',
    cve_id='CVE-2023-12345',
    advisory='Description of vulnerability',
    severity=VulnerabilitySeverity.HIGH,
    fixed_in='1.5.0'
))
```

2. **Loading from JSON file:**
```json
{
  "mypackage": [
    {
      "vulnerable_spec": "<1.5.0",
      "cve_id": "CVE-2023-12345",
      "advisory": "Description of vulnerability",
      "severity": "HIGH",
      "fixed_in": "1.5.0"
    }
  ]
}
```

## Best Practices

1. **Scan Regularly**: Check dependencies on every update or at least weekly
2. **Prioritize by Severity**: Fix CRITICAL and HIGH severity issues first
3. **Update Dependencies**: Keep packages up to date with fixed versions
4. **Review Advisories**: Understand each vulnerability's impact on your application
5. **Continuous Monitoring**: Integrate into CI/CD for ongoing security checks
6. **Pin Versions**: Use exact versions in requirements.txt after validation

## Common Use Cases

### Pre-Commit Hook
```bash
#!/bin/bash
python safety_emulator.py requirements.txt
if [ $? -ne 0 ]; then
    echo "Security vulnerabilities found! Commit rejected."
    exit 1
fi
```

### CI/CD Pipeline
```yaml
# .github/workflows/security.yml
- name: Check dependencies
  run: python safety_emulator.py requirements.txt
```

### Scheduled Audits
```bash
# Daily cron job
0 0 * * * cd /path/to/project && python safety_emulator.py requirements.txt | mail -s "Security Scan Results" team@example.com
```

## License

Part of the Emu-Soft project - see main repository LICENSE.
