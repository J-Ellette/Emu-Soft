# Certificate Authority (CA) Emulator - X.509 Certificate Management

A lightweight emulation of **Certificate Authority** functionality for X.509 certificate management and PKI operations.

## Features

This emulator implements core Certificate Authority functionality:

### Certificate Issuance
- **Root CA Generation**: Create self-signed root certificates
- **Intermediate CA**: Support for intermediate certificate authorities
- **Server Certificates**: TLS/SSL certificates for web servers
- **Client Certificates**: Certificates for client authentication
- **Code Signing Certificates**: For software signing

### X.509 Extensions
- **Subject Alternative Names (SAN)**: DNS names, IP addresses, URIs
- **Key Usage**: Digital signature, key encipherment, certificate signing
- **Extended Key Usage**: Server auth, client auth, code signing
- **Basic Constraints**: CA flag and path length constraints
- **Authority/Subject Key Identifiers**: Key identification

### Certificate Lifecycle
- **Certificate Generation**: Issue new certificates
- **Certificate Validation**: Verify signatures and validity
- **Certificate Revocation**: Revoke compromised certificates
- **Certificate Chains**: Build and validate trust chains

### Revocation Management
- **Certificate Revocation Lists (CRL)**: Standard revocation lists
- **Revocation Reasons**: Key compromise, superseded, etc.
- **CRL Generation**: Periodic CRL updates

### Key Management
- **RSA Support**: 2048 and 4096-bit keys
- **ECDSA Support**: P-256 and P-384 curves (simulated)
- **Key Pair Generation**: Automatic key generation
- **Private Key Security**: Secure key storage

## What It Emulates

This tool emulates core functionality of Certificate Authority systems like:
- [OpenSSL CA](https://www.openssl.org/)
- [EJBCA](https://www.ejbca.org/)
- [HashiCorp Vault PKI](https://www.vaultproject.io/docs/secrets/pki)
- [Let's Encrypt](https://letsencrypt.org/) (ACME protocol not included)

### Core Components Implemented

1. **Root CA Operations**
   - Self-signed root certificate generation
   - Root key management
   - Trust anchor establishment

2. **Intermediate CA Operations**
   - Subordinate CA creation
   - Path length constraints
   - Delegated certificate issuance

3. **Certificate Issuance**
   - Server certificates with SAN
   - Client certificates
   - Flexible validity periods
   - Custom distinguished names

4. **Revocation**
   - Certificate revocation
   - CRL generation and signing
   - Revocation reason tracking

## Usage

### Create Root CA

```python
from ca_emulator_tool import CertificateAuthority

# Create root CA
ca = CertificateAuthority(
    ca_name="My Root CA",
    country="US",
    organization="My Company Inc.",
    validity_days=7300  # 20 years
)

print(f"Root CA: {ca.root_ca_cert.subject.to_string()}")
print(f"Serial: {ca.root_ca_cert.serial_number}")
```

### Create Intermediate CA

```python
# Create intermediate CA
intermediate_cert, intermediate_key = ca.create_intermediate_ca(
    ca_name="My Intermediate CA",
    validity_days=3650,  # 10 years
    path_len=0  # Cannot create sub-CAs
)

print(f"Intermediate CA: {intermediate_cert.subject.to_string()}")
print(f"Issuer: {intermediate_cert.issuer.to_string()}")
```

### Issue Server Certificate

```python
# Issue server certificate
server_cert, server_key = ca.issue_server_certificate(
    common_name="www.example.com",
    dns_names=[
        "www.example.com",
        "example.com",
        "*.example.com"
    ],
    ip_addresses=["192.168.1.1", "10.0.0.1"],
    validity_days=365,
    issuer_ca="My Intermediate CA"  # Optional
)

print(f"Server Certificate: {server_cert.subject.common_name}")
print(f"Valid until: {server_cert.not_after}")
print(f"DNS Names: {server_cert.subject_alt_names.dns_names}")
```

### Issue Client Certificate

```python
# Issue client certificate
client_cert, client_key = ca.issue_client_certificate(
    common_name="John Doe",
    email="john.doe@example.com",
    validity_days=365
)

print(f"Client: {client_cert.subject.common_name}")
print(f"Email: {client_cert.subject.email}")
```

### Verify Certificate

```python
# Verify certificate
is_valid = ca.verify_certificate(server_cert)
print(f"Certificate valid: {is_valid}")

# Check validity period
if server_cert.is_valid():
    print("Certificate is currently valid")
else:
    print("Certificate is expired or not yet valid")
```

### Get Certificate Chain

```python
# Get full certificate chain
chain = ca.get_certificate_chain(server_cert)

print("Certificate Chain:")
for i, cert in enumerate(chain):
    print(f"  {i}. {cert.subject.common_name}")
    print(f"     Issuer: {cert.issuer.common_name}")
    print(f"     Serial: {cert.serial_number}")
```

### Revoke Certificate

```python
from ca_emulator_tool import RevocationReason

# Revoke certificate
success = ca.revoke_certificate(
    server_cert.serial_number,
    reason=RevocationReason.KEY_COMPROMISE
)

if success:
    print("Certificate revoked")
    print(f"Revoked at: {server_cert.revocation_date}")
    print(f"Reason: {server_cert.revocation_reason.name}")
```

### Generate CRL

```python
# Generate Certificate Revocation List
crl = ca.generate_crl()

print(f"CRL Number: {crl.crl_number}")
print(f"This Update: {crl.this_update}")
print(f"Next Update: {crl.next_update}")
print(f"Revoked Certificates: {len(crl.revoked_certificates)}")

# Check if certificate is revoked
if crl.is_revoked(server_cert.serial_number):
    print(f"Certificate {server_cert.serial_number} is revoked")
```

### Export Certificates

```python
# Export certificate to PEM format
pem = server_cert.to_pem()
print(pem)

# Export certificate bundle (cert + chain)
bundle = ca.export_certificate_bundle(server_cert)
print(bundle)
```

### Complete Example - Web Server Setup

```python
# Create CA infrastructure
ca = CertificateAuthority(
    ca_name="Corporate Root CA",
    country="US",
    organization="ACME Corporation"
)

# Create intermediate CA for web servers
web_ca_cert, web_ca_key = ca.create_intermediate_ca(
    ca_name="Web Services CA",
    validity_days=1825  # 5 years
)

# Issue certificates for multiple servers
servers = ["web1.example.com", "web2.example.com", "api.example.com"]

for server in servers:
    cert, key = ca.issue_server_certificate(
        common_name=server,
        dns_names=[server, f"*.{server}"],
        validity_days=90,  # Short-lived certificates
        issuer_ca="Web Services CA"
    )
    
    print(f"Issued certificate for {server}")
    print(f"  Serial: {cert.serial_number}")
    print(f"  Expires: {cert.not_after}")
    
    # Export for deployment
    cert_pem = cert.to_pem()
    # key_pem would be exported similarly
    
# Generate CRL for revocation checking
crl = ca.generate_crl()
print(f"\nGenerated CRL with {len(crl.revoked_certificates)} entries")
```

## Testing

```bash
python ca_emulator_tool.py
```

The demo script will demonstrate:
1. Root CA creation
2. Intermediate CA creation
3. Server certificate issuance
4. Client certificate issuance
5. Certificate verification
6. Certificate chain building
7. Certificate revocation
8. CRL generation

## Certificate Types

### Root CA Certificate
- Self-signed
- Unlimited path length
- Long validity (10-20 years)
- Key usage: Certificate signing, CRL signing

### Intermediate CA Certificate
- Signed by root or another intermediate
- Constrained path length
- Medium validity (5-10 years)
- Key usage: Certificate signing, CRL signing

### Server Certificate
- For TLS/SSL servers
- Subject Alternative Names support
- Short to medium validity (90 days to 2 years)
- Extended key usage: Server authentication

### Client Certificate
- For client authentication
- Email address support
- Medium validity (1-2 years)
- Extended key usage: Client authentication, email protection

## Key Algorithms

- **RSA-2048**: Standard security, fast
- **RSA-4096**: High security, slower
- **ECDSA-P256**: Efficient, modern (simulated)
- **ECDSA-P384**: High security, modern (simulated)

## Use Cases

1. **Development**: Test PKI without setting up real CA
2. **Testing**: Mock certificates for integration tests
3. **Learning**: Understand X.509 and PKI concepts
4. **Prototyping**: Quick certificate generation for demos
5. **Education**: Teaching certificate management

## Key Differences from Production CAs

1. **Simplified Cryptography**: Uses simulated keys and signatures
2. **No Hardware Security**: No HSM support
3. **In-Memory Storage**: No persistent certificate storage
4. **No ACME Protocol**: No automated certificate management
5. **Limited Validation**: Basic validation only
6. **No OCSP**: Only CRL support for revocation

## Security Considerations

This is an emulator for development and testing. For production:
- Use established CAs (Let's Encrypt, DigiCert, etc.) or proper PKI software
- Implement real cryptographic operations (OpenSSL, cryptography library)
- Store private keys securely (HSM, KMS)
- Implement proper access controls
- Use appropriate key sizes and algorithms
- Implement certificate transparency logging
- Regular CRL updates or OCSP

## License

Educational emulator for learning purposes.

## References

- [RFC 5280 - X.509 Certificate Profile](https://tools.ietf.org/html/rfc5280)
- [RFC 5280 - CRL Profile](https://tools.ietf.org/html/rfc5280#section-5)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [PKI Best Practices](https://www.ietf.org/rfc/rfc4158.txt)
