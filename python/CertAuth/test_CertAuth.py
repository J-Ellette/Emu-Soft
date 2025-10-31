#!/usr/bin/env python3
"""
Tests for Certificate Authority Emulator
"""

import unittest
from datetime import datetime, timedelta
from CertAuth import (
    CertificateAuthority, DistinguishedName, RevocationReason,
    CertificateType, KeyAlgorithm
)


class TestCertificateAuthority(unittest.TestCase):
    """Test Certificate Authority functionality"""
    
    def setUp(self):
        """Set up test CA"""
        self.ca = CertificateAuthority(
            ca_name="Test Root CA",
            country="US",
            organization="Test Org",
            validity_days=3650
        )
    
    def test_root_ca_creation(self):
        """Test root CA certificate creation"""
        root = self.ca.root_ca_cert
        
        self.assertIsNotNone(root)
        self.assertEqual(root.subject.common_name, "Test Root CA")
        self.assertEqual(root.subject.country, "US")
        self.assertEqual(root.subject.organization, "Test Org")
        self.assertTrue(root.is_ca_certificate())
        self.assertEqual(root.certificate_type, CertificateType.ROOT_CA)
        
        # Root CA is self-signed
        self.assertEqual(root.subject.to_string(), root.issuer.to_string())
        
        # Validity check
        self.assertTrue(root.is_valid())
    
    def test_intermediate_ca_creation(self):
        """Test intermediate CA creation"""
        inter_cert, inter_key = self.ca.create_intermediate_ca(
            ca_name="Test Intermediate CA",
            validity_days=1825,
            path_len=0
        )
        
        self.assertEqual(inter_cert.subject.common_name, "Test Intermediate CA")
        self.assertTrue(inter_cert.is_ca_certificate())
        self.assertEqual(inter_cert.certificate_type, CertificateType.INTERMEDIATE_CA)
        self.assertEqual(inter_cert.basic_constraints_path_len, 0)
        
        # Issued by root
        self.assertEqual(inter_cert.issuer.common_name, "Test Root CA")
        
        # Validity
        self.assertTrue(inter_cert.is_valid())
    
    def test_server_certificate_issuance(self):
        """Test server certificate issuance"""
        cert, key = self.ca.issue_server_certificate(
            common_name="www.example.com",
            dns_names=["www.example.com", "example.com", "*.example.com"],
            ip_addresses=["192.168.1.1"],
            validity_days=365
        )
        
        self.assertEqual(cert.subject.common_name, "www.example.com")
        self.assertEqual(cert.certificate_type, CertificateType.SERVER)
        self.assertFalse(cert.is_ca_certificate())
        self.assertTrue(cert.is_valid())
        
        # Check SAN
        self.assertIsNotNone(cert.subject_alt_names)
        self.assertIn("www.example.com", cert.subject_alt_names.dns_names)
        self.assertIn("*.example.com", cert.subject_alt_names.dns_names)
        self.assertIn("192.168.1.1", cert.subject_alt_names.ip_addresses)
        
        # Check key usage
        self.assertIsNotNone(cert.key_usage)
        self.assertTrue(cert.key_usage.digital_signature)
        self.assertTrue(cert.key_usage.key_encipherment)
        
        # Check extended key usage
        self.assertIsNotNone(cert.extended_key_usage)
        self.assertTrue(cert.extended_key_usage.server_auth)
    
    def test_client_certificate_issuance(self):
        """Test client certificate issuance"""
        cert, key = self.ca.issue_client_certificate(
            common_name="John Doe",
            email="john@example.com",
            validity_days=365
        )
        
        self.assertEqual(cert.subject.common_name, "John Doe")
        self.assertEqual(cert.subject.email, "john@example.com")
        self.assertEqual(cert.certificate_type, CertificateType.CLIENT)
        self.assertFalse(cert.is_ca_certificate())
        self.assertTrue(cert.is_valid())
        
        # Check extended key usage
        self.assertIsNotNone(cert.extended_key_usage)
        self.assertTrue(cert.extended_key_usage.client_auth)
        self.assertTrue(cert.extended_key_usage.email_protection)
    
    def test_certificate_verification(self):
        """Test certificate verification"""
        # Root CA should be valid
        self.assertTrue(self.ca.verify_certificate(self.ca.root_ca_cert))
        
        # Intermediate CA should be valid
        inter_cert, _ = self.ca.create_intermediate_ca("Test Inter CA")
        self.assertTrue(self.ca.verify_certificate(inter_cert))
        
        # Server cert should be valid
        server_cert, _ = self.ca.issue_server_certificate("test.com")
        self.assertTrue(self.ca.verify_certificate(server_cert))
    
    def test_certificate_chain(self):
        """Test certificate chain building"""
        # Create intermediate CA
        inter_cert, _ = self.ca.create_intermediate_ca("Inter CA")
        
        # Issue server cert from intermediate
        server_cert, _ = self.ca.issue_server_certificate(
            "www.test.com",
            issuer_ca="Inter CA"
        )
        
        # Get chain
        chain = self.ca.get_certificate_chain(server_cert)
        
        # Chain should be: server -> intermediate -> root
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[0].subject.common_name, "www.test.com")
        self.assertEqual(chain[1].subject.common_name, "Inter CA")
        self.assertEqual(chain[2].subject.common_name, "Test Root CA")
    
    def test_certificate_revocation(self):
        """Test certificate revocation"""
        cert, _ = self.ca.issue_server_certificate("revoke.test.com")
        
        # Certificate should be valid initially
        self.assertTrue(cert.is_valid())
        self.assertFalse(cert.revoked)
        
        # Revoke certificate
        success = self.ca.revoke_certificate(
            cert.serial_number,
            RevocationReason.KEY_COMPROMISE
        )
        
        self.assertTrue(success)
        self.assertTrue(cert.revoked)
        self.assertIsNotNone(cert.revocation_date)
        self.assertEqual(cert.revocation_reason, RevocationReason.KEY_COMPROMISE)
        
        # Certificate should no longer be valid
        self.assertFalse(cert.is_valid())
    
    def test_crl_generation(self):
        """Test CRL generation"""
        # Issue and revoke some certificates
        cert1, _ = self.ca.issue_server_certificate("revoked1.com")
        cert2, _ = self.ca.issue_server_certificate("revoked2.com")
        cert3, _ = self.ca.issue_server_certificate("valid.com")
        
        self.ca.revoke_certificate(cert1.serial_number, RevocationReason.KEY_COMPROMISE)
        self.ca.revoke_certificate(cert2.serial_number, RevocationReason.SUPERSEDED)
        
        # Generate CRL
        crl = self.ca.generate_crl()
        
        self.assertIsNotNone(crl)
        self.assertEqual(len(crl.revoked_certificates), 2)
        self.assertTrue(crl.is_revoked(cert1.serial_number))
        self.assertTrue(crl.is_revoked(cert2.serial_number))
        self.assertFalse(crl.is_revoked(cert3.serial_number))
        
        # Check CRL metadata
        self.assertEqual(crl.issuer.common_name, "Test Root CA")
        self.assertIsNotNone(crl.this_update)
        self.assertIsNotNone(crl.next_update)
        self.assertIsNotNone(crl.signature)
    
    def test_certificate_pem_export(self):
        """Test PEM export"""
        cert, _ = self.ca.issue_server_certificate("pem.test.com")
        pem = cert.to_pem()
        
        self.assertIn("-----BEGIN CERTIFICATE-----", pem)
        self.assertIn("-----END CERTIFICATE-----", pem)
    
    def test_certificate_bundle_export(self):
        """Test certificate bundle export"""
        inter_cert, _ = self.ca.create_intermediate_ca("Bundle CA")
        server_cert, _ = self.ca.issue_server_certificate(
            "bundle.test.com",
            issuer_ca="Bundle CA"
        )
        
        bundle = self.ca.export_certificate_bundle(server_cert)
        
        # Should contain multiple certificates
        self.assertGreater(bundle.count("-----BEGIN CERTIFICATE-----"), 1)
        self.assertGreater(bundle.count("-----END CERTIFICATE-----"), 1)
    
    def test_distinguished_name(self):
        """Test Distinguished Name handling"""
        dn = DistinguishedName(
            country="US",
            state="California",
            locality="San Francisco",
            organization="Example Inc",
            organizational_unit="IT",
            common_name="test.example.com",
            email="admin@example.com"
        )
        
        dn_str = dn.to_string()
        
        self.assertIn("C=US", dn_str)
        self.assertIn("ST=California", dn_str)
        self.assertIn("L=San Francisco", dn_str)
        self.assertIn("O=Example Inc", dn_str)
        self.assertIn("OU=IT", dn_str)
        self.assertIn("CN=test.example.com", dn_str)
        self.assertIn("emailAddress=admin@example.com", dn_str)
    
    def test_serial_number_uniqueness(self):
        """Test that serial numbers are unique"""
        cert1, _ = self.ca.issue_server_certificate("test1.com")
        cert2, _ = self.ca.issue_server_certificate("test2.com")
        cert3, _ = self.ca.issue_server_certificate("test3.com")
        
        serials = {cert1.serial_number, cert2.serial_number, cert3.serial_number}
        self.assertEqual(len(serials), 3)  # All unique


if __name__ == "__main__":
    unittest.main()
