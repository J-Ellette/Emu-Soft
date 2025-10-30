# Security Tools

Comprehensive security features for auditing, sanitization, and compliance.

## What This Emulates

**Emulates:** Security audit tools, content integrity systems, compliance frameworks
**Purpose:** Application security and compliance

## Features

- Security audit logging
- Content integrity verification
- Input sanitization
- Security profiles
- Compliance checking
- Security middleware

## Components

### Audit Logging
- **audit.py** - Basic security audit logging
  - Event logging
  - Audit trail generation
  - Security event tracking
  - Log retention

- **enhanced_audit.py** - Advanced audit features
  - Detailed audit trails
  - Anomaly detection
  - Forensic analysis support
  - Compliance reporting
  - Audit log encryption

### Input Sanitization
- **sanitization.py** - Input sanitization
  - XSS (Cross-Site Scripting) prevention
  - SQL injection prevention
  - HTML sanitization
  - Path traversal prevention
  - Command injection prevention
  - Input validation

### Content Integrity
- **content_integrity.py** - Content integrity verification
  - File checksum validation
  - File integrity monitoring (FIM)
  - Tampering detection
  - Digital signatures
  - Hash-based verification

- **content_integrity_demo.py** - Demo of integrity features
- **test_content_integrity.py** - Tests for content integrity

### Security Profiles
- **profiles.py** - Configurable security profiles
  - Security level configurations (low, medium, high, critical)
  - Policy enforcement
  - Compliance profiles (FISMA, PCI-DSS, etc.)
  - Custom security policies

- **profiles_demo.py** - Demo of security profiles
- **test_profiles.py** - Tests for security profiles

### Compliance
- **compliance.py** - Regulatory compliance checking
  - FISMA compliance
  - PCI-DSS compliance
  - HIPAA compliance
  - SOC 2 compliance
  - Custom compliance frameworks

### Security Middleware
- **middleware.py** - Security middleware
  - Request security validation
  - Response security headers
  - CSRF (Cross-Site Request Forgery) protection
  - XSS protection headers
  - Content Security Policy (CSP)
  - HTTPS enforcement

## Usage Examples

### Audit Logging
```python
from security.audit import SecurityAuditor
from security.enhanced_audit import EnhancedAuditor

# Basic auditing
auditor = SecurityAuditor()
auditor.log_event("user_login", {
    "user_id": 123,
    "ip_address": "192.168.1.1",
    "timestamp": datetime.now()
})

# Enhanced auditing with anomaly detection
enhanced = EnhancedAuditor()
enhanced.log_event("failed_login", data)
if enhanced.detect_anomaly("failed_login"):
    alert_security_team()
```

### Input Sanitization
```python
from security.sanitization import Sanitizer

sanitizer = Sanitizer()

# Sanitize HTML
safe_html = sanitizer.sanitize_html(user_input)

# Prevent SQL injection
safe_query = sanitizer.sanitize_sql(query_string)

# Prevent XSS
safe_output = sanitizer.escape_html(user_content)

# Validate file paths
safe_path = sanitizer.validate_path(file_path)
```

### Content Integrity
```python
from security.content_integrity import IntegrityChecker

checker = IntegrityChecker()

# Calculate checksum
checksum = checker.calculate_checksum("/path/to/file")

# Verify integrity
is_valid = checker.verify_file("/path/to/file", expected_checksum)

# Monitor file changes
checker.start_monitoring("/path/to/monitor")
if checker.has_changed("/path/to/file"):
    alert_admin()
```

### Security Profiles
```python
from security.profiles import SecurityProfile

# Load security profile
profile = SecurityProfile.load("high_security")

# Apply profile settings
profile.apply()

# Check compliance
if profile.is_compliant():
    pass
else:
    violations = profile.get_violations()
    handle_violations(violations)
```

### Compliance Checking
```python
from security.compliance import ComplianceChecker

checker = ComplianceChecker()

# Check FISMA compliance
fisma_result = checker.check_fisma_compliance()
if not fisma_result.is_compliant:
    print(fisma_result.violations)

# Check PCI-DSS compliance
pci_result = checker.check_pci_compliance()
```

### Security Middleware
```python
from security.middleware import SecurityMiddleware
from framework.application import Application

app = Application()
app.add_middleware(SecurityMiddleware(
    enable_csrf=True,
    enable_xss_protection=True,
    enable_csp=True,
    force_https=True
))
```

## Security Features

### Protection Against
- XSS (Cross-Site Scripting)
- SQL Injection
- CSRF (Cross-Site Request Forgery)
- Command Injection
- Path Traversal
- File Upload Attacks
- Session Hijacking
- Brute Force Attacks

### Security Headers
- Content-Security-Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security (HSTS)
- Referrer-Policy

### Audit Capabilities
- Event logging
- Access logging
- Change tracking
- Anomaly detection
- Forensic analysis
- Compliance reporting

## Compliance Frameworks

Supported compliance standards:
- **FISMA** - Federal Information Security Management Act
- **PCI-DSS** - Payment Card Industry Data Security Standard
- **HIPAA** - Health Insurance Portability and Accountability Act
- **SOC 2** - Service Organization Control 2
- **GDPR** - General Data Protection Regulation (basic support)

## Integration

Works with:
- Web framework (framework/ module)
- Authentication system (auth/ module)
- Admin interface (admin/ module)
- API framework (api/ module)

## Why This Was Created

Part of the CIV-ARCOS project to provide military-grade security features without external security libraries, ensuring comprehensive protection and compliance while maintaining self-containment.
