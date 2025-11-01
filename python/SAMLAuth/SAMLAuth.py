"""
Developed by PowerShield, as an alternative to SAML
"""

"""
SAML Authentication Provider Emulator

Emulates core SAML 2.0 authentication and authorization functionality for
single sign-on (SSO) systems.
"""

import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET


class BindingType(Enum):
    """SAML binding types"""
    HTTP_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    HTTP_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    SOAP = "urn:oasis:names:tc:SAML:2.0:bindings:SOAP"
    ARTIFACT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact"


class NameIDFormat(Enum):
    """SAML NameID formats"""
    EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"
    UNSPECIFIED = "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"


class StatusCode(Enum):
    """SAML status codes"""
    SUCCESS = "urn:oasis:names:tc:SAML:2.0:status:Success"
    REQUESTER = "urn:oasis:names:tc:SAML:2.0:status:Requester"
    RESPONDER = "urn:oasis:names:tc:SAML:2.0:status:Responder"
    VERSION_MISMATCH = "urn:oasis:names:tc:SAML:2.0:status:VersionMismatch"


@dataclass
class Attribute:
    """SAML attribute"""
    name: str
    value: Any
    name_format: str = "urn:oasis:names:tc:SAML:2.0:attrname-format:basic"


@dataclass
class ServiceProvider:
    """SAML Service Provider configuration"""
    entity_id: str
    acs_url: str  # Assertion Consumer Service URL
    slo_url: Optional[str] = None  # Single Logout URL
    certificate: Optional[str] = None
    name_id_format: NameIDFormat = NameIDFormat.EMAIL
    attributes_required: List[str] = field(default_factory=list)


@dataclass
class IdentityProvider:
    """SAML Identity Provider configuration"""
    entity_id: str
    sso_url: str  # Single Sign-On URL
    slo_url: Optional[str] = None
    certificate: str = ""
    signing_key: str = ""


@dataclass
class User:
    """User identity for SAML authentication"""
    username: str
    email: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    groups: List[str] = field(default_factory=list)


@dataclass
class AuthnRequest:
    """SAML Authentication Request"""
    id: str
    issue_instant: datetime
    sp_entity_id: str
    acs_url: str
    name_id_format: NameIDFormat
    force_authn: bool = False
    is_passive: bool = False


@dataclass
class Assertion:
    """SAML Assertion"""
    id: str
    issue_instant: datetime
    issuer: str
    subject: str
    audience: str
    attributes: List[Attribute]
    not_before: datetime
    not_on_or_after: datetime
    authn_instant: datetime
    session_index: str


@dataclass
class SAMLResponse:
    """SAML Response"""
    id: str
    issue_instant: datetime
    in_response_to: str
    issuer: str
    status_code: StatusCode
    assertion: Optional[Assertion] = None
    status_message: Optional[str] = None


class SAMLEmulator:
    """
    Emulates a SAML 2.0 Identity Provider (IdP) for authentication
    """
    
    def __init__(self, idp_config: IdentityProvider):
        self.idp_config = idp_config
        self.service_providers: Dict[str, ServiceProvider] = {}
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.requests: Dict[str, AuthnRequest] = {}
    
    def register_service_provider(self, sp: ServiceProvider) -> None:
        """Register a Service Provider with the IdP"""
        self.service_providers[sp.entity_id] = sp
    
    def add_user(self, user: User) -> None:
        """Add a user to the identity provider"""
        self.users[user.username] = user
    
    def parse_authn_request(self, saml_request: str) -> AuthnRequest:
        """Parse a SAML Authentication Request"""
        # Decode base64 and parse XML
        try:
            decoded = base64.b64decode(saml_request)
            root = ET.fromstring(decoded)
        except Exception:
            # Simplified parsing for emulation
            request_id = str(uuid.uuid4())
            return AuthnRequest(
                id=request_id,
                issue_instant=datetime.utcnow(),
                sp_entity_id="unknown",
                acs_url="",
                name_id_format=NameIDFormat.EMAIL
            )
        
        # Extract request details
        request_id = root.get('ID', str(uuid.uuid4()))
        issue_instant = datetime.utcnow()
        
        # Find issuer
        issuer_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Issuer')
        sp_entity_id = issuer_elem.text if issuer_elem is not None else "unknown"
        
        # Get ACS URL
        acs_url = root.get('AssertionConsumerServiceURL', '')
        
        request = AuthnRequest(
            id=request_id,
            issue_instant=issue_instant,
            sp_entity_id=sp_entity_id,
            acs_url=acs_url,
            name_id_format=NameIDFormat.EMAIL,
            force_authn=root.get('ForceAuthn', 'false').lower() == 'true',
            is_passive=root.get('IsPassive', 'false').lower() == 'true'
        )
        
        self.requests[request_id] = request
        return request
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user (simplified - no real password check)"""
        user = self.users.get(username)
        if user:
            # In real implementation, verify password hash
            # For emulation, just return the user
            return user
        return None
    
    def create_assertion(
        self,
        user: User,
        sp_entity_id: str,
        request_id: str
    ) -> Assertion:
        """Create a SAML assertion for authenticated user"""
        assertion_id = f"_assertion_{uuid.uuid4().hex}"
        now = datetime.utcnow()
        session_index = str(uuid.uuid4())
        
        # Get SP configuration
        sp = self.service_providers.get(sp_entity_id)
        if not sp:
            raise ValueError(f"Unknown Service Provider: {sp_entity_id}")
        
        # Build attributes
        attributes = [
            Attribute(name="email", value=user.email),
            Attribute(name="username", value=user.username),
        ]
        
        # Add user custom attributes
        for attr_name, attr_value in user.attributes.items():
            attributes.append(Attribute(name=attr_name, value=attr_value))
        
        # Add groups
        if user.groups:
            attributes.append(Attribute(name="groups", value=",".join(user.groups)))
        
        assertion = Assertion(
            id=assertion_id,
            issue_instant=now,
            issuer=self.idp_config.entity_id,
            subject=user.email,
            audience=sp_entity_id,
            attributes=attributes,
            not_before=now,
            not_on_or_after=now + timedelta(minutes=5),
            authn_instant=now,
            session_index=session_index
        )
        
        # Store session
        self.sessions[session_index] = {
            'user': user.username,
            'sp': sp_entity_id,
            'assertion_id': assertion_id,
            'created': now
        }
        
        return assertion
    
    def create_response(
        self,
        request: AuthnRequest,
        user: Optional[User],
        status_code: StatusCode = StatusCode.SUCCESS,
        status_message: Optional[str] = None
    ) -> SAMLResponse:
        """Create a SAML Response"""
        response_id = f"_response_{uuid.uuid4().hex}"
        now = datetime.utcnow()
        
        assertion = None
        if user and status_code == StatusCode.SUCCESS:
            assertion = self.create_assertion(
                user,
                request.sp_entity_id,
                request.id
            )
        
        response = SAMLResponse(
            id=response_id,
            issue_instant=now,
            in_response_to=request.id,
            issuer=self.idp_config.entity_id,
            status_code=status_code,
            assertion=assertion,
            status_message=status_message
        )
        
        return response
    
    def encode_response(self, response: SAMLResponse) -> str:
        """Encode SAML response to base64 XML"""
        # Build XML structure
        root = ET.Element('samlp:Response')
        root.set('xmlns:samlp', 'urn:oasis:names:tc:SAML:2.0:protocol')
        root.set('xmlns:saml', 'urn:oasis:names:tc:SAML:2.0:assertion')
        root.set('ID', response.id)
        root.set('Version', '2.0')
        root.set('IssueInstant', response.issue_instant.isoformat() + 'Z')
        root.set('InResponseTo', response.in_response_to)
        
        # Issuer
        issuer = ET.SubElement(root, 'saml:Issuer')
        issuer.text = response.issuer
        
        # Status
        status = ET.SubElement(root, 'samlp:Status')
        status_code = ET.SubElement(status, 'samlp:StatusCode')
        status_code.set('Value', response.status_code.value)
        
        if response.status_message:
            status_msg = ET.SubElement(status, 'samlp:StatusMessage')
            status_msg.text = response.status_message
        
        # Assertion
        if response.assertion:
            assertion_elem = ET.SubElement(root, 'saml:Assertion')
            assertion_elem.set('ID', response.assertion.id)
            assertion_elem.set('Version', '2.0')
            assertion_elem.set('IssueInstant', response.assertion.issue_instant.isoformat() + 'Z')
            
            # Subject
            subject = ET.SubElement(assertion_elem, 'saml:Subject')
            name_id = ET.SubElement(subject, 'saml:NameID')
            name_id.text = response.assertion.subject
            
            # Conditions
            conditions = ET.SubElement(assertion_elem, 'saml:Conditions')
            conditions.set('NotBefore', response.assertion.not_before.isoformat() + 'Z')
            conditions.set('NotOnOrAfter', response.assertion.not_on_or_after.isoformat() + 'Z')
            
            audience_restriction = ET.SubElement(conditions, 'saml:AudienceRestriction')
            audience = ET.SubElement(audience_restriction, 'saml:Audience')
            audience.text = response.assertion.audience
            
            # Attributes
            if response.assertion.attributes:
                attr_statement = ET.SubElement(assertion_elem, 'saml:AttributeStatement')
                for attr in response.assertion.attributes:
                    attr_elem = ET.SubElement(attr_statement, 'saml:Attribute')
                    attr_elem.set('Name', attr.name)
                    attr_elem.set('NameFormat', attr.name_format)
                    
                    attr_value = ET.SubElement(attr_elem, 'saml:AttributeValue')
                    attr_value.text = str(attr.value)
        
        # Convert to string and encode
        xml_str = ET.tostring(root, encoding='unicode')
        encoded = base64.b64encode(xml_str.encode('utf-8')).decode('utf-8')
        
        return encoded
    
    def initiate_sso(
        self,
        username: str,
        password: str,
        authn_request: AuthnRequest
    ) -> SAMLResponse:
        """
        Initiate Single Sign-On flow
        
        1. Authenticate user
        2. Create assertion
        3. Create response
        """
        # Authenticate
        user = self.authenticate_user(username, password)
        
        if not user:
            return self.create_response(
                authn_request,
                None,
                StatusCode.REQUESTER,
                "Authentication failed"
            )
        
        # Create successful response
        return self.create_response(authn_request, user)
    
    def validate_assertion(self, assertion_id: str) -> bool:
        """Validate an assertion"""
        # Check if assertion exists in any session
        for session_data in self.sessions.values():
            if session_data.get('assertion_id') == assertion_id:
                # Check expiration
                created = session_data.get('created')
                if datetime.utcnow() - created < timedelta(minutes=5):
                    return True
        return False
    
    def logout(self, session_index: str) -> bool:
        """
        Perform Single Logout
        """
        if session_index in self.sessions:
            del self.sessions[session_index]
            return True
        return False
    
    def get_metadata(self) -> str:
        """Generate IdP metadata XML"""
        root = ET.Element('md:EntityDescriptor')
        root.set('xmlns:md', 'urn:oasis:names:tc:SAML:2.0:metadata')
        root.set('entityID', self.idp_config.entity_id)
        
        idp_sso = ET.SubElement(root, 'md:IDPSSODescriptor')
        idp_sso.set('protocolSupportEnumeration', 'urn:oasis:names:tc:SAML:2.0:protocol')
        
        # Single Sign-On Service
        sso_service = ET.SubElement(idp_sso, 'md:SingleSignOnService')
        sso_service.set('Binding', BindingType.HTTP_POST.value)
        sso_service.set('Location', self.idp_config.sso_url)
        
        # Single Logout Service
        if self.idp_config.slo_url:
            slo_service = ET.SubElement(idp_sso, 'md:SingleLogoutService')
            slo_service.set('Binding', BindingType.HTTP_POST.value)
            slo_service.set('Location', self.idp_config.slo_url)
        
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str


class SAMLServiceProvider:
    """
    Emulates a SAML 2.0 Service Provider (SP)
    """
    
    def __init__(self, sp_config: ServiceProvider, idp_sso_url: str):
        self.sp_config = sp_config
        self.idp_sso_url = idp_sso_url
        self.pending_requests: Dict[str, AuthnRequest] = {}
    
    def create_authn_request(self) -> tuple[AuthnRequest, str]:
        """Create a SAML Authentication Request"""
        request_id = f"_request_{uuid.uuid4().hex}"
        
        request = AuthnRequest(
            id=request_id,
            issue_instant=datetime.utcnow(),
            sp_entity_id=self.sp_config.entity_id,
            acs_url=self.sp_config.acs_url,
            name_id_format=self.sp_config.name_id_format
        )
        
        self.pending_requests[request_id] = request
        
        # Build XML
        root = ET.Element('samlp:AuthnRequest')
        root.set('xmlns:samlp', 'urn:oasis:names:tc:SAML:2.0:protocol')
        root.set('xmlns:saml', 'urn:oasis:names:tc:SAML:2.0:assertion')
        root.set('ID', request.id)
        root.set('Version', '2.0')
        root.set('IssueInstant', request.issue_instant.isoformat() + 'Z')
        root.set('AssertionConsumerServiceURL', request.acs_url)
        
        # Issuer
        issuer = ET.SubElement(root, 'saml:Issuer')
        issuer.text = request.sp_entity_id
        
        # NameIDPolicy
        name_id_policy = ET.SubElement(root, 'samlp:NameIDPolicy')
        name_id_policy.set('Format', request.name_id_format.value)
        name_id_policy.set('AllowCreate', 'true')
        
        xml_str = ET.tostring(root, encoding='unicode')
        encoded = base64.b64encode(xml_str.encode('utf-8')).decode('utf-8')
        
        return request, encoded
    
    def parse_response(self, saml_response: str) -> SAMLResponse:
        """Parse SAML response from IdP"""
        # Decode
        decoded = base64.b64decode(saml_response)
        root = ET.fromstring(decoded)
        
        # Parse response
        response_id = root.get('ID')
        in_response_to = root.get('InResponseTo')
        
        # Parse issuer
        issuer_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Issuer')
        issuer = issuer_elem.text if issuer_elem is not None else ""
        
        # Parse status
        status_code_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:protocol}StatusCode')
        status_value = status_code_elem.get('Value') if status_code_elem is not None else ""
        
        status_code = StatusCode.SUCCESS
        for code in StatusCode:
            if code.value == status_value:
                status_code = code
                break
        
        # Parse assertion if present
        assertion = None
        assertion_elem = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion')
        if assertion_elem is not None:
            assertion_id = assertion_elem.get('ID')
            
            # Subject
            subject_elem = assertion_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}NameID')
            subject = subject_elem.text if subject_elem is not None else ""
            
            # Parse attributes
            attributes = []
            for attr_elem in assertion_elem.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
                attr_name = attr_elem.get('Name')
                value_elem = attr_elem.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue')
                attr_value = value_elem.text if value_elem is not None else ""
                attributes.append(Attribute(name=attr_name, value=attr_value))
            
            assertion = Assertion(
                id=assertion_id,
                issue_instant=datetime.utcnow(),
                issuer=issuer,
                subject=subject,
                audience=self.sp_config.entity_id,
                attributes=attributes,
                not_before=datetime.utcnow(),
                not_on_or_after=datetime.utcnow() + timedelta(minutes=5),
                authn_instant=datetime.utcnow(),
                session_index=str(uuid.uuid4())
            )
        
        response = SAMLResponse(
            id=response_id,
            issue_instant=datetime.utcnow(),
            in_response_to=in_response_to,
            issuer=issuer,
            status_code=status_code,
            assertion=assertion
        )
        
        return response
    
    def validate_response(self, response: SAMLResponse) -> bool:
        """Validate SAML response"""
        # Check if response is for our request
        if response.in_response_to not in self.pending_requests:
            return False
        
        # Check status
        if response.status_code != StatusCode.SUCCESS:
            return False
        
        # Check assertion
        if not response.assertion:
            return False
        
        # Check audience
        if response.assertion.audience != self.sp_config.entity_id:
            return False
        
        # Check time validity
        now = datetime.utcnow()
        if now < response.assertion.not_before or now >= response.assertion.not_on_or_after:
            return False
        
        return True
