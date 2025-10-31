# SAML Authentication Provider Emulator

A lightweight emulation of **SAML 2.0** (Security Assertion Markup Language), the XML-based standard for exchanging authentication and authorization data between identity providers and service providers.

## Features

This emulator implements core SAML 2.0 functionality:

### Identity Provider (IdP)
- **Service Provider Registration**: Register SPs with the IdP
- **User Management**: Add and authenticate users
- **Authentication Request Parsing**: Parse SAML AuthnRequest
- **Assertion Generation**: Create SAML assertions for authenticated users
- **Response Generation**: Generate SAML responses with assertions
- **Single Sign-On (SSO)**: Complete SSO flow
- **Single Logout (SLO)**: Logout from all services
- **Metadata Generation**: Generate IdP metadata XML

### Service Provider (SP)
- **Authentication Request Creation**: Generate SAML AuthnRequest
- **Response Parsing**: Parse SAML responses from IdP
- **Response Validation**: Validate assertions and responses
- **Attribute Extraction**: Extract user attributes from assertions

### SAML Protocol Features
- **Multiple Binding Types**: HTTP-POST, HTTP-Redirect, SOAP, Artifact
- **NameID Formats**: Email, Persistent, Transient, Unspecified
- **Status Codes**: Success, Requester, Responder, VersionMismatch
- **Attribute Statements**: User attributes in assertions
- **Audience Restriction**: Limit assertion usage to specific SPs
- **Time Validity**: NotBefore and NotOnOrAfter conditions
- **Session Management**: Track active sessions

### Security Features
- **Base64 Encoding**: Standard SAML encoding
- **XML Signing**: Structure for signature support (emulated)
- **Assertion Validation**: Check time validity and audience
- **Session Index**: Track user sessions across services

## What It Emulates

This tool emulates [SAML 2.0](https://en.wikipedia.org/wiki/SAML_2.0), the industry-standard protocol for single sign-on (SSO) used by enterprises worldwide.

### Core Components Implemented

1. **Identity Provider (IdP)**
   - User authentication
   - Assertion creation
   - Response generation
   - Session management
   - Metadata generation

2. **Service Provider (SP)**
   - Authentication request creation
   - Response validation
   - Attribute extraction

3. **SAML Protocol**
   - AuthnRequest/Response flow
   - Assertion format
   - Attribute statements
   - Status codes
   - Time-based conditions

## Usage

### Identity Provider Setup

```python
from saml_emulator import (
    SAMLEmulator, IdentityProvider, ServiceProvider,
    User, NameIDFormat
)

# Configure Identity Provider
idp_config = IdentityProvider(
    entity_id="https://idp.example.com",
    sso_url="https://idp.example.com/sso",
    slo_url="https://idp.example.com/slo",
    certificate="idp-cert-content",
    signing_key="idp-key-content"
)

# Create IdP emulator
idp = SAMLEmulator(idp_config)

# Register Service Provider
sp = ServiceProvider(
    entity_id="https://sp.example.com",
    acs_url="https://sp.example.com/acs",
    slo_url="https://sp.example.com/slo",
    name_id_format=NameIDFormat.EMAIL,
    attributes_required=["email", "username", "groups"]
)
idp.register_service_provider(sp)

# Add users
user = User(
    username="john.doe",
    email="john.doe@example.com",
    attributes={
        "firstName": "John",
        "lastName": "Doe",
        "department": "Engineering"
    },
    groups=["developers", "admins"]
)
idp.add_user(user)
```

### Service Provider Setup

```python
from saml_emulator import SAMLServiceProvider, ServiceProvider

# Configure Service Provider
sp_config = ServiceProvider(
    entity_id="https://sp.example.com",
    acs_url="https://sp.example.com/acs",
    name_id_format=NameIDFormat.EMAIL
)

# Create SP emulator
sp = SAMLServiceProvider(
    sp_config=sp_config,
    idp_sso_url="https://idp.example.com/sso"
)
```

### Complete SSO Flow

```python
# 1. Service Provider creates AuthnRequest
request, encoded_request = sp.create_authn_request()
print(f"AuthnRequest ID: {request.id}")
print(f"Encoded: {encoded_request[:50]}...")

# 2. IdP receives and parses the request
authn_request = idp.parse_authn_request(encoded_request)
print(f"SP Entity: {authn_request.sp_entity_id}")

# 3. User authenticates with IdP
saml_response = idp.initiate_sso(
    username="john.doe",
    password="password123",
    authn_request=authn_request
)

print(f"Status: {saml_response.status_code.value}")
if saml_response.assertion:
    print(f"Subject: {saml_response.assertion.subject}")
    print(f"Attributes: {len(saml_response.assertion.attributes)}")

# 4. Encode response
encoded_response = idp.encode_response(saml_response)

# 5. SP receives and parses response
parsed_response = sp.parse_response(encoded_response)

# 6. SP validates response
is_valid = sp.validate_response(parsed_response)
print(f"Response valid: {is_valid}")

# 7. Extract user attributes
if parsed_response.assertion:
    for attr in parsed_response.assertion.attributes:
        print(f"  {attr.name}: {attr.value}")
```

### Working with Assertions

```python
# Create assertion manually
from saml_emulator import Assertion, Attribute
from datetime import datetime, timedelta

assertion = idp.create_assertion(
    user=user,
    sp_entity_id="https://sp.example.com",
    request_id="request_123"
)

print(f"Assertion ID: {assertion.id}")
print(f"Subject: {assertion.subject}")
print(f"Valid from: {assertion.not_before}")
print(f"Valid until: {assertion.not_on_or_after}")
print(f"Session: {assertion.session_index}")

# Validate assertion
is_valid = idp.validate_assertion(assertion.id)
print(f"Assertion valid: {is_valid}")
```

### Single Logout

```python
# Logout user from all services
session_index = assertion.session_index
success = idp.logout(session_index)
print(f"Logout successful: {success}")

# Assertion no longer valid
is_valid = idp.validate_assertion(assertion.id)
print(f"Assertion valid after logout: {is_valid}")
```

### Generate IdP Metadata

```python
# Generate metadata for SP to consume
metadata_xml = idp.get_metadata()
print(metadata_xml)
```

### Multiple Service Providers

```python
# Register multiple SPs
sp1 = ServiceProvider(
    entity_id="https://app1.example.com",
    acs_url="https://app1.example.com/acs",
    name_id_format=NameIDFormat.EMAIL
)

sp2 = ServiceProvider(
    entity_id="https://app2.example.com",
    acs_url="https://app2.example.com/acs",
    name_id_format=NameIDFormat.PERSISTENT
)

idp.register_service_provider(sp1)
idp.register_service_provider(sp2)

# User can authenticate to either SP
request1, _ = sp1_emulator.create_authn_request()
request2, _ = sp2_emulator.create_authn_request()

# Same IdP, same user, different SPs
response1 = idp.initiate_sso("john.doe", "pass", request1)
response2 = idp.initiate_sso("john.doe", "pass", request2)
```

## Testing

```bash
python test_saml_emulator.py
```

## Use Cases

1. **Learning SAML**: Understand SAML protocol without complex setup
2. **Development**: Develop SAML-integrated applications
3. **Testing**: Test SSO flows in development
4. **Education**: Teaching enterprise authentication
5. **Prototyping**: Rapid prototyping of SSO solutions
6. **Integration Testing**: Test SAML integrations without external IdP

## Key Differences from Real SAML

1. **No Cryptographic Signing**: Signatures are not actually generated/validated
2. **No Encryption**: Assertions are not encrypted
3. **Simplified XML**: XML structure is simplified
4. **No Certificate Validation**: Certificates not actually validated
5. **No Real Authentication**: Password checking is simulated
6. **Limited Bindings**: Not all SAML bindings fully implemented
7. **No SAML 1.0**: Only SAML 2.0 emulated

## SAML Concepts

### Identity Provider (IdP)
The service that authenticates users and provides identity information to service providers.

### Service Provider (SP)
The application that users want to access. It trusts the IdP to authenticate users.

### Assertion
A package of information that supplies one or more statements about a user's authentication and/or attributes.

### Single Sign-On (SSO)
Allows users to log in once and access multiple applications without re-authenticating.

### NameID
The identifier used to represent a user across systems.

### Attributes
Additional information about the user (email, name, roles, etc.).

## Common SAML Flow

1. User tries to access Service Provider (SP)
2. SP generates AuthnRequest and redirects to IdP
3. User authenticates with IdP
4. IdP generates SAML Response with Assertion
5. IdP posts response to SP's Assertion Consumer Service (ACS)
6. SP validates response and grants access

## License

Educational emulator for learning purposes.

## References

- [SAML 2.0 Specification](http://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0.html)
- [SAML on Wikipedia](https://en.wikipedia.org/wiki/SAML_2.0)
- [SAML Deployment Guide](https://www.oasis-open.org/committees/download.php/27819/sstc-saml-deployment-guide-1.0.pdf)
