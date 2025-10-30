"""Security hardening profiles for different deployment environments.

This module provides predefined security configurations for various deployment
scenarios including public, intranet, government, and healthcare environments.
It also includes compliance preset configurations for HIPAA, PCI-DSS, GDPR, and SOC2.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import timedelta
import json


class ProfileType(Enum):
    """Types of security profiles."""

    PUBLIC = "public"
    INTRANET = "intranet"
    GOVERNMENT = "government"
    HEALTHCARE = "healthcare"
    CUSTOM = "custom"


class ComplianceStandard(Enum):
    """Compliance standards."""

    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOC2 = "soc2"
    FISMA = "fisma"
    FEDRAMP = "fedramp"


@dataclass
class SecuritySettings:
    """Security settings configuration."""

    # Security Headers
    csp_policy: str = "default-src 'self'"
    hsts_max_age: int = 31536000  # 1 year
    frame_options: str = "DENY"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    # CSRF Protection
    csrf_enabled: bool = True
    csrf_token_name: str = "csrf_token"
    csrf_cookie_name: str = "csrf_token"
    csrf_exempt_paths: Set[str] = field(default_factory=set)

    # Rate Limiting
    rate_limit_enabled: bool = True
    max_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_exempt_paths: Set[str] = field(default_factory=set)

    # Session Security
    session_timeout_minutes: int = 30
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "Strict"

    # Password Policy
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_expiry_days: int = 90
    password_history_count: int = 5

    # Two-Factor Authentication
    require_2fa: bool = False
    require_2fa_for_roles: Set[str] = field(default_factory=set)

    # Audit Logging
    audit_enabled: bool = True
    audit_log_retention_days: int = 365
    audit_failed_logins: bool = True
    audit_data_access: bool = True
    audit_data_modifications: bool = True

    # IP Restrictions
    ip_whitelist: Set[str] = field(default_factory=set)
    ip_blacklist: Set[str] = field(default_factory=set)
    ip_restrictions_enabled: bool = False

    # File Upload Security
    max_upload_size_mb: int = 10
    allowed_file_extensions: Set[str] = field(
        default_factory=lambda: {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".doc",
            ".docx",
        }
    )
    scan_uploads_for_malware: bool = True

    # Encryption
    encryption_algorithm: str = "AES-256-GCM"
    encrypt_sensitive_data: bool = True
    tls_version: str = "1.3"
    tls_ciphers: List[str] = field(
        default_factory=lambda: [
            "TLS_AES_256_GCM_SHA384",
            "TLS_AES_128_GCM_SHA256",
            "TLS_CHACHA20_POLY1305_SHA256",
        ]
    )

    # Additional Security Features
    enable_content_security_policy: bool = True
    enable_xss_protection: bool = True
    enable_clickjacking_protection: bool = True
    enable_mime_sniffing_protection: bool = True
    enable_cors: bool = False
    cors_allowed_origins: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, set):
                result[key] = list(value)
            else:
                result[key] = value
        return result

    def to_json(self) -> str:
        """Convert settings to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ComplianceRequirements:
    """Compliance requirements configuration."""

    standard: ComplianceStandard
    requirements: List[str] = field(default_factory=list)
    mandatory_settings: Dict[str, Any] = field(default_factory=dict)
    recommended_settings: Dict[str, Any] = field(default_factory=dict)
    documentation_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert requirements to dictionary."""
        return {
            "standard": self.standard.value,
            "requirements": self.requirements,
            "mandatory_settings": self.mandatory_settings,
            "recommended_settings": self.recommended_settings,
            "documentation_url": self.documentation_url,
        }


class SecurityProfile:
    """Security profile with predefined settings."""

    def __init__(
        self,
        name: str,
        profile_type: ProfileType,
        description: str,
        settings: SecuritySettings,
        compliance_standards: Optional[List[ComplianceStandard]] = None,
    ) -> None:
        """Initialize security profile.

        Args:
            name: Profile name
            profile_type: Type of profile
            description: Profile description
            settings: Security settings
            compliance_standards: List of compliance standards this profile meets
        """
        self.name = name
        self.profile_type = profile_type
        self.description = description
        self.settings = settings
        self.compliance_standards = compliance_standards or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "profile_type": self.profile_type.value,
            "description": self.description,
            "settings": self.settings.to_dict(),
            "compliance_standards": [s.value for s in self.compliance_standards],
        }

    def to_json(self) -> str:
        """Convert profile to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ProfileFactory:
    """Factory for creating predefined security profiles."""

    @staticmethod
    def create_public_profile() -> SecurityProfile:
        """Create a security profile for public-facing websites.

        This profile balances security with accessibility for general public use.

        Returns:
            SecurityProfile configured for public deployment
        """
        settings = SecuritySettings(
            # Moderate security headers
            csp_policy="default-src 'self' https:; img-src 'self' https: data:; "
            "script-src 'self' 'unsafe-inline' https:",
            hsts_max_age=31536000,
            frame_options="SAMEORIGIN",
            # Standard CSRF protection
            csrf_enabled=True,
            # Moderate rate limiting
            rate_limit_enabled=True,
            max_requests=100,
            rate_limit_window_seconds=60,
            # Standard session settings
            session_timeout_minutes=60,
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Lax",
            # Moderate password policy
            min_password_length=10,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=False,
            password_expiry_days=0,  # No expiry
            password_history_count=3,
            # Optional 2FA
            require_2fa=False,
            require_2fa_for_roles={"admin"},
            # Standard audit logging
            audit_enabled=True,
            audit_log_retention_days=90,
            # No IP restrictions
            ip_restrictions_enabled=False,
            # Standard file upload settings
            max_upload_size_mb=10,
            scan_uploads_for_malware=True,
            # Enable CORS for public APIs
            enable_cors=True,
        )

        return SecurityProfile(
            name="Public Website",
            profile_type=ProfileType.PUBLIC,
            description="Balanced security profile for public-facing websites",
            settings=settings,
            compliance_standards=[ComplianceStandard.GDPR],
        )

    @staticmethod
    def create_intranet_profile() -> SecurityProfile:
        """Create a security profile for internal intranet applications.

        This profile provides enhanced security for internal corporate use.

        Returns:
            SecurityProfile configured for intranet deployment
        """
        settings = SecuritySettings(
            # Strict security headers
            csp_policy="default-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'",
            hsts_max_age=63072000,  # 2 years
            frame_options="DENY",
            # Strict CSRF protection
            csrf_enabled=True,
            # Stricter rate limiting
            rate_limit_enabled=True,
            max_requests=60,
            rate_limit_window_seconds=60,
            # Shorter session timeout
            session_timeout_minutes=30,
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            # Strong password policy
            min_password_length=12,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=True,
            password_expiry_days=90,
            password_history_count=5,
            # 2FA for privileged users
            require_2fa=False,
            require_2fa_for_roles={"admin", "manager"},
            # Comprehensive audit logging
            audit_enabled=True,
            audit_log_retention_days=365,
            audit_failed_logins=True,
            audit_data_access=True,
            audit_data_modifications=True,
            # IP restrictions can be enabled
            ip_restrictions_enabled=True,
            # Stricter file upload settings
            max_upload_size_mb=5,
            scan_uploads_for_malware=True,
            # No CORS for internal use
            enable_cors=False,
        )

        return SecurityProfile(
            name="Internal Intranet",
            profile_type=ProfileType.INTRANET,
            description="Enhanced security profile for internal corporate applications",
            settings=settings,
            compliance_standards=[ComplianceStandard.SOC2],
        )

    @staticmethod
    def create_government_profile() -> SecurityProfile:
        """Create a security profile for government applications.

        This profile meets strict government security requirements like FISMA/FedRAMP.

        Returns:
            SecurityProfile configured for government deployment
        """
        settings = SecuritySettings(
            # Maximum security headers
            csp_policy="default-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'",
            hsts_max_age=63072000,  # 2 years
            frame_options="DENY",
            referrer_policy="no-referrer",
            permissions_policy="geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()",
            # Mandatory CSRF protection
            csrf_enabled=True,
            # Strict rate limiting
            rate_limit_enabled=True,
            max_requests=30,
            rate_limit_window_seconds=60,
            # Very short session timeout
            session_timeout_minutes=15,
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            # Very strong password policy
            min_password_length=16,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=True,
            password_expiry_days=60,
            password_history_count=10,
            # Mandatory 2FA for all users
            require_2fa=True,
            require_2fa_for_roles=set(),  # All users
            # Maximum audit logging
            audit_enabled=True,
            audit_log_retention_days=2555,  # 7 years
            audit_failed_logins=True,
            audit_data_access=True,
            audit_data_modifications=True,
            # Mandatory IP restrictions
            ip_restrictions_enabled=True,
            # Strict file upload settings
            max_upload_size_mb=2,
            allowed_file_extensions={".pdf", ".txt"},
            scan_uploads_for_malware=True,
            # Highest encryption standards
            encryption_algorithm="AES-256-GCM",
            encrypt_sensitive_data=True,
            tls_version="1.3",
            tls_ciphers=[
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            # No CORS
            enable_cors=False,
        )

        return SecurityProfile(
            name="Government/Federal",
            profile_type=ProfileType.GOVERNMENT,
            description="Maximum security profile for government applications (FISMA/FedRAMP)",
            settings=settings,
            compliance_standards=[
                ComplianceStandard.FISMA,
                ComplianceStandard.FEDRAMP,
            ],
        )

    @staticmethod
    def create_healthcare_profile() -> SecurityProfile:
        """Create a security profile for healthcare applications.

        This profile meets HIPAA compliance requirements for protected health information.

        Returns:
            SecurityProfile configured for healthcare deployment
        """
        settings = SecuritySettings(
            # Strict security headers
            csp_policy="default-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'",
            hsts_max_age=63072000,  # 2 years
            frame_options="DENY",
            # Mandatory CSRF protection
            csrf_enabled=True,
            # Moderate rate limiting
            rate_limit_enabled=True,
            max_requests=50,
            rate_limit_window_seconds=60,
            # Standard session timeout
            session_timeout_minutes=20,
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite="Strict",
            # Strong password policy
            min_password_length=14,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=True,
            password_expiry_days=90,
            password_history_count=6,
            # 2FA for healthcare workers
            require_2fa=True,
            require_2fa_for_roles=set(),  # All users
            # Comprehensive audit logging (HIPAA requirement)
            audit_enabled=True,
            audit_log_retention_days=2555,  # 7 years (HIPAA requirement)
            audit_failed_logins=True,
            audit_data_access=True,
            audit_data_modifications=True,
            # IP restrictions optional
            ip_restrictions_enabled=False,
            # Standard file upload settings
            max_upload_size_mb=20,  # Larger for medical documents
            allowed_file_extensions={
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".dcm",  # DICOM medical images
                ".xml",
                ".hl7",  # HL7 messages
            },
            scan_uploads_for_malware=True,
            # Strong encryption (HIPAA requirement)
            encryption_algorithm="AES-256-GCM",
            encrypt_sensitive_data=True,
            tls_version="1.3",
            tls_ciphers=[
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            # No CORS
            enable_cors=False,
        )

        return SecurityProfile(
            name="Healthcare/HIPAA",
            profile_type=ProfileType.HEALTHCARE,
            description="HIPAA-compliant security profile for healthcare applications",
            settings=settings,
            compliance_standards=[ComplianceStandard.HIPAA],
        )


class CompliancePresets:
    """Factory for creating compliance-specific configurations."""

    @staticmethod
    def get_hipaa_requirements() -> ComplianceRequirements:
        """Get HIPAA compliance requirements.

        Returns:
            ComplianceRequirements for HIPAA
        """
        return ComplianceRequirements(
            standard=ComplianceStandard.HIPAA,
            requirements=[
                "Access Controls: Implement user authentication and authorization",
                "Audit Controls: Record and examine access and activity",
                "Integrity Controls: Protect data from improper alteration/destruction",
                "Transmission Security: Protect data in transit with encryption",
                "Automatic Logoff: Terminate sessions after inactivity",
                "Encryption: Encrypt ePHI at rest and in transit",
                "Audit Logs: Retain audit logs for at least 6 years",
            ],
            mandatory_settings={
                "require_2fa": True,
                "audit_enabled": True,
                "audit_log_retention_days": 2555,  # 7 years to be safe
                "encrypt_sensitive_data": True,
                "session_timeout_minutes": 20,
                "min_password_length": 12,
                "audit_data_access": True,
                "audit_data_modifications": True,
            },
            recommended_settings={
                "tls_version": "1.3",
                "encryption_algorithm": "AES-256-GCM",
                "password_expiry_days": 90,
            },
            documentation_url="https://www.hhs.gov/hipaa/for-professionals/security/",
        )

    @staticmethod
    def get_pci_dss_requirements() -> ComplianceRequirements:
        """Get PCI-DSS compliance requirements.

        Returns:
            ComplianceRequirements for PCI-DSS
        """
        return ComplianceRequirements(
            standard=ComplianceStandard.PCI_DSS,
            requirements=[
                "Install and maintain firewall configuration",
                "Do not use vendor-supplied defaults for passwords",
                "Protect stored cardholder data with encryption",
                "Encrypt transmission of cardholder data across networks",
                "Use and regularly update anti-virus software",
                "Develop and maintain secure systems and applications",
                "Restrict access to cardholder data by business need-to-know",
                "Assign unique ID to each person with computer access",
                "Restrict physical access to cardholder data",
                "Track and monitor all access to network and cardholder data",
                "Regularly test security systems and processes",
                "Maintain information security policy",
            ],
            mandatory_settings={
                "min_password_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True,
                "password_expiry_days": 90,
                "session_timeout_minutes": 15,
                "encrypt_sensitive_data": True,
                "audit_enabled": True,
                "audit_log_retention_days": 365,
                "tls_version": "1.2",  # Minimum TLS 1.2
            },
            recommended_settings={
                "require_2fa": True,
                "ip_restrictions_enabled": True,
                "rate_limit_enabled": True,
            },
            documentation_url="https://www.pcisecuritystandards.org/",
        )

    @staticmethod
    def get_gdpr_requirements() -> ComplianceRequirements:
        """Get GDPR compliance requirements.

        Returns:
            ComplianceRequirements for GDPR
        """
        return ComplianceRequirements(
            standard=ComplianceStandard.GDPR,
            requirements=[
                "Lawful basis for processing personal data",
                "Data minimization: collect only necessary data",
                "Purpose limitation: use data only for stated purposes",
                "Storage limitation: retain data only as long as necessary",
                "Accuracy: keep personal data accurate and up to date",
                "Integrity and confidentiality: secure personal data",
                "Right to access: allow data subjects to access their data",
                "Right to erasure: allow data subjects to delete their data",
                "Right to data portability: export data in machine-readable format",
                "Privacy by design and by default",
                "Data breach notification within 72 hours",
            ],
            mandatory_settings={
                "audit_enabled": True,
                "encrypt_sensitive_data": True,
                "audit_data_access": True,
                "audit_data_modifications": True,
            },
            recommended_settings={
                "min_password_length": 10,
                "session_timeout_minutes": 30,
                "audit_log_retention_days": 365,
            },
            documentation_url="https://gdpr.eu/",
        )

    @staticmethod
    def get_soc2_requirements() -> ComplianceRequirements:
        """Get SOC2 compliance requirements.

        Returns:
            ComplianceRequirements for SOC2
        """
        return ComplianceRequirements(
            standard=ComplianceStandard.SOC2,
            requirements=[
                "Security: Protection against unauthorized access",
                "Availability: System is available for operation and use",
                "Processing Integrity: System processing is complete and accurate",
                "Confidentiality: Confidential information is protected",
                "Privacy: Personal information is collected, used, retained, and disclosed",
                "Access Controls: Logical and physical access controls",
                "Change Management: System changes are authorized and tested",
                "Risk Management: Risks are identified and mitigated",
                "Monitoring: Systems and controls are monitored",
            ],
            mandatory_settings={
                "audit_enabled": True,
                "audit_log_retention_days": 365,
                "min_password_length": 12,
                "require_2fa": True,
                "encrypt_sensitive_data": True,
                "audit_data_access": True,
                "audit_data_modifications": True,
            },
            recommended_settings={
                "session_timeout_minutes": 30,
                "ip_restrictions_enabled": True,
                "rate_limit_enabled": True,
            },
            documentation_url="https://www.aicpa.org/soc",
        )


class ProfileManager:
    """Manager for security profiles with one-click application."""

    def __init__(self) -> None:
        """Initialize profile manager."""
        self._profiles: Dict[str, SecurityProfile] = {}
        self._active_profile: Optional[SecurityProfile] = None
        self._compliance_requirements: Dict[ComplianceStandard, ComplianceRequirements] = {}

        # Load default profiles
        self._load_default_profiles()
        self._load_compliance_requirements()

    def _load_default_profiles(self) -> None:
        """Load predefined security profiles."""
        profiles = [
            ProfileFactory.create_public_profile(),
            ProfileFactory.create_intranet_profile(),
            ProfileFactory.create_government_profile(),
            ProfileFactory.create_healthcare_profile(),
        ]

        for profile in profiles:
            self._profiles[profile.name] = profile

    def _load_compliance_requirements(self) -> None:
        """Load compliance requirements."""
        requirements = [
            CompliancePresets.get_hipaa_requirements(),
            CompliancePresets.get_pci_dss_requirements(),
            CompliancePresets.get_gdpr_requirements(),
            CompliancePresets.get_soc2_requirements(),
        ]

        for req in requirements:
            self._compliance_requirements[req.standard] = req

    def get_profile(self, name: str) -> Optional[SecurityProfile]:
        """Get a security profile by name.

        Args:
            name: Profile name

        Returns:
            SecurityProfile or None if not found
        """
        return self._profiles.get(name)

    def list_profiles(self) -> List[str]:
        """List available security profiles.

        Returns:
            List of profile names
        """
        return list(self._profiles.keys())

    def get_profile_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a profile.

        Args:
            name: Profile name

        Returns:
            Profile details as dictionary or None
        """
        profile = self.get_profile(name)
        if profile:
            return profile.to_dict()
        return None

    def apply_profile(self, name: str) -> Dict[str, Any]:
        """Apply a security profile (one-click application).

        Args:
            name: Profile name

        Returns:
            Application result with settings applied

        Raises:
            ValueError: If profile not found
        """
        profile = self.get_profile(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")

        self._active_profile = profile

        return {
            "success": True,
            "profile": name,
            "profile_type": profile.profile_type.value,
            "description": profile.description,
            "settings_applied": profile.settings.to_dict(),
            "compliance_standards": [s.value for s in profile.compliance_standards],
        }

    def get_active_profile(self) -> Optional[SecurityProfile]:
        """Get currently active security profile.

        Returns:
            Active SecurityProfile or None
        """
        return self._active_profile

    def add_custom_profile(self, profile: SecurityProfile) -> None:
        """Add a custom security profile.

        Args:
            profile: Custom security profile
        """
        self._profiles[profile.name] = profile

    def get_compliance_requirements(
        self, standard: ComplianceStandard
    ) -> Optional[ComplianceRequirements]:
        """Get compliance requirements for a standard.

        Args:
            standard: Compliance standard

        Returns:
            ComplianceRequirements or None
        """
        return self._compliance_requirements.get(standard)

    def validate_profile(self, name: str) -> Dict[str, Any]:
        """Validate a security profile configuration.

        Args:
            name: Profile name

        Returns:
            Validation results
        """
        profile = self.get_profile(name)
        if not profile:
            return {"valid": False, "error": f"Profile '{name}' not found"}

        warnings = []
        errors = []
        recommendations = []

        settings = profile.settings

        # Validate password policy
        if settings.min_password_length < 8:
            errors.append("Password length should be at least 8 characters")
        elif settings.min_password_length < 12:
            warnings.append("Consider increasing minimum password length to 12+ characters")

        # Validate session timeout
        if settings.session_timeout_minutes > 60:
            warnings.append("Session timeout over 60 minutes may pose security risk")

        # Validate HSTS
        if settings.hsts_max_age < 31536000:
            warnings.append("HSTS max-age should be at least 1 year (31536000 seconds)")

        # Validate audit logging
        if not settings.audit_enabled:
            warnings.append("Audit logging should be enabled for security monitoring")

        # Validate 2FA
        if not settings.require_2fa and profile.profile_type in [
            ProfileType.GOVERNMENT,
            ProfileType.HEALTHCARE,
        ]:
            errors.append(f"2FA is required for {profile.profile_type.value} profiles")

        # Validate TLS version
        if settings.tls_version not in ["1.2", "1.3"]:
            errors.append("TLS version should be 1.2 or 1.3")

        # Validate compliance requirements
        for standard in profile.compliance_standards:
            req = self.get_compliance_requirements(standard)
            if req:
                for key, value in req.mandatory_settings.items():
                    actual_value = getattr(settings, key, None)
                    # For numeric values, check if actual is equal or stronger
                    if key in [
                        "min_password_length",
                        "audit_log_retention_days",
                        "password_history_count",
                    ]:
                        if actual_value < value:
                            errors.append(
                                f"{standard.value} requires {key}>={value}, got {actual_value}"
                            )
                    elif key == "session_timeout_minutes":
                        # Session timeout should be equal or shorter (more secure)
                        if actual_value > value:
                            errors.append(
                                f"{standard.value} requires {key}<={value}, got {actual_value}"
                            )
                    elif actual_value != value:
                        errors.append(
                            f"{standard.value} requires {key}={value}, got {actual_value}"
                        )

                for key, value in req.recommended_settings.items():
                    actual_value = getattr(settings, key, None)
                    if actual_value != value:
                        recommendations.append(
                            f"{standard.value} recommends {key}={value}, current is {actual_value}"
                        )

        return {
            "valid": len(errors) == 0,
            "profile": name,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
        }

    def compare_profiles(self, profile1: str, profile2: str) -> Dict[str, Any]:
        """Compare two security profiles.

        Args:
            profile1: First profile name
            profile2: Second profile name

        Returns:
            Comparison results

        Raises:
            ValueError: If either profile not found
        """
        p1 = self.get_profile(profile1)
        p2 = self.get_profile(profile2)

        if not p1:
            raise ValueError(f"Profile '{profile1}' not found")
        if not p2:
            raise ValueError(f"Profile '{profile2}' not found")

        differences = []
        s1 = p1.settings.to_dict()
        s2 = p2.settings.to_dict()

        all_keys = set(s1.keys()) | set(s2.keys())
        for key in sorted(all_keys):
            val1 = s1.get(key)
            val2 = s2.get(key)
            if val1 != val2:
                differences.append({"setting": key, profile1: val1, profile2: val2})

        return {
            "profile1": profile1,
            "profile2": profile2,
            "differences": differences,
            "total_differences": len(differences),
        }

    def export_profile(self, name: str) -> str:
        """Export a profile as JSON.

        Args:
            name: Profile name

        Returns:
            JSON string

        Raises:
            ValueError: If profile not found
        """
        profile = self.get_profile(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")

        return profile.to_json()

    def import_profile(self, json_str: str) -> SecurityProfile:
        """Import a profile from JSON.

        Args:
            json_str: JSON string

        Returns:
            Imported SecurityProfile

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            settings_dict = data["settings"]

            # Convert lists back to sets for certain fields
            set_fields = [
                "csrf_exempt_paths",
                "rate_limit_exempt_paths",
                "require_2fa_for_roles",
                "ip_whitelist",
                "ip_blacklist",
                "allowed_file_extensions",
                "cors_allowed_origins",
            ]
            for field in set_fields:
                if field in settings_dict and isinstance(settings_dict[field], list):
                    settings_dict[field] = set(settings_dict[field])

            settings = SecuritySettings(**settings_dict)
            profile = SecurityProfile(
                name=data["name"],
                profile_type=ProfileType(data["profile_type"]),
                description=data["description"],
                settings=settings,
                compliance_standards=[
                    ComplianceStandard(s) for s in data.get("compliance_standards", [])
                ],
            )

            self._profiles[profile.name] = profile
            return profile

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid profile JSON: {e}")


# Global profile manager instance
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get global profile manager instance.

    Returns:
        ProfileManager instance
    """
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager
