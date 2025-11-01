"""
Developed by PowerShield, as an alternative to SAML
"""

"""
Test suite for SAML Emulator
"""

import unittest
from datetime import datetime, timedelta
from SAMLAuth import (
    SAMLEmulator, SAMLServiceProvider,
    IdentityProvider, ServiceProvider, User,
    NameIDFormat, StatusCode, Attribute
)


class TestSAMLEmulator(unittest.TestCase):
    """Test SAML Identity Provider emulator"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Configure IdP
        self.idp_config = IdentityProvider(
            entity_id="https://idp.example.com",
            sso_url="https://idp.example.com/sso",
            slo_url="https://idp.example.com/slo"
        )
        self.idp = SAMLEmulator(self.idp_config)
        
        # Configure SP
        self.sp_config = ServiceProvider(
            entity_id="https://sp.example.com",
            acs_url="https://sp.example.com/acs",
            name_id_format=NameIDFormat.EMAIL
        )
        self.idp.register_service_provider(self.sp_config)
        
        # Add test user
        self.user = User(
            username="testuser",
            email="test@example.com",
            attributes={"firstName": "Test", "lastName": "User"},
            groups=["users", "testers"]
        )
        self.idp.add_user(self.user)
    
    def test_register_service_provider(self):
        """Test registering a service provider"""
        sp = ServiceProvider(
            entity_id="https://newsp.example.com",
            acs_url="https://newsp.example.com/acs"
        )
        self.idp.register_service_provider(sp)
        
        self.assertIn(sp.entity_id, self.idp.service_providers)
    
    def test_add_user(self):
        """Test adding a user"""
        new_user = User(
            username="newuser",
            email="newuser@example.com"
        )
        self.idp.add_user(new_user)
        
        self.assertIn("newuser", self.idp.users)
    
    def test_authenticate_user(self):
        """Test user authentication"""
        # Valid user
        user = self.idp.authenticate_user("testuser", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        
        # Invalid user
        user = self.idp.authenticate_user("nonexistent", "password")
        self.assertIsNone(user)
    
    def test_create_assertion(self):
        """Test creating a SAML assertion"""
        assertion = self.idp.create_assertion(
            self.user,
            self.sp_config.entity_id,
            "request_123"
        )
        
        self.assertIsNotNone(assertion)
        self.assertEqual(assertion.subject, self.user.email)
        self.assertEqual(assertion.audience, self.sp_config.entity_id)
        self.assertTrue(len(assertion.attributes) > 0)
        
        # Check time validity
        now = datetime.utcnow()
        self.assertLessEqual(assertion.not_before, now)
        self.assertGreater(assertion.not_on_or_after, now)
    
    def test_assertion_attributes(self):
        """Test assertion contains correct attributes"""
        assertion = self.idp.create_assertion(
            self.user,
            self.sp_config.entity_id,
            "request_123"
        )
        
        attr_names = [attr.name for attr in assertion.attributes]
        self.assertIn("email", attr_names)
        self.assertIn("username", attr_names)
        self.assertIn("groups", attr_names)
        
        # Check group values
        groups_attr = next(a for a in assertion.attributes if a.name == "groups")
        self.assertIn("users", groups_attr.value)
        self.assertIn("testers", groups_attr.value)
    
    def test_create_response_success(self):
        """Test creating a successful SAML response"""
        from saml_emulator import AuthnRequest
        
        request = AuthnRequest(
            id="request_123",
            issue_instant=datetime.utcnow(),
            sp_entity_id=self.sp_config.entity_id,
            acs_url=self.sp_config.acs_url,
            name_id_format=NameIDFormat.EMAIL
        )
        
        response = self.idp.create_response(request, self.user)
        
        self.assertEqual(response.status_code, StatusCode.SUCCESS)
        self.assertIsNotNone(response.assertion)
        self.assertEqual(response.in_response_to, request.id)
    
    def test_create_response_failure(self):
        """Test creating a failed SAML response"""
        from saml_emulator import AuthnRequest
        
        request = AuthnRequest(
            id="request_456",
            issue_instant=datetime.utcnow(),
            sp_entity_id=self.sp_config.entity_id,
            acs_url=self.sp_config.acs_url,
            name_id_format=NameIDFormat.EMAIL
        )
        
        response = self.idp.create_response(
            request,
            None,
            StatusCode.REQUESTER,
            "Authentication failed"
        )
        
        self.assertEqual(response.status_code, StatusCode.REQUESTER)
        self.assertIsNone(response.assertion)
        self.assertEqual(response.status_message, "Authentication failed")
    
    def test_encode_response(self):
        """Test encoding SAML response to base64"""
        from saml_emulator import AuthnRequest
        
        request = AuthnRequest(
            id="request_789",
            issue_instant=datetime.utcnow(),
            sp_entity_id=self.sp_config.entity_id,
            acs_url=self.sp_config.acs_url,
            name_id_format=NameIDFormat.EMAIL
        )
        
        response = self.idp.create_response(request, self.user)
        encoded = self.idp.encode_response(response)
        
        # Should be base64 encoded
        self.assertTrue(len(encoded) > 0)
        import base64
        decoded = base64.b64decode(encoded)
        self.assertTrue(b'samlp:Response' in decoded)
    
    def test_initiate_sso(self):
        """Test complete SSO flow"""
        from saml_emulator import AuthnRequest
        
        request = AuthnRequest(
            id="request_sso",
            issue_instant=datetime.utcnow(),
            sp_entity_id=self.sp_config.entity_id,
            acs_url=self.sp_config.acs_url,
            name_id_format=NameIDFormat.EMAIL
        )
        
        # Successful authentication
        response = self.idp.initiate_sso("testuser", "password", request)
        self.assertEqual(response.status_code, StatusCode.SUCCESS)
        self.assertIsNotNone(response.assertion)
        
        # Failed authentication
        response = self.idp.initiate_sso("baduser", "password", request)
        self.assertEqual(response.status_code, StatusCode.REQUESTER)
        self.assertIsNone(response.assertion)
    
    def test_validate_assertion(self):
        """Test assertion validation"""
        assertion = self.idp.create_assertion(
            self.user,
            self.sp_config.entity_id,
            "request_validate"
        )
        
        # Should be valid immediately after creation
        is_valid = self.idp.validate_assertion(assertion.id)
        self.assertTrue(is_valid)
        
        # Invalid assertion ID
        is_valid = self.idp.validate_assertion("nonexistent")
        self.assertFalse(is_valid)
    
    def test_logout(self):
        """Test single logout"""
        assertion = self.idp.create_assertion(
            self.user,
            self.sp_config.entity_id,
            "request_logout"
        )
        
        session_index = assertion.session_index
        
        # Should be valid before logout
        self.assertTrue(self.idp.validate_assertion(assertion.id))
        
        # Logout
        success = self.idp.logout(session_index)
        self.assertTrue(success)
        
        # Should be invalid after logout
        self.assertFalse(self.idp.validate_assertion(assertion.id))
    
    def test_get_metadata(self):
        """Test IdP metadata generation"""
        metadata = self.idp.get_metadata()
        
        self.assertIn(self.idp_config.entity_id, metadata)
        self.assertIn(self.idp_config.sso_url, metadata)
        self.assertIn('md:EntityDescriptor', metadata)


class TestSAMLServiceProvider(unittest.TestCase):
    """Test SAML Service Provider emulator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sp_config = ServiceProvider(
            entity_id="https://sp.example.com",
            acs_url="https://sp.example.com/acs",
            name_id_format=NameIDFormat.EMAIL
        )
        
        self.sp = SAMLServiceProvider(
            sp_config=self.sp_config,
            idp_sso_url="https://idp.example.com/sso"
        )
        
        # Also set up an IdP for integration tests
        idp_config = IdentityProvider(
            entity_id="https://idp.example.com",
            sso_url="https://idp.example.com/sso"
        )
        self.idp = SAMLEmulator(idp_config)
        self.idp.register_service_provider(self.sp_config)
        
        user = User(
            username="testuser",
            email="test@example.com"
        )
        self.idp.add_user(user)
    
    def test_create_authn_request(self):
        """Test creating authentication request"""
        request, encoded = self.sp.create_authn_request()
        
        self.assertIsNotNone(request)
        self.assertEqual(request.sp_entity_id, self.sp_config.entity_id)
        self.assertEqual(request.acs_url, self.sp_config.acs_url)
        
        # Check encoding
        self.assertTrue(len(encoded) > 0)
        import base64
        decoded = base64.b64decode(encoded)
        self.assertTrue(b'samlp:AuthnRequest' in decoded)
    
    def test_parse_response(self):
        """Test parsing SAML response"""
        # Create request
        request, encoded_request = self.sp.create_authn_request()
        
        # IdP processes request
        authn_request = self.idp.parse_authn_request(encoded_request)
        response = self.idp.initiate_sso("testuser", "password", authn_request)
        encoded_response = self.idp.encode_response(response)
        
        # SP parses response
        parsed_response = self.sp.parse_response(encoded_response)
        
        self.assertIsNotNone(parsed_response)
        self.assertEqual(parsed_response.status_code, StatusCode.SUCCESS)
        self.assertIsNotNone(parsed_response.assertion)
    
    def test_validate_response(self):
        """Test validating SAML response"""
        # Create and process request
        request, encoded_request = self.sp.create_authn_request()
        authn_request = self.idp.parse_authn_request(encoded_request)
        response = self.idp.initiate_sso("testuser", "password", authn_request)
        encoded_response = self.idp.encode_response(response)
        parsed_response = self.sp.parse_response(encoded_response)
        
        # Validate
        is_valid = self.sp.validate_response(parsed_response)
        self.assertTrue(is_valid)
    
    def test_full_sso_flow(self):
        """Test complete SSO flow from SP to IdP and back"""
        # 1. SP creates request
        request, encoded_request = self.sp.create_authn_request()
        
        # 2. IdP receives request
        authn_request = self.idp.parse_authn_request(encoded_request)
        self.assertEqual(authn_request.sp_entity_id, self.sp_config.entity_id)
        
        # 3. User authenticates
        response = self.idp.initiate_sso("testuser", "password", authn_request)
        self.assertEqual(response.status_code, StatusCode.SUCCESS)
        
        # 4. IdP sends response
        encoded_response = self.idp.encode_response(response)
        
        # 5. SP receives and parses response
        parsed_response = self.sp.parse_response(encoded_response)
        
        # 6. SP validates response
        is_valid = self.sp.validate_response(parsed_response)
        self.assertTrue(is_valid)
        
        # 7. Extract user info
        assertion = parsed_response.assertion
        self.assertEqual(assertion.subject, "test@example.com")
        self.assertTrue(len(assertion.attributes) > 0)


if __name__ == '__main__':
    unittest.main()
