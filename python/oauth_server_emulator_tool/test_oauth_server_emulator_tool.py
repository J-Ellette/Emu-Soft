#!/usr/bin/env python3
"""
Tests for OAuth 2.0/OIDC Server Emulator
"""

import unittest
import urllib.parse
import hashlib
import base64
import secrets
from oauth_server_emulator_tool import (
    OAuthServer, Client, User, GrantType, TokenType
)


class TestOAuthServer(unittest.TestCase):
    """Test OAuth 2.0/OIDC Server functionality"""
    
    def setUp(self):
        """Set up test server and clients"""
        self.server = OAuthServer(issuer="https://auth.test.com")
        
        # Register test client
        self.client = self.server.register_client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uris=["https://app.test.com/callback"],
            grant_types=["authorization_code", "password", "client_credentials", "refresh_token"],
            response_types=["code", "token"],
            scopes=["openid", "profile", "email", "read", "write"]
        )
        
        # Register test user
        self.user = self.server.register_user(
            user_id="user123",
            username="testuser",
            password="password123",
            email="test@example.com",
            profile={"name": "Test User"}
        )
    
    def test_client_registration(self):
        """Test client registration"""
        self.assertEqual(self.client.client_id, "test_client")
        self.assertEqual(self.client.client_secret, "test_secret")
        self.assertIn("https://app.test.com/callback", self.client.redirect_uris)
        self.assertTrue(self.client.supports_grant_type("authorization_code"))
        self.assertTrue(self.client.has_scope("openid"))
    
    def test_user_registration(self):
        """Test user registration"""
        self.assertEqual(self.user.user_id, "user123")
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.verify_password("password123"))
        self.assertFalse(self.user.verify_password("wrong"))
    
    def test_authorization_code_flow(self):
        """Test authorization code flow"""
        # Step 1: Authorize
        auth_request = self.server.authorize(
            client_id="test_client",
            response_type="code",
            redirect_uri="https://app.test.com/callback",
            scope="openid profile email",
            state="abc123"
        )
        self.assertEqual(auth_request["status"], "authorization_required")
        
        # Step 2: Grant authorization
        redirect_url = self.server.grant_authorization(
            user_id="user123",
            client_id="test_client",
            redirect_uri="https://app.test.com/callback",
            scopes={"openid", "profile", "email"},
            state="abc123"
        )
        self.assertIn("code=", redirect_url)
        self.assertIn("state=abc123", redirect_url)
        
        # Extract code
        parsed = urllib.parse.urlparse(redirect_url)
        query = urllib.parse.parse_qs(parsed.query)
        code = query["code"][0]
        
        # Step 3: Exchange code for tokens
        token_response = self.server.token(
            grant_type="authorization_code",
            client_id="test_client",
            client_secret="test_secret",
            code=code,
            redirect_uri="https://app.test.com/callback"
        )
        
        self.assertIn("access_token", token_response)
        self.assertIn("refresh_token", token_response)
        self.assertIn("id_token", token_response)
        self.assertEqual(token_response["token_type"], "Bearer")
        self.assertEqual(token_response["expires_in"], 3600)
    
    def test_password_grant(self):
        """Test password grant flow"""
        token_response = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="password123",
            scope="openid email"
        )
        
        self.assertIn("access_token", token_response)
        self.assertIn("refresh_token", token_response)
        self.assertIn("id_token", token_response)
        self.assertEqual(token_response["scope"], "openid email")
    
    def test_client_credentials_grant(self):
        """Test client credentials grant"""
        token_response = self.server.token(
            grant_type="client_credentials",
            client_id="test_client",
            client_secret="test_secret",
            scope="read write"
        )
        
        self.assertIn("access_token", token_response)
        self.assertEqual(token_response["scope"], "read write")
        # Client credentials should not have ID token
        self.assertNotIn("id_token", token_response)
    
    def test_refresh_token_grant(self):
        """Test refresh token grant"""
        # Get initial tokens
        initial_response = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="password123",
            scope="openid profile"
        )
        
        refresh_token = initial_response["refresh_token"]
        
        # Refresh tokens
        refreshed_response = self.server.token(
            grant_type="refresh_token",
            client_id="test_client",
            client_secret="test_secret",
            refresh_token=refresh_token
        )
        
        self.assertIn("access_token", refreshed_response)
        self.assertIn("refresh_token", refreshed_response)
        self.assertNotEqual(
            initial_response["access_token"],
            refreshed_response["access_token"]
        )
    
    def test_token_introspection(self):
        """Test token introspection"""
        # Get access token
        token_response = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="password123",
            scope="read"
        )
        
        access_token = token_response["access_token"]
        
        # Introspect token
        introspection = self.server.introspect(access_token)
        
        self.assertTrue(introspection["active"])
        self.assertEqual(introspection["client_id"], "test_client")
        self.assertEqual(introspection["username"], "user123")
        self.assertEqual(introspection["scope"], "read")
        self.assertIn("exp", introspection)
        self.assertIn("iat", introspection)
    
    def test_token_revocation(self):
        """Test token revocation"""
        # Get access token
        token_response = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="password123"
        )
        
        access_token = token_response["access_token"]
        
        # Verify token is active
        introspection = self.server.introspect(access_token)
        self.assertTrue(introspection["active"])
        
        # Revoke token
        revoked = self.server.revoke(access_token)
        self.assertTrue(revoked)
        
        # Verify token is inactive
        introspection = self.server.introspect(access_token)
        self.assertFalse(introspection["active"])
    
    def test_userinfo_endpoint(self):
        """Test UserInfo endpoint"""
        # Get access token with profile scope
        token_response = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="password123",
            scope="openid profile email"
        )
        
        access_token = token_response["access_token"]
        
        # Get user info
        userinfo = self.server.userinfo(access_token)
        
        self.assertEqual(userinfo["sub"], "user123")
        self.assertEqual(userinfo["email"], "test@example.com")
        self.assertEqual(userinfo["name"], "Test User")
    
    def test_pkce_flow(self):
        """Test PKCE (Proof Key for Code Exchange)"""
        # Generate code verifier and challenge
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).rstrip(b'=').decode()
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        
        # Authorize with PKCE
        auth_request = self.server.authorize(
            client_id="test_client",
            response_type="code",
            redirect_uri="https://app.test.com/callback",
            scope="openid",
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
        
        # Grant authorization with PKCE
        redirect_url = self.server.grant_authorization(
            user_id="user123",
            client_id="test_client",
            redirect_uri="https://app.test.com/callback",
            scopes={"openid"},
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
        
        # Extract code
        code = urllib.parse.parse_qs(
            urllib.parse.urlparse(redirect_url).query
        )["code"][0]
        
        # Exchange code with verifier
        token_response = self.server.token(
            grant_type="authorization_code",
            client_id="test_client",
            client_secret="test_secret",
            code=code,
            redirect_uri="https://app.test.com/callback",
            code_verifier=code_verifier
        )
        
        self.assertIn("access_token", token_response)
    
    def test_invalid_client(self):
        """Test invalid client ID"""
        result = self.server.authorize(
            client_id="invalid_client",
            response_type="code",
            redirect_uri="https://app.test.com/callback",
            scope="openid"
        )
        self.assertEqual(result["error"], "invalid_client")
    
    def test_invalid_redirect_uri(self):
        """Test invalid redirect URI"""
        result = self.server.authorize(
            client_id="test_client",
            response_type="code",
            redirect_uri="https://evil.com/callback",
            scope="openid"
        )
        self.assertEqual(result["error"], "invalid_redirect_uri")
    
    def test_invalid_password(self):
        """Test invalid password"""
        result = self.server.token(
            grant_type="password",
            client_id="test_client",
            client_secret="test_secret",
            username="testuser",
            password="wrongpassword"
        )
        self.assertEqual(result["error"], "invalid_grant")
    
    def test_discovery_document(self):
        """Test OpenID Connect discovery document"""
        discovery = self.server.get_discovery_document()
        
        self.assertEqual(discovery["issuer"], "https://auth.test.com")
        self.assertIn("authorization_endpoint", discovery)
        self.assertIn("token_endpoint", discovery)
        self.assertIn("userinfo_endpoint", discovery)
        self.assertIn("openid", discovery["scopes_supported"])
        self.assertIn("authorization_code", discovery["grant_types_supported"])


if __name__ == "__main__":
    unittest.main()
