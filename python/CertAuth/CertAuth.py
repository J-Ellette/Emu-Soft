#!/usr/bin/env python3
"""
Certificate Authority (CA) Emulator - X.509 Certificate Management

This module emulates core Certificate Authority functionality including:
- Root CA certificate generation
- Intermediate CA support
- Certificate signing requests (CSR) processing
- X.509 certificate issuance
- Certificate revocation lists (CRL)
- OCSP responder simulation
- Certificate validation and verification
"""

import hashlib
import secrets
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import base64


class KeyAlgorithm(Enum):
    """Cryptographic algorithm types"""
    RSA_2048 = "RSA-2048"
    RSA_4096 = "RSA-4096"
    ECDSA_P256 = "ECDSA-P256"
    ECDSA_P384 = "ECDSA-P384"


class CertificateType(Enum):
    """Certificate types"""
    ROOT_CA = "root_ca"
    INTERMEDIATE_CA = "intermediate_ca"
    SERVER = "server"
    CLIENT = "client"
    CODE_SIGNING = "code_signing"


class RevocationReason(Enum):
    """Certificate revocation reasons"""
    UNSPECIFIED = 0
    KEY_COMPROMISE = 1
    CA_COMPROMISE = 2
    AFFILIATION_CHANGED = 3
    SUPERSEDED = 4
    CESSATION_OF_OPERATION = 5
    CERTIFICATE_HOLD = 6
    REMOVE_FROM_CRL = 8
    PRIVILEGE_WITHDRAWN = 9
    AA_COMPROMISE = 10


@dataclass
class DistinguishedName:
    """X.509 Distinguished Name (DN)"""
    country: Optional[str] = None
    state: Optional[str] = None
    locality: Optional[str] = None
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    common_name: Optional[str] = None
    email: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert DN to string representation"""
        parts = []
        if self.country:
            parts.append(f"C={self.country}")
        if self.state:
            parts.append(f"ST={self.state}")
        if self.locality:
            parts.append(f"L={self.locality}")
        if self.organization:
            parts.append(f"O={self.organization}")
        if self.organizational_unit:
            parts.append(f"OU={self.organizational_unit}")
        if self.common_name:
            parts.append(f"CN={self.common_name}")
        if self.email:
            parts.append(f"emailAddress={self.email}")
        return ", ".join(parts)


@dataclass
class SubjectAlternativeName:
    """Subject Alternative Name (SAN) extension"""
    dns_names: List[str] = field(default_factory=list)
    ip_addresses: List[str] = field(default_factory=list)
    email_addresses: List[str] = field(default_factory=list)
    uris: List[str] = field(default_factory=list)


@dataclass
class KeyUsage:
    """Key usage extension"""
    digital_signature: bool = False
    non_repudiation: bool = False
    key_encipherment: bool = False
    data_encipherment: bool = False
    key_agreement: bool = False
    key_cert_sign: bool = False
    crl_sign: bool = False
    encipher_only: bool = False
    decipher_only: bool = False


@dataclass
class ExtendedKeyUsage:
    """Extended key usage extension"""
    server_auth: bool = False
    client_auth: bool = False
    code_signing: bool = False
    email_protection: bool = False
    time_stamping: bool = False
    ocsp_signing: bool = False


@dataclass
class PrivateKey:
    """Private key representation"""
    algorithm: KeyAlgorithm
    key_data: str  # Simulated key data
    
    def __init__(self, algorithm: KeyAlgorithm):
        self.algorithm = algorithm
        # Generate simulated private key
        self.key_data = base64.b64encode(
            secrets.token_bytes(256)
        ).decode()


@dataclass
class PublicKey:
    """Public key representation"""
    algorithm: KeyAlgorithm
    key_data: str  # Simulated key data
    
    @staticmethod
    def from_private_key(private_key: PrivateKey) -> 'PublicKey':
        """Derive public key from private key"""
        # Simulate public key derivation
        pub_data = hashlib.sha256(private_key.key_data.encode()).hexdigest()
        public_key = PublicKey(
            algorithm=private_key.algorithm,
            key_data=pub_data
        )
        return public_key


@dataclass
class CertificateSigningRequest:
    """Certificate Signing Request (CSR)"""
    subject: DistinguishedName
    public_key: PublicKey
    signature_algorithm: KeyAlgorithm
    attributes: Dict[str, str] = field(default_factory=dict)
    subject_alt_names: Optional[SubjectAlternativeName] = None
    
    def verify_signature(self) -> bool:
        """Verify CSR signature"""
        # Simplified verification
        return True


@dataclass
class Certificate:
    """X.509 Certificate"""
    serial_number: str
    subject: DistinguishedName
    issuer: DistinguishedName
    public_key: PublicKey
    not_before: datetime
    not_after: datetime
    signature_algorithm: KeyAlgorithm
    certificate_type: CertificateType
    version: int = 3
    
    # Extensions
    key_usage: Optional[KeyUsage] = None
    extended_key_usage: Optional[ExtendedKeyUsage] = None
    subject_alt_names: Optional[SubjectAlternativeName] = None
    basic_constraints_ca: bool = False
    basic_constraints_path_len: Optional[int] = None
    authority_key_identifier: Optional[str] = None
    subject_key_identifier: Optional[str] = None
    
    # CRL Distribution Points
    crl_distribution_points: List[str] = field(default_factory=list)
    
    # OCSP
    ocsp_responder_url: Optional[str] = None
    
    # Internal
    signature: Optional[str] = None
    revoked: bool = False
    revocation_date: Optional[datetime] = None
    revocation_reason: Optional[RevocationReason] = None
    
    def is_valid(self, current_time: Optional[datetime] = None) -> bool:
        """Check if certificate is valid"""
        if self.revoked:
            return False
        
        if current_time is None:
            current_time = datetime.utcnow()
        
        return self.not_before <= current_time <= self.not_after
    
    def is_ca_certificate(self) -> bool:
        """Check if this is a CA certificate"""
        return self.basic_constraints_ca
    
    def to_pem(self) -> str:
        """Export certificate to PEM format"""
        # Simplified PEM encoding
        cert_data = {
            "serial_number": self.serial_number,
            "subject": self.subject.to_string(),
            "issuer": self.issuer.to_string(),
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "is_ca": self.basic_constraints_ca
        }
        
        cert_json = str(cert_data).encode()
        cert_b64 = base64.b64encode(cert_json).decode()
        
        pem = "-----BEGIN CERTIFICATE-----\n"
        # Split into 64-character lines
        for i in range(0, len(cert_b64), 64):
            pem += cert_b64[i:i+64] + "\n"
        pem += "-----END CERTIFICATE-----"
        
        return pem


@dataclass
class RevokedCertificate:
    """Revoked certificate entry"""
    serial_number: str
    revocation_date: datetime
    revocation_reason: RevocationReason


@dataclass
class CertificateRevocationList:
    """Certificate Revocation List (CRL)"""
    issuer: DistinguishedName
    this_update: datetime
    next_update: datetime
    revoked_certificates: List[RevokedCertificate] = field(default_factory=list)
    crl_number: int = 1
    signature: Optional[str] = None
    
    def is_revoked(self, serial_number: str) -> bool:
        """Check if certificate is revoked"""
        return any(
            cert.serial_number == serial_number
            for cert in self.revoked_certificates
        )


class CertificateAuthority:
    """Certificate Authority emulator"""
    
    def __init__(
        self,
        ca_name: str,
        country: str = "US",
        organization: str = "Example CA",
        validity_days: int = 3650
    ):
        self.ca_name = ca_name
        self.certificates: Dict[str, Certificate] = {}
        self.private_keys: Dict[str, PrivateKey] = {}
        self.serial_counter = 1000000
        self.crl_number = 1
        
        # Generate root CA
        self.root_ca_cert, self.root_ca_key = self._generate_root_ca(
            ca_name,
            country,
            organization,
            validity_days
        )
        
        # Store root CA
        self.certificates[self.root_ca_cert.serial_number] = self.root_ca_cert
        self.private_keys[self.root_ca_cert.serial_number] = self.root_ca_key
        
        # Intermediate CAs
        self.intermediate_cas: Dict[str, Tuple[Certificate, PrivateKey]] = {}
        
        # CRL
        self.crl: Optional[CertificateRevocationList] = None
    
    def _generate_serial_number(self) -> str:
        """Generate unique serial number"""
        self.serial_counter += 1
        return hex(self.serial_counter)[2:].upper()
    
    def _generate_root_ca(
        self,
        ca_name: str,
        country: str,
        organization: str,
        validity_days: int
    ) -> Tuple[Certificate, PrivateKey]:
        """Generate root CA certificate"""
        # Generate key pair
        private_key = PrivateKey(KeyAlgorithm.RSA_4096)
        public_key = PublicKey.from_private_key(private_key)
        
        # Create DN
        subject = DistinguishedName(
            country=country,
            organization=organization,
            organizational_unit="Certificate Authority",
            common_name=ca_name
        )
        
        # Generate certificate
        now = datetime.utcnow()
        cert = Certificate(
            serial_number=self._generate_serial_number(),
            subject=subject,
            issuer=subject,  # Self-signed
            public_key=public_key,
            not_before=now,
            not_after=now + timedelta(days=validity_days),
            signature_algorithm=KeyAlgorithm.RSA_4096,
            certificate_type=CertificateType.ROOT_CA,
            basic_constraints_ca=True,
            basic_constraints_path_len=None,  # Unlimited
            key_usage=KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=True
            )
        )
        
        # Self-sign
        cert.signature = self._sign_certificate(cert, private_key)
        cert.subject_key_identifier = public_key.key_data[:16]
        cert.authority_key_identifier = public_key.key_data[:16]
        
        return cert, private_key
    
    def create_intermediate_ca(
        self,
        ca_name: str,
        validity_days: int = 1825,
        path_len: Optional[int] = 0
    ) -> Tuple[Certificate, PrivateKey]:
        """Create intermediate CA certificate"""
        # Generate key pair
        private_key = PrivateKey(KeyAlgorithm.RSA_4096)
        public_key = PublicKey.from_private_key(private_key)
        
        # Create DN
        subject = DistinguishedName(
            country=self.root_ca_cert.subject.country,
            organization=self.root_ca_cert.subject.organization,
            organizational_unit="Intermediate CA",
            common_name=ca_name
        )
        
        # Generate certificate
        now = datetime.utcnow()
        cert = Certificate(
            serial_number=self._generate_serial_number(),
            subject=subject,
            issuer=self.root_ca_cert.subject,
            public_key=public_key,
            not_before=now,
            not_after=now + timedelta(days=validity_days),
            signature_algorithm=KeyAlgorithm.RSA_4096,
            certificate_type=CertificateType.INTERMEDIATE_CA,
            basic_constraints_ca=True,
            basic_constraints_path_len=path_len,
            key_usage=KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=True
            ),
            authority_key_identifier=self.root_ca_cert.subject_key_identifier
        )
        
        # Sign with root CA
        cert.signature = self._sign_certificate(cert, self.root_ca_key)
        cert.subject_key_identifier = public_key.key_data[:16]
        
        # Store
        self.certificates[cert.serial_number] = cert
        self.private_keys[cert.serial_number] = private_key
        self.intermediate_cas[ca_name] = (cert, private_key)
        
        return cert, private_key
    
    def issue_server_certificate(
        self,
        common_name: str,
        dns_names: Optional[List[str]] = None,
        ip_addresses: Optional[List[str]] = None,
        validity_days: int = 365,
        issuer_ca: Optional[str] = None
    ) -> Tuple[Certificate, PrivateKey]:
        """Issue server certificate"""
        # Determine issuing CA
        if issuer_ca and issuer_ca in self.intermediate_cas:
            issuer_cert, issuer_key = self.intermediate_cas[issuer_ca]
        else:
            issuer_cert = self.root_ca_cert
            issuer_key = self.root_ca_key
        
        # Generate key pair
        private_key = PrivateKey(KeyAlgorithm.RSA_2048)
        public_key = PublicKey.from_private_key(private_key)
        
        # Create DN
        subject = DistinguishedName(
            country=issuer_cert.subject.country,
            organization=issuer_cert.subject.organization,
            common_name=common_name
        )
        
        # Subject Alternative Names
        san = SubjectAlternativeName(
            dns_names=dns_names or [common_name],
            ip_addresses=ip_addresses or []
        )
        
        # Generate certificate
        now = datetime.utcnow()
        cert = Certificate(
            serial_number=self._generate_serial_number(),
            subject=subject,
            issuer=issuer_cert.subject,
            public_key=public_key,
            not_before=now,
            not_after=now + timedelta(days=validity_days),
            signature_algorithm=KeyAlgorithm.RSA_2048,
            certificate_type=CertificateType.SERVER,
            basic_constraints_ca=False,
            key_usage=KeyUsage(
                digital_signature=True,
                key_encipherment=True
            ),
            extended_key_usage=ExtendedKeyUsage(
                server_auth=True
            ),
            subject_alt_names=san,
            authority_key_identifier=issuer_cert.subject_key_identifier
        )
        
        # Sign
        cert.signature = self._sign_certificate(cert, issuer_key)
        cert.subject_key_identifier = public_key.key_data[:16]
        
        # Store
        self.certificates[cert.serial_number] = cert
        self.private_keys[cert.serial_number] = private_key
        
        return cert, private_key
    
    def issue_client_certificate(
        self,
        common_name: str,
        email: Optional[str] = None,
        validity_days: int = 365,
        issuer_ca: Optional[str] = None
    ) -> Tuple[Certificate, PrivateKey]:
        """Issue client certificate"""
        # Determine issuing CA
        if issuer_ca and issuer_ca in self.intermediate_cas:
            issuer_cert, issuer_key = self.intermediate_cas[issuer_ca]
        else:
            issuer_cert = self.root_ca_cert
            issuer_key = self.root_ca_key
        
        # Generate key pair
        private_key = PrivateKey(KeyAlgorithm.RSA_2048)
        public_key = PublicKey.from_private_key(private_key)
        
        # Create DN
        subject = DistinguishedName(
            country=issuer_cert.subject.country,
            organization=issuer_cert.subject.organization,
            common_name=common_name,
            email=email
        )
        
        # Generate certificate
        now = datetime.utcnow()
        cert = Certificate(
            serial_number=self._generate_serial_number(),
            subject=subject,
            issuer=issuer_cert.subject,
            public_key=public_key,
            not_before=now,
            not_after=now + timedelta(days=validity_days),
            signature_algorithm=KeyAlgorithm.RSA_2048,
            certificate_type=CertificateType.CLIENT,
            basic_constraints_ca=False,
            key_usage=KeyUsage(
                digital_signature=True,
                key_encipherment=True
            ),
            extended_key_usage=ExtendedKeyUsage(
                client_auth=True,
                email_protection=True
            ),
            authority_key_identifier=issuer_cert.subject_key_identifier
        )
        
        # Sign
        cert.signature = self._sign_certificate(cert, issuer_key)
        cert.subject_key_identifier = public_key.key_data[:16]
        
        # Store
        self.certificates[cert.serial_number] = cert
        self.private_keys[cert.serial_number] = private_key
        
        return cert, private_key
    
    def _sign_certificate(self, cert: Certificate, private_key: PrivateKey) -> str:
        """Sign certificate with private key"""
        # Simulate signing
        cert_data = f"{cert.serial_number}{cert.subject.to_string()}{cert.not_before}{cert.not_after}"
        signature = hashlib.sha256(
            (cert_data + private_key.key_data).encode()
        ).hexdigest()
        return signature
    
    def revoke_certificate(
        self,
        serial_number: str,
        reason: RevocationReason = RevocationReason.UNSPECIFIED
    ) -> bool:
        """Revoke a certificate"""
        if serial_number not in self.certificates:
            return False
        
        cert = self.certificates[serial_number]
        cert.revoked = True
        cert.revocation_date = datetime.utcnow()
        cert.revocation_reason = reason
        
        return True
    
    def generate_crl(self) -> CertificateRevocationList:
        """Generate Certificate Revocation List"""
        revoked_certs = []
        
        for cert in self.certificates.values():
            if cert.revoked and cert.revocation_date and cert.revocation_reason:
                revoked_certs.append(RevokedCertificate(
                    serial_number=cert.serial_number,
                    revocation_date=cert.revocation_date,
                    revocation_reason=cert.revocation_reason
                ))
        
        now = datetime.utcnow()
        crl = CertificateRevocationList(
            issuer=self.root_ca_cert.subject,
            this_update=now,
            next_update=now + timedelta(days=7),
            revoked_certificates=revoked_certs,
            crl_number=self.crl_number
        )
        
        # Sign CRL
        crl_data = f"{crl.crl_number}{crl.this_update}{len(revoked_certs)}"
        crl.signature = hashlib.sha256(
            (crl_data + self.root_ca_key.key_data).encode()
        ).hexdigest()
        
        self.crl = crl
        self.crl_number += 1
        
        return crl
    
    def verify_certificate(self, cert: Certificate) -> bool:
        """Verify certificate signature and validity"""
        # Check expiration
        if not cert.is_valid():
            return False
        
        # Check if revoked
        if cert.revoked:
            return False
        
        # Verify signature (simplified)
        if cert.issuer == cert.subject:
            # Self-signed (root CA)
            expected_sig = self._sign_certificate(cert, self.root_ca_key)
        else:
            # Find issuer
            issuer_cert = None
            for c in self.certificates.values():
                if c.subject.to_string() == cert.issuer.to_string():
                    issuer_cert = c
                    break
            
            if not issuer_cert:
                return False
            
            issuer_key = self.private_keys.get(issuer_cert.serial_number)
            if not issuer_key:
                return False
            
            expected_sig = self._sign_certificate(cert, issuer_key)
        
        return cert.signature == expected_sig
    
    def get_certificate_chain(self, cert: Certificate) -> List[Certificate]:
        """Get certificate chain from leaf to root"""
        chain = [cert]
        
        current = cert
        while current.issuer.to_string() != current.subject.to_string():
            # Find issuer
            issuer_cert = None
            for c in self.certificates.values():
                if c.subject.to_string() == current.issuer.to_string():
                    issuer_cert = c
                    break
            
            if not issuer_cert:
                break
            
            chain.append(issuer_cert)
            current = issuer_cert
        
        return chain
    
    def export_certificate_bundle(self, cert: Certificate) -> str:
        """Export certificate with full chain in PEM format"""
        chain = self.get_certificate_chain(cert)
        bundle = ""
        for c in chain:
            bundle += c.to_pem() + "\n\n"
        return bundle.strip()


if __name__ == "__main__":
    # Example usage
    print("=== Certificate Authority Emulator Demo ===\n")
    
    # Create root CA
    ca = CertificateAuthority(
        ca_name="Example Root CA",
        country="US",
        organization="Example Inc.",
        validity_days=7300  # 20 years
    )
    
    print("1. Root CA Certificate")
    print("-" * 50)
    print(f"Subject: {ca.root_ca_cert.subject.to_string()}")
    print(f"Serial: {ca.root_ca_cert.serial_number}")
    print(f"Valid from: {ca.root_ca_cert.not_before}")
    print(f"Valid until: {ca.root_ca_cert.not_after}")
    print(f"Is CA: {ca.root_ca_cert.is_ca_certificate()}")
    
    # Create intermediate CA
    intermediate_cert, _ = ca.create_intermediate_ca(
        ca_name="Example Intermediate CA",
        validity_days=3650,
        path_len=0
    )
    
    print("\n2. Intermediate CA Certificate")
    print("-" * 50)
    print(f"Subject: {intermediate_cert.subject.to_string()}")
    print(f"Issuer: {intermediate_cert.issuer.to_string()}")
    print(f"Serial: {intermediate_cert.serial_number}")
    print(f"Is CA: {intermediate_cert.is_ca_certificate()}")
    print(f"Path Length: {intermediate_cert.basic_constraints_path_len}")
    
    # Issue server certificate
    server_cert, server_key = ca.issue_server_certificate(
        common_name="www.example.com",
        dns_names=["www.example.com", "example.com", "*.example.com"],
        ip_addresses=["192.168.1.1"],
        validity_days=365,
        issuer_ca="Example Intermediate CA"
    )
    
    print("\n3. Server Certificate")
    print("-" * 50)
    print(f"Subject: {server_cert.subject.to_string()}")
    print(f"Issuer: {server_cert.issuer.to_string()}")
    print(f"Serial: {server_cert.serial_number}")
    print(f"Valid: {server_cert.is_valid()}")
    if server_cert.subject_alt_names:
        print(f"DNS Names: {', '.join(server_cert.subject_alt_names.dns_names)}")
        print(f"IP Addresses: {', '.join(server_cert.subject_alt_names.ip_addresses)}")
    
    # Issue client certificate
    client_cert, client_key = ca.issue_client_certificate(
        common_name="John Doe",
        email="john.doe@example.com",
        validity_days=365
    )
    
    print("\n4. Client Certificate")
    print("-" * 50)
    print(f"Subject: {client_cert.subject.to_string()}")
    print(f"Serial: {client_cert.serial_number}")
    print(f"Valid: {client_cert.is_valid()}")
    
    # Verify certificates
    print("\n5. Certificate Verification")
    print("-" * 50)
    print(f"Root CA valid: {ca.verify_certificate(ca.root_ca_cert)}")
    print(f"Intermediate CA valid: {ca.verify_certificate(intermediate_cert)}")
    print(f"Server cert valid: {ca.verify_certificate(server_cert)}")
    print(f"Client cert valid: {ca.verify_certificate(client_cert)}")
    
    # Certificate chain
    print("\n6. Certificate Chain")
    print("-" * 50)
    chain = ca.get_certificate_chain(server_cert)
    for i, cert in enumerate(chain):
        print(f"  {i}. {cert.subject.common_name} (Serial: {cert.serial_number})")
    
    # Revoke certificate
    print("\n7. Certificate Revocation")
    print("-" * 50)
    print(f"Server cert valid before revocation: {server_cert.is_valid()}")
    ca.revoke_certificate(server_cert.serial_number, RevocationReason.KEY_COMPROMISE)
    print(f"Server cert valid after revocation: {server_cert.is_valid()}")
    
    # Generate CRL
    crl = ca.generate_crl()
    print(f"\nCRL Number: {crl.crl_number}")
    print(f"Revoked certificates: {len(crl.revoked_certificates)}")
    print(f"Server cert revoked in CRL: {crl.is_revoked(server_cert.serial_number)}")
    
    # Export certificate bundle
    print("\n8. Certificate Bundle (PEM)")
    print("-" * 50)
    bundle = ca.export_certificate_bundle(client_cert)
    print(bundle[:500] + "..." if len(bundle) > 500 else bundle)
