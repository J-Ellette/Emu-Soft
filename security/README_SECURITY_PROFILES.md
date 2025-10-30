# Security Hardening Profiles

## Overview

The Security Hardening Profiles feature provides predefined security configurations for different deployment environments and compliance requirements. This emulates concepts from frameworks like Django's security settings and AWS Security Hub profiles, but implemented from scratch.

## Emulated Technologies

This component emulates the following concepts:
- **Django Security Middleware**: Predefined security settings and middleware configurations
- **AWS Security Hub**: Security profiles and compliance standards
- **OWASP Security Best Practices**: Security configuration recommendations
- **Compliance Frameworks**: HIPAA, PCI-DSS, GDPR, SOC2 requirements

## Features

### 1. Predefined Security Profiles

Four built-in security profiles optimized for different deployment scenarios:

#### Public Website Profile
- **Use Case**: Public-facing websites and applications
- **Security Level**: Balanced (Moderate)
- **Compliance**: GDPR
- **Key Features**:
  - Moderate password requirements (10+ characters)
  - Optional 2FA (required for admins)
  - 60-minute session timeout
  - Standard rate limiting (100 req/60s)
  - CORS enabled for public APIs
  - 90-day audit log retention

#### Internal Intranet Profile
- **Use Case**: Internal corporate applications
- **Security Level**: Enhanced
- **Compliance**: SOC2
- **Key Features**:
  - Strong password requirements (12+ characters)
  - 2FA for privileged users (admin, manager)
  - 30-minute session timeout
  - Strict rate limiting (60 req/60s)
  - IP restrictions enabled
  - 365-day audit log retention

#### Government/Federal Profile
- **Use Case**: Government and federal applications
- **Security Level**: Maximum
- **Compliance**: FISMA, FedRAMP
- **Key Features**:
  - Very strong password requirements (16+ characters)
  - Mandatory 2FA for all users
  - 15-minute session timeout
  - Very strict rate limiting (30 req/60s)
  - Mandatory IP restrictions
  - 7-year audit log retention
  - Strictest CSP and security headers

#### Healthcare/HIPAA Profile
- **Use Case**: Healthcare applications with PHI
- **Security Level**: High
- **Compliance**: HIPAA
- **Key Features**:
  - Strong password requirements (14+ characters)
  - Mandatory 2FA for all users
  - 20-minute session timeout
  - 7-year audit log retention
  - End-to-end encryption
  - Support for medical file formats (DICOM, HL7)

### 2. Compliance Preset Configurations

Pre-configured compliance requirements for major standards:

#### HIPAA (Health Insurance Portability and Accountability Act)
- 2FA required
- 7-year audit log retention
- Data encryption at rest and in transit
- Automatic logoff after inactivity
- Access controls and audit trails

#### PCI-DSS (Payment Card Industry Data Security Standard)
- Strong password policies (12+ characters, 90-day expiry)
- 15-minute session timeout
- Data encryption
- 1-year audit log retention
- Regular security testing

#### GDPR (General Data Protection Regulation)
- Audit logging enabled
- Data encryption
- Data access and modification logging
- Right to erasure and data portability support

#### SOC2 (Service Organization Control 2)
- 2FA required
- Strong password policies
- Comprehensive audit logging
- 1-year audit log retention
- IP restrictions recommended

### 3. One-Click Profile Application

Apply security profiles with a single function call:

```python
from mycms.security.profiles import get_profile_manager

manager = get_profile_manager()
result = manager.apply_profile("Healthcare/HIPAA")
print(f"Applied profile: {result['profile']}")
```

### 4. Security Profile Validation

Validate profiles against security best practices and compliance requirements:

```python
validation = manager.validate_profile("Healthcare/HIPAA")
if validation['valid']:
    print("Profile is valid!")
else:
    print("Errors found:", validation['errors'])
```

### 5. Profile Comparison

Compare different security profiles to understand differences:

```python
comparison = manager.compare_profiles("Public Website", "Government/Federal")
print(f"Total differences: {comparison['total_differences']}")
for diff in comparison['differences']:
    print(f"{diff['setting']}: {diff['Public Website']} vs {diff['Government/Federal']}")
```

### 6. Custom Profile Creation

Create custom security profiles for specific requirements:

```python
from mycms.security.profiles import SecurityProfile, SecuritySettings, ProfileType

settings = SecuritySettings(
    min_password_length=14,
    require_2fa=True,
    session_timeout_minutes=25,
    audit_enabled=True,
)

custom_profile = SecurityProfile(
    name="Custom Corporate Profile",
    profile_type=ProfileType.CUSTOM,
    description="Custom profile for our requirements",
    settings=settings,
)

manager.add_custom_profile(custom_profile)
```

### 7. Profile Import/Export

Export profiles as JSON for backup or sharing:

```python
# Export
json_str = manager.export_profile("Healthcare/HIPAA")

# Import
imported_profile = manager.import_profile(json_str)
```

## Architecture

### Core Components

1. **SecuritySettings**: Dataclass containing all security configuration options
2. **SecurityProfile**: Container for a named security configuration
3. **ProfileFactory**: Factory for creating predefined profiles
4. **ComplianceRequirements**: Compliance standard requirements and settings
5. **CompliancePresets**: Factory for compliance configurations
6. **ProfileManager**: Central manager for all profile operations

### Security Settings Categories

- **Security Headers**: CSP, HSTS, X-Frame-Options, Referrer Policy, etc.
- **CSRF Protection**: Token-based CSRF protection configuration
- **Rate Limiting**: Request rate limits and time windows
- **Session Security**: Timeout, cookie settings, SameSite policy
- **Password Policy**: Length, complexity, expiry, history
- **Two-Factor Authentication**: Required users and roles
- **Audit Logging**: Enabled features and retention periods
- **IP Restrictions**: Whitelist/blacklist configuration
- **File Upload Security**: Size limits, allowed extensions, malware scanning
- **Encryption**: Algorithms, TLS versions, cipher suites
- **Additional Features**: XSS protection, clickjacking, CORS, etc.

## Usage Examples

### Example 1: Apply Healthcare Profile

```python
from mycms.security.profiles import get_profile_manager

manager = get_profile_manager()

# Apply HIPAA-compliant healthcare profile
result = manager.apply_profile("Healthcare/HIPAA")

if result['success']:
    print(f"Applied {result['profile']} profile")
    print(f"Compliance standards: {result['compliance_standards']}")
    
    # Get active profile
    active = manager.get_active_profile()
    print(f"Min password length: {active.settings.min_password_length}")
    print(f"2FA required: {active.settings.require_2fa}")
```

### Example 2: Validate Custom Profile

```python
from mycms.security.profiles import (
    SecurityProfile,
    SecuritySettings,
    ProfileType,
    ComplianceStandard,
    get_profile_manager,
)

# Create custom profile
settings = SecuritySettings(
    min_password_length=14,
    require_2fa=True,
    audit_log_retention_days=730,
)

profile = SecurityProfile(
    name="My Custom Profile",
    profile_type=ProfileType.CUSTOM,
    description="Custom security profile",
    settings=settings,
    compliance_standards=[ComplianceStandard.SOC2],
)

manager = get_profile_manager()
manager.add_custom_profile(profile)

# Validate
validation = manager.validate_profile("My Custom Profile")
print(f"Valid: {validation['valid']}")
print(f"Errors: {validation['errors']}")
print(f"Warnings: {validation['warnings']}")
```

### Example 3: Check Compliance Requirements

```python
from mycms.security.profiles import CompliancePresets, ComplianceStandard

# Get HIPAA requirements
hipaa = CompliancePresets.get_hipaa_requirements()
print(f"HIPAA Requirements: {len(hipaa.requirements)}")
for req in hipaa.requirements:
    print(f"  - {req}")

print(f"\nMandatory Settings:")
for key, value in hipaa.mandatory_settings.items():
    print(f"  - {key}: {value}")
```

### Example 4: Compare Profiles

```python
from mycms.security.profiles import get_profile_manager

manager = get_profile_manager()

# Compare public vs government profiles
comparison = manager.compare_profiles("Public Website", "Government/Federal")

print(f"Comparing {comparison['profile1']} vs {comparison['profile2']}")
print(f"Total differences: {comparison['total_differences']}")

for diff in comparison['differences'][:5]:  # Show first 5
    print(f"\n{diff['setting']}:")
    print(f"  Public: {diff['Public Website']}")
    print(f"  Government: {diff['Government/Federal']}")
```

## Testing

Comprehensive test suite with 37 test cases covering:
- Security settings creation and serialization
- Profile creation and management
- Profile factory for all predefined profiles
- Compliance preset configurations
- Profile manager operations
- Validation logic
- Profile comparison
- Import/export functionality
- Compliance requirement validation

Run tests:
```bash
python -m pytest tests/test_security_profiles.py -v
```

## Integration

### With Existing Security Middleware

```python
from mycms.security.middleware import (
    SecurityHeadersMiddleware,
    CSRFMiddleware,
    RateLimitMiddleware,
)
from mycms.security.profiles import get_profile_manager

# Apply profile
manager = get_profile_manager()
manager.apply_profile("Government/Federal")
active = manager.get_active_profile()

# Configure middleware from profile
security_headers = SecurityHeadersMiddleware(
    csp_policy=active.settings.csp_policy,
    hsts_max_age=active.settings.hsts_max_age,
    frame_options=active.settings.frame_options,
)

csrf = CSRFMiddleware(
    exempt_paths=active.settings.csrf_exempt_paths,
)

rate_limit = RateLimitMiddleware(
    max_requests=active.settings.max_requests,
    window_seconds=active.settings.rate_limit_window_seconds,
)
```

### With Compliance Manager

```python
from mycms.security.compliance import ComplianceManager, DataRetentionPolicy
from mycms.security.profiles import get_profile_manager

manager = get_profile_manager()
manager.apply_profile("Healthcare/HIPAA")
profile = manager.get_active_profile()

# Configure compliance manager from profile
compliance = ComplianceManager()
compliance.add_retention_policy(
    DataRetentionPolicy(
        name="Audit Logs",
        data_type="audit_logs",
        retention_days=profile.settings.audit_log_retention_days,
        description=f"Audit log retention per {profile.name}",
    )
)
```

## Best Practices

1. **Choose the Right Profile**: Select a profile that matches your deployment environment and compliance requirements
2. **Validate Regularly**: Run validation after making any changes to ensure compliance
3. **Document Customizations**: Keep track of any custom profiles and their rationale
4. **Test Before Production**: Always test profiles in staging before applying to production
5. **Monitor Compliance**: Regularly check compliance requirements and update profiles as needed
6. **Version Control**: Export profiles and store them in version control
7. **Review Settings**: Periodically review security settings to ensure they remain appropriate

## Security Considerations

- **Profile Selection**: Choose profiles based on data sensitivity and regulatory requirements
- **Custom Profiles**: When creating custom profiles, start with a predefined profile and adjust
- **Validation**: Always validate profiles before applying to production
- **Audit Logging**: Ensure audit log retention meets compliance requirements
- **Encryption**: Use appropriate encryption algorithms for your security level
- **Session Management**: Shorter timeouts provide better security but may impact UX
- **Password Policies**: Balance security with usability
- **2FA**: Consider mandatory 2FA for sensitive environments

## Files in This Implementation

- `profiles.py`: Main implementation with all classes and factories
- `test_profiles.py`: Comprehensive test suite (37 tests)
- `profiles_demo.py`: Demonstration application
- `README_SECURITY_PROFILES.md`: This documentation

## Dependencies

This implementation has no external dependencies beyond:
- Python 3.11+ (for dataclasses and type hints)
- Standard library only (json, enum, dataclasses, typing)

## Version History

- **1.0.0** (2025-10-30): Initial implementation
  - Four predefined security profiles
  - Four compliance preset configurations
  - Profile validation and comparison
  - Import/export functionality
  - Comprehensive test suite

## License

Same as parent project.

## Contributing

When adding new profiles or compliance presets:
1. Add factory methods to appropriate classes
2. Add comprehensive tests
3. Update this documentation
4. Validate against real compliance requirements

## References

- HIPAA: https://www.hhs.gov/hipaa/for-professionals/security/
- PCI-DSS: https://www.pcisecuritystandards.org/
- GDPR: https://gdpr.eu/
- SOC2: https://www.aicpa.org/soc
- FISMA: https://www.cisa.gov/fisma
- FedRAMP: https://www.fedramp.gov/
- OWASP: https://owasp.org/www-project-secure-headers/
